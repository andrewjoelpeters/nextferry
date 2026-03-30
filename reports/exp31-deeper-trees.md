# Backtest Report: exp31-deeper-trees

> max_depth=10 (was 8)

**Date:** 2026-03-29 12:16:25  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 19s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.26× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.48 min** (PL/MAE = 1.26×) |
| MAE | 1.97 min |
| Bias | -0.94 min |
| p90 (tail risk) | +1.34 min |
| 70% Interval Coverage | 69.8% (target: 70%) |
| Interval Width (mean) | 4.77 min |
| Interval Width (median) | 3.47 min |
| Baseline Pinball Loss | 4.39 min |
| Improvement vs baseline | 43.5% |

## Comparison vs Previous Run

| Metric | Previous | Current | Delta |
|--------|----------|---------|-------|
| Pinball Loss | 2.48 min | 2.48 min | 0.00 (no change) |
| MAE | 1.97 min | 1.97 min | 0.00 (no change) |
| p90 | 1.33 min | 1.34 min | +0.01 (worse) |
| Coverage | 70.0% | 69.8% | -0.20 (worse) |
| Interval Width | 4.81 min | 4.77 min | -0.04 (better) |
| Improvement % | 43.5% | 43.5% | 0.00 (no change) |

### Per-Route Comparison

| Route | Prev PL | Curr PL | Prev p90 | Curr p90 | PL Delta |
|-------|---------|---------|----------|----------|----------|
| ed-king | 2.09 | 2.1 | +1.09 | +1.10 | +0.01 (worse) |
| sea-bi | 2.9 | 2.89 | +1.65 | +1.64 | -0.01 (better) |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 2.85 | -0.86 | +1.83 |
| 1 | 6448 | 3224 | 2.2 | -0.62 | +1.42 |
| 2 | 9672 | 3224 | 2.87 | -1.49 | +1.13 |
| 3 | 12896 | 3224 | 2.29 | -0.91 | +1.19 |
| 4 | 16120 | 3228 | 2.2 | -0.81 | +1.12 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.48 | ±0.31 |
| Bias | -0.94 | ±0.29 |
| p90 | 1.34 | ±0.27 |

