"""Walk-forward backtesting pipeline for the delay prediction model.

Simulates real-world model performance by training on data up to time T,
predicting on the next fold, then sliding forward. Produces a markdown
report for experiment comparison.

Usage:
    # Run backtest with default settings (5 folds)
    python -m backend.backtest

    # Run with custom folds and save report
    python -m backend.backtest --folds 8 --name "baseline_v1"

    # Compare against a previous report
    python -m backend.backtest --name "new_features" --compare reports/baseline_v1.md
"""

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from .evaluation import _compute_group_metrics, evaluate_predictions

logger = logging.getLogger(__name__)

# Default model hyperparameters — override via backtest config
DEFAULT_HYPERPARAMS = {
    "max_iter": 200,
    "max_depth": 6,
    "learning_rate": 0.1,
    "random_state": 42,
}

FEATURE_COLS = [
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

CATEGORICAL_FEATURES = [0, 1, 2]  # route_abbrev, departing_terminal_id, day_of_week
TARGET_COL = "actual_delay_minutes"


def _encode_features(df: pd.DataFrame):
    """Encode categorical features and return (X array, route_mapping, terminal_mapping)."""
    X = df[FEATURE_COLS].copy()
    X["route_abbrev"] = X["route_abbrev"].astype("category").cat.codes
    X["departing_terminal_id"] = X["departing_terminal_id"].astype("category").cat.codes
    X["day_of_week"] = X["day_of_week"].astype("category").cat.codes

    route_mapping = dict(
        zip(
            df["route_abbrev"].astype("category").cat.categories,
            range(len(df["route_abbrev"].astype("category").cat.categories)),
        )
    )
    terminal_mapping = dict(
        zip(
            df["departing_terminal_id"].astype("category").cat.categories,
            range(len(df["departing_terminal_id"].astype("category").cat.categories)),
        )
    )
    return X.values, route_mapping, terminal_mapping


def _train_quantile_models(X_train, y_train, hyperparams: dict):
    """Train the three quantile models and return them as a dict."""
    quantiles = {"q50": 0.50, "q15": 0.15, "q85": 0.85}
    models = {}
    for name, quantile in quantiles.items():
        model = HistGradientBoostingRegressor(
            loss="quantile",
            quantile=quantile,
            categorical_features=CATEGORICAL_FEATURES,
            **hyperparams,
        )
        model.fit(X_train, y_train)
        models[name] = model
    return models


def walk_forward_backtest(
    df: pd.DataFrame,
    n_folds: int = 5,
    min_train_events: int = 200,
    hyperparams: Optional[dict] = None,
) -> dict:
    """Run walk-forward cross-validation on sailing event data.

    Splits unique sailing events into (n_folds + 1) chronological chunks.
    For fold i, trains on chunks 0..i, tests on chunk i+1.

    Returns a dict with per-fold results and aggregated metrics.
    """
    params = {**DEFAULT_HYPERPARAMS, **(hyperparams or {})}

    unique_events = df["sailing_event_id"].unique()
    n_events = len(unique_events)

    # We need n_folds + 1 chunks (first chunk is train-only, last is test-only)
    chunk_size = n_events // (n_folds + 1)
    if chunk_size < min_train_events // 2:
        logger.warning(
            f"Only {n_events} events for {n_folds} folds. "
            f"Reducing folds to fit data."
        )
        n_folds = max(1, (n_events // (min_train_events // 2)) - 1)
        chunk_size = n_events // (n_folds + 1)

    fold_results = []
    all_test_dfs = []

    for fold_idx in range(n_folds):
        # Train on events 0..(fold_idx+1)*chunk_size
        # Test on events (fold_idx+1)*chunk_size..(fold_idx+2)*chunk_size
        train_end = (fold_idx + 1) * chunk_size
        test_start = train_end
        test_end = min(test_start + chunk_size, n_events)

        if train_end < min_train_events:
            logger.info(f"Fold {fold_idx}: skipping, only {train_end} train events")
            continue

        train_event_ids = set(unique_events[:train_end])
        test_event_ids = set(unique_events[test_start:test_end])

        if len(test_event_ids) == 0:
            continue

        train_mask = df["sailing_event_id"].isin(train_event_ids)
        test_mask = df["sailing_event_id"].isin(test_event_ids)

        train_df = df[train_mask]
        test_df = df[test_mask].copy()

        # Encode and train
        X_train, _, _ = _encode_features(train_df)
        y_train = train_df[TARGET_COL].values

        # Encode test using same full-dataframe encoding for consistency
        X_test, _, _ = _encode_features(df)
        X_test = X_test[test_mask.values]

        models = _train_quantile_models(X_train, y_train, params)

        test_df["predicted_delay"] = models["q50"].predict(X_test)
        test_df["lower_bound"] = models["q15"].predict(X_test)
        test_df["upper_bound"] = models["q85"].predict(X_test)

        fold_eval = evaluate_predictions(test_df)

        # Date range for this fold's test set
        test_events_df = test_df.drop_duplicates("sailing_event_id")
        fold_eval["fold"] = fold_idx
        fold_eval["n_train_events"] = len(train_event_ids)
        fold_eval["n_test_events"] = len(test_event_ids)

        fold_results.append(fold_eval)
        all_test_dfs.append(test_df)

        logger.info(
            f"Fold {fold_idx}: train={len(train_event_ids)} events, "
            f"test={len(test_event_ids)} events, "
            f"MAE={fold_eval['overall_mae']}"
        )

    if not fold_results:
        return {"error": "Not enough data for walk-forward backtest"}

    # Aggregate across all folds
    combined_test_df = pd.concat(all_test_dfs, ignore_index=True)
    aggregate_eval = evaluate_predictions(combined_test_df)
    aggregate_eval["n_folds"] = len(fold_results)

    # Compute stability metrics (std dev across folds)
    fold_maes = [f["overall_mae"] for f in fold_results]
    fold_biases = [f["overall_mean_error"] for f in fold_results]
    fold_coverages = [f["coverage_70pct"] for f in fold_results]

    stability = {
        "mae_mean": round(float(np.mean(fold_maes)), 2),
        "mae_std": round(float(np.std(fold_maes)), 2),
        "bias_mean": round(float(np.mean(fold_biases)), 2),
        "bias_std": round(float(np.std(fold_biases)), 2),
        "coverage_mean": round(float(np.mean(fold_coverages)), 1),
        "coverage_std": round(float(np.std(fold_coverages)), 1),
    }

    return {
        "fold_results": fold_results,
        "aggregate": aggregate_eval,
        "stability": stability,
        "hyperparams": params,
        "n_total_events": int(len(unique_events)),
        "n_folds": len(fold_results),
    }


def generate_markdown_report(
    backtest_results: dict,
    experiment_name: str = "unnamed",
    description: str = "",
    comparison: Optional[dict] = None,
) -> str:
    """Generate a markdown-formatted report from backtest results."""
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append(f"# Backtest Report: {experiment_name}")
    lines.append(f"")
    lines.append(f"**Date:** {now}")
    if description:
        lines.append(f"**Description:** {description}")
    lines.append(f"**Total sailing events:** {backtest_results['n_total_events']}")
    lines.append(f"**Walk-forward folds:** {backtest_results['n_folds']}")
    lines.append("")

    # Hyperparameters
    params = backtest_results["hyperparams"]
    lines.append("## Hyperparameters")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("|-----------|-------|")
    for k, v in sorted(params.items()):
        lines.append(f"| {k} | {v} |")
    lines.append("")

    # Aggregate results
    agg = backtest_results["aggregate"]
    stab = backtest_results["stability"]

    lines.append("## Aggregate Results (all folds combined)")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Test samples | {agg['n_test_samples']} |")
    lines.append(f"| Mean Error (bias) | {agg['overall_mean_error']} min |")
    lines.append(f"| MAE | {agg['overall_mae']} min |")
    lines.append(f"| RMSE | {agg['overall_rmse']} min |")
    lines.append(f"| Median AE | {agg['overall_median_ae']} min |")
    lines.append(f"| 70% Interval Coverage | {agg['coverage_70pct']}% |")
    if "baseline_mae" in agg:
        lines.append(f"| Baseline MAE (flat delay) | {agg['baseline_mae']} min |")
        lines.append(f"| Improvement vs baseline | {agg['improvement_pct']}% |")
    lines.append("")

    # Stability across folds
    lines.append("## Stability Across Folds")
    lines.append("")
    lines.append("| Metric | Mean | Std Dev |")
    lines.append("|--------|------|---------|")
    lines.append(f"| MAE | {stab['mae_mean']} min | ±{stab['mae_std']} min |")
    lines.append(f"| Bias | {stab['bias_mean']} min | ±{stab['bias_std']} min |")
    lines.append(f"| Coverage | {stab['coverage_mean']}% | ±{stab['coverage_std']}% |")
    lines.append("")

    # Per-fold breakdown
    lines.append("## Per-Fold Results")
    lines.append("")
    lines.append("| Fold | Train Events | Test Events | MAE | Bias | Coverage | Impr% |")
    lines.append("|------|-------------|-------------|-----|------|----------|-------|")
    for f in backtest_results["fold_results"]:
        impr = f"{f['improvement_pct']}%" if "improvement_pct" in f else "N/A"
        lines.append(
            f"| {f['fold']} | {f['n_train_events']} | {f['n_test_events']} | "
            f"{f['overall_mae']} | {f['overall_mean_error']:+.2f} | "
            f"{f['coverage_70pct']}% | {impr} |"
        )
    lines.append("")

    # Per-route breakdown
    if "error_by_route" in agg:
        lines.append("## Per-Route Breakdown")
        lines.append("")
        lines.append("| Route | MAE | Bias | RMSE | Coverage | Impr% | N |")
        lines.append("|-------|-----|------|------|----------|-------|---|")
        for route, m in sorted(agg["error_by_route"].items()):
            impr = f"{m['improvement_pct']}%" if "improvement_pct" in m else "N/A"
            lines.append(
                f"| {route} | {m['mae']} | {m['mean_error']:+.2f} | "
                f"{m['rmse']} | {m['coverage_70pct']}% | {impr} | {m['n']} |"
            )
        lines.append("")

    # Error by horizon (sampled — show every 10 min to keep report readable)
    horizon_data = agg.get("error_by_horizon", [])
    if horizon_data:
        lines.append("## Error by Prediction Horizon")
        lines.append("")
        lines.append("| Minutes Out | MAE | Bias | Coverage | N |")
        lines.append("|-------------|-----|------|----------|---|")
        for row in horizon_data:
            mins = row["minutes_out"]
            # Show every 10 minutes plus first/last
            if mins % 10 == 0 or mins <= 4 or mins >= 120:
                lines.append(
                    f"| {mins}m | {row['mae']} | {row['mean_error']:+.2f} | "
                    f"{row['coverage_70pct']}% | {row['n']} |"
                )
        lines.append("")

    # Comparison section
    if comparison:
        lines.append("## Comparison vs Previous Run")
        lines.append("")
        prev = comparison
        lines.append("| Metric | Previous | Current | Delta |")
        lines.append("|--------|----------|---------|-------|")

        def _delta(prev_val, curr_val, lower_is_better=True):
            d = curr_val - prev_val
            sign = "+" if d > 0 else ""
            better = (d < 0) if lower_is_better else (d > 0)
            indicator = "better" if better else "worse"
            return f"{sign}{d:.2f} ({indicator})"

        if "overall_mae" in prev and "overall_mae" in agg:
            lines.append(
                f"| MAE | {prev['overall_mae']} | {agg['overall_mae']} | "
                f"{_delta(prev['overall_mae'], agg['overall_mae'])} |"
            )
        if "overall_rmse" in prev and "overall_rmse" in agg:
            lines.append(
                f"| RMSE | {prev['overall_rmse']} | {agg['overall_rmse']} | "
                f"{_delta(prev['overall_rmse'], agg['overall_rmse'])} |"
            )
        if "overall_mean_error" in prev and "overall_mean_error" in agg:
            prev_abs = abs(prev["overall_mean_error"])
            curr_abs = abs(agg["overall_mean_error"])
            lines.append(
                f"| |Bias| | {prev_abs:.2f} | {curr_abs:.2f} | "
                f"{_delta(prev_abs, curr_abs)} |"
            )
        if "coverage_70pct" in prev and "coverage_70pct" in agg:
            lines.append(
                f"| Coverage | {prev['coverage_70pct']}% | {agg['coverage_70pct']}% | "
                f"{_delta(prev['coverage_70pct'], agg['coverage_70pct'], lower_is_better=False)} |"
            )
        if "improvement_pct" in prev and "improvement_pct" in agg:
            lines.append(
                f"| Impr vs baseline | {prev['improvement_pct']}% | {agg['improvement_pct']}% | "
                f"{_delta(prev['improvement_pct'], agg['improvement_pct'], lower_is_better=False)} |"
            )

        # Per-route comparison
        prev_routes = prev.get("error_by_route", {})
        curr_routes = agg.get("error_by_route", {})
        all_routes = sorted(set(prev_routes) | set(curr_routes))
        if all_routes:
            lines.append("")
            lines.append("### Per-Route Comparison (MAE)")
            lines.append("")
            lines.append("| Route | Previous | Current | Delta |")
            lines.append("|-------|----------|---------|-------|")
            for r in all_routes:
                p = prev_routes.get(r, {}).get("mae", "N/A")
                c = curr_routes.get(r, {}).get("mae", "N/A")
                if isinstance(p, (int, float)) and isinstance(c, (int, float)):
                    lines.append(f"| {r} | {p} | {c} | {_delta(p, c)} |")
                else:
                    lines.append(f"| {r} | {p} | {c} | — |")
        lines.append("")

    # Raw JSON for programmatic comparison
    lines.append("## Raw Results (JSON)")
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>Click to expand</summary>")
    lines.append("")
    lines.append("```json")
    # Store only aggregate + stability + hyperparams for comparison
    exportable = {
        "aggregate": agg,
        "stability": stab,
        "hyperparams": backtest_results["hyperparams"],
        "n_total_events": backtest_results["n_total_events"],
        "n_folds": backtest_results["n_folds"],
    }
    lines.append(json.dumps(exportable, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    return "\n".join(lines)


def parse_previous_report(report_path: str) -> Optional[dict]:
    """Parse the JSON block from a previous markdown report for comparison."""
    try:
        content = Path(report_path).read_text()
        # Extract JSON from the ```json ... ``` block
        start = content.find("```json\n")
        if start == -1:
            return None
        start += len("```json\n")
        end = content.find("\n```", start)
        if end == -1:
            return None
        raw = content[start:end]
        data = json.loads(raw)
        return data.get("aggregate", data)
    except Exception as e:
        logger.warning(f"Could not parse previous report {report_path}: {e}")
        return None


def run_backtest(
    n_folds: int = 5,
    experiment_name: str = "unnamed",
    description: str = "",
    hyperparams: Optional[dict] = None,
    compare_path: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Optional[str]:
    """Run a full backtest and write a markdown report. Returns the report path."""
    from .ml_predictor import DelayPredictor

    predictor = DelayPredictor()
    df = predictor.build_training_data()
    if df is None:
        logger.error("Cannot build training data — not enough sailing events")
        return None

    logger.info(f"Running walk-forward backtest with {n_folds} folds...")
    results = walk_forward_backtest(df, n_folds=n_folds, hyperparams=hyperparams)

    if "error" in results:
        logger.error(results["error"])
        return None

    # Load comparison data if provided
    comparison = None
    if compare_path:
        comparison = parse_previous_report(compare_path)
        if comparison:
            logger.info(f"Loaded comparison from {compare_path}")
        else:
            logger.warning(f"Could not load comparison from {compare_path}")

    report = generate_markdown_report(results, experiment_name, description, comparison)

    # Write report
    reports_dir = Path(output_dir) if output_dir else Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{experiment_name}_{timestamp}.md"
    report_path = reports_dir / filename
    report_path.write_text(report)

    logger.info(f"Report written to {report_path}")
    return str(report_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Run walk-forward backtest")
    parser.add_argument(
        "--folds", type=int, default=5, help="Number of walk-forward folds (default: 5)"
    )
    parser.add_argument(
        "--name", type=str, default="experiment", help="Experiment name for the report"
    )
    parser.add_argument(
        "--description", type=str, default="", help="Description of what changed"
    )
    parser.add_argument(
        "--compare", type=str, default=None, help="Path to a previous report .md to compare against"
    )
    parser.add_argument(
        "--output-dir", type=str, default=None, help="Directory for report output (default: reports/)"
    )
    # Hyperparameter overrides
    parser.add_argument("--max-iter", type=int, default=None)
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--learning-rate", type=float, default=None)

    args = parser.parse_args()

    from .database import init_db

    init_db()

    # Build hyperparams from CLI overrides
    hp_overrides = {}
    if args.max_iter is not None:
        hp_overrides["max_iter"] = args.max_iter
    if args.max_depth is not None:
        hp_overrides["max_depth"] = args.max_depth
    if args.learning_rate is not None:
        hp_overrides["learning_rate"] = args.learning_rate

    report_path = run_backtest(
        n_folds=args.folds,
        experiment_name=args.name,
        description=args.description,
        hyperparams=hp_overrides if hp_overrides else None,
        compare_path=args.compare,
        output_dir=args.output_dir,
    )

    if report_path:
        print(f"\nReport saved to: {report_path}")
        print(Path(report_path).read_text())
    else:
        print("Backtest failed. Check logs above.")
