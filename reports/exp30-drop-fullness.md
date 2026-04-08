# Backtest Report: exp30-drop-fullness

> Ablation: drop previous_sailing_fullness

**Date:** 2026-03-29 12:13:26  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 16s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.26× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.49 min** (PL/MAE = 1.26×) |
| MAE | 1.97 min |
| Bias | -0.92 min |
| p90 (tail risk) | +1.35 min |
| 70% Interval Coverage | 70.0% (target: 70%) |
| Interval Width (mean) | 4.79 min |
| Interval Width (median) | 3.42 min |
| Baseline Pinball Loss | 4.39 min |
| Improvement vs baseline | 43.3% |

## Comparison vs Previous Run

| Metric | Previous | Current | Delta |
|--------|----------|---------|-------|
| Pinball Loss | 2.48 min | 2.49 min | +0.01 (worse) |
| MAE | 1.97 min | 1.97 min | 0.00 (no change) |
| p90 | 1.33 min | 1.35 min | +0.02 (worse) |
| Coverage | 70.0% | 70.0% | 0.00 (no change) |
| Interval Width | 4.81 min | 4.79 min | -0.02 (better) |
| Improvement % | 43.5% | 43.3% | -0.20 (worse) |

### Per-Route Comparison

| Route | Prev PL | Curr PL | Prev p90 | Curr p90 | PL Delta |
|-------|---------|---------|----------|----------|----------|
| ed-king | 2.09 | 2.09 | +1.09 | +1.11 | 0.00 (no change) |
| sea-bi | 2.9 | 2.91 | +1.65 | +1.66 | +0.01 (worse) |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 2.87 | -0.80 | +1.88 |
| 1 | 6448 | 3224 | 2.2 | -0.61 | +1.41 |
| 2 | 9672 | 3224 | 2.89 | -1.49 | +1.15 |
| 3 | 12896 | 3224 | 2.31 | -0.90 | +1.17 |
| 4 | 16120 | 3228 | 2.2 | -0.79 | +1.13 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.49 | ±0.32 |
| Bias | -0.92 | ±0.3 |
| p90 | 1.35 | ±0.28 |

