# Backtest Report: exp41-delay-ratio

> Add delay_horizon_ratio = delay/horizon feature

**Date:** 2026-03-29 22:33:58  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 6s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.19× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.41 min** (PL/MAE = 1.19×) |
| MAE | 2.03 min |
| Bias | -1.27 min |
| p90 (tail risk) | +1.01 min |
| 70% Interval Coverage | 70.4% (target: 70%) |
| Interval Width (mean) | 4.85 min |
| Interval Width (median) | 3.51 min |
| Baseline Pinball Loss | 4.39 min |
| Improvement vs baseline | 45.1% |

## Comparison vs Previous Run

| Metric | Previous | Current | Delta |
|--------|----------|---------|-------|
| Pinball Loss | 2.48 min | 2.41 min | -0.07 (better) |
| MAE | 1.97 min | 2.03 min | +0.06 (worse) |
| p90 | 1.33 min | 1.01 min | -0.32 (better) |
| Coverage | 70.0% | 70.4% | +0.40 (better) |
| Interval Width | 4.81 min | 4.85 min | +0.04 (worse) |
| Improvement % | 43.5% | 45.1% | +1.60 (better) |

### Per-Route Comparison

| Route | Prev PL | Curr PL | Prev p90 | Curr p90 | PL Delta |
|-------|---------|---------|----------|----------|----------|
| ed-king | 2.09 | 2.03 | +1.09 | +0.85 | -0.06 (better) |
| sea-bi | 2.9 | 2.81 | +1.65 | +1.24 | -0.09 (better) |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 2.78 | -1.20 | +1.45 |
| 1 | 6448 | 3224 | 2.09 | -0.96 | +1.07 |
| 2 | 9672 | 3224 | 2.86 | -1.80 | +0.87 |
| 3 | 12896 | 3224 | 2.22 | -1.24 | +0.88 |
| 4 | 16120 | 3228 | 2.1 | -1.16 | +0.82 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.41 | ±0.34 |
| Bias | -1.27 | ±0.28 |
| p90 | 1.02 | ±0.23 |

