import joblib
import numpy as np
import pandas as pd

from backend.ml_predictor import DelayPredictor
from backend.model_training.backtest_model import (FEATURE_COLS,
                                                   QuantileGBTModel,
                                                   is_peak_hour)


def _make_training_df(n: int = 200) -> pd.DataFrame:
    """Build a small synthetic training DataFrame with all current features."""
    rng = np.random.default_rng(42)
    routes = ["sea-bi", "ed-ki"]
    terminals = [1, 3, 7, 8]
    rows = []
    for _ in range(n):
        hour = int(rng.integers(5, 22))
        rows.append(
            {
                "route_abbrev": rng.choice(routes),
                "departing_terminal_id": int(rng.choice(terminals)),
                "day_of_week": int(rng.integers(0, 7)),
                "hour_of_day": hour,
                "minutes_until_scheduled_departure": float(rng.integers(5, 120)),
                "current_vessel_delay_minutes": float(rng.normal(3, 5)),
                "is_peak_hour": int(is_peak_hour(hour)),
                "previous_sailing_fullness": float(rng.uniform(0, 1)),
                "turnaround_minutes": float(rng.uniform(10, 40)),
                "actual_delay_minutes": float(rng.normal(5, 8)),
            }
        )
    return pd.DataFrame(rows)


def _save_model(model: QuantileGBTModel, tmp_path) -> None:
    """Save a model + metadata to tmp_path for loading tests."""
    model.save(tmp_path / "delay_model_v2.joblib")
    joblib.dump(
        {"last_trained": "2026-01-01", "training_data_size": 200},
        tmp_path / "delay_model_meta.joblib",
    )


class TestFeatureCompatibility:
    """Ensure models with mismatched features are rejected at load time."""

    def test_model_with_missing_feature_rejected(self, tmp_path):
        """A saved model missing a feature should not load."""
        df = _make_training_df()
        model = QuantileGBTModel()
        model.fit(df)
        # Simulate a model saved before the latest feature was added
        model._feature_cols = model._feature_cols[:-1]
        _save_model(model, tmp_path)

        predictor = DelayPredictor()
        assert not predictor.load(path=tmp_path)
        assert not predictor.is_trained

    def test_model_with_extra_feature_rejected(self, tmp_path):
        """A saved model with an extra unknown feature should not load."""
        df = _make_training_df()
        model = QuantileGBTModel()
        model.fit(df)
        model._feature_cols = model._feature_cols + ["some_future_feature"]
        _save_model(model, tmp_path)

        predictor = DelayPredictor()
        assert not predictor.load(path=tmp_path)
        assert not predictor.is_trained

    def test_compatible_model_loads_and_predicts(self, tmp_path):
        """A model trained on the current features should load and predict."""
        df = _make_training_df()
        model = QuantileGBTModel()
        model.fit(df)
        _save_model(model, tmp_path)

        predictor = DelayPredictor()
        assert predictor.load(path=tmp_path)
        assert predictor.is_trained

        result = predictor.predict(
            route_abbrev="sea-bi",
            departing_terminal_id=1,
            day_of_week=2,
            hour_of_day=8,
            minutes_until_scheduled_departure=30,
            current_vessel_delay_minutes=5.0,
            previous_sailing_fullness=0.7,
            turnaround_minutes=25.0,
        )
        assert result is not None
        assert "predicted_delay" in result
        assert "lower_bound" in result
        assert "upper_bound" in result

    def test_feature_cols_survives_save_load_roundtrip(self, tmp_path):
        """_feature_cols should be identical after save → load."""
        df = _make_training_df()
        model = QuantileGBTModel()
        model.fit(df)
        path = tmp_path / "model.joblib"
        model.save(path)

        loaded = QuantileGBTModel.load(path)
        assert loaded._feature_cols == list(FEATURE_COLS)
