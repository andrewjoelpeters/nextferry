"""Analyze predictions vs actuals to find outlier predictions.

Reconstructs predictions from vessel snapshots at various time horizons
before each sailing, using the same logic as production:
  - Flat propagation (copy current delay forward)
  - Option A / ETA-bounded (for en-route vessels with ETA)
  - Re-propagation (later sailings inherit ETA-bounded prediction)

Usage:
    # Analyze last 2 weeks
    uv run python -m scripts.analyze_prediction_outliers

    # Custom date range
    uv run python -m scripts.analyze_prediction_outliers --start 2026-03-01 --end 2026-03-08

    # Specific route only
    uv run python -m scripts.analyze_prediction_outliers --routes sea-bi
"""

import argparse
import logging
import sqlite3
from datetime import datetime, timedelta

import pandas as pd

from backend.database import get_connection, init_db

logger = logging.getLogger(__name__)

ROUTES = ["sea-bi", "ed-king"]
CROSSING_TIME = {"sea-bi": 35, "ed-king": 25}
P10_TA = {"sea-bi": 9.3, "ed-king": 14.8}
P75_TA = {"sea-bi": 22.0, "ed-king": 26.0}
CEILING_THRESHOLD = 4

# Time points before scheduled departure to sample predictions
PREDICTION_HORIZONS = [5, 10, 15, 20, 30, 45, 60]

# Prediction mode: False = flat propagation (current production), True = ETA-bounded (old)
OPTION_A_MODE = False


# ---------------------------------------------------------------------------
# Production prediction logic (matches next_sailings.py)
# ---------------------------------------------------------------------------


