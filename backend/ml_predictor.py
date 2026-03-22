"""ML delay predictor using HistGradientBoostingRegressor with quantile loss.

Three models are trained on the same data:
- q=0.50 (median point estimate)
- q=0.05 (lower bound of 90% prediction interval)
- q=0.95 (upper bound of 90% prediction interval)

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
from sklearn.ensemble import HistGradientBoostingRegressor

from .database import (
    get_connection,
    get_sailing_event_count,
    get_training_data,
)

logger = logging.getLogger(__name__)

MINIMUM_TRAINING_EVENTS = 200
TIME_HORIZONS_MINUTES = list(range(2, 62, 2)) + [
    75,
    90,
    120,
]  # every 2min to 60, then 75/90/120


def get_volume_model_dir() -> Path:
    """Model directory on the persistent volume (Railway or local data/)."""
    volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    data_dir = Path(volume_path) if volume_path else Path("./data")
    model_dir = data_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir


def get_bundled_model_dir() -> Path:
    """Model directory shipped with the repo (fallback for fresh deploys)."""
    return Path(__file__).resolve().parent.parent / "models"


def is_peak_hour(hour: int) -> bool:
    """Return True if the hour falls in commuter peak windows."""
    return (6 <= hour <= 9) or (15 <= hour <= 19)


class DelayPredictor:
    def __init__(self):
        self.model_q50 = None
        self.model_q15 = None
        self.model_q85 = None
        self.is_trained: bool = False
        self.last_trained: Optional[datetime] = None
        self.last_evaluation: Optional[dict] = None
        self.training_data_size: int = 0

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
            # --- Load events into a DataFrame ---
            events_df = pd.DataFrame(events)
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

            # --- Bulk query 1: vessel delay snapshots ---
            logger.info("Loading vessel delay snapshots...")
            delays_df = pd.read_sql_query(
                """
                SELECT vessel_id, collected_at, scheduled_departure AS snap_sched_dep,
                       (julianday(left_dock) - julianday(scheduled_departure)) * 24 * 60 AS snap_delay_minutes
                FROM vessel_snapshots
                WHERE left_dock IS NOT NULL AND scheduled_departure IS NOT NULL
                  AND left_dock != '' AND scheduled_departure != ''
                """,
                conn,
            )
            delays_df["collected_at"] = pd.to_datetime(
                delays_df["collected_at"], format="ISO8601", utc=True
            ).dt.tz_localize(None)
            delays_df.sort_values(["vessel_id", "collected_at"], inplace=True)
            logger.info(f"Loaded {len(delays_df)} delay snapshots")

            # merge_asof: for each (vessel_id, predict_time), find most recent snapshot
            # Both sides must be sorted by the on-key within each by-group
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
            # `scheduled_departure != ?` filter) and default to 0.0
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
                fullness_df.sort_values(["arriving_terminal_id", "departure_time"], inplace=True)

                # merge_asof: match each event's (departing_terminal_id, scheduled_departure)
                # to the most recent fullness for that terminal
                events_for_fullness = (
                    merged[["sailing_event_id", "departing_terminal_id", "scheduled_departure_dt"]]
                    .drop_duplicates(subset=["sailing_event_id"])
                    .sort_values("scheduled_departure_dt")
                )
                fullness_df.sort_values("departure_time", inplace=True)
                fullness_merged = pd.merge_asof(
                    events_for_fullness,
                    fullness_df,
                    left_on="scheduled_departure_dt",
                    right_on="departure_time",
                    left_by="departing_terminal_id",
                    right_by="arriving_terminal_id",
                    direction="backward",
                )
                merged = merged.merge(
                    fullness_merged[["sailing_event_id", "previous_sailing_fullness"]],
                    on="sailing_event_id",
                    how="left",
                )
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
                # Strip tzinfo to avoid naive/aware mismatch
                turnaround_df["docked_at"] = turnaround_df["docked_at"].dt.tz_localize(None)
                turnaround_df["sched_dt"] = turnaround_df["sched_dt"].dt.tz_localize(None)
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
        """Train the three quantile models. Returns True on success."""
        df = self.build_training_data()
        if df is None:
            return False

        feature_cols = [
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
        target_col = "actual_delay_minutes"

        # Encode categoricals
        categorical_features = [
            0,
            1,
            2,
        ]  # route_abbrev, departing_terminal_id, day_of_week

        X = df[feature_cols].copy()
        # Encode route_abbrev as category codes
        X["route_abbrev"] = X["route_abbrev"].astype("category").cat.codes
        X["departing_terminal_id"] = (
            X["departing_terminal_id"].astype("category").cat.codes
        )
        X["day_of_week"] = X["day_of_week"].astype("category").cat.codes

        # Store mappings for prediction time
        self._route_mapping = dict(
            zip(
                df["route_abbrev"].astype("category").cat.categories,
                range(len(df["route_abbrev"].astype("category").cat.categories)),
            )
        )
        self._terminal_mapping = dict(
            zip(
                df["departing_terminal_id"].astype("category").cat.categories,
                range(
                    len(df["departing_terminal_id"].astype("category").cat.categories)
                ),
            )
        )

        y = df[target_col].values

        # Chronological split: train on earlier data, test on later
        # Use sailing_event_id to keep all horizons from same event together
        unique_events = df["sailing_event_id"].unique()
        split_idx = int(len(unique_events) * 0.8)
        train_events = set(unique_events[:split_idx])
        test_events = set(unique_events[split_idx:])

        train_mask = df["sailing_event_id"].isin(train_events)
        test_mask = df["sailing_event_id"].isin(test_events)

        X_train, y_train = X[train_mask].values, y[train_mask]
        X_test, y_test = X[test_mask].values, y[test_mask]

        logger.info(f"Training on {len(X_train)} rows, testing on {len(X_test)} rows")

        # Train three quantile models (70% prediction interval)
        quantiles = {"q50": 0.50, "q15": 0.15, "q85": 0.85}
        models = {}

        for name, quantile in quantiles.items():
            model = HistGradientBoostingRegressor(
                loss="quantile",
                quantile=quantile,
                max_iter=200,
                max_depth=6,
                learning_rate=0.1,
                categorical_features=categorical_features,
                random_state=42,
            )
            model.fit(X_train, y_train)
            models[name] = model
            logger.info(f"Trained {name} model (quantile={quantile})")

        self.model_q50 = models["q50"]
        self.model_q15 = models["q15"]
        self.model_q85 = models["q85"]
        self.is_trained = True
        self.last_trained = datetime.now()
        self.training_data_size = len(df)

        # Evaluate on test set
        if len(X_test) > 0:
            from .evaluation import evaluate_predictions

            test_df = df[test_mask].copy()
            test_df["predicted_delay"] = self.model_q50.predict(X_test)
            test_df["lower_bound"] = self.model_q15.predict(X_test)
            test_df["upper_bound"] = self.model_q85.predict(X_test)
            self.last_evaluation = evaluate_predictions(test_df)
            logger.info(f"Evaluation: {self.last_evaluation}")

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
        if not self.is_trained:
            return None

        route_code = self._route_mapping.get(route_abbrev, -1)
        terminal_code = self._terminal_mapping.get(departing_terminal_id, -1)
        dow_code = day_of_week  # Already 0-6

        features = np.array(
            [
                [
                    route_code,
                    terminal_code,
                    dow_code,
                    hour_of_day,
                    minutes_until_scheduled_departure,
                    current_vessel_delay_minutes,
                    int(is_peak_hour(hour_of_day)),
                    previous_sailing_fullness if previous_sailing_fullness is not None else np.nan,
                    turnaround_minutes if turnaround_minutes is not None else np.nan,
                ]
            ]
        )

        try:
            predicted = self.model_q50.predict(features)[0]
            lower = self.model_q15.predict(features)[0]
            upper = self.model_q85.predict(features)[0]
        except ValueError as e:
            logger.error(f"Prediction failed (models may need retraining): {e}")
            return None

        return {
            "predicted_delay": round(predicted, 1),
            "lower_bound": round(lower, 1),
            "upper_bound": round(upper, 1),
        }

    def save(self, path: Optional[Path] = None):
        """Save models and metadata to disk."""
        model_dir = path or get_volume_model_dir()
        model_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.model_q50, model_dir / "delay_model_q50.joblib")
        joblib.dump(self.model_q15, model_dir / "delay_model_q15.joblib")
        joblib.dump(self.model_q85, model_dir / "delay_model_q85.joblib")
        joblib.dump(
            {
                "route_mapping": self._route_mapping,
                "terminal_mapping": self._terminal_mapping,
                "last_trained": self.last_trained,
                "training_data_size": self.training_data_size,
                "last_evaluation": self.last_evaluation,
            },
            model_dir / "delay_model_meta.joblib",
        )
        logger.info(f"Models saved to {model_dir}")

    def _load_from_dir(self, model_dir: Path) -> bool:
        """Attempt to load models from a specific directory."""
        required_files = [
            "delay_model_q50.joblib",
            "delay_model_q15.joblib",
            "delay_model_q85.joblib",
            "delay_model_meta.joblib",
        ]

        if not all((model_dir / f).exists() for f in required_files):
            return False

        try:
            self.model_q50 = joblib.load(model_dir / "delay_model_q50.joblib")
            self.model_q15 = joblib.load(model_dir / "delay_model_q15.joblib")
            self.model_q85 = joblib.load(model_dir / "delay_model_q85.joblib")
            meta = joblib.load(model_dir / "delay_model_meta.joblib")
            self._route_mapping = meta["route_mapping"]
            self._terminal_mapping = meta["terminal_mapping"]
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
        """Load models from disk. Checks volume first, then bundled repo models."""
        if path:
            return self._load_from_dir(path)

        # Prefer volume models (fresher, from daily retraining)
        if self._load_from_dir(get_volume_model_dir()):
            return True

        # Fall back to bundled models shipped with the repo
        bundled = get_bundled_model_dir()
        if self._load_from_dir(bundled):
            logger.info("Loaded bundled models (no volume models found)")
            return True

        logger.info("No saved models found in volume or repo")
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
