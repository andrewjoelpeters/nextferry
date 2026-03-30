# Backtest Report: exp32-consecutive-late

> Add consecutive_late_sailings feature

**Date:** 2026-03-29 12:19:44  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 13s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.26× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.48 min** (PL/MAE = 1.26×) |
| MAE | 1.97 min |
| Bias | -0.94 min |
| p90 (tail risk) | +1.33 min |
| 70% Interval Coverage | 70.0% (target: 70%) |
| Interval Width (mean) | 4.74 min |
| Interval Width (median) | 3.44 min |
| Baseline Pinball Loss | 4.39 min |
| Improvement vs baseline | 43.5% |

## Comparison vs Previous Run

| Metric | Previous | Current | Delta |
|--------|----------|---------|-------|
| Pinball Loss | 2.48 min | 2.48 min | 0.00 (no change) |
| MAE | 1.97 min | 1.97 min | 0.00 (no change) |
| p90 | 1.33 min | 1.33 min | 0.00 (no change) |
| Coverage | 70.0% | 70.0% | 0.00 (no change) |
| Interval Width | 4.81 min | 4.74 min | -0.07 (better) |
| Improvement % | 43.5% | 43.5% | 0.00 (no change) |

### Per-Route Comparison

| Route | Prev PL | Curr PL | Prev p90 | Curr p90 | PL Delta |
|-------|---------|---------|----------|----------|----------|
| ed-king | 2.09 | 2.09 | +1.09 | +1.08 | 0.00 (no change) |
| sea-bi | 2.9 | 2.89 | +1.65 | +1.64 | -0.01 (better) |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 2.9 | -0.80 | +1.90 |
| 1 | 6448 | 3224 | 2.18 | -0.65 | +1.38 |
| 2 | 9672 | 3224 | 2.88 | -1.49 | +1.16 |
| 3 | 12896 | 3224 | 2.27 | -0.92 | +1.14 |
| 4 | 16120 | 3228 | 2.18 | -0.82 | +1.11 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.48 | ±0.33 |
| Bias | -0.94 | ±0.29 |
| p90 | 1.34 | ±0.3 |

