# Backtest Report: exp40-interval-reg

> min_samples_leaf=40 for q10/q90 interval models

**Date:** 2026-03-29 21:08:52  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 31s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.18× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.4 min** (PL/MAE = 1.18×) |
| MAE | 2.03 min |
| Bias | -1.28 min |
| p90 (tail risk) | +1.01 min |
| 70% Interval Coverage | 69.6% (target: 70%) |
| Interval Width (mean) | 4.78 min |
| Interval Width (median) | 3.45 min |
| Baseline Pinball Loss | 4.39 min |
| Improvement vs baseline | 45.3% |

## Comparison vs Previous Run

| Metric | Previous | Current | Delta |
|--------|----------|---------|-------|
| Pinball Loss | 2.48 min | 2.4 min | -0.08 (better) |
| MAE | 1.97 min | 2.03 min | +0.06 (worse) |
| p90 | 1.33 min | 1.01 min | -0.32 (better) |
| Coverage | 70.0% | 69.6% | -0.40 (worse) |
| Interval Width | 4.81 min | 4.78 min | -0.03 (better) |
| Improvement % | 43.5% | 45.3% | +1.80 (better) |

### Per-Route Comparison

| Route | Prev PL | Curr PL | Prev p90 | Curr p90 | PL Delta |
|-------|---------|---------|----------|----------|----------|
| ed-king | 2.09 | 2.02 | +1.09 | +0.84 | -0.07 (better) |
| sea-bi | 2.9 | 2.8 | +1.65 | +1.23 | -0.10 (better) |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 2.75 | -1.24 | +1.40 |
| 1 | 6448 | 3224 | 2.07 | -0.94 | +1.06 |
| 2 | 9672 | 3224 | 2.86 | -1.82 | +0.87 |
| 3 | 12896 | 3224 | 2.23 | -1.23 | +0.89 |
| 4 | 16120 | 3228 | 2.11 | -1.16 | +0.82 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.4 | ±0.33 |
| Bias | -1.28 | ±0.29 |
| p90 | 1.01 | ±0.21 |

