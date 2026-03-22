"""Model interface and default implementation for backtesting.

The backtest harness (backtest.py) is model-agnostic. It consumes any object
that implements the BacktestModel protocol: fit(train_df) and predict(test_df).

To swap models, features, or encodings: change this file (or write a new
implementation). The harness never changes.
"""

from typing import Protocol, runtime_checkable

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

CATEGORICAL_FEATURES = [0, 1, 2]  # route_abbrev, departing_terminal_id, day_of_week
TARGET_COL = "actual_delay_minutes"


class QuantileGBTModel:
    """Default backtest model: three HistGradientBoostingRegressors (q15/q50/q85).

    Encapsulates feature selection, encoding, and training — none of which
    leak into the backtest harness.
    """

    def __init__(self, hyperparams: dict | None = None):
        self.params = {**DEFAULT_HYPERPARAMS, **(hyperparams or {})}
        self.models: dict = {}

    def _encode(self, df: pd.DataFrame) -> np.ndarray:
        X = df[FEATURE_COLS].copy()
        X["route_abbrev"] = X["route_abbrev"].astype("category").cat.codes
        X["departing_terminal_id"] = X["departing_terminal_id"].astype("category").cat.codes
        X["day_of_week"] = X["day_of_week"].astype("category").cat.codes
        return X.values

    def fit(self, train_df: pd.DataFrame) -> None:
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
