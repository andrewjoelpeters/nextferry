# Backtest Report: exp33-ngboost

> NGBoost distributional model (Normal, 200 estimators)

**Date:** 2026-03-29 13:33:21  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 9m 41s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.35× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.76 min** (PL/MAE = 1.35×) |
| MAE | 2.05 min |
| Bias | -0.63 min |
| p90 (tail risk) | +1.90 min |
| 70% Interval Coverage | 81.0% (target: 70%) |
| Interval Width (mean) | 5.95 min |
| Interval Width (median) | 4.63 min |
| Baseline Pinball Loss | 4.39 min |
| Improvement vs baseline | 37.1% |

## Comparison vs Previous Run

| Metric | Previous | Current | Delta |
|--------|----------|---------|-------|
| Pinball Loss | 2.48 min | 2.76 min | +0.28 (worse) |
| MAE | 1.97 min | 2.05 min | +0.08 (worse) |
| p90 | 1.33 min | 1.9 min | +0.57 (worse) |
| Coverage | 70.0% | 81.0% | +11.00 (better) |
| Interval Width | 4.81 min | 5.95 min | +1.14 (worse) |
| Improvement % | 43.5% | 37.1% | -6.40 (worse) |

### Per-Route Comparison

| Route | Prev PL | Curr PL | Prev p90 | Curr p90 | PL Delta |
|-------|---------|---------|----------|----------|----------|
| ed-king | 2.09 | 2.33 | +1.09 | +1.50 | +0.24 (worse) |
| sea-bi | 2.9 | 3.21 | +1.65 | +2.52 | +0.31 (worse) |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.28 | -0.36 | +2.69 |
| 1 | 6448 | 3224 | 2.49 | -0.36 | +1.95 |
| 2 | 9672 | 3224 | 3.11 | -1.20 | +1.67 |
| 3 | 12896 | 3224 | 2.49 | -0.63 | +1.60 |
| 4 | 16120 | 3228 | 2.42 | -0.62 | +1.57 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.76 | ±0.36 |
| Bias | -0.63 | ±0.31 |
| p90 | 1.9 | ±0.42 |