## By Route

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ed-king | 2.02 | -1.13 | +0.84 | 4.07 | 271623 |
| sea-bi | 2.8 | -1.43 | +1.23 | 5.52 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| Fri | 2.16 | -0.93 | +1.10 | 4.31 | 76527 |
| Mon | 2.15 | -1.08 | +0.92 | 4.79 | 81477 |
| Sat | 2.3 | -1.14 | +1.08 | 4.94 | 74514 |
| Sun | 3.31 | -1.68 | +1.38 | 6.36 | 71412 |
| Thu | 2.23 | -1.29 | +0.91 | 4.24 | 75306 |
| Tue | 1.92 | -1.21 | +0.72 | 4.16 | 77385 |
| Wed | 2.86 | -1.67 | +1.02 | 4.76 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 2.65 | -1.29 | +0.99 | 28314 |
| Early (5–7) | 2.67 | -1.72 | +0.78 | 46827 |
| Evening (19–22) | 1.96 | -0.98 | +0.96 | 80355 |
| Midday (10–15) | 1.5 | -0.89 | +0.68 | 63030 |
| PM Peak (15–19) | 1.86 | -0.95 | +0.94 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 2.31 | -1.19 | +1.00 | 16124 |
| 4–6m | 2.31 | -1.19 | +1.00 | 16124 |
| 6–8m | 2.31 | -1.20 | +1.00 | 16124 |
| 8–10m | 2.32 | -1.20 | +1.01 | 16124 |
| 10–14m | 2.33 | -1.21 | +1.01 | 32248 |
| 14–20m | 2.34 | -1.22 | +1.01 | 48372 |
| 20–30m | 2.37 | -1.24 | +1.02 | 80620 |
| 30–45m | 2.41 | -1.29 | +1.00 | 128992 |
| 45–60m | 2.45 | -1.32 | +1.02 | 112868 |
| 60–90m | 2.48 | -1.35 | +1.01 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.23 | -1.27 | +0.88 | 176352 |
| ed-king (peak) | 1.64 | -0.89 | +0.78 | 95271 |
| sea-bi (off-peak) | 3.05 | -1.53 | +1.35 | 163119 |
| sea-bi (peak) | 2.39 | -1.26 | +1.07 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.4,
    "overall_bias": -1.28,
    "overall_error_p90": 1.01,
    "n_test_samples": 532092,
    "overall_mae": 2.03,
    "overall_coverage_70pct": 69.6,
    "overall_mean_interval_width": 4.78,
    "overall_median_interval_width": 3.45,
    "overall_baseline_pinball_loss": 4.39,
    "overall_improvement_pct": 45.3,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.02,
        "bias": -1.13,
        "error_p90": 0.84,
        "n": 271623,
        "mae": 1.73,
        "mean_interval_width": 4.07,
        "median_interval_width": 3.1,
        "baseline_pinball_loss": 3.77,
        "improvement_pct": 46.4
      },
      "sea-bi": {
        "pinball_loss": 2.8,
        "bias": -1.43,
        "error_p90": 1.23,
        "n": 260469,
        "mae": 2.34,
        "mean_interval_width": 5.52,
        "median_interval_width": 3.91,
        "baseline_pinball_loss": 5.03,
        "improvement_pct": 44.4
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 3.31,
        "bias": -1.68,
        "error_p90": 1.38,
        "n": 71412,
        "mae": 2.77,
        "mean_interval_width": 6.36,
        "median_interval_width": 4.1,
        "baseline_pinball_loss": 6.0,
        "improvement_pct": 44.8
      },
      "Mon": {
        "pinball_loss": 2.15,
        "bias": -1.08,
        "error_p90": 0.92,
        "n": 81477,
        "mae": 1.79,
        "mean_interval_width": 4.79,
        "median_interval_width": 3.08,
        "baseline_pinball_loss": 4.21,
        "improvement_pct": 48.9
      },
      "Tue": {
        "pinball_loss": 1.92,
        "bias": -1.21,
        "error_p90": 0.72,
        "n": 77385,
        "mae": 1.68,
        "mean_interval_width": 4.16,
        "median_interval_width": 3.23,
        "baseline_pinball_loss": 3.28,
        "improvement_pct": 41.4
      },
      "Wed": {
        "pinball_loss": 2.86,
        "bias": -1.67,
        "error_p90": 1.02,
        "n": 75471,
        "mae": 2.46,
        "mean_interval_width": 4.76,
        "median_interval_width": 3.71,
        "baseline_pinball_loss": 5.6,
        "improvement_pct": 48.9
      },
      "Thu": {
        "pinball_loss": 2.23,
        "bias": -1.29,
        "error_p90": 0.91,
        "n": 75306,
        "mae": 1.91,
        "mean_interval_width": 4.24,
        "median_interval_width": 3.18,
        "baseline_pinball_loss": 3.48,
        "improvement_pct": 35.9
      },
      "Fri": {
        "pinball_loss": 2.16,
        "bias": -0.93,
        "error_p90": 1.1,
        "n": 76527,
        "mae": 1.75,
        "mean_interval_width": 4.31,
        "median_interval_width": 3.37,
        "baseline_pinball_loss": 4.26,
        "improvement_pct": 49.3
      },
      "Sat": {
        "pinball_loss": 2.3,
        "bias": -1.14,
        "error_p90": 1.08,
        "n": 74514,
        "mae": 1.91,
        "mean_interval_width": 4.94,
        "median_interval_width": 3.78,
        "baseline_pinball_loss": 4.03,
        "improvement_pct": 42.9
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 2.67,
        "bias": -1.72,
        "error_p90": 0.78,
        "n": 46827,
        "mae": 2.35,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 36.8
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 2.65,
        "bias": -1.29,
        "error_p90": 0.99,
        "n": 28314,
        "mae": 2.2,
        "baseline_pinball_loss": 5.63,
        "improvement_pct": 52.9
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.5,
        "bias": -0.89,
        "error_p90": 0.68,
        "n": 63030,
        "mae": 1.3,
        "baseline_pinball_loss": 4.83,
        "improvement_pct": 68.9
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 1.86,
        "bias": -0.95,
        "error_p90": 0.94,
        "n": 112398,
        "mae": 1.56,
        "baseline_pinball_loss": 3.49,
        "improvement_pct": 46.7
      },
      "Evening (19\u201322)": {
        "pinball_loss": 1.96,
        "bias": -0.98,
        "error_p90": 0.96,
        "n": 80355,
        "mae": 1.63,
        "baseline_pinball_loss": 2.94,
        "improvement_pct": 33.4
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 2.31,
        "bias": -1.19,
        "error_p90": 1.0,
        "n": 16124,
        "mae": 1.94,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 41.2
      },
      "4\u20136m": {
        "pinball_loss": 2.31,
        "bias": -1.19,
        "error_p90": 1.0,
        "n": 16124,
        "mae": 1.94,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 41.2
      },
      "6\u20138m": {
        "pinball_loss": 2.31,
        "bias": -1.2,
        "error_p90": 1.0,
        "n": 16124,
        "mae": 1.94,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 41.2
      },
      "8\u201310m": {
        "pinball_loss": 2.32,
        "bias": -1.2,
        "error_p90": 1.01,
        "n": 16124,
        "mae": 1.95,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 41.0
      },
      "10\u201314m": {
        "pinball_loss": 2.33,
        "bias": -1.21,
        "error_p90": 1.01,
        "n": 32248,
        "mae": 1.95,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 40.8
      },
      "14\u201320m": {
        "pinball_loss": 2.34,
        "bias": -1.22,
        "error_p90": 1.01,
        "n": 48372,
        "mae": 1.97,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 40.4
      },
      "20\u201330m": {
        "pinball_loss": 2.37,
        "bias": -1.24,
        "error_p90": 1.02,
        "n": 80620,
        "mae": 1.99,
        "baseline_pinball_loss": 3.94,
        "improvement_pct": 39.9
      },
      "30\u201345m": {
        "pinball_loss": 2.41,
        "bias": -1.29,
        "error_p90": 1.0,
        "n": 128992,
        "mae": 2.03,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 43.0
      },
      "45\u201360m": {
        "pinball_loss": 2.45,
        "bias": -1.32,
        "error_p90": 1.02,
        "n": 112868,
        "mae": 2.07,
        "baseline_pinball_loss": 4.94,
        "improvement_pct": 50.4
      },
      "60\u201390m": {
        "pinball_loss": 2.48,
        "bias": -1.35,
        "error_p90": 1.01,
        "n": 32248,
        "mae": 2.11,
        "baseline_pinball_loss": 5.02,
        "improvement_pct": 50.6
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.23,
        "bias": -1.27,
        "error_p90": 0.88,
        "n": 176352,
        "mae": 1.91,
        "baseline_pinball_loss": 4.15,
        "improvement_pct": 46.3
      },
      "ed-king (peak)": {
        "pinball_loss": 1.64,
        "bias": -0.89,
        "error_p90": 0.78,
        "n": 95271,
        "mae": 1.39,
        "baseline_pinball_loss": 3.07,
        "improvement_pct": 46.5
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.05,
        "bias": -1.53,
        "error_p90": 1.35,
        "n": 163119,
        "mae": 2.54,
        "baseline_pinball_loss": 5.37,
        "improvement_pct": 43.2
      },
      "sea-bi (peak)": {
        "pinball_loss": 2.39,
        "bias": -1.26,
        "error_p90": 1.07,
        "n": 97350,
        "mae": 2.01,
        "baseline_pinball_loss": 4.48,
        "improvement_pct": 46.6
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 2.4,
      "std": 0.33
    },
    "bias": {
      "mean": -1.28,
      "std": 0.29
    },
    "error_p90": {
      "mean": 1.01,
      "std": 0.21
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
