"""Evaluation framework for the delay prediction model.

Computes mean error (bias) stratified by time-until-departure in fine-grained
bins. Positive bias = model over-predicts delay, negative = under-predicts.

Usage:
    python -m backend.evaluation
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# 2-minute bins from 0 to 120, then a 120+ bucket
FINE_BINS = list(range(0, 122, 2))  # [0, 2, 4, ..., 120]


def _compute_group_metrics(errors: pd.Series, actuals: pd.Series,
                           predictions: pd.Series, lower: pd.Series,
                           upper: pd.Series,
                           baseline_errors: Optional[pd.Series] = None) -> dict:
    """Compute standard metrics for a group of predictions."""
    if len(errors) == 0:
        return None
    abs_errors = np.abs(errors)
    within_bounds = (actuals >= lower) & (actuals <= upper)
    metrics = {
        "mean_error": round(float(errors.mean()), 2),
        "mae": round(float(abs_errors.mean()), 2),
        "rmse": round(float(np.sqrt((errors ** 2).mean())), 2),
        "median_ae": round(float(np.median(abs_errors)), 2),
        "error_p12": round(float(np.percentile(errors, 12.5)), 2),
        "error_p88": round(float(np.percentile(errors, 87.5)), 2),
        "coverage_70pct": round(float(within_bounds.mean() * 100), 1),
        "n": int(len(errors)),
    }
    if baseline_errors is not None and len(baseline_errors) > 0:
        baseline_mae = float(np.abs(baseline_errors).mean())
        metrics["baseline_mae"] = round(baseline_mae, 2)
        metrics["improvement_pct"] = round(
            (1 - metrics["mae"] / max(baseline_mae, 0.01)) * 100, 1
        )
    return metrics


def evaluate_predictions(test_df: pd.DataFrame) -> dict:
    """Evaluate predictions on test data.

    Expects test_df to have columns:
        - actual_delay_minutes
        - predicted_delay
        - lower_bound
        - upper_bound
        - minutes_until_scheduled_departure
    Optional columns for richer breakdowns:
        - route_abbrev
        - current_vessel_delay_minutes
        - sailing_event_id
    """
    results = {}

    errors = test_df["predicted_delay"] - test_df["actual_delay_minutes"]
    actuals = test_df["actual_delay_minutes"]
    preds = test_df["predicted_delay"]
    lower = test_df["lower_bound"]
    upper = test_df["upper_bound"]

    baseline_errors = None
    if "current_vessel_delay_minutes" in test_df.columns:
        baseline_errors = (
            test_df["current_vessel_delay_minutes"] - test_df["actual_delay_minutes"]
        )

    # Overall metrics
    overall = _compute_group_metrics(errors, actuals, preds, lower, upper, baseline_errors)
    results["overall_mean_error"] = overall["mean_error"]
    results["overall_mae"] = overall["mae"]
    results["overall_rmse"] = overall["rmse"]
    results["overall_median_ae"] = overall["median_ae"]
    results["coverage_70pct"] = overall["coverage_70pct"]
    if "baseline_mae" in overall:
        results["baseline_mae"] = overall["baseline_mae"]
        results["improvement_pct"] = overall["improvement_pct"]

    # Per-route breakdown
    if "route_abbrev" in test_df.columns:
        error_by_route = {}
        for route, group in test_df.groupby("route_abbrev"):
            g_errors = group["predicted_delay"] - group["actual_delay_minutes"]
            g_baseline = None
            if "current_vessel_delay_minutes" in group.columns:
                g_baseline = group["current_vessel_delay_minutes"] - group["actual_delay_minutes"]
            route_metrics = _compute_group_metrics(
                g_errors, group["actual_delay_minutes"],
                group["predicted_delay"], group["lower_bound"],
                group["upper_bound"], g_baseline
            )
            if route_metrics:
                error_by_route[route] = route_metrics
        results["error_by_route"] = error_by_route

    # Fine-grained: mean error by 2-minute time-to-departure bins
    minutes_col = test_df["minutes_until_scheduled_departure"]
    error_by_horizon = []

    def _horizon_stats(mask):
        subset = test_df[mask]
        subset_errors = errors[mask]
        if len(subset_errors) == 0:
            return None
        subset_baseline = None
        if baseline_errors is not None:
            subset_baseline = baseline_errors[mask]
        metrics = _compute_group_metrics(
            subset_errors, subset["actual_delay_minutes"],
            subset["predicted_delay"], subset["lower_bound"],
            subset["upper_bound"], subset_baseline
        )
        return metrics

    for i in range(len(FINE_BINS) - 1):
        lo, hi = FINE_BINS[i], FINE_BINS[i + 1]
        mask = (minutes_col >= lo) & (minutes_col < hi)
        row = _horizon_stats(mask)
        if row:
            row["minutes_out"] = lo
            error_by_horizon.append(row)

    # 120+ bucket
    mask = minutes_col >= 120
    row = _horizon_stats(mask)
    if row:
        row["minutes_out"] = 120
        error_by_horizon.append(row)

    results["error_by_horizon"] = error_by_horizon
    results["n_test_samples"] = int(len(test_df))

    # Per-event accuracy (unique sailing events)
    if "sailing_event_id" in test_df.columns:
        results["n_test_events"] = int(test_df["sailing_event_id"].nunique())

    return results


def run_full_evaluation() -> Optional[dict]:
    """Run a full evaluation using the current predictor and database."""
    from .ml_predictor import DelayPredictor

    evaluator = DelayPredictor()

    # Try to load existing model
    if not evaluator.load():
        logger.warning("No trained model found. Train a model first.")
        return None

    # Build test data
    df = evaluator.build_training_data()
    if df is None:
        logger.warning("Not enough data for evaluation")
        return None

    # Chronological split - test on last 20%
    unique_events = df["sailing_event_id"].unique()
    split_idx = int(len(unique_events) * 0.8)
    test_events = set(unique_events[split_idx:])
    test_df = df[df["sailing_event_id"].isin(test_events)].copy()

    if len(test_df) == 0:
        logger.warning("No test data available")
        return None

    # Encode features the same way as training
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
    print(f"\n=== Delay Prediction Evaluation ===")
    print(f"Test samples: {results['n_test_samples']}", end="")
    if "n_test_events" in results:
        print(f" ({results['n_test_events']} sailing events)")
    else:
        print()
    print(f"Mean Error (bias): {results['overall_mean_error']} min")
    print(f"MAE: {results['overall_mae']} min")
    print(f"RMSE: {results['overall_rmse']} min")
    print(f"Median AE: {results['overall_median_ae']} min")
    print(f"70% Interval Coverage: {results['coverage_70pct']}%")

    if "baseline_mae" in results:
        print(f"\nBaseline MAE (flat delay): {results['baseline_mae']} min")
        print(f"Improvement over baseline: {results['improvement_pct']}%")

    if "error_by_route" in results:
        print(f"\nPer-route breakdown:")
        print(f"  {'Route':<12} {'Bias':>8} {'MAE':>8} {'RMSE':>8} {'Cov%':>7} {'Impr%':>7} {'N':>6}")
        for route, m in sorted(results["error_by_route"].items()):
            impr = f"{m['improvement_pct']:>6.1f}" if "improvement_pct" in m else "   N/A"
            print(
                f"  {route:<12} {m['mean_error']:>+8.2f} {m['mae']:>8.2f} "
                f"{m['rmse']:>8.2f} {m['coverage_70pct']:>6.1f} {impr} {m['n']:>6}"
            )

    print(f"\nMean error by time-to-departure (2min bins):")
    print(f"  {'Min out':>8}  {'Bias':>8}  {'MAE':>8}  {'N':>6}")
    for row in results.get("error_by_horizon", []):
        print(
            f"  {row['minutes_out']:>6}m  {row['mean_error']:>+8.2f}  {row['mae']:>8.2f}  {row['n']:>6}"
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
