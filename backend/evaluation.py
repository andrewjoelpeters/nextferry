"""Evaluation framework for the delay prediction model.

Computes RMSE stratified by time-until-departure and prediction interval coverage.

Usage:
    python -m backend.evaluation
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

HORIZON_BINS = [
    (0, 5, "0-5min"),
    (5, 15, "5-15min"),
    (15, 30, "15-30min"),
    (30, 60, "30-60min"),
    (60, float("inf"), "60+min"),
]


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

    # Overall RMSE
    residuals = test_df["actual_delay_minutes"] - test_df["predicted_delay"]
    results["overall_rmse"] = round(float(np.sqrt(np.mean(residuals**2))), 2)
    results["overall_mae"] = round(float(np.mean(np.abs(residuals))), 2)

    # Coverage: % of actuals within [lower_bound, upper_bound]
    within_bounds = (test_df["actual_delay_minutes"] >= test_df["lower_bound"]) & (
        test_df["actual_delay_minutes"] <= test_df["upper_bound"]
    )
    results["coverage_70pct"] = round(float(within_bounds.mean() * 100), 1)

    # RMSE by time horizon
    horizon_results = {}
    for lo, hi, label in HORIZON_BINS:
        mask = (test_df["minutes_until_scheduled_departure"] >= lo) & (
            test_df["minutes_until_scheduled_departure"] < hi
        )
        subset = test_df[mask]
        if len(subset) > 0:
            r = subset["actual_delay_minutes"] - subset["predicted_delay"]
            horizon_results[label] = {
                "rmse": round(float(np.sqrt(np.mean(r**2))), 2),
                "mae": round(float(np.mean(np.abs(r))), 2),
                "n_samples": int(len(subset)),
            }
    results["by_horizon"] = horizon_results

    # Baseline comparison: "flat delay" = use current_vessel_delay_minutes as prediction
    if "current_vessel_delay_minutes" in test_df.columns:
        baseline_residuals = (
            test_df["actual_delay_minutes"] - test_df["current_vessel_delay_minutes"]
        )
        results["baseline_rmse"] = round(
            float(np.sqrt(np.mean(baseline_residuals**2))), 2
        )
        results["improvement_pct"] = round(
            (1 - results["overall_rmse"] / max(results["baseline_rmse"], 0.01)) * 100,
            1,
        )

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
        print(f"Overall RMSE: {results['overall_rmse']} min")
        print(f"Overall MAE: {results['overall_mae']} min")
        print(f"70% Interval Coverage: {results['coverage_70pct']}%")

        if "baseline_rmse" in results:
            print(f"\nBaseline RMSE (flat delay): {results['baseline_rmse']} min")
            print(f"Improvement over baseline: {results['improvement_pct']}%")

        print("\nRMSE by time horizon:")
        for label, metrics in results.get("by_horizon", {}).items():
            print(
                f"  {label}: RMSE={metrics['rmse']}, MAE={metrics['mae']}, n={metrics['n_samples']}"
            )
    else:
        print("Evaluation could not be run. Ensure model is trained and data exists.")
