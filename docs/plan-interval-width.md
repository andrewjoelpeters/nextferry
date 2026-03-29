# Plan: Add Mean Interval Width Metric to evaluation.py

## Goal

Add `mean_interval_width` and `median_interval_width` as metrics alongside pinball loss, bias, p90, and coverage. This measures how wide the prediction interval (upper_bound - lower_bound) is on average — narrower is better, given acceptable coverage.

## Why

Two models with the same pinball loss but different interval widths are not equal. The one with narrower intervals gives users more actionable predictions. We need this metric to compare the current quantile GBT against distributional models (NGBoost, AFT) that should produce tighter, more coherent intervals.

## Files to Change

### 1. `backend/model_training/evaluation.py`

**In `compute_metrics()` (line 80):**

Add interval width inside the existing `if actuals is not None and lower is not None and upper is not None:` block (line 111), right after the coverage calculation (line 113):

```python
widths = upper - lower
metrics["mean_interval_width"] = round(float(widths.mean()), 2)
metrics["median_interval_width"] = round(float(widths.median()), 2)
```

**In `_slice_metrics()` (line 124):**

Pass `lower`, `upper`, and `actuals` through to `compute_metrics()` so per-slice breakdowns also get interval width:

```python
m = compute_metrics(
    g_errors,
    actuals=test_df.loc[idx, "actual_delay_minutes"],
    lower=test_df.loc[idx, "lower_bound"],
    upper=test_df.loc[idx, "upper_bound"],
    baseline_errors=g_baseline,
)
```

Note: this also gives per-slice coverage as a bonus. The key deliverable is interval width.

**In `evaluate_predictions()` (line 137):**

No changes needed — top-level already passes `lower` and `upper` to `compute_metrics()` (line 161), so `mean_interval_width` will automatically appear as `overall_mean_interval_width` via the key-prefixing logic on line 162-163.

**In `print_evaluation()` (line 264):**

Add after coverage (line 279):

```python
if "overall_mean_interval_width" in results:
    print(f"  Interval Width: {results['overall_mean_interval_width']} min (mean), "
          f"{results['overall_median_interval_width']} min (median)")
```

**Update the module docstring** (lines 1-25): add `mean_interval_width` and `median_interval_width` to the "Top-level only" list.

### 2. `backend/model_training/report.py`

**In `generate_markdown_report()`, Top-Line Results table (around line 92-106):**

Add after the coverage row (line 99):

```python
if "overall_mean_interval_width" in agg:
    lines.append(
        f"| Interval Width (mean) | {agg['overall_mean_interval_width']} min |"
    )
    lines.append(
        f"| Interval Width (median) | {agg['overall_median_interval_width']} min |"
    )
```

**In `_comparison_section()` (line 180):**

Add to the comparison metrics list (line 187-193):

```python
("Interval Width", "overall_mean_interval_width", " min", True),
```

### 3. `tests/test_evaluation.py` (NEW FILE)

No existing tests cover evaluation.py. Create tests for:

- `test_mean_interval_width_computed` — `compute_metrics` returns interval width when bounds provided
- `test_interval_width_not_present_without_bounds` — omitted when lower/upper are None
- `test_interval_width_values` — verify the math (lower=[0,2,4], upper=[10,8,6] → mean=6.0, median=6.0)
- `test_evaluate_predictions_includes_interval_width` — full pipeline includes `overall_mean_interval_width`

Use synthetic data following the pattern from `tests/test_ml_predictor.py::_make_training_df`. The test DataFrame needs: `actual_delay_minutes`, `predicted_delay`, `lower_bound`, `upper_bound`, `minutes_until_scheduled_departure`, and optionally `sailing_event_id`.

## Files NOT to Change

- `backend/model_training/backtest.py` — model-agnostic harness
- `backend/model_training/backtest_model.py` — model definitions
- `backend/ml_predictor.py` — serving layer
- `backend/dock_predictor.py` — at-dock serving layer

## Verification

```bash
uv run pytest tests/test_evaluation.py -v
uv run ruff check backend/model_training/evaluation.py backend/model_training/report.py
uv run mypy backend/model_training/evaluation.py backend/model_training/report.py
uv run pytest tests/ -v  # full suite to check nothing broke
```