## By Route

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ed-king | 2.09 | -0.83 | +1.11 | 4.15 | 271623 |
| sea-bi | 2.91 | -1.01 | +1.66 | 5.45 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| Fri | 2.28 | -0.64 | +1.36 | 4.31 | 76527 |
| Mon | 2.24 | -0.70 | +1.25 | 4.7 | 81477 |
| Sat | 2.39 | -0.69 | +1.56 | 5.02 | 74514 |
| Sun | 3.43 | -1.17 | +1.91 | 6.4 | 71412 |
| Thu | 2.28 | -0.99 | +1.15 | 4.2 | 75306 |
| Tue | 1.97 | -0.91 | +1.00 | 4.22 | 77385 |
| Wed | 2.95 | -1.36 | +1.37 | 4.76 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 2.74 | -0.94 | +1.35 | 28314 |
| Early (5–7) | 2.74 | -1.27 | +1.12 | 46827 |
| Evening (19–22) | 2.06 | -0.64 | +1.31 | 80355 |
| Midday (10–15) | 1.53 | -0.62 | +0.95 | 63030 |
| PM Peak (15–19) | 1.99 | -0.65 | +1.25 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 2.41 | -0.84 | +1.34 | 16124 |
| 4–6m | 2.4 | -0.85 | +1.34 | 16124 |
| 6–8m | 2.4 | -0.85 | +1.34 | 16124 |
| 8–10m | 2.41 | -0.86 | +1.34 | 16124 |
| 10–14m | 2.41 | -0.86 | +1.34 | 32248 |
| 14–20m | 2.43 | -0.87 | +1.34 | 48372 |
| 20–30m | 2.46 | -0.88 | +1.36 | 80620 |
| 30–45m | 2.5 | -0.92 | +1.35 | 128992 |
| 45–60m | 2.54 | -0.95 | +1.36 | 112868 |
| 60–90m | 2.57 | -0.98 | +1.35 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.28 | -0.94 | +1.16 | 176352 |
| ed-king (peak) | 1.74 | -0.62 | +1.02 | 95271 |
| sea-bi (off-peak) | 3.15 | -1.08 | +1.86 | 163119 |
| sea-bi (peak) | 2.5 | -0.89 | +1.43 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.49,
    "overall_bias": -0.92,
    "overall_error_p90": 1.35,
    "n_test_samples": 532092,
    "overall_mae": 1.97,
    "overall_coverage_70pct": 70.0,
    "overall_mean_interval_width": 4.79,
    "overall_median_interval_width": 3.42,
    "overall_baseline_pinball_loss": 4.39,
    "overall_improvement_pct": 43.3,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.09,
        "bias": -0.83,
        "error_p90": 1.11,
        "n": 271623,
        "mae": 1.67,
        "mean_interval_width": 4.15,
        "median_interval_width": 3.13,
        "baseline_pinball_loss": 3.77,
        "improvement_pct": 44.6
      },
      "sea-bi": {
        "pinball_loss": 2.91,
        "bias": -1.01,
        "error_p90": 1.66,
        "n": 260469,
        "mae": 2.28,
        "mean_interval_width": 5.45,
        "median_interval_width": 3.86,
        "baseline_pinball_loss": 5.03,
        "improvement_pct": 42.2
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 3.43,
        "bias": -1.17,
        "error_p90": 1.91,
        "n": 71412,
        "mae": 2.68,
        "mean_interval_width": 6.4,
        "median_interval_width": 4.15,
        "baseline_pinball_loss": 6.0,
        "improvement_pct": 42.8
      },
      "Mon": {
        "pinball_loss": 2.24,
        "bias": -0.7,
        "error_p90": 1.25,
        "n": 81477,
        "mae": 1.73,
        "mean_interval_width": 4.7,
        "median_interval_width": 3.0,
        "baseline_pinball_loss": 4.21,
        "improvement_pct": 46.8
      },
      "Tue": {
        "pinball_loss": 1.97,
        "bias": -0.91,
        "error_p90": 1.0,
        "n": 77385,
        "mae": 1.62,
        "mean_interval_width": 4.22,
        "median_interval_width": 3.19,
        "baseline_pinball_loss": 3.28,
        "improvement_pct": 39.9
      },
      "Wed": {
        "pinball_loss": 2.95,
        "bias": -1.36,
        "error_p90": 1.37,
        "n": 75471,
        "mae": 2.42,
        "mean_interval_width": 4.76,
        "median_interval_width": 3.58,
        "baseline_pinball_loss": 5.6,
        "improvement_pct": 47.3
      },
      "Thu": {
        "pinball_loss": 2.28,
        "bias": -0.99,
        "error_p90": 1.15,
        "n": 75306,
        "mae": 1.85,
        "mean_interval_width": 4.2,
        "median_interval_width": 3.13,
        "baseline_pinball_loss": 3.48,
        "improvement_pct": 34.5
      },
      "Fri": {
        "pinball_loss": 2.28,
        "bias": -0.64,
        "error_p90": 1.36,
        "n": 76527,
        "mae": 1.74,
        "mean_interval_width": 4.31,
        "median_interval_width": 3.36,
        "baseline_pinball_loss": 4.26,
        "improvement_pct": 46.5
      },
      "Sat": {
        "pinball_loss": 2.39,
        "bias": -0.69,
        "error_p90": 1.56,
        "n": 74514,
        "mae": 1.82,
        "mean_interval_width": 5.02,
        "median_interval_width": 3.88,
        "baseline_pinball_loss": 4.03,
        "improvement_pct": 40.6
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 2.74,
        "bias": -1.27,
        "error_p90": 1.12,
        "n": 46827,
        "mae": 2.25,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 35.2
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 2.74,
        "bias": -0.94,
        "error_p90": 1.35,
        "n": 28314,
        "mae": 2.14,
        "baseline_pinball_loss": 5.63,
        "improvement_pct": 51.3
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.53,
        "bias": -0.62,
        "error_p90": 0.95,
        "n": 63030,
        "mae": 1.23,
        "baseline_pinball_loss": 4.83,
        "improvement_pct": 68.3
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 1.99,
        "bias": -0.65,
        "error_p90": 1.25,
        "n": 112398,
        "mae": 1.54,
        "baseline_pinball_loss": 3.49,
        "improvement_pct": 43.0
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.06,
        "bias": -0.64,
        "error_p90": 1.31,
        "n": 80355,
        "mae": 1.58,
        "baseline_pinball_loss": 2.94,
        "improvement_pct": 29.9
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 2.41,
        "bias": -0.84,
        "error_p90": 1.34,
        "n": 16124,
        "mae": 1.88,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.6
      },
      "4\u20136m": {
        "pinball_loss": 2.4,
        "bias": -0.85,
        "error_p90": 1.34,
        "n": 16124,
        "mae": 1.88,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.9
      },
      "6\u20138m": {
        "pinball_loss": 2.4,
        "bias": -0.85,
        "error_p90": 1.34,
        "n": 16124,
        "mae": 1.89,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.9
      },
      "8\u201310m": {
        "pinball_loss": 2.41,
        "bias": -0.86,
        "error_p90": 1.34,
        "n": 16124,
        "mae": 1.89,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.7
      },
      "10\u201314m": {
        "pinball_loss": 2.41,
        "bias": -0.86,
        "error_p90": 1.34,
        "n": 32248,
        "mae": 1.9,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.7
      },
      "14\u201320m": {
        "pinball_loss": 2.43,
        "bias": -0.87,
        "error_p90": 1.34,
        "n": 48372,
        "mae": 1.91,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 38.1
      },
      "20\u201330m": {
        "pinball_loss": 2.46,
        "bias": -0.88,
        "error_p90": 1.36,
        "n": 80620,
        "mae": 1.94,
        "baseline_pinball_loss": 3.94,
        "improvement_pct": 37.6
      },
      "30\u201345m": {
        "pinball_loss": 2.5,
        "bias": -0.92,
        "error_p90": 1.35,
        "n": 128992,
        "mae": 1.97,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 40.9
      },
      "45\u201360m": {
        "pinball_loss": 2.54,
        "bias": -0.95,
        "error_p90": 1.36,
        "n": 112868,
        "mae": 2.01,
        "baseline_pinball_loss": 4.94,
        "improvement_pct": 48.6
      },
      "60\u201390m": {
        "pinball_loss": 2.57,
        "bias": -0.98,
        "error_p90": 1.35,
        "n": 32248,
        "mae": 2.04,
        "baseline_pinball_loss": 5.02,
        "improvement_pct": 48.8
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.28,
        "bias": -0.94,
        "error_p90": 1.16,
        "n": 176352,
        "mae": 1.84,
        "baseline_pinball_loss": 4.15,
        "improvement_pct": 45.1
      },
      "ed-king (peak)": {
        "pinball_loss": 1.74,
        "bias": -0.62,
        "error_p90": 1.02,
        "n": 95271,
        "mae": 1.37,
        "baseline_pinball_loss": 3.07,
        "improvement_pct": 43.3
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.15,
        "bias": -1.08,
        "error_p90": 1.86,
        "n": 163119,
        "mae": 2.46,
        "baseline_pinball_loss": 5.37,
        "improvement_pct": 41.3
      },
      "sea-bi (peak)": {
        "pinball_loss": 2.5,
        "bias": -0.89,
        "error_p90": 1.43,
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
      "mean": 2.49,
      "std": 0.32
    },
    "bias": {
      "mean": -0.92,
      "std": 0.3
    },
    "error_p90": {
      "mean": 1.35,
      "std": 0.28
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
