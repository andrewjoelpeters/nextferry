# Backtest Report: exp38-clip-targets

> Clip extreme delay targets to [-10, 30] min

**Date:** 2026-03-29 19:07:14  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 14s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.17× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.44 min** (PL/MAE = 1.17×) |
| MAE | 2.09 min |
| Bias | -1.40 min |
| p90 (tail risk) | +0.98 min |
| 70% Interval Coverage | 71.2% (target: 70%) |
| Interval Width (mean) | 4.77 min |
| Interval Width (median) | 3.76 min |
| Baseline Pinball Loss | 4.39 min |
| Improvement vs baseline | 44.4% |

## Comparison vs Previous Run

| Metric | Previous | Current | Delta |
|--------|----------|---------|-------|
| Pinball Loss | 2.48 min | 2.44 min | -0.04 (better) |
| MAE | 1.97 min | 2.09 min | +0.12 (worse) |
| p90 | 1.33 min | 0.98 min | -0.35 (better) |
| Coverage | 70.0% | 71.2% | +1.20 (better) |
| Interval Width | 4.81 min | 4.77 min | -0.04 (better) |
| Improvement % | 43.5% | 44.4% | +0.90 (better) |

### Per-Route Comparison

| Route | Prev PL | Curr PL | Prev p90 | Curr p90 | PL Delta |
|-------|---------|---------|----------|----------|----------|
| ed-king | 2.09 | 2.04 | +1.09 | +0.82 | -0.05 (better) |
| sea-bi | 2.9 | 2.85 | +1.65 | +1.18 | -0.05 (better) |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 2.79 | -1.44 | +1.31 |
| 1 | 6448 | 3224 | 2.07 | -1.01 | +1.05 |
| 2 | 9672 | 3224 | 2.9 | -1.90 | +0.86 |
| 3 | 12896 | 3224 | 2.27 | -1.35 | +0.86 |
| 4 | 16120 | 3228 | 2.15 | -1.30 | +0.78 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.44 | ±0.34 |
| Bias | -1.4 | ±0.29 |
| p90 | 0.97 | ±0.19 |

