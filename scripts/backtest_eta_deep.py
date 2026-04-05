"""Deep-dive experiments: next-sailing delay prediction approaches.

Compares flat propagation, ETA+turnaround, and hybrid approaches
on sea-bi and ed-king routes.

Usage:
    uv run python -m scripts.backtest_eta_deep
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from backend.database import get_connection, init_db

logger = logging.getLogger(__name__)

ROUTES = ["sea-bi", "ed-king"]
CROSSING_TIME = {"sea-bi": 35, "ed-king": 25}  # approximate minutes


# ---------------------------------------------------------------------------
# Data loading (shared across all experiments)
# ---------------------------------------------------------------------------


def load_experiment_data(conn: sqlite3.Connection) -> pd.DataFrame:
    """Load and prepare all data needed for experiments.

    Returns a DataFrame with one row per (sailing, best-ETA snapshot),
    containing: current sailing info, sane ETA, next sailing info,
    and actual turnaround time.
    """
    # --- Sailing events ---
    events = pd.read_sql_query(
        """
        SELECT id as event_id, vessel_id, vessel_name, route_abbrev,
               departing_terminal_id, arriving_terminal_id,
               scheduled_departure, actual_departure, delay_minutes,
               day_of_week, hour_of_day
        FROM sailing_events
        WHERE route_abbrev IN ('sea-bi', 'ed-king')
          AND arriving_terminal_id IS NOT NULL
        ORDER BY scheduled_departure
        """,
        conn,
    )
    events["actual_departure"] = pd.to_datetime(
        events["actual_departure"], format="ISO8601", utc=True
    )
    events["scheduled_departure"] = pd.to_datetime(
        events["scheduled_departure"], format="ISO8601", utc=True
    )
    events["arriving_terminal_id"] = events["arriving_terminal_id"].astype("Int64")
    logger.info(f"Loaded {len(events)} sailing events")

    # --- Derive actual arrivals via merge_asof ---
    dock_df = pd.read_sql_query(
        """
        SELECT vessel_id, collected_at,
               departing_terminal_id as arriving_terminal_id
        FROM vessel_snapshots WHERE at_dock = 1
        ORDER BY vessel_id, collected_at
        """,
        conn,
    )
    dock_df["collected_at"] = pd.to_datetime(
        dock_df["collected_at"], format="ISO8601", utc=True
    )
    dock_df["arriving_terminal_id"] = dock_df["arriving_terminal_id"].astype("Int64")

    dock_groups = dock_df.groupby(["vessel_id", "arriving_terminal_id"])
    arrival_results = []
    for key, ev_group in events.groupby(["vessel_id", "arriving_terminal_id"]):
        ev_sorted = ev_group.sort_values("actual_departure")
        if key not in dock_groups.groups:
            ev_sorted = ev_sorted.copy()
            ev_sorted["actual_arrival"] = pd.NaT
            arrival_results.append(ev_sorted)
            continue
        dk = (
            dock_df.loc[dock_groups.groups[key]]
            .sort_values("collected_at")[["collected_at"]]
            .rename(columns={"collected_at": "actual_arrival"})
        )
        arrival_results.append(
            pd.merge_asof(
                ev_sorted,
                dk,
                left_on="actual_departure",
                right_on="actual_arrival",
                direction="forward",
                tolerance=pd.Timedelta(minutes=90),
            )
        )
    events = pd.concat(arrival_results, ignore_index=True).sort_values(
        "scheduled_departure"
    )
    n_with = events["actual_arrival"].notna().sum()
    logger.info(
        f"Derived {n_with}/{len(events)} arrivals ({n_with / len(events) * 100:.0f}%)"
    )

    # --- Build next-sailing chain (same vessel, consecutive) ---
    events_arr = events.dropna(subset=["actual_arrival"]).sort_values(
        ["vessel_id", "scheduled_departure"]
    )
    next_rows = []
    for _vid, grp in events_arr.groupby("vessel_id"):
        grp = grp.reset_index(drop=True)
        for i in range(len(grp) - 1):
            curr = grp.loc[i]
            nxt = grp.loc[i + 1]
            gap = (
                nxt["actual_departure"] - curr["actual_arrival"]
            ).total_seconds() / 60
            if gap < 5 or gap > 60:
                continue
            next_rows.append(
                {
                    "event_id": curr["event_id"],
                    "next_sched": nxt["scheduled_departure"],
                    "next_actual_dep": nxt["actual_departure"],
                    "next_delay": float(nxt["delay_minutes"]),
                    "actual_turnaround": gap,
                    "current_delay": float(curr["delay_minutes"]),
                }
            )
    next_df = pd.DataFrame(next_rows)
    logger.info(f"Built {len(next_df)} next-sailing pairs")

    # --- En-route snapshots with ETA ---
    enroute = pd.read_sql_query(
        """
        SELECT vessel_id, collected_at, eta, scheduled_departure, speed
        FROM vessel_snapshots
        WHERE at_dock = 0 AND eta IS NOT NULL AND eta != ''
          AND route_abbrev IN ('sea-bi', 'ed-king')
        ORDER BY vessel_id, collected_at
        """,
        conn,
    )
    enroute["collected_at"] = pd.to_datetime(
        enroute["collected_at"], format="ISO8601", utc=True
    )
    enroute["eta"] = pd.to_datetime(enroute["eta"], format="ISO8601", utc=True)
    enroute["scheduled_departure"] = pd.to_datetime(
        enroute["scheduled_departure"], format="ISO8601", utc=True
    )

    arrivals = events[
        [
            "event_id",
            "vessel_id",
            "scheduled_departure",
            "actual_arrival",
            "route_abbrev",
            "delay_minutes",
            "vessel_name",
            "actual_departure",
        ]
    ].dropna(subset=["actual_arrival"])

    merged = enroute.merge(
        arrivals, on=["vessel_id", "scheduled_departure"], how="inner"
    )
    merged["mins_to_arrival"] = (
        merged["actual_arrival"] - merged["collected_at"]
    ).dt.total_seconds() / 60
    merged = merged[merged["mins_to_arrival"] > 0]

    # Sanity filter
    merged["eta_mins_from_now"] = (
        merged["eta"] - merged["collected_at"]
    ).dt.total_seconds() / 60
    merged["max_reasonable"] = merged["route_abbrev"].map(CROSSING_TIME) * 2.0
    merged["eta_sane"] = (merged["eta_mins_from_now"] > 0) & (
        merged["eta_mins_from_now"] <= merged["max_reasonable"]
    )
    n_sane = merged["eta_sane"].sum()
    logger.info(
        f"ETA sanity: {n_sane}/{len(merged)} sane ({n_sane / len(merged) * 100:.1f}%)"
    )

    # Last sane snapshot per event (best ETA)
    sane = merged[merged["eta_sane"]].sort_values("collected_at")
    best_eta = sane.groupby("event_id").last().reset_index()

    result = best_eta.merge(next_df, on="event_id", how="inner")
    logger.info(f"Final dataset: {len(result)} prediction opportunities")
    return result


# ---------------------------------------------------------------------------
# Prediction strategies
# ---------------------------------------------------------------------------


def predict_flat(row: pd.Series) -> float:
    """Flat propagation: next delay = current delay."""
    return row["current_delay"]


def predict_eta_ta(row: pd.Series, turnaround: float) -> float:
    """ETA + fixed turnaround."""
    eta_plus_ta = row["eta"] + timedelta(minutes=turnaround)
    next_sched = row["next_sched"]
    if eta_plus_ta > next_sched:
        return (eta_plus_ta - next_sched).total_seconds() / 60
    return 0.0


def predict_clamped(row: pd.Series, min_turnaround: float) -> float:
    """Physics-clamped flat: max(flat_delay, ETA-implied floor)."""
    flat = row["current_delay"]
    eta_floor = predict_eta_ta(row, min_turnaround)
    return max(flat, eta_floor)


def predict_blend(row: pd.Series, turnaround: float, crossing_time: float) -> float:
    """Weighted blend: interpolate flat→ETA as crossing progresses."""
    flat = row["current_delay"]
    eta_based = predict_eta_ta(row, turnaround)
    elapsed = (row["collected_at"] - row["actual_departure"]).total_seconds() / 60
    progress = min(1.0, max(0.0, elapsed / crossing_time))
    return (1 - progress) * flat + progress * eta_based


def predict_smart_clamp(row: pd.Series, min_ta: float, max_ta: float) -> float:
    """Floor + ceiling: clamp flat between physical bounds."""
    flat = row["current_delay"]
    eta_floor = predict_eta_ta(row, min_ta)
    eta_ceiling = predict_eta_ta(row, max_ta)
    return max(eta_floor, min(flat, eta_ceiling))


def predict_conditional_ceiling(
    row: pd.Series, min_ta: float, max_ta: float, threshold: float
) -> float:
    """Floor always, ceiling only when current delay exceeds threshold."""
    flat = row["current_delay"]
    eta_floor = predict_eta_ta(row, min_ta)
    if flat > threshold:
        eta_ceiling = predict_eta_ta(row, max_ta)
        return max(eta_floor, min(flat, eta_ceiling))
    return max(flat, eta_floor)


def predict_late_eta_override(
    row: pd.Series,
    min_ta: float,
    max_ta: float,
    crossing_time: float,
    delay_threshold: float = 10.0,
    progress_threshold: float = 0.7,
) -> float:
    """Use ETA-based prediction near end of crossing for large delays.

    Early crossing: clamped flat (floor only).
    Late crossing + large delay: ETA + median turnaround.
    Always: physics floor (p10 turnaround).
    """
    flat = row["current_delay"]
    eta_floor = predict_eta_ta(row, min_ta)
    elapsed = (row["collected_at"] - row["actual_departure"]).total_seconds() / 60
    progress = min(1.0, max(0.0, elapsed / crossing_time))

    if progress >= progress_threshold and flat > delay_threshold:
        eta_pred = predict_eta_ta(row, max_ta)
        return max(eta_floor, eta_pred)
    return max(flat, eta_floor)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def evaluate(df: pd.DataFrame, predictions: pd.Series, label: str) -> dict:
    """Evaluate predictions against actual next-sailing delays."""
    errors = predictions - df["next_delay"]
    abs_errors = errors.abs()

    metrics = {
        "label": label,
        "n": len(df),
        "mae": round(float(abs_errors.mean()), 2),
        "bias": round(float(errors.mean()), 2),
        "within_3": round(float((abs_errors <= 3).mean() * 100), 1),
        "within_5": round(float((abs_errors <= 5).mean() * 100), 1),
        "missed_delay": round(float((errors < -5).mean() * 100), 1),
        "big_overpred": round(float((errors > 10).mean() * 100), 1),
        "p5": round(float(errors.quantile(0.05)), 1),
        "p95": round(float(errors.quantile(0.95)), 1),
    }

    # Howler: predicted departure before ETA + p10 turnaround
    min_ta = df["route_abbrev"].map({"sea-bi": 9.3, "ed-king": 14.8})
    pred_dep = df["next_sched"] + pd.to_timedelta(predictions, unit="m")
    earliest = df["eta"] + pd.to_timedelta(min_ta, unit="m")
    howlers = pred_dep < earliest
    metrics["howler_pct"] = round(float(howlers.mean() * 100), 1)
    metrics["howler_n"] = int(howlers.sum())

    return metrics


def eval_buckets(df: pd.DataFrame, predictions: pd.Series, label: str) -> dict:
    """Evaluate overall + by route + by delay bucket."""
    out = {"overall": evaluate(df, predictions, label)}
    for route in ROUTES:
        m = df["route_abbrev"] == route
        if m.sum():
            out[route] = evaluate(df[m], predictions[m], f"{label} ({route})")
    for name, lo, hi in [
        ("on_time", -999, 1),
        ("minor", 1, 5),
        ("moderate", 5, 15),
        ("major", 15, 999),
    ]:
        m = (df["next_delay"] >= lo) & (df["next_delay"] < hi)
        if m.sum():
            out[name] = evaluate(df[m], predictions[m], f"{label} ({name})")
    return out


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------


def run_experiments(df: pd.DataFrame) -> list[dict]:
    """Run all prediction experiments."""
    ta_p10 = {"sea-bi": 9.3, "ed-king": 14.8}
    ta_med = {"sea-bi": 16.8, "ed-king": 21.4}
    ta_p75 = {"sea-bi": 22.0, "ed-king": 26.0}
    crossing = {"sea-bi": 35.0, "ed-king": 25.0}

    strategies = [
        ("Flat propagation", lambda r: predict_flat(r)),
        ("Clamped (p10 TA)", lambda r: predict_clamped(r, ta_p10[r["route_abbrev"]])),
        (
            "Cond ceil p75 (>10)",
            lambda r: predict_conditional_ceiling(
                r, ta_p10[r["route_abbrev"]], ta_p75[r["route_abbrev"]], 10.0
            ),
        ),
        (
            "Late ETA (70%/>10)",
            lambda r: predict_late_eta_override(
                r,
                ta_p10[r["route_abbrev"]],
                ta_med[r["route_abbrev"]],
                crossing[r["route_abbrev"]],
                10.0,
                0.7,
            ),
        ),
        (
            "Late ETA (50%/>10)",
            lambda r: predict_late_eta_override(
                r,
                ta_p10[r["route_abbrev"]],
                ta_med[r["route_abbrev"]],
                crossing[r["route_abbrev"]],
                10.0,
                0.5,
            ),
        ),
        (
            "Late ETA p75 (70%/>10)",
            lambda r: predict_late_eta_override(
                r,
                ta_p10[r["route_abbrev"]],
                ta_p75[r["route_abbrev"]],
                crossing[r["route_abbrev"]],
                10.0,
                0.7,
            ),
        ),
        (
            "Late ETA p75 (50%/>10)",
            lambda r: predict_late_eta_override(
                r,
                ta_p10[r["route_abbrev"]],
                ta_p75[r["route_abbrev"]],
                crossing[r["route_abbrev"]],
                10.0,
                0.5,
            ),
        ),
    ]

    experiments = []
    for name, fn in strategies:
        preds = df.apply(fn, axis=1)
        results = eval_buckets(df, preds, name)
        experiments.append({"name": name, "results": results})
        o = results["overall"]
        logger.info(
            f"{name}: MAE={o['mae']} bias={o['bias']:+.1f} "
            f"±3={o['within_3']}% howlers={o['howler_n']}"
        )

    return experiments


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def generate_report(experiments: list[dict], df: pd.DataFrame) -> str:
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append("# ETA Deep Dive: Next-Sailing Prediction Experiments")
    lines.append("")
    lines.append(f"**Date:** {now}  ")
    lines.append(f"**Routes:** {', '.join(ROUTES)}  ")
    lines.append(f"**Prediction pairs:** {len(df)}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append("| Experiment | MAE | Bias | ±3min | ±5min | Missed | Howlers |")
    lines.append("|---|---|---|---|---|---|---|")
    for exp in experiments:
        o = exp["results"]["overall"]
        lines.append(
            f"| **{o['label']}** | {o['mae']} | {o['bias']:+.1f} | "
            f"{o['within_3']}% | {o['within_5']}% | "
            f"{o['missed_delay']}% | {o['howler_n']} ({o['howler_pct']}%) |"
        )
    lines.append("")

    # By route
    for route in ROUTES:
        lines.append(f"### {route}")
        lines.append("")
        lines.append("| Experiment | MAE | Bias | ±3min | Howlers |")
        lines.append("|---|---|---|---|---|")
        for exp in experiments:
            r = exp["results"].get(route)
            if r:
                lines.append(
                    f"| {r['label']} | {r['mae']} | {r['bias']:+.1f} | "
                    f"{r['within_3']}% | {r['howler_n']} |"
                )
        lines.append("")

    # By delay bucket
    lines.append("## By Actual Next-Sailing Delay")
    lines.append("")
    for bkt, label in [
        ("on_time", "On-time (≤1)"),
        ("minor", "Minor (1–5)"),
        ("moderate", "Moderate (5–15)"),
        ("major", "Major (15+)"),
    ]:
        lines.append(f"### {label}")
        lines.append("")
        lines.append("| Experiment | MAE | Bias | ±5min |")
        lines.append("|---|---|---|---|")
        for exp in experiments:
            r = exp["results"].get(bkt)
            if r:
                lines.append(
                    f"| {r['label']} | {r['mae']} | {r['bias']:+.1f} | {r['within_5']}% |"
                )
        lines.append("")

    # Howler analysis
    lines.append("## Howler Analysis")
    lines.append("")
    lines.append(
        "A **howler** is when we predict the boat will depart before the "
        "inbound vessel can physically arrive and turn around (ETA + p10 turnaround)."
    )
    lines.append("")
    flat = experiments[0]["results"]["overall"]
    lines.append(
        f"Flat propagation produces **{flat['howler_n']} howlers** "
        f"out of {flat['n']} predictions ({flat['howler_pct']}%)."
    )
    lines.append("")
    for exp in experiments:
        o = exp["results"]["overall"]
        if o["howler_n"] == 0:
            lines.append(f"- **{o['label']}**: zero howlers ✓")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    init_db()

    conn = get_connection()
    df = load_experiment_data(conn)
    conn.close()

    experiments = run_experiments(df)

    report = generate_report(experiments, df)

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = (
        reports_dir / f"eta_deep_dive_{datetime.now().strftime('%Y-%m-%d')}.md"
    )
    report_path.write_text(report)

    print(f"\nReport saved to: {report_path}")
    print(report)


if __name__ == "__main__":
    main()