def predict_option_a(current_delay: float, eta, next_sched, route: str) -> float:
    """ETA-bounded prediction (Option A)."""
    p10 = P10_TA.get(route)
    p75 = P75_TA.get(route)
    if p10 is None or p75 is None:
        return current_delay

    eta_floor_t = eta + timedelta(minutes=p10)
    floor = max(0.0, (eta_floor_t - next_sched).total_seconds() / 60)

    if current_delay > CEILING_THRESHOLD:
        eta_ceil_t = eta + timedelta(minutes=p75)
        ceiling = max(0.0, (eta_ceil_t - next_sched).total_seconds() / 60)
        return max(floor, min(current_delay, ceiling))
    return max(current_delay, floor)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_data(
    conn: sqlite3.Connection,
    start_date: str,
    end_date: str,
    routes: list[str],
) -> dict:
    """Load sailing events and vessel snapshots for the date range."""
    route_filter = ",".join(f"'{r}'" for r in routes)

    # Sailing events (ground truth)
    events = pd.read_sql_query(
        f"""
        SELECT id as event_id, vessel_id, vessel_name, route_abbrev,
               departing_terminal_id, arriving_terminal_id,
               scheduled_departure, actual_departure, delay_minutes,
               day_of_week, hour_of_day
        FROM sailing_events
        WHERE route_abbrev IN ({route_filter})
          AND arriving_terminal_id IS NOT NULL
          AND scheduled_departure >= ?
          AND scheduled_departure < ?
        ORDER BY vessel_id, scheduled_departure
        """,
        conn,
        params=(start_date, end_date),
    )
    for col in ["actual_departure", "scheduled_departure"]:
        events[col] = pd.to_datetime(events[col], format="ISO8601", utc=True)
    events["arriving_terminal_id"] = events["arriving_terminal_id"].astype("Int64")

    logger.info(f"Loaded {len(events)} sailing events")

    # Derive actual arrivals via merge_asof on dock snapshots
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
    arrival_parts = []
    for key, ev_group in events.groupby(["vessel_id", "arriving_terminal_id"]):
        ev_sorted = ev_group.sort_values("actual_departure")
        if key not in dock_groups.groups:
            ev_sorted = ev_sorted.copy()
            ev_sorted["actual_arrival"] = pd.NaT
            arrival_parts.append(ev_sorted)
            continue
        dk = (
            dock_df.loc[dock_groups.groups[key]]
            .sort_values("collected_at")[["collected_at"]]
            .rename(columns={"collected_at": "actual_arrival"})
        )
        arrival_parts.append(
            pd.merge_asof(
                ev_sorted,
                dk,
                left_on="actual_departure",
                right_on="actual_arrival",
                direction="forward",
                tolerance=pd.Timedelta(minutes=90),
            )
        )
    events = pd.concat(arrival_parts, ignore_index=True).sort_values(
        "scheduled_departure"
    )
    n_arrived = events["actual_arrival"].notna().sum()
    logger.info(f"Derived {n_arrived}/{len(events)} actual arrivals")

    # Vessel snapshots (for prediction reconstruction)
    snapshots = pd.read_sql_query(
        f"""
        SELECT vessel_id, collected_at, at_dock, left_dock, eta,
               scheduled_departure, speed, departing_terminal_id,
               arriving_terminal_id, route_abbrev
        FROM vessel_snapshots
        WHERE route_abbrev IN ({route_filter})
          AND collected_at >= ?
          AND collected_at < ?
        ORDER BY vessel_id, collected_at
        """,
        conn,
        params=(start_date, end_date),
    )
    for col in ["collected_at", "left_dock", "eta", "scheduled_departure"]:
        snapshots[col] = pd.to_datetime(
            snapshots[col], format="ISO8601", utc=True, errors="coerce"
        )
    snapshots["departing_terminal_id"] = snapshots["departing_terminal_id"].astype(
        "Int64"
    )
    snapshots["arriving_terminal_id"] = snapshots["arriving_terminal_id"].astype(
        "Int64"
    )

    # Add sailing space snapshots
    space = pd.read_sql_query(
        """
        SELECT departing_terminal_id, arriving_terminal_id, departure_time,
               collected_at, max_space_count, drive_up_space_count
        FROM sailing_space_snapshots
        WHERE max_space_count > 0
        ORDER BY departing_terminal_id, collected_at
        """,
        conn,
    )
    if not space.empty:
        space["collected_at"] = pd.to_datetime(
            space["collected_at"], format="ISO8601", utc=True
        )
        space["departure_time"] = pd.to_datetime(
            space["departure_time"], format="ISO8601", utc=True
        )

    logger.info(f"Loaded {len(snapshots)} vessel snapshots")
    return {
        "events": events,
        "snapshots": snapshots,
        "space": space,
    }


# ---------------------------------------------------------------------------
# Build sailing chains per vessel
# ---------------------------------------------------------------------------


def build_vessel_chains(events: pd.DataFrame) -> pd.DataFrame:
    """Build consecutive sailing chains per vessel.

    Returns one row per chain with s0, s1, s2 columns identifying
    consecutive sailings.
    """
    ev = events.dropna(subset=["actual_arrival"]).sort_values(
        ["vessel_id", "scheduled_departure"]
    )
    chains = []
    for _vid, grp in ev.groupby("vessel_id"):
        grp = grp.reset_index(drop=True)
        for i in range(len(grp) - 1):
            curr = grp.loc[i]
            nxt = grp.loc[i + 1]
            gap = (
                nxt["actual_departure"] - curr["actual_arrival"]
            ).total_seconds() / 60
            if gap < 5 or gap > 60:
                continue

            is_same_route = curr["route_abbrev"] == nxt["route_abbrev"]
            if not is_same_route:
                continue

            chains.append(
                {
                    "vessel_id": curr["vessel_id"],
                    "vessel_name": curr["vessel_name"],
                    "route": curr["route_abbrev"],
                    "s0_event_id": curr["event_id"],
                    "s0_sched": curr["scheduled_departure"],
                    "s0_actual_dep": curr["actual_departure"],
                    "s0_actual_arrival": curr["actual_arrival"],
                    "s0_delay": float(curr["delay_minutes"]),
                    "s0_dep_terminal": int(curr["departing_terminal_id"]),
                    "s0_arr_terminal": int(curr["arriving_terminal_id"]),
                    "s1_event_id": nxt["event_id"],
                    "s1_sched": nxt["scheduled_departure"],
                    "s1_actual_dep": nxt["actual_departure"],
                    "s1_delay": float(nxt["delay_minutes"]),
                    "s1_dep_terminal": int(nxt["departing_terminal_id"]),
                    "s1_arr_terminal": int(nxt["arriving_terminal_id"]),
                }
            )

    df = pd.DataFrame(chains)
    logger.info(f"Built {len(df)} sailing chains")
    return df


