"""Fill risk predictor: predicts whether a sailing will fill up and when.

Uses historical sailing space snapshots to learn fill patterns by route,
terminal, day-of-week, and hour. Outputs a fill probability and, for
sailings likely to fill, an estimate of how many minutes before departure
spaces run out.

Trained alongside the delay model on the daily 2 AM schedule.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
)

from .database import get_connection

logger = logging.getLogger(__name__)

MINIMUM_FILL_SAILINGS = 50  # need at least this many historical sailings


def _get_volume_model_dir() -> Path:
    volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    data_dir = Path(volume_path) if volume_path else Path("./data")
    model_dir = data_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir


def _get_bundled_model_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "models"


def _is_peak_hour(hour: int) -> bool:
    return (6 <= hour <= 9) or (15 <= hour <= 19)


class FillRiskPredictor:
    def __init__(self):
        self.classifier = None  # P(fill)
        self.regressor = None  # minutes before departure it fills (for filled sailings)
        self.is_trained: bool = False
        self.last_trained: datetime | None = None
        self.training_data_size: int = 0
        self.fill_rate: float = 0.0  # overall % of sailings that filled
        self._route_mapping: dict = {}
        self._terminal_mapping: dict = {}

    def build_training_data(self) -> pd.DataFrame | None:
        """Extract fill events from sailing_space_snapshots.

        For each historical sailing (departing_terminal_id, departure_time),
        reconstruct the capacity curve and determine:
        - did_fill: 1 if drive_up_space_count ever reached 0, else 0
        - fill_minutes_before: minutes before departure it first hit 0 (if filled)
        """
        conn = get_connection()
        try:
            # Get all distinct sailings with their capacity curves
            rows = conn.execute(
                """
                SELECT
                    departing_terminal_id,
                    arriving_terminal_id,
                    departing_terminal_name,
                    departure_time,
                    collected_at,
                    drive_up_space_count,
                    max_space_count
                FROM sailing_space_snapshots
                WHERE departure_time IS NOT NULL
                  AND departure_time != ''
                ORDER BY departing_terminal_id, departure_time, collected_at
                """
            ).fetchall()
        finally:
            conn.close()

        if not rows:
            logger.warning("No sailing space snapshots found")
            return None

        # Group by sailing identity
        sailings = {}
        for row in rows:
            key = (row["departing_terminal_id"], row["departure_time"])
            if key not in sailings:
                sailings[key] = {
                    "departing_terminal_id": row["departing_terminal_id"],
                    "arriving_terminal_id": row["arriving_terminal_id"],
                    "departing_terminal_name": row["departing_terminal_name"],
                    "departure_time": row["departure_time"],
                    "max_space_count": row["max_space_count"],
                    "snapshots": [],
                }
            sailings[key]["snapshots"].append(
                {
                    "collected_at": row["collected_at"],
                    "drive_up_space_count": row["drive_up_space_count"],
                }
            )

        if len(sailings) < MINIMUM_FILL_SAILINGS:
            logger.warning(
                f"Only {len(sailings)} sailings with space data, "
                f"need {MINIMUM_FILL_SAILINGS}"
            )
            return None

        # Build training rows
        training_rows = []
        for _key, sailing in sailings.items():
            try:
                dep_time = datetime.fromisoformat(sailing["departure_time"])
            except (ValueError, TypeError):
                continue

            # Determine route from terminal IDs
            route = self._route_from_terminals(
                sailing["departing_terminal_id"],
                sailing["arriving_terminal_id"],
            )

            # Check if this sailing ever hit 0 spaces
            did_fill = 0
            fill_minutes_before = None
            for snap in sailing["snapshots"]:
                if snap["drive_up_space_count"] == 0:
                    try:
                        snap_time = datetime.fromisoformat(snap["collected_at"])
                        minutes_before = (dep_time - snap_time).total_seconds() / 60
                        if minutes_before > 0:  # only count pre-departure fills
                            did_fill = 1
                            fill_minutes_before = minutes_before
                            break  # first time it hit 0
                    except (ValueError, TypeError):
                        continue

            training_rows.append(
                {
                    "route_abbrev": route,
                    "departing_terminal_id": sailing["departing_terminal_id"],
                    "day_of_week": dep_time.weekday(),
                    "hour_of_day": dep_time.hour,
                    "is_peak_hour": int(_is_peak_hour(dep_time.hour)),
                    "max_space_count": sailing["max_space_count"],
                    "did_fill": did_fill,
                    "fill_minutes_before": fill_minutes_before,
                }
            )

        df = pd.DataFrame(training_rows)
        logger.info(
            f"Built fill risk training data: {len(df)} sailings, "
            f"{df['did_fill'].sum()} filled ({df['did_fill'].mean() * 100:.1f}%)"
        )
        return df

    def _route_from_terminals(self, dep_id: int, arr_id: int) -> str:
        """Map terminal IDs to route abbreviation."""
        from .config import ROUTES

        for route in ROUTES:
            if dep_id in route["terminals"] and arr_id in route["terminals"]:
                return route["route_name"]
        return "unknown"

    def train(self) -> bool:
        """Train the fill risk classifier and optional regressor."""
        df = self.build_training_data()
        if df is None:
            return False

        feature_cols = [
            "route_abbrev",
            "departing_terminal_id",
            "day_of_week",
            "hour_of_day",
            "is_peak_hour",
            "max_space_count",
        ]
        categorical_features = [0, 1, 2]  # route, terminal, dow

        X = df[feature_cols].copy()
        X["route_abbrev"] = X["route_abbrev"].astype("category").cat.codes
        X["departing_terminal_id"] = (
            X["departing_terminal_id"].astype("category").cat.codes
        )
        X["day_of_week"] = X["day_of_week"].astype("category").cat.codes

        self._route_mapping = dict(
            zip(
                df["route_abbrev"].astype("category").cat.categories,
                range(len(df["route_abbrev"].astype("category").cat.categories)),
                strict=True,
            )
        )
        self._terminal_mapping = dict(
            zip(
                df["departing_terminal_id"].astype("category").cat.categories,
                range(
                    len(df["departing_terminal_id"].astype("category").cat.categories)
                ),
                strict=True,
            )
        )

        # --- Classification: will it fill? ---
        y_fill = df["did_fill"].values
        X_values = X.values

        self.classifier = HistGradientBoostingClassifier(
            max_iter=200,
            max_depth=4,
            learning_rate=0.1,
            categorical_features=categorical_features,
            random_state=42,
        )
        self.classifier.fit(X_values, y_fill)
        logger.info("Trained fill risk classifier")

        # --- Regression: how many minutes before departure? ---
        filled_mask = df["did_fill"] == 1
        if filled_mask.sum() >= 10:
            y_minutes = df.loc[filled_mask, "fill_minutes_before"].values
            X_filled = X[filled_mask].values

            self.regressor = HistGradientBoostingRegressor(
                max_iter=200,
                max_depth=4,
                learning_rate=0.1,
                categorical_features=categorical_features,
                random_state=42,
            )
            self.regressor.fit(X_filled, y_minutes)
            logger.info(
                f"Trained fill time regressor on {filled_mask.sum()} fill events"
            )
        else:
            self.regressor = None
            logger.info("Not enough fill events for time regression")

        self.is_trained = True
        self.last_trained = datetime.now()
        self.training_data_size = len(df)
        self.fill_rate = float(df["did_fill"].mean())

        return True

    def predict(
        self,
        route_abbrev: str,
        departing_terminal_id: int,
        day_of_week: int,
        hour_of_day: int,
        max_space_count: int = 200,
    ) -> dict | None:
        """Predict fill risk for a sailing.

        Returns:
            {
                "fill_probability": float (0-1),
                "risk_level": str ("low", "moderate", "high"),
                "fills_minutes_before": float or None,
                "label": str (human-readable),
            }
        """
        if not self.is_trained:
            return None

        route_code = self._route_mapping.get(route_abbrev, -1)
        terminal_code = self._terminal_mapping.get(departing_terminal_id, -1)

        features = np.array(
            [
                [
                    route_code,
                    terminal_code,
                    day_of_week,
                    hour_of_day,
                    int(_is_peak_hour(hour_of_day)),
                    max_space_count,
                ]
            ]
        )

        fill_prob = self.classifier.predict_proba(features)[0][1]

        # Determine risk level and label
        fills_minutes_before = None
        if fill_prob >= 0.6:
            risk_level = "high"
            if self.regressor is not None:
                fills_minutes_before = max(
                    0, round(self.regressor.predict(features)[0])
                )
                label = f"Often full ~{fills_minutes_before}m early"
            else:
                label = "Often fills up"
        elif fill_prob >= 0.3:
            risk_level = "moderate"
            label = "Can fill up"
        else:
            risk_level = "low"
            label = "Usually has space"

        return {
            "fill_probability": round(fill_prob, 2),
            "risk_level": risk_level,
            "fills_minutes_before": fills_minutes_before,
            "label": label,
        }

    def save(self, path: Path | None = None):
        model_dir = path or _get_volume_model_dir()
        model_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.classifier, model_dir / "fill_risk_classifier.joblib")
        if self.regressor is not None:
            joblib.dump(self.regressor, model_dir / "fill_risk_regressor.joblib")

        joblib.dump(
            {
                "route_mapping": self._route_mapping,
                "terminal_mapping": self._terminal_mapping,
                "last_trained": self.last_trained,
                "training_data_size": self.training_data_size,
                "fill_rate": self.fill_rate,
            },
            model_dir / "fill_risk_meta.joblib",
        )
        logger.info(f"Fill risk models saved to {model_dir}")

    def _load_from_dir(self, model_dir: Path) -> bool:
        required = ["fill_risk_classifier.joblib", "fill_risk_meta.joblib"]
        if not all((model_dir / f).exists() for f in required):
            return False

        try:
            self.classifier = joblib.load(model_dir / "fill_risk_classifier.joblib")
            meta = joblib.load(model_dir / "fill_risk_meta.joblib")
            self._route_mapping = meta["route_mapping"]
            self._terminal_mapping = meta["terminal_mapping"]
            self.last_trained = meta["last_trained"]
            self.training_data_size = meta["training_data_size"]
            self.fill_rate = meta.get("fill_rate", 0.0)

            regressor_path = model_dir / "fill_risk_regressor.joblib"
            if regressor_path.exists():
                self.regressor = joblib.load(regressor_path)

            self.is_trained = True
            logger.info(
                f"Fill risk model loaded from {model_dir} "
                f"(trained: {self.last_trained})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to load fill risk model from {model_dir}: {e}")
            return False

    def load(self, path: Path | None = None) -> bool:
        if path:
            return self._load_from_dir(path)

        if self._load_from_dir(_get_volume_model_dir()):
            return True

        bundled = _get_bundled_model_dir()
        if self._load_from_dir(bundled):
            logger.info("Loaded bundled fill risk model")
            return True

        logger.info("No saved fill risk model found")
        return False


# Module-level singleton
fill_predictor = FillRiskPredictor()