## By Route

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ed-king | 2.09 | -0.85 | +1.08 | 4.09 | 271623 |
| sea-bi | 2.89 | -1.03 | +1.64 | 5.41 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| Fri | 2.26 | -0.66 | +1.35 | 4.25 | 76527 |
| Mon | 2.25 | -0.70 | +1.28 | 4.67 | 81477 |
| Sat | 2.37 | -0.77 | +1.43 | 4.94 | 74514 |
| Sun | 3.41 | -1.16 | +1.98 | 6.19 | 71412 |
| Thu | 2.25 | -0.99 | +1.11 | 4.24 | 75306 |
| Tue | 1.95 | -0.95 | +0.97 | 4.26 | 77385 |
| Wed | 2.96 | -1.35 | +1.36 | 4.72 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 2.7 | -0.92 | +1.42 | 28314 |
| Early (5–7) | 2.75 | -1.28 | +1.10 | 46827 |
| Evening (19–22) | 2.04 | -0.66 | +1.28 | 80355 |
| Midday (10–15) | 1.51 | -0.68 | +0.88 | 63030 |
| PM Peak (15–19) | 1.96 | -0.69 | +1.20 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 2.4 | -0.86 | +1.32 | 16124 |
| 4–6m | 2.39 | -0.86 | +1.31 | 16124 |
| 6–8m | 2.39 | -0.87 | +1.31 | 16124 |
| 8–10m | 2.4 | -0.87 | +1.31 | 16124 |
| 10–14m | 2.41 | -0.88 | +1.32 | 32248 |
| 14–20m | 2.42 | -0.89 | +1.33 | 48372 |
| 20–30m | 2.45 | -0.90 | +1.34 | 80620 |
| 30–45m | 2.49 | -0.94 | +1.32 | 128992 |
| 45–60m | 2.53 | -0.97 | +1.34 | 112868 |
| 60–90m | 2.56 | -1.00 | +1.33 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.29 | -0.95 | +1.16 | 176352 |
| ed-king (peak) | 1.73 | -0.65 | +0.98 | 95271 |
| sea-bi (off-peak) | 3.14 | -1.09 | +1.82 | 163119 |
| sea-bi (peak) | 2.47 | -0.91 | +1.42 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.48,
    "overall_bias": -0.94,
    "overall_error_p90": 1.33,
    "n_test_samples": 532092,
    "overall_mae": 1.97,
    "overall_coverage_70pct": 70.0,
    "overall_mean_interval_width": 4.74,
    "overall_median_interval_width": 3.44,
    "overall_baseline_pinball_loss": 4.39,
    "overall_improvement_pct": 43.5,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.09,
        "bias": -0.85,
        "error_p90": 1.08,
        "n": 271623,
        "mae": 1.68,
        "mean_interval_width": 4.09,
        "median_interval_width": 3.09,
        "baseline_pinball_loss": 3.77,
        "improvement_pct": 44.6
      },
      "sea-bi": {
        "pinball_loss": 2.89,
        "bias": -1.03,
        "error_p90": 1.64,
        "n": 260469,
        "mae": 2.27,
        "mean_interval_width": 5.41,
        "median_interval_width": 3.89,
        "baseline_pinball_loss": 5.03,
        "improvement_pct": 42.6
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 3.41,
        "bias": -1.16,
        "error_p90": 1.98,
        "n": 71412,
        "mae": 2.66,
        "mean_interval_width": 6.19,
        "median_interval_width": 4.0,
        "baseline_pinball_loss": 6.0,
        "improvement_pct": 43.2
      },
      "Mon": {
        "pinball_loss": 2.25,
        "bias": -0.7,
        "error_p90": 1.28,
        "n": 81477,
        "mae": 1.73,
        "mean_interval_width": 4.67,
        "median_interval_width": 3.04,
        "baseline_pinball_loss": 4.21,
        "improvement_pct": 46.6
      },
      "Tue": {
        "pinball_loss": 1.95,
        "bias": -0.95,
        "error_p90": 0.97,
        "n": 77385,
        "mae": 1.62,
        "mean_interval_width": 4.26,
        "median_interval_width": 3.24,
        "baseline_pinball_loss": 3.28,
        "improvement_pct": 40.5
      },
      "Wed": {
        "pinball_loss": 2.96,
        "bias": -1.35,
        "error_p90": 1.36,
        "n": 75471,
        "mae": 2.42,
        "mean_interval_width": 4.72,
        "median_interval_width": 3.62,
        "baseline_pinball_loss": 5.6,
        "improvement_pct": 47.1
      },
      "Thu": {
        "pinball_loss": 2.25,
        "bias": -0.99,
        "error_p90": 1.11,
        "n": 75306,
        "mae": 1.83,
        "mean_interval_width": 4.24,
        "median_interval_width": 3.18,
        "baseline_pinball_loss": 3.48,
        "improvement_pct": 35.4
      },
      "Fri": {
        "pinball_loss": 2.26,
        "bias": -0.66,
        "error_p90": 1.35,
        "n": 76527,
        "mae": 1.73,
        "mean_interval_width": 4.25,
        "median_interval_width": 3.3,
        "baseline_pinball_loss": 4.26,
        "improvement_pct": 46.9
      },
      "Sat": {
        "pinball_loss": 2.37,
        "bias": -0.77,
        "error_p90": 1.43,
        "n": 74514,
        "mae": 1.84,
        "mean_interval_width": 4.94,
        "median_interval_width": 3.79,
        "baseline_pinball_loss": 4.03,
        "improvement_pct": 41.1
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 2.75,
        "bias": -1.28,
        "error_p90": 1.1,
        "n": 46827,
        "mae": 2.26,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 34.9
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 2.7,
        "bias": -0.92,
        "error_p90": 1.42,
        "n": 28314,
        "mae": 2.1,
        "baseline_pinball_loss": 5.63,
        "improvement_pct": 52.0
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.51,
        "bias": -0.68,
        "error_p90": 0.88,
        "n": 63030,
        "mae": 1.23,
        "baseline_pinball_loss": 4.83,
        "improvement_pct": 68.7
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 1.96,
        "bias": -0.69,
        "error_p90": 1.2,
        "n": 112398,
        "mae": 1.54,
        "baseline_pinball_loss": 3.49,
        "improvement_pct": 43.9
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.04,
        "bias": -0.66,
        "error_p90": 1.28,
        "n": 80355,
        "mae": 1.58,
        "baseline_pinball_loss": 2.94,
        "improvement_pct": 30.6
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 2.4,
        "bias": -0.86,
        "error_p90": 1.32,
        "n": 16124,
        "mae": 1.88,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.9
      },
      "4\u20136m": {
        "pinball_loss": 2.39,
        "bias": -0.86,
        "error_p90": 1.31,
        "n": 16124,
        "mae": 1.88,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 39.2
      },
      "6\u20138m": {
        "pinball_loss": 2.39,
        "bias": -0.87,
        "error_p90": 1.31,
        "n": 16124,
        "mae": 1.89,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 39.2
      },
      "8\u201310m": {
        "pinball_loss": 2.4,
        "bias": -0.87,
        "error_p90": 1.31,
        "n": 16124,
        "mae": 1.89,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.9
      },
      "10\u201314m": {
        "pinball_loss": 2.41,
        "bias": -0.88,
        "error_p90": 1.32,
        "n": 32248,
        "mae": 1.9,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.7
      },
      "14\u201320m": {
        "pinball_loss": 2.42,
        "bias": -0.89,
        "error_p90": 1.33,
        "n": 48372,
        "mae": 1.91,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.4
      },
      "20\u201330m": {
        "pinball_loss": 2.45,
        "bias": -0.9,
        "error_p90": 1.34,
        "n": 80620,
        "mae": 1.93,
        "baseline_pinball_loss": 3.94,
        "improvement_pct": 37.9
      },
      "30\u201345m": {
        "pinball_loss": 2.49,
        "bias": -0.94,
        "error_p90": 1.32,
        "n": 128992,
        "mae": 1.97,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 41.1
      },
      "45\u201360m": {
        "pinball_loss": 2.53,
        "bias": -0.97,
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
        "pinball_loss": 2.29,
        "bias": -0.95,
        "error_p90": 1.16,
        "n": 176352,
        "mae": 1.84,
        "baseline_pinball_loss": 4.15,
        "improvement_pct": 44.8
      },
      "ed-king (peak)": {
        "pinball_loss": 1.73,
        "bias": -0.65,
        "error_p90": 0.98,
        "n": 95271,
        "mae": 1.37,
        "baseline_pinball_loss": 3.07,
        "improvement_pct": 43.6
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.14,
        "bias": -1.09,
        "error_p90": 1.82,
        "n": 163119,
        "mae": 2.46,
        "baseline_pinball_loss": 5.37,
        "improvement_pct": 41.5
      },
      "sea-bi (peak)": {
        "pinball_loss": 2.47,
        "bias": -0.91,
        "error_p90": 1.42,
        "n": 97350,
        "mae": 1.95,
        "baseline_pinball_loss": 4.48,
        "improvement_pct": 44.8
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 2.48,
      "std": 0.33
    },
    "bias": {
      "mean": -0.94,
      "std": 0.29
    },
    "error_p90": {
      "mean": 1.34,
      "std": 0.3
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
