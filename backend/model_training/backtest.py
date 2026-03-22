"""Walk-forward backtesting harness for delay prediction models.

MODEL-AGNOSTIC. This module knows nothing about features, encodings, or
sklearn. It only:
1. Splits data into chronological folds by sailing_event_id
2. Calls model.fit(train_df) and model.predict(test_df)
3. Scores predictions via evaluation.py

To change the model or features, edit backtest_model.py or pass a custom
model_factory. Never change this file for model experiments.

Walk-forward strategy and data leakage prevention
--------------------------------------------------
Standard k-fold CV randomly assigns rows to folds. This is WRONG for time
series because it lets the model train on future data and predict the past.
For ferry delays, that would mean training on a Friday afternoon sailing and
"predicting" a Monday morning one — the model sees patterns it wouldn't have
in production.

Walk-forward CV fixes this:

    Events (chronological):  [----chunk 0----][----chunk 1----][----chunk 2----][----chunk 3----]

    Fold 0:  train=[chunk 0]           test=[chunk 1]
    Fold 1:  train=[chunk 0, chunk 1]  test=[chunk 2]
    Fold 2:  train=[chunk 0..2]        test=[chunk 3]

At every fold, the model ONLY trains on data that came before the test set.
This matches production exactly: we deploy a model trained on historical data
and predict future sailings.

Additional safeguards:
- Splits are by sailing_event_id, not by row. Each sailing event generates
  many rows (one per prediction horizon: 2min, 4min, ..., 90min before
  departure). If we split by row, some horizons from the same event could
  land in train and others in test — leaking the outcome.
- min_train_events ensures the model has enough data before we start scoring,
  so early folds with tiny training sets don't pollute the aggregate metrics.

Usage:
    python -m backend.model_training.backtest
    python -m backend.model_training.backtest --folds 8 --name "baseline_v1"
    python -m backend.model_training.backtest --name "new_features" --compare reports/baseline_v1.md
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pandas as pd

from .backtest_model import BacktestModel, QuantileGBTModel
from .evaluation import evaluate_predictions
from .report import generate_markdown_report, parse_previous_report

logger = logging.getLogger(__name__)


def walk_forward_backtest(
    df: pd.DataFrame,
    model_factory: Callable[[], BacktestModel],
    n_folds: int = 5,
    min_train_events: int = 200,
) -> dict:
    """Run walk-forward cross-validation on sailing event data.

    model_factory: callable that returns a fresh BacktestModel for each fold.
    The harness calls model.fit(train_df) then model.predict(test_df).
    predict() must return test_df with columns: predicted_delay, lower_bound,
    upper_bound.

    Splits unique sailing events into (n_folds + 1) chronological chunks.
    For fold i, trains on chunks 0..i, tests on chunk i+1.
    """
    unique_events = df["sailing_event_id"].unique()
    n_events = len(unique_events)

    chunk_size = n_events // (n_folds + 1)
    if chunk_size < min_train_events // 2:
        logger.warning(
            f"Only {n_events} events for {n_folds} folds. Reducing folds to fit data."
        )
        n_folds = max(1, (n_events // (min_train_events // 2)) - 1)
        chunk_size = n_events // (n_folds + 1)

    # When n_folds==1, ensure the train window is at least min_train_events
    # so the single fold doesn't get skipped by the threshold check below.
    if n_folds == 1 and chunk_size < min_train_events and n_events >= min_train_events:
        chunk_size = min_train_events

    fold_results = []
    all_test_dfs = []

    for fold_idx in range(n_folds):
        train_end = (fold_idx + 1) * chunk_size
        test_start = train_end
        # Last fold absorbs all remaining events (fixes remainder-drop bug)
        if fold_idx == n_folds - 1:
            test_end = n_events
        else:
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
        test_df = df[test_mask]

        # Model owns all feature/encoding/training logic
        model = model_factory()
        model.fit(train_df)
        test_df = model.predict(test_df)

        fold_eval = evaluate_predictions(test_df)
        fold_eval["fold"] = fold_idx
        fold_eval["n_train_events"] = len(train_event_ids)

        fold_results.append(fold_eval)
        all_test_dfs.append(test_df)

        logger.info(
            f"Fold {fold_idx}: train={len(train_event_ids)} events, "
            f"test={fold_eval.get('n_test_events', '?')} events, "
            f"PL={fold_eval['overall_pinball_loss']}, "
            f"bias={fold_eval['overall_bias']:+.2f}, "
            f"p90={fold_eval['overall_error_p90']:+.2f}"
        )

    if not fold_results:
        return {"error": "Not enough data for walk-forward backtest"}

    combined_test_df = pd.concat(all_test_dfs, ignore_index=True)
    aggregate_eval = evaluate_predictions(combined_test_df)
    aggregate_eval["n_folds"] = len(fold_results)

    def _fold_stat(key):
        vals = [f[key] for f in fold_results if key in f]
        if not vals:
            return None
        return {"mean": round(float(np.mean(vals)), 2), "std": round(float(np.std(vals)), 2)}

    stability = {
        "pinball_loss": _fold_stat("overall_pinball_loss"),
        "bias": _fold_stat("overall_bias"),
        "error_p90": _fold_stat("overall_error_p90"),
    }

    return {
        "fold_results": fold_results,
        "aggregate": aggregate_eval,
        "stability": stability,
        "n_total_events": int(len(unique_events)),
        "n_folds": len(fold_results),
    }


def run_backtest(
    model_factory: Optional[Callable[[], BacktestModel]] = None,
    n_folds: int = 5,
    experiment_name: str = "unnamed",
    description: str = "",
    compare_path: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Optional[str]:
    """Run a full backtest and write a markdown report. Returns the report path."""
    from ..ml_predictor import DelayPredictor

    if model_factory is None:
        model_factory = QuantileGBTModel

    predictor = DelayPredictor()
    df = predictor.build_training_data()
    if df is None:
        logger.error("Cannot build training data — not enough sailing events")
        return None

    logger.info(f"Running walk-forward backtest with {n_folds} folds...")
    results = walk_forward_backtest(df, model_factory=model_factory, n_folds=n_folds)

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
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--name", type=str, default="experiment")
    parser.add_argument("--description", type=str, default="")
    parser.add_argument("--compare", type=str, default=None)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--max-iter", type=int, default=None)
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--learning-rate", type=float, default=None)

    args = parser.parse_args()

    from ..database import init_db

    init_db()

    hp_overrides = {}
    if args.max_iter is not None:
        hp_overrides["max_iter"] = args.max_iter
    if args.max_depth is not None:
        hp_overrides["max_depth"] = args.max_depth
    if args.learning_rate is not None:
        hp_overrides["learning_rate"] = args.learning_rate

    factory = (lambda: QuantileGBTModel(hp_overrides)) if hp_overrides else None

    report_path = run_backtest(
        model_factory=factory,
        n_folds=args.folds,
        experiment_name=args.name,
        description=args.description,
        compare_path=args.compare,
        output_dir=args.output_dir,
    )

    if report_path:
        print(f"\nReport saved to: {report_path}")
        print(Path(report_path).read_text())
    else:
        print("Backtest failed. Check logs above.")
