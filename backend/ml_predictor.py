"""ML delay predictor using HistGradientBoostingRegressor with quantile loss.

Delegates model training, encoding, and prediction to QuantileGBTModel
(backend.model_training.backtest_model), which is the single source of truth
for features, hyperparams, and categorical encoding.

This module owns:
- Data loading (build_training_data)
- Save/load orchestration (volume models, feature-compatibility validation)
- The predict() API surface consumed by the serving layer
- The module-level singleton

Usage:
    # Train from command line
    python -m backend.ml_predictor
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from .config import ROUTES
from .database import (
    get_connection,
    get_sailing_event_count,
    get_training_data,
)
from .model_training.backtest_model import FEATURE_COLS, QuantileGBTModel, is_peak_hour

logger = logging.getLogger(__name__)

MINIMUM_TRAINING_EVENTS = 200
TIME_HORIZONS_MINUTES = list(range(2, 62, 2)) + [
    75,
    90,
    120,
]  # every 2min to 60, then 75/90/120

# New single-file save name (v2 format)
_MODEL_FILENAME = "delay_model_v2.joblib"
_META_FILENAME = "delay_model_meta.joblib"


def get_volume_model_dir() -> Path:
    """Model directory on the persistent volume (Railway or local data/)."""
    volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    data_dir = Path(volume_path) if volume_path else Path("./data")
    model_dir = data_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir


class DelayPredictor:
    def __init__(self):
        self._model: Optional[QuantileGBTModel] = None
        self.is_trained: bool = False
        self.last_trained: Optional[datetime] = None
        self.last_evaluation: Optional[dict] = None
        self.training_data_size: int = 0

    @property
    def _route_mapping(self) -> dict:
        """Backward-compatible access to route category mapping."""
        if self._model is None:
            return {}
        return self._model._category_maps.get("route_abbrev", {})

    @property
    def _terminal_mapping(self) -> dict:
        """Backward-compatible access to terminal category mapping."""
        if self._model is None:
            return {}
        return self._model._category_maps.get("departing_terminal_id", {})

    def build_training_data(self) -> Optional[pd.DataFrame]:
        """Build training dataset from sailing events and vessel snapshots.

        For each sailing event, generates multiple training rows at different
        time horizons (2-120 min before departure), using the vessel delay
        observable at each horizon from historical data.

        Uses bulk SQL queries + pandas merge_asof instead of per-row queries
        for performance (~3 queries instead of ~3M).
        """
        events = get_training_data()
        if len(events) < MINIMUM_TRAINING_EVENTS:
            logger.warning(
                f"Only {len(events)} sailing events, need {MINIMUM_TRAINING_EVENTS} to train"
            )
            return None

        conn = get_connection()
        try:
            # --- Load events into a DataFrame, filtered to configured routes ---
            events_df = pd.DataFrame(events)
            active_routes = {r["route_name"] for r in ROUTES}
            events_df = events_df[events_df["route_abbrev"].isin(active_routes)].copy()
            logger.info(
                f"Filtered to {len(events_df)} events for routes: {active_routes}"
            )
            if len(events_df) < MINIMUM_TRAINING_EVENTS:
                logger.warning(
                    f"Only {len(events_df)} events for active routes, "
                    f"need {MINIMUM_TRAINING_EVENTS}"
                )
                return None
            events_df["departing_terminal_id"] = events_df["departing_terminal_id"].fillna(0).astype(int)
            events_df["route_abbrev"] = events_df["route_abbrev"].fillna("unknown")
            events_df["scheduled_departure_dt"] = pd.to_datetime(
                events_df["scheduled_departure"], format="ISO8601", utc=True
            ).dt.tz_localize(None)
            events_df.rename(columns={
                "delay_minutes": "actual_delay_minutes",
                "id": "sailing_event_id",
            }, inplace=True)

            # --- Expand events × horizons ---
            horizons = pd.DataFrame({"horizon_min": TIME_HORIZONS_MINUTES})
            expanded = events_df.assign(key=1).merge(horizons.assign(key=1), on="key").drop(columns="key")
            expanded["predict_time"] = expanded["scheduled_departure_dt"] - pd.to_timedelta(expanded["horizon_min"], unit="m")

            # --- Bulk query 1: vessel delay snapshots (filtered to relevant vessels) ---
            logger.info("Loading vessel delay snapshots...")
            vessel_ids = events_df["vessel_id"].unique().tolist()
            placeholders = ",".join("?" * len(vessel_ids))
            delays_df = pd.read_sql_query(
                f"""
                SELECT vessel_id, collected_at, scheduled_departure AS snap_sched_dep,
                       (julianday(left_dock) - julianday(scheduled_departure)) * 24 * 60 AS snap_delay_minutes
                FROM vessel_snapshots
                WHERE left_dock IS NOT NULL AND scheduled_departure IS NOT NULL
                  AND left_dock != '' AND scheduled_departure != ''
                  AND vessel_id IN ({placeholders})
                """,
                conn,
                params=vessel_ids,
            )
            delays_df["collected_at"] = pd.to_datetime(
                delays_df["collected_at"], format="ISO8601", utc=True
            ).dt.tz_localize(None)
            delays_df.sort_values(["vessel_id", "collected_at"], inplace=True)
            logger.info(f"Loaded {len(delays_df)} delay snapshots")

            # merge_asof: for each (vessel_id, predict_time), find most recent snapshot.
            # Both sides must be sorted by the on-key for merge_asof.
            expanded.sort_values("predict_time", inplace=True)
            delays_df.sort_values("collected_at", inplace=True)
            merged = pd.merge_asof(
                expanded,
                delays_df,
                left_on="predict_time",
                right_on="collected_at",
                by="vessel_id",
                direction="backward",
            )

            # Exclude snapshots from the *same* sailing (matches original query's
            # `scheduled_departure != ?` filter) and default to 0.0.
            # ~2.5% of rows are affected; defaulting these to 0.0 rather than
            # falling back to an older snapshot has negligible impact on model quality.
            same_sailing = merged["snap_sched_dep"] == merged["scheduled_departure"]
            merged.loc[same_sailing, "snap_delay_minutes"] = np.nan
            merged["current_vessel_delay_minutes"] = merged["snap_delay_minutes"].fillna(0.0)

            # --- Bulk query 2: previous sailing fullness ---
            logger.info("Loading sailing space snapshots...")
            fullness_df = pd.read_sql_query(
                """
                SELECT arriving_terminal_id, departure_time, max_space_count, drive_up_space_count
                FROM sailing_space_snapshots
                WHERE max_space_count > 0
                """,
                conn,
            )
            if not fullness_df.empty:
                fullness_df["departure_time"] = pd.to_datetime(
                    fullness_df["departure_time"], format="ISO8601", utc=True
                ).dt.tz_localize(None)
                fullness_df["previous_sailing_fullness"] = (
                    1.0 - fullness_df["drive_up_space_count"] / fullness_df["max_space_count"]
                )
                fullness_df = fullness_df[["arriving_terminal_id", "departure_time", "previous_sailing_fullness"]]

                # merge_asof per terminal to avoid global sort requirement on on-key
                events_for_fullness = (
                    merged[["sailing_event_id", "departing_terminal_id", "scheduled_departure_dt"]]
                    .drop_duplicates(subset=["sailing_event_id"])
                )
                fullness_parts = []
                for terminal_id in events_for_fullness["departing_terminal_id"].unique():
                    ev_term = events_for_fullness.loc[
                        events_for_fullness["departing_terminal_id"] == terminal_id
                    ].sort_values("scheduled_departure_dt")
                    fu_term = fullness_df.loc[
                        fullness_df["arriving_terminal_id"] == terminal_id
                    ].sort_values("departure_time")
                    if fu_term.empty:
                        continue
                    matched = pd.merge_asof(
                        ev_term[["sailing_event_id", "scheduled_departure_dt"]],
                        fu_term[["departure_time", "previous_sailing_fullness"]],
                        left_on="scheduled_departure_dt",
                        right_on="departure_time",
                        direction="backward",
                    )
                    fullness_parts.append(matched[["sailing_event_id", "previous_sailing_fullness"]])

                if fullness_parts:
                    fullness_result = pd.concat(fullness_parts, ignore_index=True)
                    merged = merged.merge(fullness_result, on="sailing_event_id", how="left")
                else:
                    merged["previous_sailing_fullness"] = np.nan
            else:
                merged["previous_sailing_fullness"] = np.nan
            logger.info("Fullness features joined")

            # --- Bulk query 3: turnaround minutes ---
            logger.info("Loading turnaround data...")
            turnaround_df = pd.read_sql_query(
                """
                SELECT vessel_id, scheduled_departure, MIN(collected_at) AS docked_at
                FROM vessel_snapshots
                WHERE at_dock = 1
                  AND scheduled_departure IS NOT NULL AND scheduled_departure != ''
                  AND collected_at <= scheduled_departure
                GROUP BY vessel_id, scheduled_departure
                """,
                conn,
            )
            if not turnaround_df.empty:
                turnaround_df["docked_at"] = pd.to_datetime(
                    turnaround_df["docked_at"], format="ISO8601", utc=True
                ).dt.tz_localize(None)
                turnaround_df["sched_dt"] = pd.to_datetime(
                    turnaround_df["scheduled_departure"], format="ISO8601", utc=True
                ).dt.tz_localize(None)
                turnaround_df["turnaround_minutes"] = (
                    (turnaround_df["sched_dt"] - turnaround_df["docked_at"]).dt.total_seconds() / 60
                ).clip(lower=0)
                turnaround_lookup = turnaround_df[["vessel_id", "scheduled_departure", "turnaround_minutes"]]

                merged = merged.merge(
                    turnaround_lookup,
                    on=["vessel_id", "scheduled_departure"],
                    how="left",
                )
            else:
                merged["turnaround_minutes"] = np.nan
            logger.info("Turnaround features joined")

        finally:
            conn.close()

        # --- Build final training DataFrame ---
        merged["is_peak_hour"] = merged["hour_of_day"].apply(lambda h: int(is_peak_hour(h)))
        merged.rename(columns={"horizon_min": "minutes_until_scheduled_departure"}, inplace=True)

        result = merged[
            [
                "sailing_event_id",
                "route_abbrev",
                "departing_terminal_id",
                "day_of_week",
                "hour_of_day",
                "minutes_until_scheduled_departure",
                "current_vessel_delay_minutes",
                "is_peak_hour",
                "previous_sailing_fullness",
                "turnaround_minutes",
                "actual_delay_minutes",
            ]
        ].copy()

        if result.empty:
            logger.warning("No training rows generated")
            return None

        logger.info(
            f"Built training data: {len(result)} rows from {len(events)} sailing events"
        )
        return result

    def train(self) -> bool:
        """Train the model. Returns True on success."""
        df = self.build_training_data()
        if df is None:
            return False

        # Chronological split for evaluation
        unique_events = df["sailing_event_id"].unique()
        split_idx = int(len(unique_events) * 0.8)
        train_events = set(unique_events[:split_idx])
        test_events = set(unique_events[split_idx:])

        train_mask = df["sailing_event_id"].isin(train_events)
        test_mask = df["sailing_event_id"].isin(test_events)

        train_df = df[train_mask]
        test_df = df[test_mask].copy()

        logger.info(f"Training on {len(train_df)} rows, testing on {len(test_df)} rows")

        # Evaluate on 80/20 split
        eval_model = QuantileGBTModel()
        eval_model.fit(train_df)

        if len(test_df) > 0:
            from .model_training.evaluation import evaluate_predictions

            test_df = eval_model.predict(test_df)
            self.last_evaluation = evaluate_predictions(test_df)
            logger.info(f"Evaluation: {self.last_evaluation}")

        # Train production model on all data
        self._model = QuantileGBTModel()
        self._model.fit(df)
        self.is_trained = True
        self.last_trained = datetime.now()
        self.training_data_size = len(df)

        return True

    def predict(
        self,
        route_abbrev: str,
        departing_terminal_id: int,
        day_of_week: int,
        hour_of_day: int,
        minutes_until_scheduled_departure: float,
        current_vessel_delay_minutes: float,
        previous_sailing_fullness: Optional[float] = None,
        turnaround_minutes: Optional[float] = None,
    ) -> Optional[dict]:
        """Predict delay with confidence interval.

        Returns dict with predicted_delay, lower_bound, upper_bound (all in minutes),
        or None if model is not trained.
        """
        if not self.is_trained or self._model is None:
            return None

        try:
            return self._model.predict_single(
                route_abbrev=route_abbrev,
                departing_terminal_id=departing_terminal_id,
                day_of_week=day_of_week,
                hour_of_day=hour_of_day,
                minutes_until_scheduled_departure=minutes_until_scheduled_departure,
                current_vessel_delay_minutes=current_vessel_delay_minutes,
                previous_sailing_fullness=previous_sailing_fullness,
                turnaround_minutes=turnaround_minutes,
            )
        except ValueError as e:
            logger.error(f"Prediction failed (models may need retraining): {e}")
            return None

    def save(self, path: Optional[Path] = None):
        """Save model and metadata to disk."""
        model_dir = path or get_volume_model_dir()
        model_dir.mkdir(parents=True, exist_ok=True)

        self._model.save(model_dir / _MODEL_FILENAME)
        joblib.dump(
            {
                "last_trained": self.last_trained,
                "training_data_size": self.training_data_size,
                "last_evaluation": self.last_evaluation,
            },
            model_dir / _META_FILENAME,
        )
        logger.info(f"Models saved to {model_dir}")

    def _load_from_dir(self, model_dir: Path) -> bool:
        """Load a v2 model from model_dir, validating feature compatibility."""
        v2_path = model_dir / _MODEL_FILENAME
        if not v2_path.exists():
            return False

        try:
            model = QuantileGBTModel.load(v2_path)
            if model._feature_cols != FEATURE_COLS:
                logger.warning(
                    f"Model in {model_dir} has stale features "
                    f"({len(model._feature_cols)} vs {len(FEATURE_COLS)} expected), "
                    f"skipping — will retrain"
                )
                return False
            self._model = model
            meta = joblib.load(model_dir / _META_FILENAME)
            self.last_trained = meta["last_trained"]
            self.training_data_size = meta["training_data_size"]
            self.last_evaluation = meta.get("last_evaluation")
            self.is_trained = True
            logger.info(
                f"Models loaded from {model_dir} (trained: {self.last_trained})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to load models from {model_dir}: {e}")
            return False

    def load(self, path: Optional[Path] = None) -> bool:
        """Load models from the volume model directory."""
        model_dir = path or get_volume_model_dir()
        if self._load_from_dir(model_dir):
            return True

        logger.info("No compatible saved models found")
        return False


# Module-level singleton
predictor = DelayPredictor()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    from .database import get_sailing_event_count, init_db

    init_db()
    event_count = get_sailing_event_count()
    print(f"Sailing events in database: {event_count}")

    if event_count < MINIMUM_TRAINING_EVENTS:
        print(
            f"Need at least {MINIMUM_TRAINING_EVENTS} events to train. "
            f"Currently have {event_count}."
        )
    else:
        success = predictor.train()
        if success:
            predictor.save()
            print(f"Model trained on {predictor.training_data_size} rows")
            if predictor.last_evaluation:
                print(f"Evaluation: {predictor.last_evaluation}")
        else:
            print("Training failed")
