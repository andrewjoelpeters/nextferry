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

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression

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
            sched_gap = (
                nxt["scheduled_departure"] - curr["actual_arrival"]
            ).total_seconds() / 60
            next_rows.append(
                {
                    "event_id": curr["event_id"],
                    "next_sched": nxt["scheduled_departure"],
                    "next_actual_dep": nxt["actual_departure"],
                    "next_delay": float(nxt["delay_minutes"]),
                    "actual_turnaround": gap,
                    "current_delay": float(curr["delay_minutes"]),
                    "turnaround_terminal_id": int(curr["arriving_terminal_id"]),
                    "next_scheduled_departure": nxt["scheduled_departure"],
                    "minutes_until_next_scheduled": sched_gap,
                    "ta_hour_of_day": int(curr["hour_of_day"]),
                    "ta_day_of_week": int(curr["day_of_week"]),
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
            "departing_terminal_id",
            "arriving_terminal_id",
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

    # --- Join vehicle fullness from sailing_space_snapshots ---
    logger.info("Loading sailing space snapshots for turnaround features...")
    space_df = pd.read_sql_query(
        """
        SELECT departing_terminal_id, arriving_terminal_id, departure_time,
               collected_at, max_space_count, drive_up_space_count
        FROM sailing_space_snapshots
        WHERE max_space_count > 0
        """,
        conn,
    )
    if not space_df.empty:
        space_df["collected_at_dt"] = pd.to_datetime(
            space_df["collected_at"], format="ISO8601", utc=True
        )
        space_df["departure_time_dt"] = pd.to_datetime(
            space_df["departure_time"], format="ISO8601", utc=True
        )
        space_df["fullness"] = (
            1.0 - space_df["drive_up_space_count"] / space_df["max_space_count"]
        )

        # A. arriving_fullness: how full was the inbound vessel (cars to unload)
        # Last snapshot per inbound sailing = best estimate of final load
        inbound = (
            space_df.sort_values("collected_at_dt")
            .groupby(["arriving_terminal_id", "departure_time"])
            .last()
            .reset_index()
        )
        arr_parts = []
        for term_id in result["arriving_terminal_id"].dropna().unique():
            r_term = result.loc[result["arriving_terminal_id"] == term_id].sort_values(
                "actual_arrival"
            )
            i_term = inbound.loc[
                inbound["arriving_terminal_id"] == term_id
            ].sort_values("departure_time_dt")
            if i_term.empty:
                continue
            matched = pd.merge_asof(
                r_term[["event_id", "actual_arrival"]],
                i_term[["departure_time_dt", "fullness"]].rename(
                    columns={
                        "departure_time_dt": "actual_arrival",
                        "fullness": "arriving_fullness",
                    }
                ),
                on="actual_arrival",
                direction="backward",
            )
            arr_parts.append(matched[["event_id", "arriving_fullness"]])
        if arr_parts:
            result = result.merge(
                pd.concat(arr_parts, ignore_index=True),
                on="event_id",
                how="left",
            )
        else:
            result["arriving_fullness"] = np.nan

        # B. outbound_fullness: how many cars waiting at turnaround terminal
        # Space snapshot for the NEXT departure at the turnaround terminal,
        # taken closest to (but before) vessel arrival
        out_parts = []
        for term_id in result["turnaround_terminal_id"].dropna().unique():
            r_term = result.loc[
                result["turnaround_terminal_id"] == term_id
            ].sort_values("actual_arrival")
            o_term = space_df.loc[
                space_df["departing_terminal_id"] == term_id
            ].sort_values("collected_at_dt")
            if o_term.empty:
                continue
            matched = pd.merge_asof(
                r_term[["event_id", "actual_arrival"]],
                o_term[["collected_at_dt", "fullness"]].rename(
                    columns={
                        "collected_at_dt": "actual_arrival",
                        "fullness": "outbound_fullness",
                    }
                ),
                on="actual_arrival",
                direction="backward",
            )
            out_parts.append(matched[["event_id", "outbound_fullness"]])
        if out_parts:
            result = result.merge(
                pd.concat(out_parts, ignore_index=True),
                on="event_id",
                how="left",
            )
        else:
            result["outbound_fullness"] = np.nan

        n_arr = result["arriving_fullness"].notna().sum()
        n_out = result["outbound_fullness"].notna().sum()
        logger.info(
            f"Vehicle features: arriving_fullness={n_arr}/{len(result)} "
            f"({n_arr / len(result) * 100:.0f}%), "
            f"outbound_fullness={n_out}/{len(result)} "
            f"({n_out / len(result) * 100:.0f}%)"
        )
    else:
        result["arriving_fullness"] = np.nan
        result["outbound_fullness"] = np.nan
        logger.warning("No sailing space snapshots found")

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
# Turnaround models
# ---------------------------------------------------------------------------

TA_FEATURE_COLS = [
    "arriving_fullness",
    "outbound_fullness",
    "minutes_until_next_scheduled",
    "route_code",
    "ta_hour_of_day",
]


def build_turnaround_models(df: pd.DataFrame) -> dict:
    """Train linear and GBT turnaround models, return predictions + diagnostics."""
    work = df.copy()
    work["route_code"] = (work["route_abbrev"] == "sea-bi").astype(int)
    work = work.dropna(subset=["arriving_fullness", "outbound_fullness"])

    X = work[TA_FEATURE_COLS].values
    y = work["actual_turnaround"].values
    logger.info(f"Turnaround model training: {len(work)} rows with vehicle features")

    # --- Model A: LinearRegression + residual quantiles ---
    lr = LinearRegression()
    lr.fit(X, y)
    lr_pred = lr.predict(X)
    residuals = y - lr_pred
    r2 = float(1 - np.var(residuals) / np.var(y))

    # Per-route residual quantiles for better calibration
    route_residual_q = {}
    for route_code, _route_name in [(0, "ed-king"), (1, "sea-bi")]:
        mask = work["route_code"].values == route_code
        if mask.sum() > 0:
            r = residuals[mask]
            route_residual_q[route_code] = {
                "p10": float(np.quantile(r, 0.10)),
                "p75": float(np.quantile(r, 0.75)),
            }

    # Global fallback
    global_q = {
        "p10": float(np.quantile(residuals, 0.10)),
        "p75": float(np.quantile(residuals, 0.75)),
    }

    logger.info(f"Linear turnaround model: R²={r2:.3f}")
    logger.info(f"  Coefficients: {dict(zip(TA_FEATURE_COLS, lr.coef_, strict=True))}")
    logger.info(f"  Intercept: {lr.intercept_:.2f}")
    logger.info(f"  Residual p10={global_q['p10']:.1f} p75={global_q['p75']:.1f}")

    # --- Model B: HistGBT quantile pair ---
    gbt_p10 = HistGradientBoostingRegressor(
        loss="quantile", quantile=0.10, max_iter=100, max_depth=4
    )
    gbt_p75 = HistGradientBoostingRegressor(
        loss="quantile", quantile=0.75, max_iter=100, max_depth=4
    )
    gbt_p10.fit(X, y)
    gbt_p75.fit(X, y)
    gbt_p10_pred = gbt_p10.predict(X)
    gbt_p75_pred = gbt_p75.predict(X)
    logger.info(
        f"GBT turnaround model: p10 MAE={np.abs(y - gbt_p10_pred).mean():.2f}, "
        f"p75 MAE={np.abs(y - gbt_p75_pred).mean():.2f}"
    )

    return {
        "linear": lr,
        "linear_r2": r2,
        "linear_coefs": dict(zip(TA_FEATURE_COLS, lr.coef_, strict=True)),
        "linear_intercept": lr.intercept_,
        "route_residual_q": route_residual_q,
        "global_q": global_q,
        "gbt_p10": gbt_p10,
        "gbt_p75": gbt_p75,
        "n_train": len(work),
        "feature_cols": TA_FEATURE_COLS,
    }


# Hard floor for model-predicted turnaround — never go below observed p10
_TA_HARD_FLOOR = {"sea-bi": 9.3, "ed-king": 14.8}


def _predict_ta_linear(row: pd.Series, models: dict, quantile: str) -> float:
    """Predict turnaround using linear model + residual quantiles."""
    features = np.array([[row[c] for c in TA_FEATURE_COLS]])
    median = models["linear"].predict(features)[0]
    route_code = int(row["route_code"])
    rq = models["route_residual_q"].get(route_code, models["global_q"])
    route = "sea-bi" if route_code == 1 else "ed-king"
    hard_floor = _TA_HARD_FLOOR[route]
    return float(np.clip(median + rq[quantile], hard_floor, 45.0))


def _predict_ta_gbt(row: pd.Series, models: dict, quantile: str) -> float:
    """Predict turnaround using GBT quantile model."""
    features = np.array([[row[c] for c in TA_FEATURE_COLS]])
    if quantile == "p10":
        val = models["gbt_p10"].predict(features)[0]
    else:
        val = models["gbt_p75"].predict(features)[0]
    route_code = int(row["route_code"])
    route = "sea-bi" if route_code == 1 else "ed-king"
    hard_floor = _TA_HARD_FLOOR[route]
    return float(np.clip(val, hard_floor, 45.0))


def predict_conditional_ceiling_model(
    row: pd.Series,
    models: dict,
    threshold: float,
    ta_fn,
) -> float:
    """Conditional ceiling using model-predicted turnaround bounds."""
    min_ta = ta_fn(row, models, "p10")
    max_ta = max(min_ta + 2.0, ta_fn(row, models, "p75"))

    flat = row["current_delay"]
    eta_floor = predict_eta_ta(row, min_ta)
    if flat > threshold:
        eta_ceiling = predict_eta_ta(row, max_ta)
        return max(eta_floor, min(flat, eta_ceiling))
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
    ta_p75 = {"sea-bi": 22.0, "ed-king": 26.0}

    # Train turnaround models
    ta_models = build_turnaround_models(df)

    # Add route_code column for model-based predictions
    df = df.copy()
    df["route_code"] = (df["route_abbrev"] == "sea-bi").astype(int)
    has_features = df["arriving_fullness"].notna() & df["outbound_fullness"].notna()

    def _model_or_fallback(row, ta_fn):
        """Use model if features available, else fixed percentiles."""
        if pd.notna(row.get("arriving_fullness")) and pd.notna(
            row.get("outbound_fullness")
        ):
            return predict_conditional_ceiling_model(row, ta_models, 10.0, ta_fn)
        return predict_conditional_ceiling(
            row, ta_p10[row["route_abbrev"]], ta_p75[row["route_abbrev"]], 10.0
        )

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
            "Cond ceil LINEAR (>10)",
            lambda r: _model_or_fallback(r, _predict_ta_linear),
        ),
        (
            "Cond ceil GBT (>10)",
            lambda r: _model_or_fallback(r, _predict_ta_gbt),
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

    # Log feature coverage
    logger.info(
        f"Feature coverage: {has_features.sum()}/{len(df)} "
        f"({has_features.mean() * 100:.0f}%) rows had vehicle features"
    )

    experiments.append({"ta_models": ta_models})
    return experiments


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def generate_report(experiments: list[dict], df: pd.DataFrame) -> str:
    # Separate strategy results from model diagnostics
    strategy_exps = [e for e in experiments if "results" in e]
    ta_models = next((e["ta_models"] for e in experiments if "ta_models" in e), None)

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
    for exp in strategy_exps:
        o = exp["results"]["overall"]
        lines.append(
            f"| **{o['label']}** | {o['mae']} | {o['bias']:+.1f} | "
            f"{o['within_3']}% | {o['within_5']}% | "
            f"{o['missed_delay']}% | {o['howler_n']} ({o['howler_pct']}%) |"
        )
    lines.append("")

    # Turnaround model diagnostics
    if ta_models:
        lines.append("## Turnaround Model Diagnostics")
        lines.append("")
        lines.append(f"**Training rows:** {ta_models['n_train']}")
        lines.append(f"**Linear R²:** {ta_models['linear_r2']:.3f}")
        lines.append("")
        lines.append("**Linear model coefficients:**")
        lines.append("")
        lines.append("| Feature | Coefficient | Interpretation |")
        lines.append("|---|---|---|")
        interp = {
            "arriving_fullness": "min added per 100% fullness increase (cars to unload)",
            "outbound_fullness": "min added per 100% fullness increase (cars to load)",
            "minutes_until_next_scheduled": "min added per min of schedule gap",
            "route_code": "min added for sea-bi vs ed-king",
            "ta_hour_of_day": "min added per hour of day",
        }
        for feat, coef in ta_models["linear_coefs"].items():
            lines.append(f"| {feat} | {coef:+.3f} | {interp.get(feat, '')} |")
        lines.append(f"| (intercept) | {ta_models['linear_intercept']:.2f} | |")
        lines.append("")

        lines.append("**Residual quantiles (for turnaround bounds):**")
        lines.append("")
        lines.append("| Route | p10 (floor offset) | p75 (ceiling offset) |")
        lines.append("|---|---|---|")
        for rc, rname in [(0, "ed-king"), (1, "sea-bi")]:
            rq = ta_models["route_residual_q"].get(rc, ta_models["global_q"])
            lines.append(f"| {rname} | {rq['p10']:+.1f} min | {rq['p75']:+.1f} min |")
        lines.append("")

    # By route
    for route in ROUTES:
        lines.append(f"### {route}")
        lines.append("")
        lines.append("| Experiment | MAE | Bias | ±3min | Howlers |")
        lines.append("|---|---|---|---|---|")
        for exp in strategy_exps:
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
        for exp in strategy_exps:
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
    flat = strategy_exps[0]["results"]["overall"]
    lines.append(
        f"Flat propagation produces **{flat['howler_n']} howlers** "
        f"out of {flat['n']} predictions ({flat['howler_pct']}%)."
    )
    lines.append("")
    for exp in strategy_exps:
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
