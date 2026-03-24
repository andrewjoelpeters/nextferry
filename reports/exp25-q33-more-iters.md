# Backtest Report: exp25-q33-more-iters

**Date:** 2026-03-22 23:46:42  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 4m 42s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.25× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.77 min** (PL/MAE = 1.25×) |
| MAE | 2.22 min |
| Bias | -1.13 min |
| p90 (tail risk) | +1.36 min |
| 70% Interval Coverage | 68.8% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 61.0% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.2 | -0.63 | +2.29 |
| 1 | 6448 | 3224 | 2.66 | -0.85 | +1.56 |
| 2 | 9672 | 3224 | 3.12 | -1.81 | +0.98 |
| 3 | 12896 | 3224 | 2.42 | -1.16 | +1.06 |
| 4 | 16120 | 3228 | 2.46 | -1.20 | +1.03 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.77 | ±0.33 |
| Bias | -1.13 | ±0.4 |
| p90 | 1.38 | ±0.5 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 2.24 | -1.00 | +1.12 | 271623 |
| sea-bi | 3.33 | -1.26 | +1.72 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 2.27 | -0.83 | +1.23 | 76527 |
| Mon | 2.63 | -0.97 | +1.34 | 81477 |
| Sat | 2.93 | -1.01 | +1.68 | 74514 |
| Sun | 4.02 | -1.54 | +1.96 | 71412 |
| Thu | 2.37 | -1.12 | +1.07 | 75306 |
| Tue | 2.2 | -1.04 | +1.07 | 77385 |
| Wed | 3.09 | -1.42 | +1.34 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 3.53 | -1.18 | +2.15 | 28314 |
| Early (5–7) | 3.19 | -1.36 | +1.38 | 46827 |
| Evening (19–22) | 2.13 | -0.96 | +1.14 | 80355 |
| Midday (10–15) | 1.6 | -0.73 | +0.84 | 63030 |
| PM Peak (15–19) | 1.94 | -0.87 | +1.03 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 2.79 | -1.15 | +1.35 | 16124 |
| 4–6m | 2.79 | -1.15 | +1.34 | 16124 |
| 6–8m | 2.79 | -1.15 | +1.35 | 16124 |
| 8–10m | 2.78 | -1.15 | +1.35 | 16124 |
| 10–14m | 2.79 | -1.14 | +1.35 | 32248 |
| 14–20m | 2.78 | -1.14 | +1.36 | 48372 |
| 20–30m | 2.77 | -1.14 | +1.36 | 80620 |
| 30–45m | 2.77 | -1.13 | +1.36 | 128992 |
| 45–60m | 2.76 | -1.12 | +1.36 | 112868 |
| 60–90m | 2.76 | -1.11 | +1.35 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.53 | -1.13 | +1.19 | 176352 |
| ed-king (peak) | 1.72 | -0.77 | +0.97 | 95271 |
| sea-bi (off-peak) | 3.62 | -1.31 | +1.93 | 163119 |
| sea-bi (peak) | 2.82 | -1.18 | +1.45 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.77,
    "overall_bias": -1.13,
    "overall_error_p90": 1.36,
    "n_test_samples": 532092,
    "overall_mae": 2.22,
    "overall_coverage_70pct": 68.8,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 61.0,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.24,
        "bias": -1.0,
        "error_p90": 1.12,
        "n": 271623,
        "mae": 1.83,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 56.4
      },
      "sea-bi": {
        "pinball_loss": 3.33,
        "bias": -1.26,
        "error_p90": 1.72,
        "n": 260469,
        "mae": 2.64,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 63.7
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 4.02,
        "bias": -1.54,
        "error_p90": 1.96,
        "n": 71412,
        "mae": 3.19,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 62.4
      },
      "Mon": {
        "pinball_loss": 2.63,
        "bias": -0.97,
        "error_p90": 1.34,
        "n": 81477,
        "mae": 2.08,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 49.7
      },
      "Tue": {
        "pinball_loss": 2.2,
        "bias": -1.04,
        "error_p90": 1.07,
        "n": 77385,
        "mae": 1.81,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 61.5
      },
      "Wed": {
        "pinball_loss": 3.09,
        "bias": -1.42,
        "error_p90": 1.34,
        "n": 75471,
        "mae": 2.53,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 41.2
      },
      "Thu": {
        "pinball_loss": 2.37,
        "bias": -1.12,
        "error_p90": 1.07,
        "n": 75306,
        "mae": 1.95,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 57.5
      },
      "Fri": {
        "pinball_loss": 2.27,
        "bias": -0.83,
        "error_p90": 1.23,
        "n": 76527,
        "mae": 1.79,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 66.2
      },
      "Sat": {
        "pinball_loss": 2.93,
        "bias": -1.01,
        "error_p90": 1.68,
        "n": 74514,
        "mae": 2.29,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 73.5
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.19,
        "bias": -1.36,
        "error_p90": 1.38,
        "n": 46827,
        "mae": 2.58,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 38.2
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 3.53,
        "bias": -1.18,
        "error_p90": 2.15,
        "n": 28314,
        "mae": 2.75,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 35.9
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.6,
        "bias": -0.73,
        "error_p90": 0.84,
        "n": 63030,
        "mae": 1.31,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 67.8
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 1.94,
        "bias": -0.87,
        "error_p90": 1.03,
        "n": 112398,
        "mae": 1.58,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 79.6
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.13,
        "bias": -0.96,
        "error_p90": 1.14,
        "n": 80355,
        "mae": 1.74,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 74.4
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 2.79,
        "bias": -1.15,
        "error_p90": 1.35,
        "n": 16124,
        "mae": 2.24,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 62.3
      },
      "4\u20136m": {
        "pinball_loss": 2.79,
        "bias": -1.15,
        "error_p90": 1.34,
        "n": 16124,
        "mae": 2.24,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 62.2
      },
      "6\u20138m": {
        "pinball_loss": 2.79,
        "bias": -1.15,
        "error_p90": 1.35,
        "n": 16124,
        "mae": 2.24,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 62.2
      },
      "8\u201310m": {
        "pinball_loss": 2.78,
        "bias": -1.15,
        "error_p90": 1.35,
        "n": 16124,
        "mae": 2.24,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 62.4
      },
      "10\u201314m": {
        "pinball_loss": 2.79,
        "bias": -1.14,
        "error_p90": 1.35,
        "n": 32248,
        "mae": 2.24,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 62.2
      },
      "14\u201320m": {
        "pinball_loss": 2.78,
        "bias": -1.14,
        "error_p90": 1.36,
        "n": 48372,
        "mae": 2.23,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 61.9
      },
      "20\u201330m": {
        "pinball_loss": 2.77,
        "bias": -1.14,
        "error_p90": 1.36,
        "n": 80620,
        "mae": 2.23,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 61.3
      },
      "30\u201345m": {
        "pinball_loss": 2.77,
        "bias": -1.13,
        "error_p90": 1.36,
        "n": 128992,
        "mae": 2.22,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 60.2
      },
      "45\u201360m": {
        "pinball_loss": 2.76,
        "bias": -1.12,
        "error_p90": 1.36,
        "n": 112868,
        "mae": 2.22,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 61.0
      },
      "60\u201390m": {
        "pinball_loss": 2.76,
        "bias": -1.11,
        "error_p90": 1.35,
        "n": 32248,
        "mae": 2.21,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 60.8
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.53,
        "bias": -1.13,
        "error_p90": 1.19,
        "n": 176352,
        "mae": 2.06,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 43.1
      },
      "ed-king (peak)": {
        "pinball_loss": 1.72,
        "bias": -0.77,
        "error_p90": 0.97,
        "n": 95271,
        "mae": 1.4,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 73.2
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.62,
        "bias": -1.31,
        "error_p90": 1.93,
        "n": 163119,
        "mae": 2.85,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 57.3
      },
      "sea-bi (peak)": {
        "pinball_loss": 2.82,
        "bias": -1.18,
        "error_p90": 1.45,
        "n": 97350,
        "mae": 2.28,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 72.7
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 2.77,
      "std": 0.33
    },
    "bias": {
      "mean": -1.13,
      "std": 0.4
    },
    "error_p90": {
      "mean": 1.38,
      "std": 0.5
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