## By Route

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ed-king | 2.03 | -1.14 | +0.85 | 4.14 | 271623 |
| sea-bi | 2.81 | -1.41 | +1.24 | 5.58 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| Fri | 2.17 | -0.93 | +1.09 | 4.36 | 76527 |
| Mon | 2.13 | -1.08 | +0.93 | 4.78 | 81477 |
| Sat | 2.3 | -1.14 | +1.09 | 5.05 | 74514 |
| Sun | 3.32 | -1.66 | +1.43 | 6.4 | 71412 |
| Thu | 2.22 | -1.29 | +0.89 | 4.3 | 75306 |
| Tue | 1.93 | -1.20 | +0.73 | 4.28 | 77385 |
| Wed | 2.87 | -1.65 | +1.03 | 4.86 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 2.66 | -1.29 | +0.97 | 28314 |
| Early (5–7) | 2.66 | -1.71 | +0.78 | 46827 |
| Evening (19–22) | 1.98 | -0.98 | +0.97 | 80355 |
| Midday (10–15) | 1.51 | -0.89 | +0.69 | 63030 |
| PM Peak (15–19) | 1.87 | -0.94 | +0.94 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 2.32 | -1.18 | +1.01 | 16124 |
| 4–6m | 2.32 | -1.19 | +1.00 | 16124 |
| 6–8m | 2.32 | -1.19 | +1.00 | 16124 |
| 8–10m | 2.32 | -1.20 | +1.01 | 16124 |
| 10–14m | 2.33 | -1.21 | +1.01 | 32248 |
| 14–20m | 2.35 | -1.22 | +1.01 | 48372 |
| 20–30m | 2.37 | -1.24 | +1.02 | 80620 |
| 30–45m | 2.41 | -1.28 | +1.01 | 128992 |
| 45–60m | 2.46 | -1.31 | +1.02 | 112868 |
| 60–90m | 2.49 | -1.35 | +1.02 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.23 | -1.27 | +0.89 | 176352 |
| ed-king (peak) | 1.65 | -0.88 | +0.78 | 95271 |
| sea-bi (off-peak) | 3.05 | -1.52 | +1.38 | 163119 |
| sea-bi (peak) | 2.39 | -1.25 | +1.07 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.41,
    "overall_bias": -1.27,
    "overall_error_p90": 1.01,
    "n_test_samples": 532092,
    "overall_mae": 2.03,
    "overall_coverage_70pct": 70.4,
    "overall_mean_interval_width": 4.85,
    "overall_median_interval_width": 3.51,
    "overall_baseline_pinball_loss": 4.39,
    "overall_improvement_pct": 45.1,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.03,
        "bias": -1.14,
        "error_p90": 0.85,
        "n": 271623,
        "mae": 1.73,
        "mean_interval_width": 4.14,
        "median_interval_width": 3.14,
        "baseline_pinball_loss": 3.77,
        "improvement_pct": 46.2
      },
      "sea-bi": {
        "pinball_loss": 2.81,
        "bias": -1.41,
        "error_p90": 1.24,
        "n": 260469,
        "mae": 2.34,
        "mean_interval_width": 5.58,
        "median_interval_width": 3.98,
        "baseline_pinball_loss": 5.03,
        "improvement_pct": 44.2
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 3.32,
        "bias": -1.66,
        "error_p90": 1.43,
        "n": 71412,
        "mae": 2.77,
        "mean_interval_width": 6.4,
        "median_interval_width": 4.15,
        "baseline_pinball_loss": 6.0,
        "improvement_pct": 44.7
      },
      "Mon": {
        "pinball_loss": 2.13,
        "bias": -1.08,
        "error_p90": 0.93,
        "n": 81477,
        "mae": 1.78,
        "mean_interval_width": 4.78,
        "median_interval_width": 3.1,
        "baseline_pinball_loss": 4.21,
        "improvement_pct": 49.4
      },
      "Tue": {
        "pinball_loss": 1.93,
        "bias": -1.2,
        "error_p90": 0.73,
        "n": 77385,
        "mae": 1.69,
        "mean_interval_width": 4.28,
        "median_interval_width": 3.31,
        "baseline_pinball_loss": 3.28,
        "improvement_pct": 41.1
      },
      "Wed": {
        "pinball_loss": 2.87,
        "bias": -1.65,
        "error_p90": 1.03,
        "n": 75471,
        "mae": 2.46,
        "mean_interval_width": 4.86,
        "median_interval_width": 3.75,
        "baseline_pinball_loss": 5.6,
        "improvement_pct": 48.7
      },
      "Thu": {
        "pinball_loss": 2.22,
        "bias": -1.29,
        "error_p90": 0.89,
        "n": 75306,
        "mae": 1.91,
        "mean_interval_width": 4.3,
        "median_interval_width": 3.26,
        "baseline_pinball_loss": 3.48,
        "improvement_pct": 36.2
      },
      "Fri": {
        "pinball_loss": 2.17,
        "bias": -0.93,
        "error_p90": 1.09,
        "n": 76527,
        "mae": 1.76,
        "mean_interval_width": 4.36,
        "median_interval_width": 3.4,
        "baseline_pinball_loss": 4.26,
        "improvement_pct": 49.0
      },
      "Sat": {
        "pinball_loss": 2.3,
        "bias": -1.14,
        "error_p90": 1.09,
        "n": 74514,
        "mae": 1.91,
        "mean_interval_width": 5.05,
        "median_interval_width": 3.86,
        "baseline_pinball_loss": 4.03,
        "improvement_pct": 42.9
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 2.66,
        "bias": -1.71,
        "error_p90": 0.78,
        "n": 46827,
        "mae": 2.34,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 37.1
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 2.66,
        "bias": -1.29,
        "error_p90": 0.97,
        "n": 28314,
        "mae": 2.2,
        "baseline_pinball_loss": 5.63,
        "improvement_pct": 52.7
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.51,
        "bias": -0.89,
        "error_p90": 0.69,
        "n": 63030,
        "mae": 1.31,
        "baseline_pinball_loss": 4.83,
        "improvement_pct": 68.7
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 1.87,
        "bias": -0.94,
        "error_p90": 0.94,
        "n": 112398,
        "mae": 1.56,
        "baseline_pinball_loss": 3.49,
        "improvement_pct": 46.5
      },
      "Evening (19\u201322)": {
        "pinball_loss": 1.98,
        "bias": -0.98,
        "error_p90": 0.97,
        "n": 80355,
        "mae": 1.64,
        "baseline_pinball_loss": 2.94,
        "improvement_pct": 32.7
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 2.32,
        "bias": -1.18,
        "error_p90": 1.01,
        "n": 16124,
        "mae": 1.94,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 40.9
      },
      "4\u20136m": {
        "pinball_loss": 2.32,
        "bias": -1.19,
        "error_p90": 1.0,
        "n": 16124,
        "mae": 1.94,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 41.0
      },
      "6\u20138m": {
        "pinball_loss": 2.32,
        "bias": -1.19,
        "error_p90": 1.0,
        "n": 16124,
        "mae": 1.94,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 41.0
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
        "mae": 1.96,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 40.8
      },
      "14\u201320m": {
        "pinball_loss": 2.35,
        "bias": -1.22,
        "error_p90": 1.01,
        "n": 48372,
        "mae": 1.97,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 40.2
      },
      "20\u201330m": {
        "pinball_loss": 2.37,
        "bias": -1.24,
        "error_p90": 1.02,
        "n": 80620,
        "mae": 2.0,
        "baseline_pinball_loss": 3.94,
        "improvement_pct": 39.9
      },
      "30\u201345m": {
        "pinball_loss": 2.41,
        "bias": -1.28,
        "error_p90": 1.01,
        "n": 128992,
        "mae": 2.04,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 43.0
      },
      "45\u201360m": {
        "pinball_loss": 2.46,
        "bias": -1.31,
        "error_p90": 1.02,
        "n": 112868,
        "mae": 2.08,
        "baseline_pinball_loss": 4.94,
        "improvement_pct": 50.2
      },
      "60\u201390m": {
        "pinball_loss": 2.49,
        "bias": -1.35,
        "error_p90": 1.02,
        "n": 32248,
        "mae": 2.11,
        "baseline_pinball_loss": 5.02,
        "improvement_pct": 50.4
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.23,
        "bias": -1.27,
        "error_p90": 0.89,
        "n": 176352,
        "mae": 1.91,
        "baseline_pinball_loss": 4.15,
        "improvement_pct": 46.3
      },
      "ed-king (peak)": {
        "pinball_loss": 1.65,
        "bias": -0.88,
        "error_p90": 0.78,
        "n": 95271,
        "mae": 1.4,
        "baseline_pinball_loss": 3.07,
        "improvement_pct": 46.2
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.05,
        "bias": -1.52,
        "error_p90": 1.38,
        "n": 163119,
        "mae": 2.54,
        "baseline_pinball_loss": 5.37,
        "improvement_pct": 43.2
      },
      "sea-bi (peak)": {
        "pinball_loss": 2.39,
        "bias": -1.25,
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
      "mean": 2.41,
      "std": 0.34
    },
    "bias": {
      "mean": -1.27,
      "std": 0.28
    },
    "error_p90": {
      "mean": 1.02,
      "std": 0.23
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