# ---------------------------------------------------------------------------
# Reconstruct predictions from snapshots
# ---------------------------------------------------------------------------


def reconstruct_predictions(
    chains: pd.DataFrame,
    snapshots: pd.DataFrame,
    horizons: list[int] | None = None,
) -> pd.DataFrame:
    """For each chain, reconstruct what we would have predicted at each horizon.

    At each prediction time (various minutes before s1's scheduled departure),
    looks at the vessel's state and applies production prediction logic.
    """
    records = []

    for _, chain in chains.iterrows():
        s1_sched = chain["s1_sched"]
        vessel_id = int(chain["vessel_id"])
        route = chain["route"]
        s0_arr_terminal = int(chain["s0_arr_terminal"])
        s1_dep_terminal = int(chain["s1_dep_terminal"])

        # Find snapshots for this vessel before s1_sched
        vessel_snaps = snapshots[
            (snapshots["vessel_id"] == vessel_id)
            & (snapshots["collected_at"] < s1_sched)
        ].sort_values("collected_at")

        if vessel_snaps.empty:
            continue

        # Check if s1 is opposite terminal from s0 (i.e., Option A applies)
        s1_is_opposite = s1_dep_terminal == s0_arr_terminal

        # For each horizon, find the nearest snapshot
        for horizon_min in horizons or PREDICTION_HORIZONS:
            prediction_time = s1_sched - timedelta(minutes=horizon_min)

            # Find the snapshot closest to (but not after) prediction_time
            nearby = vessel_snaps[vessel_snaps["collected_at"] <= prediction_time]
            if nearby.empty:
                continue
            snap = nearby.iloc[-1]
            snap_time = snap["collected_at"]

            # Compute current delay from snapshot
            current_delay = _compute_delay_from_snapshot(snap, route)

            if current_delay is None:
                continue

            # Determine prediction
            is_en_route = bool(snap["at_dock"] == 0)
            has_eta = pd.notna(snap["eta"]) and snap["eta"] != ""

            # Flat propagation is the default (matches current production).
            # When --option-a is given, compare with ETA-bounded logic.
            use_option_a = is_en_route and has_eta and s1_is_opposite

            if use_option_a and OPTION_A_MODE:
                pred_delay = predict_option_a(
                    current_delay, snap["eta"], s1_sched, route
                )
                pred_source = "eta_bounded"
            else:
                pred_delay = current_delay
                pred_source = "flat_propagation"

            # Compute error
            actual_delay = chain["s1_delay"]
            error = pred_delay - actual_delay
            abs_error = abs(error)

            # Howler check (only meaningful for ETA-bounded predictions)
            howler = False
            if use_option_a and OPTION_A_MODE:
                earliest_dep = snap["eta"] + timedelta(minutes=P10_TA[route])
                pred_dep = s1_sched + timedelta(minutes=pred_delay)
                howler = bool(pred_dep < earliest_dep)

            # Time from prediction to actual departure
            mins_to_dep = (s1_sched - snap_time).total_seconds() / 60

            records.append(
                {
                    "vessel_id": vessel_id,
                    "vessel_name": chain["vessel_name"],
                    "route": route,
                    "s0_sched": chain["s0_sched"],
                    "s0_delay": round(chain["s0_delay"], 1),
                    "s1_sched": s1_sched,
                    "s1_actual_dep": chain["s1_actual_dep"],
                    "prediction_time": snap_time,
                    "horizon_minutes": horizon_min,
                    "actual_horizon": round(mins_to_dep, 0),
                    "current_delay": round(current_delay, 1),
                    "predicted_delay": round(pred_delay, 0),
                    "actual_delay": round(actual_delay, 1),
                    "error": round(error, 1),
                    "abs_error": round(abs_error, 1),
                    "pred_source": pred_source,
                    "howler": howler,
                    "snap_at_dock": bool(snap["at_dock"]),
                    "snap_has_eta": bool(has_eta),
                    "snap_has_left_dock": bool(pd.notna(snap["left_dock"])),
                }
            )

    return pd.DataFrame(records)


