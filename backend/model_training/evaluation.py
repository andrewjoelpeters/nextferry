"""Evaluation framework for the delay prediction model.

The top-line metric is **pinball_loss** — an asymmetric MAE (pinball loss)
that penalizes overprediction more heavily than underprediction:

    pinball_loss = mean(α · max(e, 0) + max(-e, 0))

where α = OVERPREDICTION_PENALTY (default 2).  When α=1 this reduces to MAE.
When the model errs on the safe side (underpredicts delay, rider arrives
early), pinball_loss ≈ MAE.  When it errs dangerously (overpredicts delay,
rider might miss the boat), pinball_loss >> MAE (up to α × MAE).

Core metrics per slice:
- "pinball_loss": asymmetric MAE (the one number)
- "bias": mean signed error — diagnostic for direction
- "error_p90": 90th percentile of signed error — tail risk

Top-level only:
- "mae": standard MAE (reference, universally understood)
- "coverage_70pct": prediction interval calibration check
- "improvement_pct": vs naive "current delay = future delay" baseline

Usage:
    python -m backend.model_training.evaluation
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Overprediction is this many times worse than underprediction.
# α=2 means a 1-min overprediction costs 2, a 1-min underprediction costs 1.
# Grounded in domain reality: missing a ferry (overprediction) means waiting
# 30–60 min for the next sailing, while arriving early just means waiting.
OVERPREDICTION_PENALTY = 2

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

# Prediction horizon buckets — fine-grained where it matters (2–30 min),
# coarser further out, nothing beyond 90 min
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


def pinball_loss(errors: np.ndarray, alpha: float = OVERPREDICTION_PENALTY) -> float:
    """Asymmetric MAE (pinball loss): penalize overprediction α× more.

    pinball_loss = mean(α · max(e, 0) + max(-e, 0))

    When α=1 this is identical to MAE.
    """
    overpred = np.maximum(errors, 0)
    underpred = np.maximum(-errors, 0)
    return float(np.mean(alpha * overpred + underpred))


def compute_metrics(errors: pd.Series,
                    actuals: Optional[pd.Series] = None,
                    lower: Optional[pd.Series] = None,
                    upper: Optional[pd.Series] = None,
                    baseline_errors: Optional[pd.Series] = None) -> Optional[dict]:
    """Compute metrics for a group of predictions.

    errors = predicted - actual.
    Positive = overpredicted delay = predicted departure AFTER actual = DANGEROUS.
    Negative = underpredicted delay = rider arrives early = safe.

    actuals/lower/upper are only needed for coverage (top-level use).
    """
    if len(errors) == 0:
        return None

    err_arr = errors.values

    metrics = {
        "pinball_loss": round(pinball_loss(err_arr), 2),
        "bias": round(float(errors.mean()), 2),
        "error_p90": round(float(np.percentile(err_arr, 90)), 2),
        "n": int(len(errors)),
    }

    # MAE — included for reference / universally understood
    metrics["mae"] = round(float(np.abs(err_arr).mean()), 2)

    # Coverage — only meaningful when interval bounds are provided
    if actuals is not None and lower is not None and upper is not None:
        within_bounds = (actuals >= lower) & (actuals <= upper)
        metrics["coverage_70pct"] = round(float(within_bounds.mean() * 100), 1)

    if baseline_errors is not None and len(baseline_errors) > 0:
        baseline_pl = pinball_loss(baseline_errors.values)
        metrics["baseline_pinball_loss"] = round(baseline_pl, 2)
        metrics["improvement_pct"] = round(
            (1 - metrics["pinball_loss"] / max(baseline_pl, 0.01)) * 100, 1
        )
    return metrics


def _slice_metrics(test_df, errors, baseline_errors, groupby_col):
    """Compute core metrics for each value of groupby_col."""
    result = {}
    for val, group in test_df.groupby(groupby_col):
        idx = group.index
        g_errors = errors.loc[idx]
        g_baseline = baseline_errors.loc[idx] if baseline_errors is not None else None
        m = compute_metrics(g_errors, baseline_errors=g_baseline)
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
    actuals = test_df["actual_delay_minutes"]
    lower = test_df["lower_bound"]
    upper = test_df["upper_bound"]

    baseline_errors = None
    if "current_vessel_delay_minutes" in test_df.columns:
        baseline_errors = (
            test_df["current_vessel_delay_minutes"] - test_df["actual_delay_minutes"]
        )

    # --- Top-line metrics (with coverage + baseline) ---
    overall = compute_metrics(errors, actuals, lower, upper, baseline_errors)
    for k, v in overall.items():
        results[f"overall_{k}" if k != "n" else "n_test_samples"] = v

    # --- Dimensional breakdowns (core three only) ---

    if "route_abbrev" in test_df.columns:
        results["by_route"] = _slice_metrics(
            test_df, errors, baseline_errors, "route_abbrev"
        )

    if "day_of_week" in test_df.columns:
        raw = _slice_metrics(test_df, errors, baseline_errors, "day_of_week")
        results["by_day_of_week"] = {
            DOW_LABELS.get(k, str(k)): v for k, v in sorted(raw.items())
        }

    if "hour_of_day" in test_df.columns:
        by_tod = {}
        for label, h_start, h_end in TIME_OF_DAY_BUCKETS:
            mask = (test_df["hour_of_day"] >= h_start) & (test_df["hour_of_day"] < h_end)
            if mask.sum() == 0:
                continue
            g_baseline = baseline_errors.loc[mask] if baseline_errors is not None else None
            m = compute_metrics(errors.loc[mask], baseline_errors=g_baseline)
            if m:
                by_tod[label] = m
        results["by_time_of_day"] = by_tod

    if "scheduled_departure" in test_df.columns:
        try:
            months = pd.to_datetime(test_df["scheduled_departure"]).dt.strftime("%Y-%m")
            temp_df = test_df.copy()
            temp_df["_month"] = months
            results["by_month"] = _slice_metrics(
                temp_df, errors, baseline_errors, "_month"
            )
        except Exception:
            pass

    minutes_col = test_df["minutes_until_scheduled_departure"]
    by_horizon = {}
    for label, lo, hi in HORIZON_BUCKETS:
        mask = (minutes_col >= lo) & (minutes_col < hi)
        if mask.sum() == 0:
            continue
        g_baseline = baseline_errors.loc[mask] if baseline_errors is not None else None
        m = compute_metrics(errors.loc[mask], baseline_errors=g_baseline)
        if m:
            by_horizon[label] = m
    results["by_horizon"] = by_horizon

    if "route_abbrev" in test_df.columns and "is_peak_hour" in test_df.columns:
        cross = {}
        for (route, peak), group in test_df.groupby(["route_abbrev", "is_peak_hour"]):
            idx = group.index
            g_baseline = baseline_errors.loc[idx] if baseline_errors is not None else None
            m = compute_metrics(errors.loc[idx], baseline_errors=g_baseline)
            if m:
                suffix = "peak" if peak else "off-peak"
                cross[f"{route} ({suffix})"] = m
        results["by_route_x_peak"] = cross

    if "sailing_event_id" in test_df.columns:
        results["n_test_events"] = int(test_df["sailing_event_id"].nunique())

    return results


def run_full_evaluation() -> Optional[dict]:
    """Run a full evaluation using the current predictor and database."""
    from ..ml_predictor import DelayPredictor

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

    test_df = evaluator._model.predict(test_df)
    return evaluate_predictions(test_df)


def print_evaluation(results: dict):
    """Pretty-print evaluation results to stdout."""
    print("\n=== Delay Prediction Evaluation ===")
    print(f"Test samples: {results.get('n_test_samples', '?')}", end="")
    if "n_test_events" in results:
        print(f" ({results['n_test_events']} sailing events)")
    else:
        print()

    print(f"\n  Pinball Loss: {results['overall_pinball_loss']} min (α={OVERPREDICTION_PENALTY})")
    print(f"  MAE:          {results['overall_mae']} min")
    print(f"  Bias:         {results['overall_bias']:+.2f} min (positive = risky)")
    print(f"  p90:          {results['overall_error_p90']:+.2f} min")
    print(f"  70% Coverage: {results['overall_coverage_70pct']}%")

    if "overall_baseline_pinball_loss" in results:
        print(f"\n  Baseline PL:   {results['overall_baseline_pinball_loss']} min")
        print(f"  Improvement:   {results['overall_improvement_pct']}%")

    if "by_route" in results:
        print(f"\nBy route:")
        print(f"  {'Route':<12} {'PL':>6} {'Bias':>7} {'p90':>7} {'N':>6}")
        for route, m in sorted(results["by_route"].items()):
            print(
                f"  {route:<12} {m['pinball_loss']:>6.2f} {m['bias']:>+6.2f} "
                f"{m['error_p90']:>+6.2f} {m['n']:>6}"
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
