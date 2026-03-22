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

from .evaluation import compute_metrics, evaluate_predictions

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

    chunk_size = n_events // (n_folds + 1)
    if chunk_size < min_train_events // 2:
        logger.warning(
            f"Only {n_events} events for {n_folds} folds. Reducing folds to fit data."
        )
        n_folds = max(1, (n_events // (min_train_events // 2)) - 1)
        chunk_size = n_events // (n_folds + 1)

    fold_results = []
    all_test_dfs = []

    for fold_idx in range(n_folds):
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

        X_train, _, _ = _encode_features(train_df)
        y_train = train_df[TARGET_COL].values

        X_test, _, _ = _encode_features(df)
        X_test = X_test[test_mask.values]

        models = _train_quantile_models(X_train, y_train, params)

        test_df["predicted_delay"] = models["q50"].predict(X_test)
        test_df["lower_bound"] = models["q15"].predict(X_test)
        test_df["upper_bound"] = models["q85"].predict(X_test)

        fold_eval = evaluate_predictions(test_df)
        fold_eval["fold"] = fold_idx
        fold_eval["n_train_events"] = len(train_event_ids)

        fold_results.append(fold_eval)
        all_test_dfs.append(test_df)

        logger.info(
            f"Fold {fold_idx}: train={len(train_event_ids)} events, "
            f"test={fold_eval.get('n_test_events', '?')} events, "
            f"MAE={fold_eval['overall_mae']}, ±2min={fold_eval['overall_within_2min']}%"
        )

    if not fold_results:
        return {"error": "Not enough data for walk-forward backtest"}

    # Aggregate across all folds
    combined_test_df = pd.concat(all_test_dfs, ignore_index=True)
    aggregate_eval = evaluate_predictions(combined_test_df)
    aggregate_eval["n_folds"] = len(fold_results)

    # Stability across folds
    def _fold_stat(key):
        vals = [f[key] for f in fold_results if key in f]
        if not vals:
            return None
        return {"mean": round(float(np.mean(vals)), 2), "std": round(float(np.std(vals)), 2)}

    stability = {
        "within_2min": _fold_stat("overall_within_2min"),
        "mae": _fold_stat("overall_mae"),
        "bias": _fold_stat("overall_bias"),
        "coverage": _fold_stat("overall_coverage_70pct"),
    }

    return {
        "fold_results": fold_results,
        "aggregate": aggregate_eval,
        "stability": stability,
        "hyperparams": params,
        "n_total_events": int(len(unique_events)),
        "n_folds": len(fold_results),
    }


# ---------------------------------------------------------------------------
# Markdown report generation
# ---------------------------------------------------------------------------

def _metric_table(data: dict, key_label: str, sort_by: Optional[str] = None) -> list:
    """Render a dict of {label: metrics} as a markdown table.

    Columns: key_label | ±2 min | ±5 min | MAE | Bias | Coverage | Impr% | N
    """
    lines = []
    lines.append(f"| {key_label} | ±2 min | ±5 min | MAE | Bias | Coverage | Impr% | N |")
    lines.append("|" + "|".join(["---"] * 8) + "|")

    items = sorted(data.items(), key=lambda x: x[1].get(sort_by, x[0]) if sort_by else x[0])
    for label, m in items:
        impr = f"{m['improvement_pct']}%" if "improvement_pct" in m else "—"
        lines.append(
            f"| {label} | {m['within_2min']}% | {m['within_5min']}% | "
            f"{m['mae']} | {m['bias']:+.2f} | {m['coverage_70pct']}% | {impr} | {m['n']} |"
        )
    return lines


def _delta_str(prev_val, curr_val, lower_is_better=True):
    """Format a delta with better/worse indicator."""
    d = curr_val - prev_val
    sign = "+" if d > 0 else ""
    better = (d < 0) if lower_is_better else (d > 0)
    return f"{sign}{d:.2f} ({'better' if better else 'worse'})"


def generate_markdown_report(
    backtest_results: dict,
    experiment_name: str = "unnamed",
    description: str = "",
    comparison: Optional[dict] = None,
) -> str:
    """Generate a markdown-formatted report from backtest results."""
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    agg = backtest_results["aggregate"]
    stab = backtest_results["stability"]

    # ---- Header ----
    lines.append(f"# Backtest Report: {experiment_name}")
    lines.append("")
    if description:
        lines.append(f"> {description}")
        lines.append("")
    lines.append(f"**Date:** {now}  ")
    lines.append(f"**Sailing events:** {backtest_results['n_total_events']}  ")
    lines.append(f"**Walk-forward folds:** {backtest_results['n_folds']}")
    lines.append("")

    # ---- TOP-LINE RESULTS (the thing you look at first) ----
    lines.append("## Top-Line Results")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")

    w2 = agg["overall_within_2min"]
    w5 = agg["overall_within_5min"]
    mae = agg["overall_mae"]
    bias = agg["overall_bias"]
    cov = agg["overall_coverage_70pct"]

    lines.append(f"| **Predictions within ±2 min** | **{w2}%** |")
    lines.append(f"| Predictions within ±5 min | {w5}% |")
    lines.append(f"| Mean Absolute Error | {mae} min |")
    lines.append(f"| Bias (positive = overpredicts delay) | {bias:+.2f} min |")
    lines.append(f"| 70% Prediction Interval Coverage | {cov}% |")
    if "overall_baseline_mae" in agg:
        lines.append(f"| Baseline MAE (flat delay) | {agg['overall_baseline_mae']} min |")
        lines.append(f"| Improvement vs baseline | {agg['overall_improvement_pct']}% |")
    lines.append("")

    # ---- Comparison (right after top-line if available) ----
    if comparison:
        lines.extend(_comparison_section(agg, comparison))

    # ---- Stability across folds ----
    lines.append("## Walk-Forward Stability")
    lines.append("")
    lines.append("| Metric | Mean | Std Dev | Interpretation |")
    lines.append("|--------|------|---------|----------------|")
    for key, label, note_fn in [
        ("within_2min", "±2 min accuracy", lambda s: "stable" if s["std"] < 3 else "variable"),
        ("mae", "MAE", lambda s: "stable" if s["std"] < 0.5 else "variable"),
        ("bias", "Bias", lambda s: "consistent" if abs(s["mean"]) < 1 and s["std"] < 0.5 else "drifting"),
        ("coverage", "Coverage", lambda s: "calibrated" if abs(s["mean"] - 70) < 5 else "miscalibrated"),
    ]:
        s = stab.get(key)
        if s:
            lines.append(f"| {label} | {s['mean']} | ±{s['std']} | {note_fn(s)} |")
    lines.append("")

    # Per-fold detail
    lines.append("| Fold | Train Events | Test Events | ±2 min | MAE | Bias |")
    lines.append("|------|-------------|-------------|--------|-----|------|")
    for f in backtest_results["fold_results"]:
        lines.append(
            f"| {f['fold']} | {f['n_train_events']} | {f.get('n_test_events', '?')} | "
            f"{f['overall_within_2min']}% | {f['overall_mae']} | {f['overall_bias']:+.2f} |"
        )
    lines.append("")

    # ---- Dimensional breakdowns ----

    if "by_route" in agg and agg["by_route"]:
        lines.append("## By Route")
        lines.append("")
        lines.extend(_metric_table(agg["by_route"], "Route"))
        lines.append("")

    if "by_day_of_week" in agg and agg["by_day_of_week"]:
        lines.append("## By Day of Week")
        lines.append("")
        lines.extend(_metric_table(agg["by_day_of_week"], "Day"))
        lines.append("")

    if "by_time_of_day" in agg and agg["by_time_of_day"]:
        lines.append("## By Time of Day")
        lines.append("")
        lines.extend(_metric_table(agg["by_time_of_day"], "Period"))
        lines.append("")

    if "by_month" in agg and agg["by_month"]:
        lines.append("## By Month")
        lines.append("")
        lines.extend(_metric_table(agg["by_month"], "Month"))
        lines.append("")

    if "by_horizon" in agg and agg["by_horizon"]:
        lines.append("## By Prediction Horizon")
        lines.append("")
        lines.extend(_metric_table(agg["by_horizon"], "Horizon"))
        lines.append("")

    if "by_route_x_peak" in agg and agg["by_route_x_peak"]:
        lines.append("## Route x Peak vs Off-Peak")
        lines.append("")
        lines.extend(_metric_table(agg["by_route_x_peak"], "Route (period)"))
        lines.append("")

    # ---- Hyperparameters ----
    params = backtest_results["hyperparams"]
    lines.append("## Hyperparameters")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("|-----------|-------|")
    for k, v in sorted(params.items()):
        lines.append(f"| {k} | {v} |")
    lines.append("")

    # ---- Raw JSON ----
    lines.append("## Raw Results (JSON)")
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>Click to expand</summary>")
    lines.append("")
    lines.append("```json")
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


def _comparison_section(agg: dict, prev: dict) -> list:
    """Build the comparison-vs-previous section."""
    lines = []
    lines.append("## Comparison vs Previous Run")
    lines.append("")
    lines.append("| Metric | Previous | Current | Delta |")
    lines.append("|--------|----------|---------|-------|")

    comparisons = [
        ("±2 min accuracy", "overall_within_2min", "%", False),
        ("±5 min accuracy", "overall_within_5min", "%", False),
        ("MAE", "overall_mae", " min", True),
        ("Bias (abs)", None, " min", True),  # special handling
        ("Coverage", "overall_coverage_70pct", "%", False),
        ("Improvement vs baseline", "overall_improvement_pct", "%", False),
    ]

    for label, key, suffix, lower_is_better in comparisons:
        if key is None:
            # Bias absolute value
            p = prev.get("overall_bias")
            c = agg.get("overall_bias")
            if p is not None and c is not None:
                pa, ca = abs(p), abs(c)
                lines.append(
                    f"| {label} | {pa:.2f}{suffix} | {ca:.2f}{suffix} | "
                    f"{_delta_str(pa, ca, lower_is_better=True)} |"
                )
            continue

        p = prev.get(key)
        c = agg.get(key)
        if p is not None and c is not None:
            lines.append(
                f"| {label} | {p}{suffix} | {c}{suffix} | "
                f"{_delta_str(p, c, lower_is_better)} |"
            )

    # Per-route comparison
    prev_routes = prev.get("by_route", {})
    curr_routes = agg.get("by_route", {})
    all_routes = sorted(set(prev_routes) | set(curr_routes))
    if all_routes:
        lines.append("")
        lines.append("### Per-Route Comparison")
        lines.append("")
        lines.append("| Route | Prev ±2min | Curr ±2min | Prev MAE | Curr MAE | MAE Delta |")
        lines.append("|-------|-----------|-----------|----------|----------|-----------|")
        for r in all_routes:
            pw2 = prev_routes.get(r, {}).get("within_2min", "—")
            cw2 = curr_routes.get(r, {}).get("within_2min", "—")
            pm = prev_routes.get(r, {}).get("mae", "—")
            cm = curr_routes.get(r, {}).get("mae", "—")
            delta = _delta_str(pm, cm) if isinstance(pm, (int, float)) and isinstance(cm, (int, float)) else "—"
            lines.append(f"| {r} | {pw2}% | {cw2}% | {pm} | {cm} | {delta} |")

    lines.append("")
    return lines


def parse_previous_report(report_path: str) -> Optional[dict]:
    """Parse the JSON block from a previous markdown report for comparison."""
    try:
        content = Path(report_path).read_text()
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

    comparison = None
    if compare_path:
        comparison = parse_previous_report(compare_path)
        if comparison:
            logger.info(f"Loaded comparison from {compare_path}")
        else:
            logger.warning(f"Could not load comparison from {compare_path}")

    report = generate_markdown_report(results, experiment_name, description, comparison)

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
    parser.add_argument("--folds", type=int, default=5, help="Number of walk-forward folds (default: 5)")
    parser.add_argument("--name", type=str, default="experiment", help="Experiment name for the report")
    parser.add_argument("--description", type=str, default="", help="Description of what changed")
    parser.add_argument("--compare", type=str, default=None, help="Path to a previous report .md to compare against")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory for report output (default: reports/)")
    parser.add_argument("--max-iter", type=int, default=None)
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--learning-rate", type=float, default=None)

    args = parser.parse_args()

    from .database import init_db

    init_db()

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
