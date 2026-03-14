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


def evaluate_predictions(test_df: pd.DataFrame) -> dict:
    """Evaluate predictions on test data.

    Expects test_df to have columns:
        - actual_delay_minutes
        - predicted_delay
        - lower_bound
        - upper_bound
        - minutes_until_scheduled_departure
    """
    results = {}

    errors = test_df["predicted_delay"] - test_df["actual_delay_minutes"]

    # Overall metrics
    results["overall_mean_error"] = round(float(errors.mean()), 2)
    results["overall_mae"] = round(float(np.abs(errors).mean()), 2)

    # Coverage: % of actuals within [lower_bound, upper_bound]
    within_bounds = (test_df["actual_delay_minutes"] >= test_df["lower_bound"]) & (
        test_df["actual_delay_minutes"] <= test_df["upper_bound"]
    )
    results["coverage_70pct"] = round(float(within_bounds.mean() * 100), 1)

    # Baseline comparison: "flat delay" = use current_vessel_delay_minutes as prediction
    if "current_vessel_delay_minutes" in test_df.columns:
        baseline_errors = (
            test_df["current_vessel_delay_minutes"] - test_df["actual_delay_minutes"]
        )
        results["baseline_mae"] = round(float(np.abs(baseline_errors).mean()), 2)
        results["improvement_pct"] = round(
            (1 - results["overall_mae"] / max(results["baseline_mae"], 0.01)) * 100,
            1,
        )

    # Fine-grained: mean error by 2-minute time-to-departure bins
    minutes_col = test_df["minutes_until_scheduled_departure"]
    error_by_horizon = []

    def _horizon_stats(mask):
        subset_errors = errors[mask]
        if len(subset_errors) == 0:
            return None
        return {
            "minutes_out": None,
            "mean_error": round(float(subset_errors.mean()), 2),
            "mae": round(float(np.abs(subset_errors).mean()), 2),
            "error_p12": round(float(np.percentile(subset_errors, 12.5)), 2),
            "error_p88": round(float(np.percentile(subset_errors, 87.5)), 2),
            "n": int(len(subset_errors)),
        }

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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    from .database import init_db

    init_db()

    results = run_full_evaluation()
    if results:
        print("\n=== Delay Prediction Evaluation ===")
        print(f"Test samples: {results['n_test_samples']}")
        print(f"Mean Error (bias): {results['overall_mean_error']} min")
        print(f"MAE: {results['overall_mae']} min")
        print(f"70% Interval Coverage: {results['coverage_70pct']}%")

        if "baseline_mae" in results:
            print(f"\nBaseline MAE (flat delay): {results['baseline_mae']} min")
            print(f"Improvement over baseline: {results['improvement_pct']}%")

        print("\nMean error by time-to-departure (2min bins):")
        print(f"  {'Min out':>8}  {'Bias':>8}  {'MAE':>8}  {'N':>6}")
        for row in results.get("error_by_horizon", []):
            print(
                f"  {row['minutes_out']:>6}m  {row['mean_error']:>+8.2f}  {row['mae']:>8.2f}  {row['n']:>6}"
            )
    else:
        print("Evaluation could not be run. Ensure model is trained and data exists.")
