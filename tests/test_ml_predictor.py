from backend.ml_predictor import DelayPredictor, get_bundled_model_dir


class TestBundledModels:
    """Verify bundled models are compatible with the current prediction code.

    These tests load the .joblib models shipped in the repo and run a dummy
    prediction.  If the code adds/removes features without retraining the
    bundled models, the prediction will raise ValueError and these tests fail.
    """

    def test_bundled_models_accept_current_features(self):
        model_dir = get_bundled_model_dir()
        predictor = DelayPredictor()
        loaded = predictor.load(path=model_dir)
        if not loaded:
            # No bundled models yet — nothing to validate
            return

        # Use the first available route/terminal from the saved mappings
        route = next(iter(predictor._route_mapping))
        terminal = next(iter(predictor._terminal_mapping))

        result = predictor.predict(
            route_abbrev=route,
            departing_terminal_id=terminal,
            day_of_week=2,
            hour_of_day=8,
            minutes_until_scheduled_departure=30,
            current_vessel_delay_minutes=5.0,
            previous_sailing_fullness=0.7,
            turnaround_minutes=25.0,
        )
        assert result is not None, (
            "predict() returned None — bundled models likely expect a different "
            "number of features than the code provides. Retrain with: "
            "python -m backend.ml_predictor"
        )
        assert "predicted_delay" in result
        assert "lower_bound" in result
        assert "upper_bound" in result

    def test_bundled_models_handle_missing_optional_features(self):
        """Ensure prediction works when optional features are None."""
        model_dir = get_bundled_model_dir()
        predictor = DelayPredictor()
        loaded = predictor.load(path=model_dir)
        if not loaded:
            return

        route = next(iter(predictor._route_mapping))
        terminal = next(iter(predictor._terminal_mapping))

        result = predictor.predict(
            route_abbrev=route,
            departing_terminal_id=terminal,
            day_of_week=5,
            hour_of_day=17,
            minutes_until_scheduled_departure=10,
            current_vessel_delay_minutes=0.0,
            previous_sailing_fullness=None,
            turnaround_minutes=None,
        )
        assert result is not None, (
            "predict() returned None with optional features as None — "
            "bundled models may need retraining."
        )
