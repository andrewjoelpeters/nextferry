"""Backtest harness for the at-dock delay prediction model.

Runs walk-forward cross-validation on at-dock training data, comparing
the AtDockGBTModel against the FlatDelayBaseline (option C).

Usage:
    python -m backend.model_training.backtest_at_dock
    python -m backend.model_training.backtest_at_dock --folds 5 --name "at_dock_v1"
"""

import argparse
import logging
import time
from pathlib import Path

from sklearn.inspection import permutation_importance

from .at_dock_model import (
    AT_DOCK_FEATURE_COLS,
    AT_DOCK_TARGET_COL,
    AtDockGBTModel,
    FlatDelayBaseline,
)
from .backtest import walk_forward_backtest
from .report import generate_markdown_report

logger = logging.getLogger(__name__)


def _compute_feature_importance(
    df, n_repeats: int = 5
) -> dict:
    """Compute permutation importance overall and per route."""
    results = {}

    def _importance(subset_df) -> list[dict]:
        model = AtDockGBTModel()
        model.fit(subset_df)
        X = model._encode(subset_df)
        y = subset_df[AT_DOCK_TARGET_COL].values
        r = permutation_importance(
            model.models["q50"],
            X,
            y,
            n_repeats=n_repeats,
            random_state=42,
            scoring="neg_mean_absolute_error",
        )
        pairs = sorted(
            zip(AT_DOCK_FEATURE_COLS, r.importances_mean, strict=True),
            key=lambda x: -x[1],
        )
        return [
            {"feature": feat, "importance": round(float(imp), 4)}
            for feat, imp in pairs
        ]

    results["overall"] = _importance(df)

    for route in sorted(df["route_abbrev"].unique()):
        route_df = df[df["route_abbrev"] == route]
        results[route] = _importance(route_df)

    return results


def run_at_dock_backtest(
    n_folds: int = 5,
    experiment_name: str = "at_dock",
    output_dir: str | None = None,
) -> str | None:
    """Run walk-forward backtests for both the GBT model and flat baseline."""
    from ..dock_predictor import DockPredictor

    predictor = DockPredictor()
    df = predictor.build_training_data()
    if df is None:
        logger.error("Cannot build at-dock training data — not enough data")
        return None

    n_events = df["sailing_event_id"].nunique()
    n_rows = len(df)
    logger.info(f"At-dock training data: {n_rows} rows from {n_events} events")

    reports_dir = Path(output_dir) if output_dir else Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    # --- Run baseline (flat delay = option C) ---
    logger.info("=" * 60)
    logger.info("Running baseline (flat delay propagation)...")
    t0 = time.monotonic()
    baseline_results = walk_forward_backtest(
        df, model_factory=FlatDelayBaseline, n_folds=n_folds
    )
    baseline_time = time.monotonic() - t0

    if "error" in baseline_results:
        logger.error(f"Baseline failed: {baseline_results['error']}")
        return None

    baseline_results["training_time_seconds"] = round(baseline_time, 1)
    baseline_report = generate_markdown_report(
        baseline_results,
        f"{experiment_name}_baseline",
        "Flat delay baseline (option C): predict departure delay = previous vessel delay",
    )
    baseline_path = reports_dir / f"{experiment_name}_baseline.md"
    baseline_path.write_text(baseline_report)
    logger.info(f"Baseline report: {baseline_path}")

    # --- Run GBT model ---
    logger.info("=" * 60)
    logger.info("Running at-dock GBT model...")
    t0 = time.monotonic()
    gbt_results = walk_forward_backtest(
        df, model_factory=AtDockGBTModel, n_folds=n_folds
    )
    gbt_time = time.monotonic() - t0

    if "error" in gbt_results:
        logger.error(f"GBT model failed: {gbt_results['error']}")
        return None

    gbt_results["training_time_seconds"] = round(gbt_time, 1)

    # --- Feature importance (train on all data, permutation importance) ---
    logger.info("Computing feature importance...")
    feature_importance = _compute_feature_importance(df)
    gbt_results["feature_importance"] = feature_importance

    # Use baseline aggregate as comparison

    comparison = baseline_results.get("aggregate")

    gbt_report = generate_markdown_report(
        gbt_results,
        experiment_name,
        "At-dock GBT model: predicts departure delay for vessels currently at dock",
        comparison=comparison,
    )
    gbt_path = reports_dir / f"{experiment_name}_gbt.md"
    gbt_path.write_text(gbt_report)
    logger.info(f"GBT report: {gbt_path}")

    # --- Print summary ---
    ba = baseline_results["aggregate"]
    ga = gbt_results["aggregate"]

    print("\n" + "=" * 60)
    print("AT-DOCK MODEL BACKTEST SUMMARY")
    print("=" * 60)
    print(f"\nTraining data: {n_rows} rows from {n_events} sailing events")
    print(f"Walk-forward folds: {n_folds}")
    print()
    print(f"{'Metric':<25} {'Baseline (C)':>14} {'GBT Model (B)':>14}")
    print("-" * 55)
    print(
        f"{'Pinball Loss':<25} {ba['overall_pinball_loss']:>14.2f} "
        f"{ga['overall_pinball_loss']:>14.2f}"
    )
    print(
        f"{'MAE':<25} {ba['overall_mae']:>14.2f} "
        f"{ga['overall_mae']:>14.2f}"
    )
    print(
        f"{'Bias':<25} {ba['overall_bias']:>+14.2f} "
        f"{ga['overall_bias']:>+14.2f}"
    )
    print(
        f"{'p90 (tail risk)':<25} {ba['overall_error_p90']:>+14.2f} "
        f"{ga['overall_error_p90']:>+14.2f}"
    )
    print(
        f"{'70% Coverage':<25} {ba['overall_coverage_70pct']:>13.1f}% "
        f"{ga['overall_coverage_70pct']:>13.1f}%"
    )

    if ga.get("overall_improvement_pct") is not None:
        print(f"\nGBT improvement vs baseline: {ga['overall_improvement_pct']}%")

    print("\nReports saved to:")
    print(f"  Baseline: {baseline_path}")
    print(f"  GBT:      {gbt_path}")

    return str(gbt_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Backtest at-dock delay model")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--name", type=str, default="at_dock")
    parser.add_argument("--output-dir", type=str, default=None)

    args = parser.parse_args()

    from ..database import init_db

    init_db()

    run_at_dock_backtest(
        n_folds=args.folds,
        experiment_name=args.name,
        output_dir=args.output_dir,
    )