## By Route

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ed-king | 2.04 | -1.20 | +0.82 | 4.25 | 271623 |
| sea-bi | 2.85 | -1.61 | +1.18 | 5.31 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| Fri | 2.17 | -0.99 | +1.08 | 4.67 | 76527 |
| Mon | 2.21 | -1.33 | +0.84 | 4.37 | 81477 |
| Sat | 2.37 | -1.29 | +1.03 | 5.01 | 74514 |
| Sun | 3.39 | -1.97 | +1.32 | 5.51 | 71412 |
| Thu | 2.23 | -1.31 | +0.90 | 4.44 | 75306 |
| Tue | 1.92 | -1.23 | +0.73 | 4.51 | 77385 |
| Wed | 2.83 | -1.71 | +1.01 | 4.97 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 2.62 | -1.36 | +0.98 | 28314 |
| Early (5–7) | 2.68 | -1.88 | +0.75 | 46827 |
| Evening (19–22) | 1.98 | -1.00 | +0.98 | 80355 |
| Midday (10–15) | 1.49 | -0.88 | +0.69 | 63030 |
| PM Peak (15–19) | 1.86 | -0.95 | +0.93 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 2.36 | -1.32 | +0.97 | 16124 |
| 4–6m | 2.36 | -1.32 | +0.97 | 16124 |
| 6–8m | 2.36 | -1.33 | +0.97 | 16124 |
| 8–10m | 2.37 | -1.33 | +0.97 | 16124 |
| 10–14m | 2.37 | -1.34 | +0.97 | 32248 |
| 14–20m | 2.38 | -1.34 | +0.98 | 48372 |
| 20–30m | 2.4 | -1.36 | +0.99 | 80620 |
| 30–45m | 2.44 | -1.41 | +0.98 | 128992 |
| 45–60m | 2.48 | -1.43 | +0.99 | 112868 |
| 60–90m | 2.51 | -1.46 | +0.99 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.26 | -1.36 | +0.87 | 176352 |
| ed-king (peak) | 1.64 | -0.89 | +0.77 | 95271 |
| sea-bi (off-peak) | 3.13 | -1.80 | +1.24 | 163119 |
| sea-bi (peak) | 2.38 | -1.29 | +1.08 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.44,
    "overall_bias": -1.4,
    "overall_error_p90": 0.98,
    "n_test_samples": 532092,
    "overall_mae": 2.09,
    "overall_coverage_70pct": 71.2,
    "overall_mean_interval_width": 4.77,
    "overall_median_interval_width": 3.76,
    "overall_baseline_pinball_loss": 4.39,
    "overall_improvement_pct": 44.4,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.04,
        "bias": -1.2,
        "error_p90": 0.82,
        "n": 271623,
        "mae": 1.76,
        "mean_interval_width": 4.25,
        "median_interval_width": 3.39,
        "baseline_pinball_loss": 3.77,
        "improvement_pct": 45.9
      },
      "sea-bi": {
        "pinball_loss": 2.85,
        "bias": -1.61,
        "error_p90": 1.18,
        "n": 260469,
        "mae": 2.43,
        "mean_interval_width": 5.31,
        "median_interval_width": 4.26,
        "baseline_pinball_loss": 5.03,
        "improvement_pct": 43.4
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 3.39,
        "bias": -1.97,
        "error_p90": 1.32,
        "n": 71412,
        "mae": 2.92,
        "mean_interval_width": 5.51,
        "median_interval_width": 4.29,
        "baseline_pinball_loss": 6.0,
        "improvement_pct": 43.5
      },
      "Mon": {
        "pinball_loss": 2.21,
        "bias": -1.33,
        "error_p90": 0.84,
        "n": 81477,
        "mae": 1.92,
        "mean_interval_width": 4.37,
        "median_interval_width": 3.38,
        "baseline_pinball_loss": 4.21,
        "improvement_pct": 47.5
      },
      "Tue": {
        "pinball_loss": 1.92,
        "bias": -1.23,
        "error_p90": 0.73,
        "n": 77385,
        "mae": 1.69,
        "mean_interval_width": 4.51,
        "median_interval_width": 3.57,
        "baseline_pinball_loss": 3.28,
        "improvement_pct": 41.4
      },
      "Wed": {
        "pinball_loss": 2.83,
        "bias": -1.71,
        "error_p90": 1.01,
        "n": 75471,
        "mae": 2.46,
        "mean_interval_width": 4.97,
        "median_interval_width": 3.96,
        "baseline_pinball_loss": 5.6,
        "improvement_pct": 49.4
      },
      "Thu": {
        "pinball_loss": 2.23,
        "bias": -1.31,
        "error_p90": 0.9,
        "n": 75306,
        "mae": 1.93,
        "mean_interval_width": 4.44,
        "median_interval_width": 3.58,
        "baseline_pinball_loss": 3.48,
        "improvement_pct": 35.9
      },
      "Fri": {
        "pinball_loss": 2.17,
        "bias": -0.99,
        "error_p90": 1.08,
        "n": 76527,
        "mae": 1.78,
        "mean_interval_width": 4.67,
        "median_interval_width": 3.71,
        "baseline_pinball_loss": 4.26,
        "improvement_pct": 49.0
      },
      "Sat": {
        "pinball_loss": 2.37,
        "bias": -1.29,
        "error_p90": 1.03,
        "n": 74514,
        "mae": 2.01,
        "mean_interval_width": 5.01,
        "median_interval_width": 3.95,
        "baseline_pinball_loss": 4.03,
        "improvement_pct": 41.1
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 2.68,
        "bias": -1.88,
        "error_p90": 0.75,
        "n": 46827,
        "mae": 2.42,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 36.6
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 2.62,
        "bias": -1.36,
        "error_p90": 0.98,
        "n": 28314,
        "mae": 2.2,
        "baseline_pinball_loss": 5.63,
        "improvement_pct": 53.5
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.49,
        "bias": -0.88,
        "error_p90": 0.69,
        "n": 63030,
        "mae": 1.29,
        "baseline_pinball_loss": 4.83,
        "improvement_pct": 69.1
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 1.86,
        "bias": -0.95,
        "error_p90": 0.93,
        "n": 112398,
        "mae": 1.56,
        "baseline_pinball_loss": 3.49,
        "improvement_pct": 46.7
      },
      "Evening (19\u201322)": {
        "pinball_loss": 1.98,
        "bias": -1.0,
        "error_p90": 0.98,
        "n": 80355,
        "mae": 1.65,
        "baseline_pinball_loss": 2.94,
        "improvement_pct": 32.7
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 2.36,
        "bias": -1.32,
        "error_p90": 0.97,
        "n": 16124,
        "mae": 2.01,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 39.9
      },
      "4\u20136m": {
        "pinball_loss": 2.36,
        "bias": -1.32,
        "error_p90": 0.97,
        "n": 16124,
        "mae": 2.01,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 40.0
      },
      "6\u20138m": {
        "pinball_loss": 2.36,
        "bias": -1.33,
        "error_p90": 0.97,
        "n": 16124,
        "mae": 2.02,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 39.9
      },
      "8\u201310m": {
        "pinball_loss": 2.37,
        "bias": -1.33,
        "error_p90": 0.97,
        "n": 16124,
        "mae": 2.02,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 39.7
      },
      "10\u201314m": {
        "pinball_loss": 2.37,
        "bias": -1.34,
        "error_p90": 0.97,
        "n": 32248,
        "mae": 2.02,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 39.7
      },
      "14\u201320m": {
        "pinball_loss": 2.38,
        "bias": -1.34,
        "error_p90": 0.98,
        "n": 48372,
        "mae": 2.03,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 39.4
      },
      "20\u201330m": {
        "pinball_loss": 2.4,
        "bias": -1.36,
        "error_p90": 0.99,
        "n": 80620,
        "mae": 2.06,
        "baseline_pinball_loss": 3.94,
        "improvement_pct": 39.1
      },
      "30\u201345m": {
        "pinball_loss": 2.44,
        "bias": -1.41,
        "error_p90": 0.98,
        "n": 128992,
        "mae": 2.1,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 42.3
      },
      "45\u201360m": {
        "pinball_loss": 2.48,
        "bias": -1.43,
        "error_p90": 0.99,
        "n": 112868,
        "mae": 2.13,
        "baseline_pinball_loss": 4.94,
        "improvement_pct": 49.8
      },
      "60\u201390m": {
        "pinball_loss": 2.51,
        "bias": -1.46,
        "error_p90": 0.99,
        "n": 32248,
        "mae": 2.16,
        "baseline_pinball_loss": 5.02,
        "improvement_pct": 50.0
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.26,
        "bias": -1.36,
        "error_p90": 0.87,
        "n": 176352,
        "mae": 1.96,
        "baseline_pinball_loss": 4.15,
        "improvement_pct": 45.5
      },
      "ed-king (peak)": {
        "pinball_loss": 1.64,
        "bias": -0.89,
        "error_p90": 0.77,
        "n": 95271,
        "mae": 1.39,
        "baseline_pinball_loss": 3.07,
        "improvement_pct": 46.5
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.13,
        "bias": -1.8,
        "error_p90": 1.24,
        "n": 163119,
        "mae": 2.69,
        "baseline_pinball_loss": 5.37,
        "improvement_pct": 41.7
      },
      "sea-bi (peak)": {
        "pinball_loss": 2.38,
        "bias": -1.29,
        "error_p90": 1.08,
        "n": 97350,
        "mae": 2.01,
        "baseline_pinball_loss": 4.48,
        "improvement_pct": 46.8
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 2.44,
      "std": 0.34
    },
    "bias": {
      "mean": -1.4,
      "std": 0.29
    },
    "error_p90": {
      "mean": 0.97,
      "std": 0.19
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
