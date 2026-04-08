# Backtest Report: exp39-higher-lr

> lr=0.08, iter=800 with q25

**Date:** 2026-03-29 20:10:40  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 3m 2s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.2× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.42 min** (PL/MAE = 1.2×) |
| MAE | 2.02 min |
| Bias | -1.21 min |
| p90 (tail risk) | +1.10 min |
| 70% Interval Coverage | 66.8% (target: 70%) |
| Interval Width (mean) | 4.54 min |
| Interval Width (median) | 3.23 min |
| Baseline Pinball Loss | 4.39 min |
| Improvement vs baseline | 44.9% |

## Comparison vs Previous Run

| Metric | Previous | Current | Delta |
|--------|----------|---------|-------|
| Pinball Loss | 2.48 min | 2.42 min | -0.06 (better) |
| MAE | 1.97 min | 2.02 min | +0.05 (worse) |
| p90 | 1.33 min | 1.1 min | -0.23 (better) |
| Coverage | 70.0% | 66.8% | -3.20 (worse) |
| Interval Width | 4.81 min | 4.54 min | -0.27 (better) |
| Improvement % | 43.5% | 44.9% | +1.40 (better) |

### Per-Route Comparison

| Route | Prev PL | Curr PL | Prev p90 | Curr p90 | PL Delta |
|-------|---------|---------|----------|----------|----------|
| ed-king | 2.09 | 2.03 | +1.09 | +0.91 | -0.06 (better) |
| sea-bi | 2.9 | 2.83 | +1.65 | +1.33 | -0.07 (better) |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 2.75 | -1.14 | +1.51 |
| 1 | 6448 | 3224 | 2.13 | -0.87 | +1.21 |
| 2 | 9672 | 3224 | 2.89 | -1.76 | +0.98 |
| 3 | 12896 | 3224 | 2.25 | -1.19 | +0.95 |
| 4 | 16120 | 3228 | 2.11 | -1.11 | +0.90 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.43 | ±0.33 |
| Bias | -1.21 | ±0.29 |
| p90 | 1.11 | ±0.23 |