## By Route

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ed-king | 2.1 | -0.84 | +1.10 | 4.08 | 271623 |
| sea-bi | 2.89 | -1.03 | +1.64 | 5.49 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| Fri | 2.27 | -0.66 | +1.38 | 4.29 | 76527 |
| Mon | 2.26 | -0.69 | +1.27 | 4.79 | 81477 |
| Sat | 2.37 | -0.73 | +1.50 | 4.98 | 74514 |
| Sun | 3.39 | -1.19 | +1.87 | 6.37 | 71412 |
| Thu | 2.29 | -1.00 | +1.15 | 4.21 | 75306 |
| Tue | 1.95 | -0.94 | +0.97 | 4.15 | 77385 |
| Wed | 2.94 | -1.37 | +1.36 | 4.73 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 2.74 | -0.94 | +1.33 | 28314 |
| Early (5–7) | 2.73 | -1.32 | +1.09 | 46827 |
| Evening (19–22) | 2.05 | -0.66 | +1.28 | 80355 |
| Midday (10–15) | 1.5 | -0.65 | +0.90 | 63030 |
| PM Peak (15–19) | 1.97 | -0.67 | +1.24 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 2.4 | -0.85 | +1.35 | 16124 |
| 4–6m | 2.4 | -0.86 | +1.34 | 16124 |
| 6–8m | 2.4 | -0.86 | +1.34 | 16124 |
| 8–10m | 2.4 | -0.87 | +1.34 | 16124 |
| 10–14m | 2.41 | -0.88 | +1.33 | 32248 |
| 14–20m | 2.42 | -0.89 | +1.34 | 48372 |
| 20–30m | 2.45 | -0.90 | +1.35 | 80620 |
| 30–45m | 2.49 | -0.94 | +1.34 | 128992 |
| 45–60m | 2.53 | -0.97 | +1.35 | 112868 |
| 60–90m | 2.56 | -1.00 | +1.33 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.29 | -0.96 | +1.16 | 176352 |
| ed-king (peak) | 1.75 | -0.63 | +1.02 | 95271 |
| sea-bi (off-peak) | 3.13 | -1.10 | +1.82 | 163119 |
| sea-bi (peak) | 2.47 | -0.92 | +1.41 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.48,
    "overall_bias": -0.94,
    "overall_error_p90": 1.34,
    "n_test_samples": 532092,
    "overall_mae": 1.97,
    "overall_coverage_70pct": 69.8,
    "overall_mean_interval_width": 4.77,
    "overall_median_interval_width": 3.47,
    "overall_baseline_pinball_loss": 4.39,
    "overall_improvement_pct": 43.5,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.1,
        "bias": -0.84,
        "error_p90": 1.1,
        "n": 271623,
        "mae": 1.68,
        "mean_interval_width": 4.08,
        "median_interval_width": 3.09,
        "baseline_pinball_loss": 3.77,
        "improvement_pct": 44.3
      },
      "sea-bi": {
        "pinball_loss": 2.89,
        "bias": -1.03,
        "error_p90": 1.64,
        "n": 260469,
        "mae": 2.27,
        "mean_interval_width": 5.49,
        "median_interval_width": 3.96,
        "baseline_pinball_loss": 5.03,
        "improvement_pct": 42.6
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 3.39,
        "bias": -1.19,
        "error_p90": 1.87,
        "n": 71412,
        "mae": 2.65,
        "mean_interval_width": 6.37,
        "median_interval_width": 4.18,
        "baseline_pinball_loss": 6.0,
        "improvement_pct": 43.5
      },
      "Mon": {
        "pinball_loss": 2.26,
        "bias": -0.69,
        "error_p90": 1.27,
        "n": 81477,
        "mae": 1.74,
        "mean_interval_width": 4.79,
        "median_interval_width": 3.13,
        "baseline_pinball_loss": 4.21,
        "improvement_pct": 46.3
      },
      "Tue": {
        "pinball_loss": 1.95,
        "bias": -0.94,
        "error_p90": 0.97,
        "n": 77385,
        "mae": 1.61,
        "mean_interval_width": 4.15,
        "median_interval_width": 3.24,
        "baseline_pinball_loss": 3.28,
        "improvement_pct": 40.5
      },
      "Wed": {
        "pinball_loss": 2.94,
        "bias": -1.37,
        "error_p90": 1.36,
        "n": 75471,
        "mae": 2.42,
        "mean_interval_width": 4.73,
        "median_interval_width": 3.62,
        "baseline_pinball_loss": 5.6,
        "improvement_pct": 47.5
      },
      "Thu": {
        "pinball_loss": 2.29,
        "bias": -1.0,
        "error_p90": 1.15,
        "n": 75306,
        "mae": 1.86,
        "mean_interval_width": 4.21,
        "median_interval_width": 3.18,
        "baseline_pinball_loss": 3.48,
        "improvement_pct": 34.2
      },
      "Fri": {
        "pinball_loss": 2.27,
        "bias": -0.66,
        "error_p90": 1.38,
        "n": 76527,
        "mae": 1.73,
        "mean_interval_width": 4.29,
        "median_interval_width": 3.31,
        "baseline_pinball_loss": 4.26,
        "improvement_pct": 46.7
      },
      "Sat": {
        "pinball_loss": 2.37,
        "bias": -0.73,
        "error_p90": 1.5,
        "n": 74514,
        "mae": 1.82,
        "mean_interval_width": 4.98,
        "median_interval_width": 3.81,
        "baseline_pinball_loss": 4.03,
        "improvement_pct": 41.1
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 2.73,
        "bias": -1.32,
        "error_p90": 1.09,
        "n": 46827,
        "mae": 2.26,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 35.4
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 2.74,
        "bias": -0.94,
        "error_p90": 1.33,
        "n": 28314,
        "mae": 2.14,
        "baseline_pinball_loss": 5.63,
        "improvement_pct": 51.3
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.5,
        "bias": -0.65,
        "error_p90": 0.9,
        "n": 63030,
        "mae": 1.22,
        "baseline_pinball_loss": 4.83,
        "improvement_pct": 68.9
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 1.97,
        "bias": -0.67,
        "error_p90": 1.24,
        "n": 112398,
        "mae": 1.53,
        "baseline_pinball_loss": 3.49,
        "improvement_pct": 43.6
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.05,
        "bias": -0.66,
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
        "error_p90": 1.35,
        "n": 16124,
        "mae": 1.88,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.9
      },
      "4\u20136m": {
        "pinball_loss": 2.4,
        "bias": -0.86,
        "error_p90": 1.34,
        "n": 16124,
        "mae": 1.88,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.9
      },
      "6\u20138m": {
        "pinball_loss": 2.4,
        "bias": -0.86,
        "error_p90": 1.34,
        "n": 16124,
        "mae": 1.89,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.9
      },
      "8\u201310m": {
        "pinball_loss": 2.4,
        "bias": -0.87,
        "error_p90": 1.34,
        "n": 16124,
        "mae": 1.89,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.9
      },
      "10\u201314m": {
        "pinball_loss": 2.41,
        "bias": -0.88,
        "error_p90": 1.33,
        "n": 32248,
        "mae": 1.9,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.7
      },
      "14\u201320m": {
        "pinball_loss": 2.42,
        "bias": -0.89,
        "error_p90": 1.34,
        "n": 48372,
        "mae": 1.91,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.4
      },
      "20\u201330m": {
        "pinball_loss": 2.45,
        "bias": -0.9,
        "error_p90": 1.35,
        "n": 80620,
        "mae": 1.94,
        "baseline_pinball_loss": 3.94,
        "improvement_pct": 37.9
      },
      "30\u201345m": {
        "pinball_loss": 2.49,
        "bias": -0.94,
        "error_p90": 1.34,
        "n": 128992,
        "mae": 1.97,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 41.1
      },
      "45\u201360m": {
        "pinball_loss": 2.53,
        "bias": -0.97,
        "error_p90": 1.35,
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
        "bias": -0.96,
        "error_p90": 1.16,
        "n": 176352,
        "mae": 1.84,
        "baseline_pinball_loss": 4.15,
        "improvement_pct": 44.8
      },
      "ed-king (peak)": {
        "pinball_loss": 1.75,
        "bias": -0.63,
        "error_p90": 1.02,
        "n": 95271,
        "mae": 1.37,
        "baseline_pinball_loss": 3.07,
        "improvement_pct": 42.9
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.13,
        "bias": -1.1,
        "error_p90": 1.82,
        "n": 163119,
        "mae": 2.46,
        "baseline_pinball_loss": 5.37,
        "improvement_pct": 41.7
      },
      "sea-bi (peak)": {
        "pinball_loss": 2.47,
        "bias": -0.92,
        "error_p90": 1.41,
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
      "std": 0.31
    },
    "bias": {
      "mean": -0.94,
      "std": 0.29
    },
    "error_p90": {
      "mean": 1.34,
      "std": 0.27
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
