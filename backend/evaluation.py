"""Evaluation framework for the delay prediction model.

Metrics are chosen from the ferry rider's perspective — asymmetric because
overpredicting delay is dangerous (rider shows up late, boat already left):

- "safe_2min": % where predicted departure is within 2 min after actual.
   Underpredicting delay (rider arrives early, waits) is always safe.
   Overpredicting delay (rider thinks boat leaves later) is the risk.
- "safe_5min": same with 5-min tolerance
- "risky_rate": % where predicted delay > actual delay + 3 min — the model
   told the rider the boat departs later than it really did
- "mae": mean absolute error in minutes
- "bias": mean signed error (positive = overpredicts delay = DANGEROUS)
- "coverage_70pct": % of actuals inside the [q15, q85] prediction interval
- "ece": expected calibration error for quantile predictions
- "baseline_mae" / "improvement_pct": vs naive "current delay = future delay"

Usage:
    python -m backend.evaluation
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Day-of-week labels (strftime %w convention: 0=Sunday)
DOW_LABELS = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}

# Time-of-day buckets that match how riders think about their day
TIME_OF_DAY_BUCKETS = [
    ("Early (5–7)", 5, 7),
    ("AM Peak (7–10)", 7, 10),
    ("Midday (10–15)", 10, 15),
    ("PM Peak (15–19)", 15, 19),
    ("Evening (19–22)", 19, 22),
]

# Prediction horizon buckets — fine-grained where it matters (5–30 min),
# coarser further out, nothing beyond 90 min (riders don't plan that far)
HORIZON_BUCKETS = [
    ("2–4m", 2, 4),
    ("4–6m", 4, 6),
    ("6–8m", 6, 8),
    ("8–10m", 8, 10),
    ("10–14m", 10, 14),
    ("14–20m", 14, 20),
    ("20–30m", 20, 30),
    ("30–45m", 30, 45),
    ("45–60m", 45, 60),
    ("60–90m", 60, 90),
]


def compute_metrics(errors: pd.Series, actuals: pd.Series,
                    predictions: pd.Series,
                    lower: pd.Series, upper: pd.Series,
                    baseline_errors: Optional[pd.Series] = None) -> Optional[dict]:
    """Compute user-centric metrics for a group of predictions.

    errors = predicted - actual.
    Positive error = overpredicted delay = predicted departure AFTER actual
        = DANGEROUS (rider arrives after the boat left).
    Negative error = underpredicted delay = predicted departure BEFORE actual
        = safe (rider arrives early, waits a bit).
    """
    if len(errors) == 0:
        return None

    abs_errors = np.abs(errors)
    within_bounds = (actuals >= lower) & (actuals <= upper)

    # "Safe" means predicted departure is at most N min AFTER actual departure.
    # predicted_delay <= actual_delay + threshold  →  error <= threshold
    # Underpredicting (error < 0) is always safe — rider arrives early.
    safe_2min = (errors <= 2)
    safe_5min = (errors <= 5)

    # "Risky" means predicted delay > actual delay + 3 min — the model said
    # the boat would leave later than it did, rider could miss it.
    risky = (errors > 3)

    # Expected calibration error: how well do quantile predictions match
    # their nominal levels? Measures |observed_freq - target_freq| for
    # the q15 and q85 bounds.
    q15_observed = float((actuals < lower).mean())  # should be ~0.15
    q85_observed = float((actuals < upper).mean())   # should be ~0.85
    ece = round(abs(q15_observed - 0.15) + abs(q85_observed - 0.85), 3)

    metrics = {
        "safe_2min": round(float(safe_2min.mean() * 100), 1),
        "safe_5min": round(float(safe_5min.mean() * 100), 1),
        "risky_rate": round(float(risky.mean() * 100), 1),
        "mae": round(float(abs_errors.mean()), 2),
        "bias": round(float(errors.mean()), 2),
        "coverage_70pct": round(float(within_bounds.mean() * 100), 1),
        "ece": ece,
        "n": int(len(errors)),
    }
    if baseline_errors is not None and len(baseline_errors) > 0:
        baseline_mae = float(np.abs(baseline_errors).mean())
        metrics["baseline_mae"] = round(baseline_mae, 2)
        metrics["improvement_pct"] = round(
            (1 - metrics["mae"] / max(baseline_mae, 0.01)) * 100, 1
        )
    return metrics


def _slice_metrics(test_df, errors, predictions, baseline_errors, groupby_col):
    """Compute metrics for each value of groupby_col."""
    result = {}
    for val, group in test_df.groupby(groupby_col):
        idx = group.index
        g_errors = errors.loc[idx]
        g_preds = predictions.loc[idx]
        g_baseline = baseline_errors.loc[idx] if baseline_errors is not None else None
        m = compute_metrics(
            g_errors, group["actual_delay_minutes"], g_preds,
            group["lower_bound"], group["upper_bound"], g_baseline
        )
        if m:
            result[val] = m
    return result


def evaluate_predictions(test_df: pd.DataFrame) -> dict:
    """Evaluate predictions on test data.

    Required columns:
        actual_delay_minutes, predicted_delay, lower_bound, upper_bound,
        minutes_until_scheduled_departure
    Optional columns for richer breakdowns:
        route_abbrev, current_vessel_delay_minutes, sailing_event_id,
        day_of_week, hour_of_day, scheduled_departure, is_peak_hour
    """
    results = {}

    errors = test_df["predicted_delay"] - test_df["actual_delay_minutes"]
    predictions = test_df["predicted_delay"]
    actuals = test_df["actual_delay_minutes"]
    lower = test_df["lower_bound"]
    upper = test_df["upper_bound"]

    baseline_errors = None
    if "current_vessel_delay_minutes" in test_df.columns:
        baseline_errors = (
            test_df["current_vessel_delay_minutes"] - test_df["actual_delay_minutes"]
        )

    # --- Top-line metrics ---
    overall = compute_metrics(errors, actuals, predictions, lower, upper, baseline_errors)
    for k, v in overall.items():
        results[f"overall_{k}" if k != "n" else "n_test_samples"] = v

    # --- Per-route ---
    if "route_abbrev" in test_df.columns:
        results["by_route"] = _slice_metrics(
            test_df, errors, predictions, baseline_errors, "route_abbrev"
        )

    # --- Per day of week ---
    if "day_of_week" in test_df.columns:
        raw = _slice_metrics(test_df, errors, predictions, baseline_errors, "day_of_week")
        results["by_day_of_week"] = {
            DOW_LABELS.get(k, str(k)): v for k, v in sorted(raw.items())
        }

    # --- Per time of day ---
    if "hour_of_day" in test_df.columns:
        by_tod = {}
        for label, h_start, h_end in TIME_OF_DAY_BUCKETS:
            mask = (test_df["hour_of_day"] >= h_start) & (test_df["hour_of_day"] < h_end)
            subset = test_df[mask]
            if len(subset) == 0:
                continue
            idx = subset.index
            g_baseline = baseline_errors.loc[idx] if baseline_errors is not None else None
            m = compute_metrics(
                errors.loc[idx], subset["actual_delay_minutes"],
                predictions.loc[idx],
                subset["lower_bound"], subset["upper_bound"], g_baseline
            )
            if m:
                by_tod[label] = m
        results["by_time_of_day"] = by_tod

    # --- Per month ---
    if "scheduled_departure" in test_df.columns:
        try:
            months = pd.to_datetime(test_df["scheduled_departure"]).dt.strftime("%Y-%m")
            temp_df = test_df.copy()
            temp_df["_month"] = months
            results["by_month"] = _slice_metrics(
                temp_df, errors, predictions, baseline_errors, "_month"
            )
        except Exception:
            pass

    # --- Per prediction horizon ---
    minutes_col = test_df["minutes_until_scheduled_departure"]
    by_horizon = {}
    for label, lo, hi in HORIZON_BUCKETS:
        mask = (minutes_col >= lo) & (minutes_col < hi)
        subset = test_df[mask]
        if len(subset) == 0:
            continue
        idx = subset.index
        g_baseline = baseline_errors.loc[idx] if baseline_errors is not None else None
        m = compute_metrics(
            errors.loc[idx], subset["actual_delay_minutes"],
            predictions.loc[idx],
            subset["lower_bound"], subset["upper_bound"], g_baseline
        )
        if m:
            by_horizon[label] = m
    results["by_horizon"] = by_horizon

    # --- Cross-cut: route × peak/off-peak ---
    if "route_abbrev" in test_df.columns and "is_peak_hour" in test_df.columns:
        cross = {}
        for (route, peak), group in test_df.groupby(["route_abbrev", "is_peak_hour"]):
            idx = group.index
            g_baseline = baseline_errors.loc[idx] if baseline_errors is not None else None
            m = compute_metrics(
                errors.loc[idx], group["actual_delay_minutes"],
                predictions.loc[idx],
                group["lower_bound"], group["upper_bound"], g_baseline
            )
            if m:
                suffix = "peak" if peak else "off-peak"
                cross[f"{route} ({suffix})"] = m
        results["by_route_x_peak"] = cross

    # Event count
    if "sailing_event_id" in test_df.columns:
        results["n_test_events"] = int(test_df["sailing_event_id"].nunique())

    return results


def run_full_evaluation() -> Optional[dict]:
    """Run a full evaluation using the current predictor and database."""
    from .ml_predictor import DelayPredictor

    evaluator = DelayPredictor()

    if not evaluator.load():
        logger.warning("No trained model found. Train a model first.")
        return None

    df = evaluator.build_training_data()
    if df is None:
        logger.warning("Not enough data for evaluation")
        return None

    unique_events = df["sailing_event_id"].unique()
    split_idx = int(len(unique_events) * 0.8)
    test_events = set(unique_events[split_idx:])
    test_df = df[df["sailing_event_id"].isin(test_events)].copy()

    if len(test_df) == 0:
        logger.warning("No test data available")
        return None

    X_test = test_df[
        [
            "route_abbrev",
            "departing_terminal_id",
            "day_of_week",
            "hour_of_day",
            "minutes_until_scheduled_departure",
            "current_vessel_delay_minutes",
            "is_peak_hour",
            "previous_sailing_fullness",
            "turnaround_minutes",
        ]
    ].copy()

    X_test["route_abbrev"] = (
        X_test["route_abbrev"].map(evaluator._route_mapping).fillna(-1)
    )
    X_test["departing_terminal_id"] = (
        X_test["departing_terminal_id"].map(evaluator._terminal_mapping).fillna(-1)
    )

    X_arr = X_test.values
    test_df["predicted_delay"] = evaluator.model_q50.predict(X_arr)
    test_df["lower_bound"] = evaluator.model_q15.predict(X_arr)
    test_df["upper_bound"] = evaluator.model_q85.predict(X_arr)

    return evaluate_predictions(test_df)


def print_evaluation(results: dict):
    """Pretty-print evaluation results to stdout."""
    print("\n=== Delay Prediction Evaluation ===")
    print(f"Test samples: {results.get('n_test_samples', '?')}", end="")
    if "n_test_events" in results:
        print(f" ({results['n_test_events']} sailing events)")
    else:
        print()

    print(f"\n  Safe within 2 min: {results['overall_safe_2min']}%")
    print(f"  Safe within 5 min: {results['overall_safe_5min']}%")
    print(f"  Risky rate (>3m over): {results['overall_risky_rate']}%")
    print(f"  MAE:               {results['overall_mae']} min")
    print(f"  Bias:              {results['overall_bias']:+.2f} min (positive = risky)")
    print(f"  70% Coverage:      {results['overall_coverage_70pct']}%")
    print(f"  ECE:               {results['overall_ece']}")

    if "overall_baseline_mae" in results:
        print(f"\n  Baseline MAE:      {results['overall_baseline_mae']} min")
        print(f"  Improvement:       {results['overall_improvement_pct']}%")

    if "by_route" in results:
        print(f"\nBy route:")
        print(f"  {'Route':<12} {'Safe2m':>7} {'Risky':>7} {'MAE':>6} {'Bias':>7} {'N':>6}")
        for route, m in sorted(results["by_route"].items()):
            print(
                f"  {route:<12} {m['safe_2min']:>6.1f}% {m['risky_rate']:>6.1f}% "
                f"{m['mae']:>6.2f} {m['bias']:>+6.2f} {m['n']:>6}"
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    from .database import init_db

    init_db()

    results = run_full_evaluation()
    if results:
        print_evaluation(results)
    else:
        print("Evaluation could not be run. Ensure model is trained and data exists.")
