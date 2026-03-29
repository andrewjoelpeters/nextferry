"""Tests for the evaluation module's interval width metrics."""

import pandas as pd

from backend.model_training.evaluation import compute_metrics, evaluate_predictions


class TestComputeMetricsIntervalWidth:
    def test_interval_width_computed_when_bounds_provided(self):
        errors = pd.Series([1.0, -2.0, 0.5])
        lower = pd.Series([0.0, 2.0, 4.0])
        upper = pd.Series([10.0, 8.0, 6.0])
        result = compute_metrics(errors, lower=lower, upper=upper)
        assert "mean_interval_width" in result
        assert "median_interval_width" in result

    def test_interval_width_not_present_without_bounds(self):
        errors = pd.Series([1.0, -2.0, 0.5])
        result = compute_metrics(errors)
        assert "mean_interval_width" not in result
        assert "median_interval_width" not in result

    def test_interval_width_values(self):
        errors = pd.Series([1.0, -2.0, 0.5])
        lower = pd.Series([0.0, 2.0, 4.0])
        upper = pd.Series([10.0, 8.0, 6.0])
        # widths = [10, 6, 2], mean = 6.0, median = 6.0
        result = compute_metrics(errors, lower=lower, upper=upper)
        assert result["mean_interval_width"] == 6.0
        assert result["median_interval_width"] == 6.0

    def test_interval_width_asymmetric(self):
        errors = pd.Series([0.0, 0.0, 0.0, 0.0])
        lower = pd.Series([0.0, 0.0, 0.0, 0.0])
        upper = pd.Series([2.0, 4.0, 6.0, 20.0])
        # widths = [2, 4, 6, 20], mean = 8.0, median = 5.0
        result = compute_metrics(errors, lower=lower, upper=upper)
        assert result["mean_interval_width"] == 8.0
        assert result["median_interval_width"] == 5.0


class TestEvaluatePredictionsIntervalWidth:
    def test_overall_interval_width_in_results(self):
        test_df = pd.DataFrame(
            {
                "actual_delay_minutes": [2.0, 4.0, 6.0, 3.0],
                "predicted_delay": [3.0, 3.0, 5.0, 4.0],
                "lower_bound": [1.0, 1.0, 3.0, 2.0],
                "upper_bound": [5.0, 7.0, 9.0, 6.0],
                "minutes_until_scheduled_departure": [10.0, 20.0, 30.0, 15.0],
            }
        )
        results = evaluate_predictions(test_df)
        assert "overall_mean_interval_width" in results
        assert "overall_median_interval_width" in results
        # widths = [4, 6, 6, 4], mean = 5.0, median = 5.0
        assert results["overall_mean_interval_width"] == 5.0
        assert results["overall_median_interval_width"] == 5.0
