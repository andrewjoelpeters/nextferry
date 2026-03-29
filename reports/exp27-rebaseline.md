# Backtest Report: exp27-rebaseline

> Re-establish baseline with exp24 config on latest data

**Date:** 2026-03-28 22:47:26  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 49s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.26× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.48 min** (PL/MAE = 1.26×) |
| MAE | 1.97 min |
| Bias | -0.93 min |
| p90 (tail risk) | +1.33 min |
| 70% Interval Coverage | 70.0% (target: 70%) |
| Interval Width (mean) | 4.81 min |
| Interval Width (median) | 3.5 min |
| Baseline Pinball Loss | 4.39 min |
| Improvement vs baseline | 43.5% |

## Comparison vs Previous Run

| Metric | Previous | Current | Delta |
|--------|----------|---------|-------|
| Pinball Loss | 2.76 min | 2.48 min | -0.28 (better) |
| MAE | 2.22 min | 1.97 min | -0.25 (better) |
| p90 | 1.33 min | 1.33 min | 0.00 (no change) |
| Coverage | 70.0% | 70.0% | 0.00 (no change) |
| Improvement % | 61.2% | 43.5% | -17.70 (worse) |

### Per-Route Comparison

| Route | Prev PL | Curr PL | Prev p90 | Curr p90 | PL Delta |
|-------|---------|---------|----------|----------|----------|
| ed-king | 2.23 | 2.09 | +1.09 | +1.09 | -0.14 (better) |
| sea-bi | 3.32 | 2.9 | +1.68 | +1.65 | -0.42 (better) |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 2.87 | -0.81 | +1.86 |
| 1 | 6448 | 3224 | 2.18 | -0.64 | +1.40 |
| 2 | 9672 | 3224 | 2.87 | -1.49 | +1.13 |
| 3 | 12896 | 3224 | 2.31 | -0.92 | +1.17 |
| 4 | 16120 | 3228 | 2.19 | -0.79 | +1.12 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.48 | ±0.32 |
| Bias | -0.93 | ±0.29 |
| p90 | 1.34 | ±0.28 |

