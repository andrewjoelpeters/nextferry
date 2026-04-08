# Backtest Report: exp29-add-turnaround

> Add turnaround_minutes back to features

**Date:** 2026-03-29 12:09:59  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 16s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.24× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.94 min** (PL/MAE = 1.24×) |
| MAE | 2.37 min |
| Bias | -1.25 min |
| p90 (tail risk) | +1.37 min |
| 70% Interval Coverage | 71.4% (target: 70%) |
| Interval Width (mean) | 6.18 min |
| Interval Width (median) | 4.46 min |
| Baseline Pinball Loss | 4.39 min |
| Improvement vs baseline | 33.0% |

## Comparison vs Previous Run

| Metric | Previous | Current | Delta |
|--------|----------|---------|-------|
| Pinball Loss | 2.48 min | 2.94 min | +0.46 (worse) |
| MAE | 1.97 min | 2.37 min | +0.40 (worse) |
| p90 | 1.33 min | 1.37 min | +0.04 (worse) |
| Coverage | 70.0% | 71.4% | +1.40 (better) |
| Interval Width | 4.81 min | 6.18 min | +1.37 (worse) |
| Improvement % | 43.5% | 33.0% | -10.50 (worse) |

### Per-Route Comparison

| Route | Prev PL | Curr PL | Prev p90 | Curr p90 | PL Delta |
|-------|---------|---------|----------|----------|----------|
| ed-king | 2.09 | 2.43 | +1.09 | +1.21 | +0.34 (worse) |
| sea-bi | 2.9 | 3.46 | +1.65 | +1.56 | +0.56 (worse) |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.56 | -0.97 | +2.08 |
| 1 | 6448 | 3224 | 2.63 | -0.92 | +1.55 |
| 2 | 9672 | 3224 | 3.4 | -1.93 | +1.20 |
| 3 | 12896 | 3224 | 2.62 | -1.22 | +1.12 |
| 4 | 16120 | 3228 | 2.47 | -1.22 | +1.00 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.94 | ±0.45 |
| Bias | -1.25 | ±0.36 |
| p90 | 1.39 | ±0.39 |