## By Route

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ed-king | 2.03 | -1.07 | +0.91 | 3.87 | 271623 |
| sea-bi | 2.83 | -1.36 | +1.33 | 5.24 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| Fri | 2.16 | -0.87 | +1.13 | 4.08 | 76527 |
| Mon | 2.15 | -1.00 | +1.01 | 4.46 | 81477 |
| Sat | 2.32 | -1.05 | +1.22 | 4.76 | 74514 |
| Sun | 3.35 | -1.58 | +1.57 | 6.04 | 71412 |
| Thu | 2.26 | -1.22 | +1.00 | 3.98 | 75306 |
| Tue | 1.94 | -1.16 | +0.79 | 4.0 | 77385 |
| Wed | 2.87 | -1.63 | +1.09 | 4.55 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 2.69 | -1.27 | +1.05 | 28314 |
| Early (5–7) | 2.69 | -1.64 | +0.87 | 46827 |
| Evening (19–22) | 1.99 | -0.94 | +1.05 | 80355 |
| Midday (10–15) | 1.53 | -0.78 | +0.80 | 63030 |
| PM Peak (15–19) | 1.9 | -0.90 | +1.01 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 2.34 | -1.13 | +1.09 | 16124 |
| 4–6m | 2.34 | -1.13 | +1.09 | 16124 |
| 6–8m | 2.34 | -1.14 | +1.09 | 16124 |
| 8–10m | 2.35 | -1.14 | +1.09 | 16124 |
| 10–14m | 2.35 | -1.15 | +1.09 | 32248 |
| 14–20m | 2.37 | -1.16 | +1.10 | 48372 |
| 20–30m | 2.39 | -1.18 | +1.11 | 80620 |
| 30–45m | 2.43 | -1.22 | +1.10 | 128992 |
| 45–60m | 2.47 | -1.25 | +1.11 | 112868 |
| 60–90m | 2.5 | -1.28 | +1.10 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.24 | -1.19 | +0.98 | 176352 |
| ed-king (peak) | 1.66 | -0.84 | +0.82 | 95271 |
| sea-bi (off-peak) | 3.07 | -1.45 | +1.47 | 163119 |
| sea-bi (peak) | 2.44 | -1.21 | +1.18 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.42,
    "overall_bias": -1.21,
    "overall_error_p90": 1.1,
    "n_test_samples": 532092,
    "overall_mae": 2.02,
    "overall_coverage_70pct": 66.8,
    "overall_mean_interval_width": 4.54,
    "overall_median_interval_width": 3.23,
    "overall_baseline_pinball_loss": 4.39,
    "overall_improvement_pct": 44.9,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.03,
        "bias": -1.07,
        "error_p90": 0.91,
        "n": 271623,
        "mae": 1.71,
        "mean_interval_width": 3.87,
        "median_interval_width": 2.93,
        "baseline_pinball_loss": 3.77,
        "improvement_pct": 46.2
      },
      "sea-bi": {
        "pinball_loss": 2.83,
        "bias": -1.36,
        "error_p90": 1.33,
        "n": 260469,
        "mae": 2.34,
        "mean_interval_width": 5.24,
        "median_interval_width": 3.67,
        "baseline_pinball_loss": 5.03,
        "improvement_pct": 43.8
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 3.35,
        "bias": -1.58,
        "error_p90": 1.57,
        "n": 71412,
        "mae": 2.76,
        "mean_interval_width": 6.04,
        "median_interval_width": 3.86,
        "baseline_pinball_loss": 6.0,
        "improvement_pct": 44.2
      },
      "Mon": {
        "pinball_loss": 2.15,
        "bias": -1.0,
        "error_p90": 1.01,
        "n": 81477,
        "mae": 1.77,
        "mean_interval_width": 4.46,
        "median_interval_width": 2.82,
        "baseline_pinball_loss": 4.21,
        "improvement_pct": 48.9
      },
      "Tue": {
        "pinball_loss": 1.94,
        "bias": -1.16,
        "error_p90": 0.79,
        "n": 77385,
        "mae": 1.68,
        "mean_interval_width": 4.0,
        "median_interval_width": 3.05,
        "baseline_pinball_loss": 3.28,
        "improvement_pct": 40.8
      },
      "Wed": {
        "pinball_loss": 2.87,
        "bias": -1.63,
        "error_p90": 1.09,
        "n": 75471,
        "mae": 2.46,
        "mean_interval_width": 4.55,
        "median_interval_width": 3.39,
        "baseline_pinball_loss": 5.6,
        "improvement_pct": 48.7
      },
      "Thu": {
        "pinball_loss": 2.26,
        "bias": -1.22,
        "error_p90": 1.0,
        "n": 75306,
        "mae": 1.92,
        "mean_interval_width": 3.98,
        "median_interval_width": 2.94,
        "baseline_pinball_loss": 3.48,
        "improvement_pct": 35.1
      },
      "Fri": {
        "pinball_loss": 2.16,
        "bias": -0.87,
        "error_p90": 1.13,
        "n": 76527,
        "mae": 1.73,
        "mean_interval_width": 4.08,
        "median_interval_width": 3.16,
        "baseline_pinball_loss": 4.26,
        "improvement_pct": 49.3
      },
      "Sat": {
        "pinball_loss": 2.32,
        "bias": -1.05,
        "error_p90": 1.22,
        "n": 74514,
        "mae": 1.9,
        "mean_interval_width": 4.76,
        "median_interval_width": 3.69,
        "baseline_pinball_loss": 4.03,
        "improvement_pct": 42.4
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 2.69,
        "bias": -1.64,
        "error_p90": 0.87,
        "n": 46827,
        "mae": 2.34,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 36.3
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 2.69,
        "bias": -1.27,
        "error_p90": 1.05,
        "n": 28314,
        "mae": 2.22,
        "baseline_pinball_loss": 5.63,
        "improvement_pct": 52.2
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.53,
        "bias": -0.78,
        "error_p90": 0.8,
        "n": 63030,
        "mae": 1.28,
        "baseline_pinball_loss": 4.83,
        "improvement_pct": 68.3
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 1.9,
        "bias": -0.9,
        "error_p90": 1.01,
        "n": 112398,
        "mae": 1.56,
        "baseline_pinball_loss": 3.49,
        "improvement_pct": 45.6
      },
      "Evening (19\u201322)": {
        "pinball_loss": 1.99,
        "bias": -0.94,
        "error_p90": 1.05,
        "n": 80355,
        "mae": 1.64,
        "baseline_pinball_loss": 2.94,
        "improvement_pct": 32.3
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 2.34,
        "bias": -1.13,
        "error_p90": 1.09,
        "n": 16124,
        "mae": 1.94,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 40.4
      },
      "4\u20136m": {
        "pinball_loss": 2.34,
        "bias": -1.13,
        "error_p90": 1.09,
        "n": 16124,
        "mae": 1.94,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 40.5
      },
      "6\u20138m": {
        "pinball_loss": 2.34,
        "bias": -1.14,
        "error_p90": 1.09,
        "n": 16124,
        "mae": 1.94,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 40.5
      },
      "8\u201310m": {
        "pinball_loss": 2.35,
        "bias": -1.14,
        "error_p90": 1.09,
        "n": 16124,
        "mae": 1.94,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 40.2
      },
      "10\u201314m": {
        "pinball_loss": 2.35,
        "bias": -1.15,
        "error_p90": 1.09,
        "n": 32248,
        "mae": 1.95,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 40.2
      },
      "14\u201320m": {
        "pinball_loss": 2.37,
        "bias": -1.16,
        "error_p90": 1.1,
        "n": 48372,
        "mae": 1.96,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 39.6
      },
      "20\u201330m": {
        "pinball_loss": 2.39,
        "bias": -1.18,
        "error_p90": 1.11,
        "n": 80620,
        "mae": 1.99,
        "baseline_pinball_loss": 3.94,
        "improvement_pct": 39.4
      },
      "30\u201345m": {
        "pinball_loss": 2.43,
        "bias": -1.22,
        "error_p90": 1.1,
        "n": 128992,
        "mae": 2.03,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 42.6
      },
      "45\u201360m": {
        "pinball_loss": 2.47,
        "bias": -1.25,
        "error_p90": 1.11,
        "n": 112868,
        "mae": 2.06,
        "baseline_pinball_loss": 4.94,
        "improvement_pct": 50.0
      },
      "60\u201390m": {
        "pinball_loss": 2.5,
        "bias": -1.28,
        "error_p90": 1.1,
        "n": 32248,
        "mae": 2.09,
        "baseline_pinball_loss": 5.02,
        "improvement_pct": 50.2
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.24,
        "bias": -1.19,
        "error_p90": 0.98,
        "n": 176352,
        "mae": 1.89,
        "baseline_pinball_loss": 4.15,
        "improvement_pct": 46.0
      },
      "ed-king (peak)": {
        "pinball_loss": 1.66,
        "bias": -0.84,
        "error_p90": 0.82,
        "n": 95271,
        "mae": 1.39,
        "baseline_pinball_loss": 3.07,
        "improvement_pct": 45.9
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.07,
        "bias": -1.45,
        "error_p90": 1.47,
        "n": 163119,
        "mae": 2.53,
        "baseline_pinball_loss": 5.37,
        "improvement_pct": 42.8
      },
      "sea-bi (peak)": {
        "pinball_loss": 2.44,
        "bias": -1.21,
        "error_p90": 1.18,
        "n": 97350,
        "mae": 2.03,
        "baseline_pinball_loss": 4.48,
        "improvement_pct": 45.5
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 2.43,
      "std": 0.33
    },
    "bias": {
      "mean": -1.21,
      "std": 0.29
    },
    "error_p90": {
      "mean": 1.11,
      "std": 0.23
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