## By Route

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ed-king | 2.09 | -0.84 | +1.09 | 4.12 | 271623 |
| sea-bi | 2.9 | -1.03 | +1.65 | 5.53 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| Fri | 2.27 | -0.66 | +1.36 | 4.33 | 76527 |
| Mon | 2.23 | -0.69 | +1.26 | 4.77 | 81477 |
| Sat | 2.36 | -0.72 | +1.51 | 4.98 | 74514 |
| Sun | 3.42 | -1.15 | +1.92 | 6.38 | 71412 |
| Thu | 2.29 | -1.03 | +1.14 | 4.27 | 75306 |
| Tue | 1.96 | -0.94 | +0.98 | 4.26 | 77385 |
| Wed | 2.94 | -1.36 | +1.36 | 4.79 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 2.75 | -0.96 | +1.36 | 28314 |
| Early (5–7) | 2.75 | -1.31 | +1.07 | 46827 |
| Evening (19–22) | 2.05 | -0.65 | +1.28 | 80355 |
| Midday (10–15) | 1.51 | -0.63 | +0.92 | 63030 |
| PM Peak (15–19) | 1.98 | -0.66 | +1.26 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 2.4 | -0.85 | +1.33 | 16124 |
| 4–6m | 2.4 | -0.86 | +1.33 | 16124 |
| 6–8m | 2.4 | -0.86 | +1.33 | 16124 |
| 8–10m | 2.4 | -0.87 | +1.33 | 16124 |
| 10–14m | 2.41 | -0.87 | +1.33 | 32248 |
| 14–20m | 2.42 | -0.88 | +1.33 | 48372 |
| 20–30m | 2.45 | -0.89 | +1.34 | 80620 |
| 30–45m | 2.49 | -0.93 | +1.33 | 128992 |
| 45–60m | 2.53 | -0.96 | +1.34 | 112868 |
| 60–90m | 2.56 | -1.00 | +1.33 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.27 | -0.95 | +1.13 | 176352 |
| ed-king (peak) | 1.74 | -0.63 | +1.02 | 95271 |
| sea-bi (off-peak) | 3.14 | -1.09 | +1.80 | 163119 |
| sea-bi (peak) | 2.5 | -0.91 | +1.45 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.48,
    "overall_bias": -0.93,
    "overall_error_p90": 1.33,
    "n_test_samples": 532092,
    "overall_mae": 1.97,
    "overall_coverage_70pct": 70.0,
    "overall_mean_interval_width": 4.81,
    "overall_median_interval_width": 3.5,
    "overall_baseline_pinball_loss": 4.39,
    "overall_improvement_pct": 43.5,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.09,
        "bias": -0.84,
        "error_p90": 1.09,
        "n": 271623,
        "mae": 1.67,
        "mean_interval_width": 4.12,
        "median_interval_width": 3.13,
        "baseline_pinball_loss": 3.77,
        "improvement_pct": 44.6
      },
      "sea-bi": {
        "pinball_loss": 2.9,
        "bias": -1.03,
        "error_p90": 1.65,
        "n": 260469,
        "mae": 2.27,
        "mean_interval_width": 5.53,
        "median_interval_width": 3.99,
        "baseline_pinball_loss": 5.03,
        "improvement_pct": 42.4
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 3.42,
        "bias": -1.15,
        "error_p90": 1.92,
        "n": 71412,
        "mae": 2.66,
        "mean_interval_width": 6.38,
        "median_interval_width": 4.14,
        "baseline_pinball_loss": 6.0,
        "improvement_pct": 43.0
      },
      "Mon": {
        "pinball_loss": 2.23,
        "bias": -0.69,
        "error_p90": 1.26,
        "n": 81477,
        "mae": 1.72,
        "mean_interval_width": 4.77,
        "median_interval_width": 3.04,
        "baseline_pinball_loss": 4.21,
        "improvement_pct": 47.0
      },
      "Tue": {
        "pinball_loss": 1.96,
        "bias": -0.94,
        "error_p90": 0.98,
        "n": 77385,
        "mae": 1.62,
        "mean_interval_width": 4.26,
        "median_interval_width": 3.3,
        "baseline_pinball_loss": 3.28,
        "improvement_pct": 40.2
      },
      "Wed": {
        "pinball_loss": 2.94,
        "bias": -1.36,
        "error_p90": 1.36,
        "n": 75471,
        "mae": 2.42,
        "mean_interval_width": 4.79,
        "median_interval_width": 3.71,
        "baseline_pinball_loss": 5.6,
        "improvement_pct": 47.5
      },
      "Thu": {
        "pinball_loss": 2.29,
        "bias": -1.03,
        "error_p90": 1.14,
        "n": 75306,
        "mae": 1.87,
        "mean_interval_width": 4.27,
        "median_interval_width": 3.19,
        "baseline_pinball_loss": 3.48,
        "improvement_pct": 34.2
      },
      "Fri": {
        "pinball_loss": 2.27,
        "bias": -0.66,
        "error_p90": 1.36,
        "n": 76527,
        "mae": 1.73,
        "mean_interval_width": 4.33,
        "median_interval_width": 3.41,
        "baseline_pinball_loss": 4.26,
        "improvement_pct": 46.7
      },
      "Sat": {
        "pinball_loss": 2.36,
        "bias": -0.72,
        "error_p90": 1.51,
        "n": 74514,
        "mae": 1.81,
        "mean_interval_width": 4.98,
        "median_interval_width": 3.82,
        "baseline_pinball_loss": 4.03,
        "improvement_pct": 41.4
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 2.75,
        "bias": -1.31,
        "error_p90": 1.07,
        "n": 46827,
        "mae": 2.27,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 34.9
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 2.75,
        "bias": -0.96,
        "error_p90": 1.36,
        "n": 28314,
        "mae": 2.16,
        "baseline_pinball_loss": 5.63,
        "improvement_pct": 51.1
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.51,
        "bias": -0.63,
        "error_p90": 0.92,
        "n": 63030,
        "mae": 1.22,
        "baseline_pinball_loss": 4.83,
        "improvement_pct": 68.7
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 1.98,
        "bias": -0.66,
        "error_p90": 1.26,
        "n": 112398,
        "mae": 1.54,
        "baseline_pinball_loss": 3.49,
        "improvement_pct": 43.3
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.05,
        "bias": -0.65,
        "error_p90": 1.28,
        "n": 80355,
        "mae": 1.58,
        "baseline_pinball_loss": 2.94,
        "improvement_pct": 30.3
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 2.4,
        "bias": -0.85,
        "error_p90": 1.33,
        "n": 16124,
        "mae": 1.88,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.9
      },
      "4\u20136m": {
        "pinball_loss": 2.4,
        "bias": -0.86,
        "error_p90": 1.33,
        "n": 16124,
        "mae": 1.88,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.9
      },
      "6\u20138m": {
        "pinball_loss": 2.4,
        "bias": -0.86,
        "error_p90": 1.33,
        "n": 16124,
        "mae": 1.89,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.9
      },
      "8\u201310m": {
        "pinball_loss": 2.4,
        "bias": -0.87,
        "error_p90": 1.33,
        "n": 16124,
        "mae": 1.89,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.9
      },
      "10\u201314m": {
        "pinball_loss": 2.41,
        "bias": -0.87,
        "error_p90": 1.33,
        "n": 32248,
        "mae": 1.9,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.7
      },
      "14\u201320m": {
        "pinball_loss": 2.42,
        "bias": -0.88,
        "error_p90": 1.33,
        "n": 48372,
        "mae": 1.91,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.4
      },
      "20\u201330m": {
        "pinball_loss": 2.45,
        "bias": -0.89,
        "error_p90": 1.34,
        "n": 80620,
        "mae": 1.93,
        "baseline_pinball_loss": 3.94,
        "improvement_pct": 37.9
      },
      "30\u201345m": {
        "pinball_loss": 2.49,
        "bias": -0.93,
        "error_p90": 1.33,
        "n": 128992,
        "mae": 1.97,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 41.1
      },
      "45\u201360m": {
        "pinball_loss": 2.53,
        "bias": -0.96,
        "error_p90": 1.34,
        "n": 112868,
        "mae": 2.01,
        "baseline_pinball_loss": 4.94,
        "improvement_pct": 48.8
      },
      "60\u201390m": {
        "pinball_loss": 2.56,
        "bias": -1.0,
        "error_p90": 1.33,
        "n": 32248,
        "mae": 2.04,
        "baseline_pinball_loss": 5.02,
        "improvement_pct": 49.0
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.27,
        "bias": -0.95,
        "error_p90": 1.13,
        "n": 176352,
        "mae": 1.83,
        "baseline_pinball_loss": 4.15,
        "improvement_pct": 45.3
      },
      "ed-king (peak)": {
        "pinball_loss": 1.74,
        "bias": -0.63,
        "error_p90": 1.02,
        "n": 95271,
        "mae": 1.37,
        "baseline_pinball_loss": 3.07,
        "improvement_pct": 43.3
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.14,
        "bias": -1.09,
        "error_p90": 1.8,
        "n": 163119,
        "mae": 2.46,
        "baseline_pinball_loss": 5.37,
        "improvement_pct": 41.5
      },
      "sea-bi (peak)": {
        "pinball_loss": 2.5,
        "bias": -0.91,
        "error_p90": 1.45,
        "n": 97350,
        "mae": 1.97,
        "baseline_pinball_loss": 4.48,
        "improvement_pct": 44.2
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 2.48,
      "std": 0.32
    },
    "bias": {
      "mean": -0.93,
      "std": 0.29
    },
    "error_p90": {
      "mean": 1.34,
      "std": 0.28
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
