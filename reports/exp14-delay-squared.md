# Backtest Report: exp14-delay-squared

**Date:** 2026-03-22 23:14:29  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 12s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.43× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.31 min** (PL/MAE = 1.43×) |
| MAE | 2.31 min |
| Bias | -0.31 min |
| p90 (tail risk) | +2.42 min |
| 70% Interval Coverage | 60.7% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 53.4% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.78 | +0.14 | +3.35 |
| 1 | 6448 | 3224 | 4.01 | +0.45 | +3.34 |
| 2 | 9672 | 3224 | 3.34 | -1.15 | +1.63 |
| 3 | 12896 | 3224 | 2.74 | -0.48 | +1.65 |
| 4 | 16120 | 3228 | 2.69 | -0.50 | +1.68 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.31 | ±0.53 |
| Bias | -0.31 | ±0.56 |
| p90 | 2.33 | ±0.83 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 2.76 | -0.29 | +2.13 | 271623 |
| sea-bi | 3.88 | -0.33 | +2.87 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 2.83 | -0.13 | +2.29 | 76527 |
| Mon | 3.25 | -0.08 | +2.49 | 81477 |
| Sat | 3.42 | -0.13 | +2.84 | 74514 |
| Sun | 4.75 | -0.26 | +3.55 | 71412 |
| Thu | 2.8 | -0.46 | +1.96 | 75306 |
| Tue | 2.62 | -0.42 | +1.92 | 77385 |
| Wed | 3.61 | -0.68 | +2.40 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.21 | -0.08 | +3.71 | 28314 |
| Early (5–7) | 3.91 | -0.37 | +2.54 | 46827 |
| Evening (19–22) | 2.72 | -0.19 | +2.42 | 80355 |
| Midday (10–15) | 1.87 | -0.25 | +1.40 | 63030 |
| PM Peak (15–19) | 2.41 | -0.22 | +1.89 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.32 | -0.33 | +2.38 | 16124 |
| 4–6m | 3.31 | -0.33 | +2.38 | 16124 |
| 6–8m | 3.31 | -0.33 | +2.37 | 16124 |
| 8–10m | 3.31 | -0.33 | +2.38 | 16124 |
| 10–14m | 3.31 | -0.33 | +2.38 | 32248 |
| 14–20m | 3.31 | -0.32 | +2.39 | 48372 |
| 20–30m | 3.31 | -0.32 | +2.40 | 80620 |
| 30–45m | 3.31 | -0.31 | +2.42 | 128992 |
| 45–60m | 3.31 | -0.30 | +2.45 | 112868 |
| 60–90m | 3.31 | -0.28 | +2.45 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.02 | -0.37 | +2.26 | 176352 |
| ed-king (peak) | 2.29 | -0.12 | +1.99 | 95271 |
| sea-bi (off-peak) | 4.19 | -0.36 | +3.23 | 163119 |
| sea-bi (peak) | 3.36 | -0.28 | +2.36 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.31,
    "overall_bias": -0.31,
    "overall_error_p90": 2.42,
    "n_test_samples": 532092,
    "overall_mae": 2.31,
    "overall_coverage_70pct": 60.7,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 53.4,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.76,
        "bias": -0.29,
        "error_p90": 2.13,
        "n": 271623,
        "mae": 1.94,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 46.3
      },
      "sea-bi": {
        "pinball_loss": 3.88,
        "bias": -0.33,
        "error_p90": 2.87,
        "n": 260469,
        "mae": 2.7,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 57.7
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 4.75,
        "bias": -0.26,
        "error_p90": 3.55,
        "n": 71412,
        "mae": 3.26,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 55.5
      },
      "Mon": {
        "pinball_loss": 3.25,
        "bias": -0.08,
        "error_p90": 2.49,
        "n": 81477,
        "mae": 2.19,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 37.8
      },
      "Tue": {
        "pinball_loss": 2.62,
        "bias": -0.42,
        "error_p90": 1.92,
        "n": 77385,
        "mae": 1.88,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 54.1
      },
      "Wed": {
        "pinball_loss": 3.61,
        "bias": -0.68,
        "error_p90": 2.4,
        "n": 75471,
        "mae": 2.63,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 31.3
      },
      "Thu": {
        "pinball_loss": 2.8,
        "bias": -0.46,
        "error_p90": 1.96,
        "n": 75306,
        "mae": 2.02,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 49.8
      },
      "Fri": {
        "pinball_loss": 2.83,
        "bias": -0.13,
        "error_p90": 2.29,
        "n": 76527,
        "mae": 1.93,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 57.8
      },
      "Sat": {
        "pinball_loss": 3.42,
        "bias": -0.13,
        "error_p90": 2.84,
        "n": 74514,
        "mae": 2.33,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 69.1
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.91,
        "bias": -0.37,
        "error_p90": 2.54,
        "n": 46827,
        "mae": 2.73,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 24.3
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.21,
        "bias": -0.08,
        "error_p90": 3.71,
        "n": 28314,
        "mae": 2.83,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 23.5
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.87,
        "bias": -0.25,
        "error_p90": 1.4,
        "n": 63030,
        "mae": 1.33,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 62.4
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.41,
        "bias": -0.22,
        "error_p90": 1.89,
        "n": 112398,
        "mae": 1.68,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 74.7
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.72,
        "bias": -0.19,
        "error_p90": 2.42,
        "n": 80355,
        "mae": 1.88,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 67.3
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.32,
        "bias": -0.33,
        "error_p90": 2.38,
        "n": 16124,
        "mae": 2.32,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 55.1
      },
      "4\u20136m": {
        "pinball_loss": 3.31,
        "bias": -0.33,
        "error_p90": 2.38,
        "n": 16124,
        "mae": 2.32,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 55.2
      },
      "6\u20138m": {
        "pinball_loss": 3.31,
        "bias": -0.33,
        "error_p90": 2.37,
        "n": 16124,
        "mae": 2.32,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 55.1
      },
      "8\u201310m": {
        "pinball_loss": 3.31,
        "bias": -0.33,
        "error_p90": 2.38,
        "n": 16124,
        "mae": 2.32,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 55.2
      },
      "10\u201314m": {
        "pinball_loss": 3.31,
        "bias": -0.33,
        "error_p90": 2.38,
        "n": 32248,
        "mae": 2.32,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 55.1
      },
      "14\u201320m": {
        "pinball_loss": 3.31,
        "bias": -0.32,
        "error_p90": 2.39,
        "n": 48372,
        "mae": 2.32,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 54.6
      },
      "20\u201330m": {
        "pinball_loss": 3.31,
        "bias": -0.32,
        "error_p90": 2.4,
        "n": 80620,
        "mae": 2.31,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 53.7
      },
      "30\u201345m": {
        "pinball_loss": 3.31,
        "bias": -0.31,
        "error_p90": 2.42,
        "n": 128992,
        "mae": 2.31,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 52.4
      },
      "45\u201360m": {
        "pinball_loss": 3.31,
        "bias": -0.3,
        "error_p90": 2.45,
        "n": 112868,
        "mae": 2.31,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 53.3
      },
      "60\u201390m": {
        "pinball_loss": 3.31,
        "bias": -0.28,
        "error_p90": 2.45,
        "n": 32248,
        "mae": 2.3,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 53.0
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.02,
        "bias": -0.37,
        "error_p90": 2.26,
        "n": 176352,
        "mae": 2.14,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 32.1
      },
      "ed-king (peak)": {
        "pinball_loss": 2.29,
        "bias": -0.12,
        "error_p90": 1.99,
        "n": 95271,
        "mae": 1.57,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 64.3
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.19,
        "bias": -0.36,
        "error_p90": 3.23,
        "n": 163119,
        "mae": 2.91,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 50.6
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.36,
        "bias": -0.28,
        "error_p90": 2.36,
        "n": 97350,
        "mae": 2.33,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 67.5
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.31,
      "std": 0.53
    },
    "bias": {
      "mean": -0.31,
      "std": 0.56
    },
    "error_p90": {
      "mean": 2.33,
      "std": 0.83
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
