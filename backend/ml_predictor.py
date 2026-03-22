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
    get_previous_sailing_fullness,
    get_sailing_event_count,
    get_training_data,
    get_turnaround_minutes,
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
        time horizons (5, 15, 30, 60, 120 min before departure), using the
        vessel delay observable at each horizon from historical data.
        """
        events = get_training_data()
        if len(events) < MINIMUM_TRAINING_EVENTS:
            logger.warning(
                f"Only {len(events)} sailing events, need {MINIMUM_TRAINING_EVENTS} to train"
            )
            return None

        conn = get_connection()
        rows = []

        try:
            for event in events:
                scheduled_dep = event["scheduled_departure"]
                vessel_id = event["vessel_id"]
                actual_delay = event["delay_minutes"]
                departing_terminal_id = event["departing_terminal_id"] or 0

                # Get docking features (same for all horizons of this event)
                prev_fullness = get_previous_sailing_fullness(
                    departing_terminal_id, scheduled_dep
                )
                turnaround = get_turnaround_minutes(vessel_id, scheduled_dep)

                for horizon_min in TIME_HORIZONS_MINUTES:
                    # Compute the time at which we'd be predicting
                    # (horizon_min minutes before scheduled departure)
                    try:
                        sched_dt = datetime.fromisoformat(scheduled_dep)
                        from datetime import timedelta

                        predict_time = sched_dt - timedelta(minutes=horizon_min)
                        predict_time_str = predict_time.isoformat()
                    except (ValueError, TypeError):
                        continue

                    # Get the vessel's most recent observed delay at predict_time
                    # from a *different* sailing (not the current one)
                    row = conn.execute(
                        """
                        SELECT
                            (julianday(left_dock) - julianday(scheduled_departure)) * 24 * 60 AS delay_minutes
                        FROM vessel_snapshots
                        WHERE vessel_id = ?
                          AND collected_at <= ?
                          AND left_dock IS NOT NULL
                          AND scheduled_departure IS NOT NULL
                          AND left_dock != ''
                          AND scheduled_departure != ''
                          AND scheduled_departure != ?
                        ORDER BY collected_at DESC
                        LIMIT 1
                        """,
                        (vessel_id, predict_time_str, scheduled_dep),
                    ).fetchone()

                    current_vessel_delay = row["delay_minutes"] if row else 0.0

                    rows.append(
                        {
                            "sailing_event_id": event["id"],
                            "scheduled_departure": scheduled_dep,
                            "route_abbrev": event["route_abbrev"] or "unknown",
                            "departing_terminal_id": departing_terminal_id,
                            "day_of_week": event["day_of_week"],
                            "hour_of_day": event["hour_of_day"],
                            "minutes_until_scheduled_departure": horizon_min,
                            "current_vessel_delay_minutes": current_vessel_delay,
                            "is_peak_hour": int(is_peak_hour(event["hour_of_day"])),
                            "previous_sailing_fullness": prev_fullness if prev_fullness is not None else np.nan,
                            "turnaround_minutes": turnaround if turnaround is not None else np.nan,
                            "actual_delay_minutes": actual_delay,
                        }
                    )
        finally:
            conn.close()

        if not rows:
            logger.warning("No training rows generated")
            return None

        df = pd.DataFrame(rows)
        logger.info(
            f"Built training data: {len(df)} rows from {len(events)} sailing events"
        )
        return df

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
            from .model_training.evaluation import evaluate_predictions

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

        predicted = self.model_q50.predict(features)[0]
        lower = self.model_q15.predict(features)[0]
        upper = self.model_q85.predict(features)[0]

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
