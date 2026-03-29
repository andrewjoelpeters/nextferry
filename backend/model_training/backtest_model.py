"""Model interface and default implementation for backtesting.

The backtest harness (backtest.py) is model-agnostic. It consumes any object
that implements the BacktestModel protocol: fit(train_df) and predict(test_df).

To swap models, features, or encodings: change this file (or write a new
implementation). The harness never changes.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

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
    "max_iter": 600,
    "max_depth": 8,
    "learning_rate": 0.05,
    "min_samples_leaf": 20,
    "random_state": 42,
}

FEATURE_COLS = [
    "route_abbrev",
    "departing_terminal_id",
    "vessel_id",
    "day_of_week",
    "hour_of_day",
    "is_weekend",
    "minutes_until_scheduled_departure",
    "current_vessel_delay_minutes",
    "vessel_speed",
    "previous_sailing_fullness",
    "turnaround_minutes",
]

CATEGORICAL_COLS = ["route_abbrev", "departing_terminal_id", "vessel_id", "day_of_week"]
CATEGORICAL_FEATURES = [FEATURE_COLS.index(c) for c in CATEGORICAL_COLS]
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

        for name, quantile in [("q50", 0.28), ("q10", 0.10), ("q90", 0.90)]:
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
        out["lower_bound"] = self.models.get("q15", self.models.get("q10")).predict(
            X_test
        )
        out["upper_bound"] = self.models.get("q85", self.models.get("q90")).predict(
            X_test
        )
        return out

    def predict_single(
        self,
        route_abbrev: str,
        departing_terminal_id: int,
        vessel_id: int,
        day_of_week: int,
        hour_of_day: int,
        minutes_until_scheduled_departure: float,
        current_vessel_delay_minutes: float,
        vessel_speed: float | None = None,
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
                    "vessel_id": vessel_id,
                    "day_of_week": day_of_week,
                    "hour_of_day": hour_of_day,
                    "is_weekend": int(day_of_week in (0, 6)),
                    "minutes_until_scheduled_departure": minutes_until_scheduled_departure,
                    "current_vessel_delay_minutes": current_vessel_delay_minutes,
                    "vessel_speed": (vessel_speed if vessel_speed is not None else 0.0),
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

        lower_model = self.models.get("q15") or self.models.get("q10")
        upper_model = self.models.get("q85") or self.models.get("q90")
        X = self._encode(row)
        return {
            "predicted_delay": round(float(self.models["q50"].predict(X)[0]), 1),
            "lower_bound": round(float(lower_model.predict(X)[0]), 1),
            "upper_bound": round(float(upper_model.predict(X)[0]), 1),
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
    def load(cls, path: Path) -> "QuantileGBTModel | None":
        """Load model from a v2 joblib file. Returns None if file doesn't exist."""
        if not path.exists():
            return None
        data = joblib.load(path)
        instance = cls(hyperparams=data["params"])
        instance.models = data["models"]
        instance._category_maps = data["category_maps"]
        instance._feature_cols = data.get("feature_cols", list(FEATURE_COLS))
        return instance


class NGBoostModel:
    """NGBoost distributional model — fits a Normal distribution per prediction.

    Jointly optimizes location (mu) and scale (sigma), producing coherent
    intervals and a natural confidence measure.
    """

    def __init__(self):
        self._category_maps: dict[str, dict] = {}
        self._feature_cols: list[str] = list(FEATURE_COLS)
        self.model = None

    def _learn_categories(self, df: pd.DataFrame) -> None:
        for col in CATEGORICAL_COLS:
            categories = sorted(df[col].unique())
            self._category_maps[col] = {
                cat: code for code, cat in enumerate(categories)
            }

    def _encode(self, df: pd.DataFrame) -> np.ndarray:
        X = df[self._feature_cols].copy()
        for col in CATEGORICAL_COLS:
            mapping = self._category_maps[col]
            X[col] = X[col].map(mapping).fillna(UNSEEN_CATEGORY_CODE).astype(int)
        return X.values

    def fit(self, train_df: pd.DataFrame) -> None:
        from ngboost import NGBRegressor
        from ngboost.distns import Normal
        from sklearn.tree import DecisionTreeRegressor

        self._learn_categories(train_df)
        X_train = self._encode(train_df)
        y_train = train_df[TARGET_COL].values

        base_learner = DecisionTreeRegressor(
            max_depth=4,
            min_samples_leaf=20,
        )

        self.model = NGBRegressor(
            Dist=Normal,
            Base=base_learner,
            n_estimators=200,
            learning_rate=0.05,
            random_state=42,
            verbose=False,
        )
        self.model.fit(X_train, y_train)

    def predict(self, test_df: pd.DataFrame) -> pd.DataFrame:
        X_test = self._encode(test_df)
        dist = self.model.pred_dist(X_test)
        mu = dist.loc
        sigma = dist.scale

        out = test_df.copy()
        # Use q33 for point estimate (matches asymmetric pinball loss)
        out["predicted_delay"] = dist.ppf(0.333)
        out["lower_bound"] = dist.ppf(0.10)
        out["upper_bound"] = dist.ppf(0.90)
        return out