def _compute_delay_from_snapshot(snap: pd.Series, route: str) -> float | None:
    """Compute observed vessel delay from a snapshot.

    Priority:
    1. If left_dock is set: delay = left_dock - scheduled_departure
    2. If at_dock and overdue: delay = collected_at - scheduled_departure
    """
    sched = snap.get("scheduled_departure")
    left = snap.get("left_dock")
    at_dock = snap.get("at_dock", 0)
    collected = snap["collected_at"]

    if pd.notna(left) and pd.notna(sched):
        delay = (left - sched).total_seconds() / 60
        if delay >= 0:
            return delay

    if at_dock and pd.notna(sched):
        mins_past = (collected - sched).total_seconds() / 60
        if mins_past > 0:
            return mins_past

    return 0.0


# ---------------------------------------------------------------------------
# Outlier detection and reporting
# ---------------------------------------------------------------------------


def find_outliers(df: pd.DataFrame, top_n: int = 50) -> pd.DataFrame:
    """Find the worst predictions within each horizon."""
    if df.empty:
        return df
    outliers = (
        df.sort_values("abs_error", ascending=False)
        .groupby("horizon_minutes")
        .head(top_n)
        .reset_index(drop=True)
    )
    return outliers.sort_values(
        ["horizon_minutes", "abs_error"], ascending=[True, False]
    )