## By Route

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ed-king | 2.43 | -1.03 | +1.21 | 5.23 | 271623 |
| sea-bi | 3.46 | -1.49 | +1.56 | 7.17 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| Fri | 2.83 | -0.71 | +1.55 | 5.78 | 76527 |
| Mon | 2.55 | -0.97 | +1.15 | 5.67 | 81477 |
| Sat | 2.82 | -1.18 | +1.49 | 6.78 | 74514 |
| Sun | 4.03 | -1.57 | +1.98 | 7.88 | 71412 |
| Thu | 2.64 | -1.22 | +1.20 | 5.55 | 75306 |
| Tue | 2.36 | -1.35 | +0.96 | 5.39 | 77385 |
| Wed | 3.42 | -1.80 | +1.40 | 6.37 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 3.21 | -1.50 | +1.09 | 28314 |
| Early (5–7) | 3.09 | -1.64 | +1.09 | 46827 |
| Evening (19–22) | 2.31 | -0.88 | +1.35 | 80355 |
| Midday (10–15) | 1.71 | -1.00 | +0.78 | 63030 |
| PM Peak (15–19) | 2.13 | -1.01 | +1.09 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 2.69 | -1.10 | +1.33 | 16124 |
| 4–6m | 2.69 | -1.10 | +1.33 | 16124 |
| 6–8m | 2.69 | -1.11 | +1.33 | 16124 |
| 8–10m | 2.7 | -1.11 | +1.33 | 16124 |
| 10–14m | 2.71 | -1.12 | +1.33 | 32248 |
| 14–20m | 2.71 | -1.14 | +1.34 | 48372 |
| 20–30m | 2.75 | -1.20 | +1.32 | 80620 |
| 30–45m | 2.92 | -1.31 | +1.32 | 128992 |
| 45–60m | 3.15 | -1.30 | +1.45 | 112868 |
| 60–90m | 3.21 | -1.35 | +1.45 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.71 | -1.15 | +1.33 | 176352 |
| ed-king (peak) | 1.91 | -0.80 | +1.04 | 95271 |
| sea-bi (off-peak) | 3.84 | -1.50 | +1.93 | 163119 |
| sea-bi (peak) | 2.83 | -1.47 | +1.17 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.94,
    "overall_bias": -1.25,
    "overall_error_p90": 1.37,
    "n_test_samples": 532092,
    "overall_mae": 2.37,
    "overall_coverage_70pct": 71.4,
    "overall_mean_interval_width": 6.18,
    "overall_median_interval_width": 4.46,
    "overall_baseline_pinball_loss": 4.39,
    "overall_improvement_pct": 33.0,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.43,
        "bias": -1.03,
        "error_p90": 1.21,
        "n": 271623,
        "mae": 1.96,
        "mean_interval_width": 5.23,
        "median_interval_width": 4.01,
        "baseline_pinball_loss": 3.77,
        "improvement_pct": 35.5
      },
      "sea-bi": {
        "pinball_loss": 3.46,
        "bias": -1.49,
        "error_p90": 1.56,
        "n": 260469,
        "mae": 2.8,
        "mean_interval_width": 7.17,
        "median_interval_width": 5.08,
        "baseline_pinball_loss": 5.03,
        "improvement_pct": 31.3
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 4.03,
        "bias": -1.57,
        "error_p90": 1.98,
        "n": 71412,
        "mae": 3.21,
        "mean_interval_width": 7.88,
        "median_interval_width": 5.4,
        "baseline_pinball_loss": 6.0,
        "improvement_pct": 32.8
      },
      "Mon": {
        "pinball_loss": 2.55,
        "bias": -0.97,
        "error_p90": 1.15,
        "n": 81477,
        "mae": 2.02,
        "mean_interval_width": 5.67,
        "median_interval_width": 3.76,
        "baseline_pinball_loss": 4.21,
        "improvement_pct": 39.4
      },
      "Tue": {
        "pinball_loss": 2.36,
        "bias": -1.35,
        "error_p90": 0.96,
        "n": 77385,
        "mae": 2.02,
        "mean_interval_width": 5.39,
        "median_interval_width": 3.93,
        "baseline_pinball_loss": 3.28,
        "improvement_pct": 28.0
      },
      "Wed": {
        "pinball_loss": 3.42,
        "bias": -1.8,
        "error_p90": 1.4,
        "n": 75471,
        "mae": 2.88,
        "mean_interval_width": 6.37,
        "median_interval_width": 4.93,
        "baseline_pinball_loss": 5.6,
        "improvement_pct": 38.9
      },
      "Thu": {
        "pinball_loss": 2.64,
        "bias": -1.22,
        "error_p90": 1.2,
        "n": 75306,
        "mae": 2.17,
        "mean_interval_width": 5.55,
        "median_interval_width": 3.87,
        "baseline_pinball_loss": 3.48,
        "improvement_pct": 24.2
      },
      "Fri": {
        "pinball_loss": 2.83,
        "bias": -0.71,
        "error_p90": 1.55,
        "n": 76527,
        "mae": 2.13,
        "mean_interval_width": 5.78,
        "median_interval_width": 4.46,
        "baseline_pinball_loss": 4.26,
        "improvement_pct": 33.5
      },
      "Sat": {
        "pinball_loss": 2.82,
        "bias": -1.18,
        "error_p90": 1.49,
        "n": 74514,
        "mae": 2.27,
        "mean_interval_width": 6.78,
        "median_interval_width": 5.36,
        "baseline_pinball_loss": 4.03,
        "improvement_pct": 30.0
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.09,
        "bias": -1.64,
        "error_p90": 1.09,
        "n": 46827,
        "mae": 2.61,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 26.9
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 3.21,
        "bias": -1.5,
        "error_p90": 1.09,
        "n": 28314,
        "mae": 2.64,
        "baseline_pinball_loss": 5.63,
        "improvement_pct": 43.0
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.71,
        "bias": -1.0,
        "error_p90": 0.78,
        "n": 63030,
        "mae": 1.47,
        "baseline_pinball_loss": 4.83,
        "improvement_pct": 64.6
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.13,
        "bias": -1.01,
        "error_p90": 1.09,
        "n": 112398,
        "mae": 1.76,
        "baseline_pinball_loss": 3.49,
        "improvement_pct": 39.0
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.31,
        "bias": -0.88,
        "error_p90": 1.35,
        "n": 80355,
        "mae": 1.83,
        "baseline_pinball_loss": 2.94,
        "improvement_pct": 21.4
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 2.69,
        "bias": -1.1,
        "error_p90": 1.33,
        "n": 16124,
        "mae": 2.16,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 31.5
      },
      "4\u20136m": {
        "pinball_loss": 2.69,
        "bias": -1.1,
        "error_p90": 1.33,
        "n": 16124,
        "mae": 2.16,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 31.6
      },
      "6\u20138m": {
        "pinball_loss": 2.69,
        "bias": -1.11,
        "error_p90": 1.33,
        "n": 16124,
        "mae": 2.16,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 31.6
      },
      "8\u201310m": {
        "pinball_loss": 2.7,
        "bias": -1.11,
        "error_p90": 1.33,
        "n": 16124,
        "mae": 2.17,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 31.3
      },
      "10\u201314m": {
        "pinball_loss": 2.71,
        "bias": -1.12,
        "error_p90": 1.33,
        "n": 32248,
        "mae": 2.18,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 31.1
      },
      "14\u201320m": {
        "pinball_loss": 2.71,
        "bias": -1.14,
        "error_p90": 1.34,
        "n": 48372,
        "mae": 2.19,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 31.0
      },
      "20\u201330m": {
        "pinball_loss": 2.75,
        "bias": -1.2,
        "error_p90": 1.32,
        "n": 80620,
        "mae": 2.23,
        "baseline_pinball_loss": 3.94,
        "improvement_pct": 30.2
      },
      "30\u201345m": {
        "pinball_loss": 2.92,
        "bias": -1.31,
        "error_p90": 1.32,
        "n": 128992,
        "mae": 2.38,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 31.0
      },
      "45\u201360m": {
        "pinball_loss": 3.15,
        "bias": -1.3,
        "error_p90": 1.45,
        "n": 112868,
        "mae": 2.53,
        "baseline_pinball_loss": 4.94,
        "improvement_pct": 36.3
      },
      "60\u201390m": {
        "pinball_loss": 3.21,
        "bias": -1.35,
        "error_p90": 1.45,
        "n": 32248,
        "mae": 2.59,
        "baseline_pinball_loss": 5.02,
        "improvement_pct": 36.1
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.71,
        "bias": -1.15,
        "error_p90": 1.33,
        "n": 176352,
        "mae": 2.19,
        "baseline_pinball_loss": 4.15,
        "improvement_pct": 34.7
      },
      "ed-king (peak)": {
        "pinball_loss": 1.91,
        "bias": -0.8,
        "error_p90": 1.04,
        "n": 95271,
        "mae": 1.54,
        "baseline_pinball_loss": 3.07,
        "improvement_pct": 37.7
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.84,
        "bias": -1.5,
        "error_p90": 1.93,
        "n": 163119,
        "mae": 3.06,
        "baseline_pinball_loss": 5.37,
        "improvement_pct": 28.5
      },
      "sea-bi (peak)": {
        "pinball_loss": 2.83,
        "bias": -1.47,
        "error_p90": 1.17,
        "n": 97350,
        "mae": 2.38,
        "baseline_pinball_loss": 4.48,
        "improvement_pct": 36.8
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 2.94,
      "std": 0.45
    },
    "bias": {
      "mean": -1.25,
      "std": 0.36
    },
    "error_p90": {
      "mean": 1.39,
      "std": 0.39
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