## By Route

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ed-king | 2.33 | -0.59 | +1.50 | 5.34 | 271623 |
| sea-bi | 3.21 | -0.68 | +2.52 | 6.58 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| Fri | 2.56 | -0.39 | +2.01 | 5.57 | 76527 |
| Mon | 2.55 | -0.41 | +1.83 | 5.81 | 81477 |
| Sat | 2.65 | -0.42 | +2.09 | 6.03 | 74514 |
| Sun | 3.74 | -0.78 | +2.58 | 7.15 | 71412 |
| Thu | 2.49 | -0.70 | +1.56 | 5.48 | 75306 |
| Tue | 2.18 | -0.68 | +1.45 | 5.41 | 77385 |
| Wed | 3.21 | -1.08 | +1.96 | 6.27 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 2.97 | -0.61 | +1.84 | 28314 |
| Early (5–7) | 2.98 | -0.98 | +1.53 | 46827 |
| Evening (19–22) | 2.27 | -0.43 | +1.79 | 80355 |
| Midday (10–15) | 1.65 | -0.64 | +1.01 | 63030 |
| PM Peak (15–19) | 2.25 | -0.40 | +1.70 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 2.68 | -0.55 | +1.90 | 16124 |
| 4–6m | 2.67 | -0.56 | +1.89 | 16124 |
| 6–8m | 2.66 | -0.57 | +1.88 | 16124 |
| 8–10m | 2.66 | -0.58 | +1.87 | 16124 |
| 10–14m | 2.67 | -0.59 | +1.87 | 32248 |
| 14–20m | 2.68 | -0.60 | +1.87 | 48372 |
| 20–30m | 2.7 | -0.62 | +1.86 | 80620 |
| 30–45m | 2.76 | -0.63 | +1.89 | 128992 |
| 45–60m | 2.83 | -0.66 | +1.93 | 112868 |
| 60–90m | 2.85 | -0.69 | +1.93 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.52 | -0.68 | +1.61 | 176352 |
| ed-king (peak) | 1.98 | -0.43 | +1.32 | 95271 |
| sea-bi (off-peak) | 3.47 | -0.71 | +2.86 | 163119 |
| sea-bi (peak) | 2.76 | -0.61 | +2.05 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.76,
    "overall_bias": -0.63,
    "overall_error_p90": 1.9,
    "n_test_samples": 532092,
    "overall_mae": 2.05,
    "overall_coverage_70pct": 81.0,
    "overall_mean_interval_width": 5.95,
    "overall_median_interval_width": 4.63,
    "overall_baseline_pinball_loss": 4.39,
    "overall_improvement_pct": 37.1,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.33,
        "bias": -0.59,
        "error_p90": 1.5,
        "n": 271623,
        "mae": 1.75,
        "mean_interval_width": 5.34,
        "median_interval_width": 4.3,
        "baseline_pinball_loss": 3.77,
        "improvement_pct": 38.2
      },
      "sea-bi": {
        "pinball_loss": 3.21,
        "bias": -0.68,
        "error_p90": 2.52,
        "n": 260469,
        "mae": 2.36,
        "mean_interval_width": 6.58,
        "median_interval_width": 5.07,
        "baseline_pinball_loss": 5.03,
        "improvement_pct": 36.2
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 3.74,
        "bias": -0.78,
        "error_p90": 2.58,
        "n": 71412,
        "mae": 2.75,
        "mean_interval_width": 7.15,
        "median_interval_width": 5.1,
        "baseline_pinball_loss": 6.0,
        "improvement_pct": 37.7
      },
      "Mon": {
        "pinball_loss": 2.55,
        "bias": -0.41,
        "error_p90": 1.83,
        "n": 81477,
        "mae": 1.84,
        "mean_interval_width": 5.81,
        "median_interval_width": 4.25,
        "baseline_pinball_loss": 4.21,
        "improvement_pct": 39.4
      },
      "Tue": {
        "pinball_loss": 2.18,
        "bias": -0.68,
        "error_p90": 1.45,
        "n": 77385,
        "mae": 1.68,
        "mean_interval_width": 5.41,
        "median_interval_width": 4.45,
        "baseline_pinball_loss": 3.28,
        "improvement_pct": 33.4
      },
      "Wed": {
        "pinball_loss": 3.21,
        "bias": -1.08,
        "error_p90": 1.96,
        "n": 75471,
        "mae": 2.5,
        "mean_interval_width": 6.27,
        "median_interval_width": 5.18,
        "baseline_pinball_loss": 5.6,
        "improvement_pct": 42.6
      },
      "Thu": {
        "pinball_loss": 2.49,
        "bias": -0.7,
        "error_p90": 1.56,
        "n": 75306,
        "mae": 1.89,
        "mean_interval_width": 5.48,
        "median_interval_width": 4.39,
        "baseline_pinball_loss": 3.48,
        "improvement_pct": 28.5
      },
      "Fri": {
        "pinball_loss": 2.56,
        "bias": -0.39,
        "error_p90": 2.01,
        "n": 76527,
        "mae": 1.84,
        "mean_interval_width": 5.57,
        "median_interval_width": 4.42,
        "baseline_pinball_loss": 4.26,
        "improvement_pct": 39.9
      },
      "Sat": {
        "pinball_loss": 2.65,
        "bias": -0.42,
        "error_p90": 2.09,
        "n": 74514,
        "mae": 1.91,
        "mean_interval_width": 6.03,
        "median_interval_width": 4.75,
        "baseline_pinball_loss": 4.03,
        "improvement_pct": 34.2
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 2.98,
        "bias": -0.98,
        "error_p90": 1.53,
        "n": 46827,
        "mae": 2.31,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 29.5
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 2.97,
        "bias": -0.61,
        "error_p90": 1.84,
        "n": 28314,
        "mae": 2.18,
        "baseline_pinball_loss": 5.63,
        "improvement_pct": 47.2
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.65,
        "bias": -0.64,
        "error_p90": 1.01,
        "n": 63030,
        "mae": 1.32,
        "baseline_pinball_loss": 4.83,
        "improvement_pct": 65.8
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.25,
        "bias": -0.4,
        "error_p90": 1.7,
        "n": 112398,
        "mae": 1.63,
        "baseline_pinball_loss": 3.49,
        "improvement_pct": 35.6
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.27,
        "bias": -0.43,
        "error_p90": 1.79,
        "n": 80355,
        "mae": 1.66,
        "baseline_pinball_loss": 2.94,
        "improvement_pct": 22.8
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 2.68,
        "bias": -0.55,
        "error_p90": 1.9,
        "n": 16124,
        "mae": 1.97,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 31.8
      },
      "4\u20136m": {
        "pinball_loss": 2.67,
        "bias": -0.56,
        "error_p90": 1.89,
        "n": 16124,
        "mae": 1.97,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 32.1
      },
      "6\u20138m": {
        "pinball_loss": 2.66,
        "bias": -0.57,
        "error_p90": 1.88,
        "n": 16124,
        "mae": 1.97,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 32.3
      },
      "8\u201310m": {
        "pinball_loss": 2.66,
        "bias": -0.58,
        "error_p90": 1.87,
        "n": 16124,
        "mae": 1.97,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 32.3
      },
      "10\u201314m": {
        "pinball_loss": 2.67,
        "bias": -0.59,
        "error_p90": 1.87,
        "n": 32248,
        "mae": 1.97,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 32.1
      },
      "14\u201320m": {
        "pinball_loss": 2.68,
        "bias": -0.6,
        "error_p90": 1.87,
        "n": 48372,
        "mae": 1.99,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 31.8
      },
      "20\u201330m": {
        "pinball_loss": 2.7,
        "bias": -0.62,
        "error_p90": 1.86,
        "n": 80620,
        "mae": 2.01,
        "baseline_pinball_loss": 3.94,
        "improvement_pct": 31.5
      },
      "30\u201345m": {
        "pinball_loss": 2.76,
        "bias": -0.63,
        "error_p90": 1.89,
        "n": 128992,
        "mae": 2.05,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 34.8
      },
      "45\u201360m": {
        "pinball_loss": 2.83,
        "bias": -0.66,
        "error_p90": 1.93,
        "n": 112868,
        "mae": 2.11,
        "baseline_pinball_loss": 4.94,
        "improvement_pct": 42.7
      },
      "60\u201390m": {
        "pinball_loss": 2.85,
        "bias": -0.69,
        "error_p90": 1.93,
        "n": 32248,
        "mae": 2.13,
        "baseline_pinball_loss": 5.02,
        "improvement_pct": 43.3
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.52,
        "bias": -0.68,
        "error_p90": 1.61,
        "n": 176352,
        "mae": 1.91,
        "baseline_pinball_loss": 4.15,
        "improvement_pct": 39.3
      },
      "ed-king (peak)": {
        "pinball_loss": 1.98,
        "bias": -0.43,
        "error_p90": 1.32,
        "n": 95271,
        "mae": 1.46,
        "baseline_pinball_loss": 3.07,
        "improvement_pct": 35.4
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.47,
        "bias": -0.71,
        "error_p90": 2.86,
        "n": 163119,
        "mae": 2.55,
        "baseline_pinball_loss": 5.37,
        "improvement_pct": 35.4
      },
      "sea-bi (peak)": {
        "pinball_loss": 2.76,
        "bias": -0.61,
        "error_p90": 2.05,
        "n": 97350,
        "mae": 2.04,
        "baseline_pinball_loss": 4.48,
        "improvement_pct": 38.3
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 2.76,
      "std": 0.36
    },
    "bias": {
      "mean": -0.63,
      "std": 0.31
    },
    "error_p90": {
      "mean": 1.9,
      "std": 0.42
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