def generate_report(
    predictions: pd.DataFrame,
    df_chains: pd.DataFrame,
    start_date: str,
    end_date: str,
    routes: list[str],
    horizons: list[int] | None = None,
) -> str:
    """Generate a markdown report with outlier analysis."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Prediction Outlier Analysis",
        "",
        f"**Generated:** {now}",
        f"**Period:** {start_date} to {end_date}",
        f"**Routes:** {', '.join(routes)}",
        f"**Chains analyzed:** {len(df_chains)}",
        f"**Prediction samples:** {len(predictions)}",
        "",
    ]

    if predictions.empty:
        lines.append("No predictions found for this period.")
        return "\n".join(lines)

    # === Summary by horizon ===
    lines.append("## Summary by Prediction Horizon")
    lines.append("")
    lines.append(
        "| Horizon | Samples | MAE | Bias | ±3min | ±5min | "
        "Missed (>5) | Howlers | Top Error |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")

    active_horizons = horizons or PREDICTION_HORIZONS
    for h in active_horizons:
        subset = predictions[predictions["horizon_minutes"] == h]
        if subset.empty:
            continue
        errors = subset["error"]
        abs_errors = subset["abs_error"]
        lines.append(
            f"| {h}m | {len(subset)} | "
            f"{abs_errors.mean():.1f} | {errors.mean():+.1f} | "
            f"{(abs_errors <= 3).mean() * 100:.0f}% | "
            f"{(abs_errors <= 5).mean() * 100:.0f}% | "
            f"{(errors < -5).mean() * 100:.0f}% | "
            f"{subset['howler'].sum()} | "
            f"{subset.loc[abs_errors.idxmax(), 'error']:+.1f} |"
        )
    lines.append("")

    # === By route ===
    for route in routes:
        lines.append(f"### {route}")
        lines.append("")
        r_df = predictions[predictions["route"] == route]
        if r_df.empty:
            lines.append("No predictions.")
            lines.append("")
            continue
        lines.append("| Horizon | Samples | MAE | Bias | ±3min | Howlers |")
        lines.append("|---|---|---|---|---|---|")
        active_horizons = horizons or PREDICTION_HORIZONS
        for h in active_horizons:
            s = r_df[r_df["horizon_minutes"] == h]
            if s.empty:
                continue
            lines.append(
                f"| {h}m | {len(s)} | "
                f"{s['abs_error'].mean():.1f} | {s['error'].mean():+.1f} | "
                f"{(s['abs_error'] <= 3).mean() * 100:.0f}% | "
                f"{s['howler'].sum()} |"
            )
        lines.append("")

    # === Outliers (worst predictions) ===
    lines.append("## Worst Predictions (Top 50 by Absolute Error)")
    lines.append("")
    worst = predictions.sort_values("abs_error", ascending=False).head(50)
    lines.append(
        "| # | Date | Route | Vessel | Horizon | Predicted | Actual | Error | Source | Howler |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for i, (_, row) in enumerate(worst.iterrows(), 1):
        date_str = row["s1_sched"].strftime("%m/%d %H:%M")
        lines.append(
            f"| {i} | {date_str} | {row['route']} | {row['vessel_name']} | "
            f"{int(row['horizon_minutes'])}m | "
            f"{int(row['predicted_delay'])}m | {row['actual_delay']:.0f}m | "
            f"{row['error']:+.0f}m | {row['pred_source'][:8]} | "
            f"{'🚨' if row['howler'] else ''} |"
        )
    lines.append("")

    # === Howler analysis ===
    howlers = predictions[predictions["howler"]]
    lines.append("## Howler Analysis")
    lines.append("")
    lines.append(
        "A howler is when we predicted the ferry would depart before the "
        "inbound vessel could physically arrive and turn around "
        "(predicted departure < ETA + p10 turnaround)."
    )
    lines.append("")
    lines.append(f"**Total howlers:** {len(howlers)}")
    if not howlers.empty:
        lines.append("")
        worst_howlers = howlers.sort_values("abs_error", ascending=False).head(20)
        lines.append(
            "| # | Date | Route | Vessel | Predicted | Actual | ETA | p10 Dep |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        for i, (_, row) in enumerate(worst_howlers.iterrows(), 1):
            lines.append(
                f"| {i} | {row['s1_sched'].strftime('%m/%d %H:%M')} | "
                f"{row['route']} | {row['vessel_name']} | "
                f"{int(row['predicted_delay'])}m | {row['actual_delay']:.0f}m | "
                f"{'?'} | {'?'} |"
            )
    lines.append("")

    # === Big misses (predicted on-time, actual delayed) ===
    big_misses = predictions[
        (predictions["predicted_delay"] <= 3) & (predictions["actual_delay"] > 10)
    ].sort_values("actual_delay", ascending=False)
    lines.append("## Missed Delays")
    lines.append("")
    lines.append("Predictions that said on-time (≤3min) but the ferry was >10min late.")
    lines.append("")
    lines.append(f"**Count:** {len(big_misses)}")
    if not big_misses.empty:
        lines.append("")
        lines.append(
            "| # | Date | Route | Vessel | Horizon | Predicted | Actual | Error | Source |"
        )
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for i, (_, row) in enumerate(big_misses.head(30).iterrows(), 1):
            lines.append(
                f"| {i} | {row['s1_sched'].strftime('%m/%d %H:%M')} | "
                f"{row['route']} | {row['vessel_name']} | "
                f"{int(row['horizon_minutes'])}m | "
                f"{int(row['predicted_delay'])}m | "
                f"{row['actual_delay']:.0f}m | "
                f"{row['error']:+.0f}m | {row['pred_source'][:8]} |"
            )
    lines.append("")

    # === Big overpredictions (predicted delayed, actual on-time) ===
    big_over = predictions[
        (predictions["predicted_delay"] > 10) & (predictions["actual_delay"] <= 3)
    ].sort_values("predicted_delay", ascending=False)
    lines.append("## Big Overpredictions")
    lines.append("")
    lines.append("Predictions that said >10min late but the ferry was on-time (≤3min).")
    lines.append("")
    lines.append(f"**Count:** {len(big_over)}")
    if not big_over.empty:
        lines.append("")
        lines.append(
            "| # | Date | Route | Vessel | Horizon | Predicted | Actual | Error | Source |"
        )
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for i, (_, row) in enumerate(big_over.head(30).iterrows(), 1):
            lines.append(
                f"| {i} | {row['s1_sched'].strftime('%m/%d %H:%M')} | "
                f"{row['route']} | {row['vessel_name']} | "
                f"{int(row['horizon_minutes'])}m | "
                f"{int(row['predicted_delay'])}m | "
                f"{row['actual_delay']:.0f}m | "
                f"{row['error']:+.0f}m | {row['pred_source'][:8]} |"
            )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Analyze prediction outliers from historical data"
    )
    parser.add_argument(
        "--start",
        default="",
        help="Start date (YYYY-MM-DD). Default: 14 days before latest data.",
    )
    parser.add_argument(
        "--end",
        default="",
        help="End date (YYYY-MM-DD). Default: latest available data.",
    )
    parser.add_argument(
        "--routes",
        nargs="+",
        default=ROUTES,
        choices=ROUTES + ["all"],
        help="Routes to analyze (default: all)",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output report path (default: reports/prediction_outliers_YYYY-MM-DD.md)",
    )
    parser.add_argument(
        "--horizons",
        type=int,
        nargs="+",
        default=PREDICTION_HORIZONS,
        help="Prediction horizons in minutes before departure (default: 5 10 15 20 30 45 60)",
    )
    parser.add_argument(
        "--daytime-only",
        action="store_true",
        help="Exclude sailings scheduled between midnight and 6am",
    )
    parser.add_argument(
        "--option-a",
        action="store_true",
        help="Use ETA-bounded (Option A) logic instead of flat propagation",
    )
    args = parser.parse_args()

    global OPTION_A_MODE
    OPTION_A_MODE = args.option_a

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    init_db()

    conn = get_connection()

    # Auto-detect date range if not specified
    if not args.end:
        row = conn.execute(
            "SELECT MAX(scheduled_departure) FROM sailing_events"
        ).fetchone()
        max_date = row[0] if row[0] else datetime.now().isoformat()
        args.end = max_date[:10]
    if not args.start:
        end_dt = datetime.fromisoformat(args.end)
        start_dt = end_dt - timedelta(days=14)
        args.start = start_dt.strftime("%Y-%m-%d")

    routes = args.routes if args.routes != ["all"] else ROUTES

    logger.info(
        f"Analyzing predictions from {args.start} to {args.end} for routes: {routes}"
    )

    data = load_data(conn, args.start, args.end, routes)
    conn.close()

    chains = build_vessel_chains(data["events"])
    if chains.empty:
        logger.warning("No sailing chains found for this period/route.")
        print("No data to analyze.")
        return

    predictions = reconstruct_predictions(chains, data["snapshots"], args.horizons)
    if predictions.empty:
        logger.warning("No predictions could be reconstructed.")
        print("No predictions to analyze.")
        return

    if args.daytime_only:
        before = len(predictions)
        predictions["s1_hour"] = predictions["s1_sched"].dt.hour
        predictions = predictions[~predictions["s1_hour"].between(0, 5)]
        logger.info(
            f"Daytime filter: {before} → {len(predictions)} samples "
            f"(removed {before - len(predictions)} overnight sailings)"
        )

    logger.info(f"Reconstructed {len(predictions)} prediction samples")

    report = generate_report(
        predictions, chains, args.start, args.end, routes, args.horizons
    )

    from pathlib import Path

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    if not args.output:
        args.output = (
            reports_dir
            / f"prediction_outliers_{datetime.now().strftime('%Y-%m-%d')}.md"
        )
    else:
        args.output = Path(args.output)

    args.output.write_text(report)
    print(f"\nReport saved to: {args.output}")
    print(report)


if __name__ == "__main__":
    main()
