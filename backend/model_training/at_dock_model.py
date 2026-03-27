"""At-dock delay prediction model.

Predicts how late a vessel will depart when it's currently at dock loading.
This is a different prediction task from the en-route delay model: we observe
the vessel sitting at the terminal and predict its actual departure delay.

Features specific to the at-dock scenario:
- minutes_at_dock: how long the vessel has been docked
- current_fullness: how full the boat is right now (drive-up cars loaded)
- minutes_until_scheduled_departure: time remaining before scheduled departure

The baseline (FlatDelayBaseline) simply predicts the vessel's previous trip
delay as the departure delay — equivalent to what the Map view currently shows.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

AT_DOCK_FEATURE_COLS = [
    "route_abbrev",
    "departing_terminal_id",
    "vessel_id",
    "day_of_week",
    "hour_of_day",
    "is_weekend",
    "minutes_until_scheduled_departure",
    "minutes_at_dock",
    "current_fullness",
    "incoming_vehicle_fullness",
    "current_vessel_delay_minutes",
]

AT_DOCK_CATEGORICAL_COLS = [
    "route_abbrev",
    "departing_terminal_id",
    "vessel_id",
    "day_of_week",
]
AT_DOCK_CATEGORICAL_FEATURES = [
    AT_DOCK_FEATURE_COLS.index(c) for c in AT_DOCK_CATEGORICAL_COLS
]
AT_DOCK_TARGET_COL = "actual_delay_minutes"

UNSEEN_CATEGORY_CODE = -1

DEFAULT_HYPERPARAMS = {
    "max_iter": 200,
    "max_depth": 5,
    "learning_rate": 0.1,
    "min_samples_leaf": 20,
    "random_state": 42,
}

_SAVE_VERSION = 1


class AtDockGBTModel:
    """Quantile GBT model for at-dock delay prediction.

    Implements BacktestModel protocol: fit(train_df) and predict(test_df).
    """

    def __init__(self, hyperparams: dict | None = None):
        self.params = {**DEFAULT_HYPERPARAMS, **(hyperparams or {})}
        self.models: dict = {}
        self._category_maps: dict[str, dict] = {}
        self._feature_cols: list[str] = list(AT_DOCK_FEATURE_COLS)

    @property
    def is_fitted(self) -> bool:
        return bool(self.models)

    def _learn_categories(self, df: pd.DataFrame) -> None:
        for col in AT_DOCK_CATEGORICAL_COLS:
            categories = sorted(df[col].unique())
            self._category_maps[col] = {
                cat: code for code, cat in enumerate(categories)
            }

    def _encode(self, df: pd.DataFrame) -> np.ndarray:
        X = df[self._feature_cols].copy()
        for col in AT_DOCK_CATEGORICAL_COLS:
            mapping = self._category_maps[col]
            X[col] = X[col].map(mapping).fillna(UNSEEN_CATEGORY_CODE).astype(int)
        return X.values

    def fit(self, train_df: pd.DataFrame) -> None:
        self._learn_categories(train_df)
        X_train = self._encode(train_df)
        y_train = train_df[AT_DOCK_TARGET_COL].values

        for name, quantile in [("q50", 0.333), ("q10", 0.10), ("q90", 0.90)]:
            model = HistGradientBoostingRegressor(
                loss="quantile",
                quantile=quantile,
                categorical_features=AT_DOCK_CATEGORICAL_FEATURES,
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
        minutes_at_dock: float,
        current_fullness: float | None = None,
        incoming_vehicle_fullness: float | None = None,
        current_vessel_delay_minutes: float = 0.0,
    ) -> dict | None:
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
                    "minutes_at_dock": minutes_at_dock,
                    "current_fullness": (
                        current_fullness if current_fullness is not None else np.nan
                    ),
                    "incoming_vehicle_fullness": (
                        incoming_vehicle_fullness
                        if incoming_vehicle_fullness is not None
                        else np.nan
                    ),
                    "current_vessel_delay_minutes": current_vessel_delay_minutes,
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

    def save(self, path) -> None:
        import joblib

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
    def load(cls, path) -> "AtDockGBTModel | None":
        import joblib

        if not path.exists():
            return None
        data = joblib.load(path)
        instance = cls(hyperparams=data["params"])
        instance.models = data["models"]
        instance._category_maps = data["category_maps"]
        instance._feature_cols = data.get("feature_cols", list(AT_DOCK_FEATURE_COLS))
        return instance


class FlatDelayBaseline:
    """Baseline: predict departure delay = previous vessel delay (option C).

    This is what the Map view currently shows — just carry forward the
    delay from the vessel's last trip.
    """

    def fit(self, train_df: pd.DataFrame) -> None:
        pass

    def predict(self, test_df: pd.DataFrame) -> pd.DataFrame:
        out = test_df.copy()
        out["predicted_delay"] = out["current_vessel_delay_minutes"].fillna(0.0)
        out["lower_bound"] = out["predicted_delay"]
        out["upper_bound"] = out["predicted_delay"]
        return out


# Verify protocol compliance
assert isinstance(AtDockGBTModel, type) and issubclass(AtDockGBTModel, object)
assert isinstance(FlatDelayBaseline, type) and issubclass(FlatDelayBaseline, object)
