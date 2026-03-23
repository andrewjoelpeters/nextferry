"""Model interface and default implementation for backtesting.

The backtest harness (backtest.py) is model-agnostic. It consumes any object
that implements the BacktestModel protocol: fit(train_df) and predict(test_df).

To swap models, features, or encodings: change this file (or write a new
implementation). The harness never changes.
"""

from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

# ---------------------------------------------------------------------------
# Protocol — the contract between model and harness
# ---------------------------------------------------------------------------


@runtime_checkable
class BacktestModel(Protocol):
    """Interface a model must implement to plug into the backtest harness.

    fit() receives the raw training DataFrame (all columns from build_training_data).
    predict() receives the raw test DataFrame and must return it with three new
    columns added: predicted_delay, lower_bound, upper_bound.
    """

    def fit(self, train_df: pd.DataFrame) -> None: ...
    def predict(self, test_df: pd.DataFrame) -> pd.DataFrame: ...


# ---------------------------------------------------------------------------
# Feature helpers
# ---------------------------------------------------------------------------


def is_peak_hour(hour: int) -> bool:
    """Return True if the hour falls in commuter peak windows."""
    return (6 <= hour <= 9) or (15 <= hour <= 19)


# ---------------------------------------------------------------------------
# Default implementation — quantile GBT
# ---------------------------------------------------------------------------

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

CATEGORICAL_COLS = ["route_abbrev", "departing_terminal_id", "day_of_week"]
CATEGORICAL_FEATURES = [0, 1, 2]  # indices into FEATURE_COLS
TARGET_COL = "actual_delay_minutes"

# Sentinel for categories seen at predict time but not during fit
UNSEEN_CATEGORY_CODE = -1

# Save format version for forward/backward compatibility
_SAVE_VERSION = 2


class QuantileGBTModel:
    """Default backtest model: three HistGradientBoostingRegressors (q15/q50/q85).

    Encapsulates feature selection, encoding, and training — none of which
    leak into the backtest harness.
    """

    def __init__(self, hyperparams: dict | None = None):
        self.params = {**DEFAULT_HYPERPARAMS, **(hyperparams or {})}
        self.models: dict = {}
        self._category_maps: dict[str, dict] = {}
        self._feature_cols: list[str] = list(FEATURE_COLS)

    @property
    def is_fitted(self) -> bool:
        return bool(self.models)

    def _learn_categories(self, df: pd.DataFrame) -> None:
        """Learn category→code mappings from training data."""
        for col in CATEGORICAL_COLS:
            categories = sorted(df[col].unique())
            self._category_maps[col] = {
                cat: code for code, cat in enumerate(categories)
            }

    def _encode(self, df: pd.DataFrame) -> np.ndarray:
        """Encode features using mappings learned during fit().

        Unseen categories get UNSEEN_CATEGORY_CODE (-1), which
        HistGradientBoosting handles via its missing-value path.
        """
        X = df[self._feature_cols].copy()
        for col in CATEGORICAL_COLS:
            mapping = self._category_maps[col]
            X[col] = X[col].map(mapping).fillna(UNSEEN_CATEGORY_CODE).astype(int)
        return X.values

    def fit(self, train_df: pd.DataFrame) -> None:
        self._learn_categories(train_df)
        X_train = self._encode(train_df)
        y_train = train_df[TARGET_COL].values

        for name, quantile in [("q50", 0.50), ("q15", 0.15), ("q85", 0.85)]:
            model = HistGradientBoostingRegressor(
                loss="quantile",
                quantile=quantile,
                categorical_features=CATEGORICAL_FEATURES,
                **self.params,
            )
            model.fit(X_train, y_train)
            self.models[name] = model

    def predict(self, test_df: pd.DataFrame) -> pd.DataFrame:
        X_test = self._encode(test_df)
        out = test_df.copy()
        out["predicted_delay"] = self.models["q50"].predict(X_test)
        out["lower_bound"] = self.models["q15"].predict(X_test)
        out["upper_bound"] = self.models["q85"].predict(X_test)
        return out

    def predict_single(
        self,
        route_abbrev: str,
        departing_terminal_id: int,
        day_of_week: int,
        hour_of_day: int,
        minutes_until_scheduled_departure: float,
        current_vessel_delay_minutes: float,
        previous_sailing_fullness: float | None = None,
        turnaround_minutes: float | None = None,
    ) -> dict | None:
        """Predict delay for a single sailing.

        Returns dict with predicted_delay, lower_bound, upper_bound (minutes),
        or None if the model is not fitted.
        """
        if not self.is_fitted:
            return None

        row = pd.DataFrame(
            [
                {
                    "route_abbrev": route_abbrev,
                    "departing_terminal_id": departing_terminal_id,
                    "day_of_week": day_of_week,
                    "hour_of_day": hour_of_day,
                    "minutes_until_scheduled_departure": minutes_until_scheduled_departure,
                    "current_vessel_delay_minutes": current_vessel_delay_minutes,
                    "is_peak_hour": int(is_peak_hour(hour_of_day)),
                    "previous_sailing_fullness": (
                        previous_sailing_fullness
                        if previous_sailing_fullness is not None
                        else np.nan
                    ),
                    "turnaround_minutes": (
                        turnaround_minutes if turnaround_minutes is not None else np.nan
                    ),
                }
            ]
        )

        X = self._encode(row)
        return {
            "predicted_delay": round(float(self.models["q50"].predict(X)[0]), 1),
            "lower_bound": round(float(self.models["q15"].predict(X)[0]), 1),
            "upper_bound": round(float(self.models["q85"].predict(X)[0]), 1),
        }

    def save(self, path: Path) -> None:
        """Save model state to a single joblib file."""
        joblib.dump(
            {
                "version": _SAVE_VERSION,
                "models": self.models,
                "category_maps": self._category_maps,
                "params": self.params,
                "feature_cols": self._feature_cols,
            },
            path,
        )

    @classmethod
    def load(cls, path: Path) -> Optional["QuantileGBTModel"]:
        """Load model from a v2 joblib file. Returns None if file doesn't exist."""
        if not path.exists():
            return None
        data = joblib.load(path)
        instance = cls(hyperparams=data["params"])
        instance.models = data["models"]
        instance._category_maps = data["category_maps"]
        instance._feature_cols = data.get("feature_cols", list(FEATURE_COLS))
        return instance
