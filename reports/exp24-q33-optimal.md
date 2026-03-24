# Backtest Report: exp24-q33-optimal

**Date:** 2026-03-22 23:41:49  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 40s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.24× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.76 min** (PL/MAE = 1.24×) |
| MAE | 2.22 min |
| Bias | -1.15 min |
| p90 (tail risk) | +1.33 min |
| 70% Interval Coverage | 70.0% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 61.2% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.18 | -0.65 | +2.26 |
| 1 | 6448 | 3224 | 2.63 | -0.87 | +1.52 |
| 2 | 9672 | 3224 | 3.12 | -1.84 | +0.95 |
| 3 | 12896 | 3224 | 2.41 | -1.17 | +1.06 |
| 4 | 16120 | 3228 | 2.45 | -1.21 | +1.01 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.76 | ±0.33 |
| Bias | -1.15 | ±0.4 |
| p90 | 1.36 | ±0.49 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 2.23 | -1.02 | +1.09 | 271623 |
| sea-bi | 3.32 | -1.28 | +1.68 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 2.26 | -0.85 | +1.19 | 76527 |
| Mon | 2.63 | -0.99 | +1.33 | 81477 |
| Sat | 2.92 | -1.05 | +1.61 | 74514 |
| Sun | 4.0 | -1.59 | +1.86 | 71412 |
| Thu | 2.36 | -1.14 | +1.06 | 75306 |
| Tue | 2.19 | -1.05 | +1.06 | 77385 |
| Wed | 3.08 | -1.44 | +1.33 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 3.54 | -1.18 | +2.09 | 28314 |
| Early (5–7) | 3.18 | -1.38 | +1.33 | 46827 |
| Evening (19–22) | 2.12 | -0.97 | +1.12 | 80355 |
| Midday (10–15) | 1.59 | -0.74 | +0.84 | 63030 |
| PM Peak (15–19) | 1.94 | -0.88 | +1.02 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 2.78 | -1.17 | +1.33 | 16124 |
| 4–6m | 2.78 | -1.17 | +1.32 | 16124 |
| 6–8m | 2.78 | -1.17 | +1.33 | 16124 |
| 8–10m | 2.77 | -1.17 | +1.33 | 16124 |
| 10–14m | 2.77 | -1.17 | +1.33 | 32248 |
| 14–20m | 2.77 | -1.16 | +1.33 | 48372 |
| 20–30m | 2.77 | -1.16 | +1.33 | 80620 |
| 30–45m | 2.76 | -1.15 | +1.33 | 128992 |
| 45–60m | 2.75 | -1.14 | +1.32 | 112868 |
| 60–90m | 2.75 | -1.13 | +1.32 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.51 | -1.16 | +1.15 | 176352 |
| ed-king (peak) | 1.71 | -0.78 | +0.96 | 95271 |
| sea-bi (off-peak) | 3.61 | -1.34 | +1.87 | 163119 |
| sea-bi (peak) | 2.82 | -1.19 | +1.43 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.76,
    "overall_bias": -1.15,
    "overall_error_p90": 1.33,
    "n_test_samples": 532092,
    "overall_mae": 2.22,
    "overall_coverage_70pct": 70.0,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 61.2,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.23,
        "bias": -1.02,
        "error_p90": 1.09,
        "n": 271623,
        "mae": 1.83,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 56.6
      },
      "sea-bi": {
        "pinball_loss": 3.32,
        "bias": -1.28,
        "error_p90": 1.68,
        "n": 260469,
        "mae": 2.64,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 63.8
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 4.0,
        "bias": -1.59,
        "error_p90": 1.86,
        "n": 71412,
        "mae": 3.2,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 62.5
      },
      "Mon": {
        "pinball_loss": 2.63,
        "bias": -0.99,
        "error_p90": 1.33,
        "n": 81477,
        "mae": 2.08,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 49.7
      },
      "Tue": {
        "pinball_loss": 2.19,
        "bias": -1.05,
        "error_p90": 1.06,
        "n": 77385,
        "mae": 1.81,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 61.6
      },
      "Wed": {
        "pinball_loss": 3.08,
        "bias": -1.44,
        "error_p90": 1.33,
        "n": 75471,
        "mae": 2.53,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 41.4
      },
      "Thu": {
        "pinball_loss": 2.36,
        "bias": -1.14,
        "error_p90": 1.06,
        "n": 75306,
        "mae": 1.95,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 57.7
      },
      "Fri": {
        "pinball_loss": 2.26,
        "bias": -0.85,
        "error_p90": 1.19,
        "n": 76527,
        "mae": 1.79,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 66.3
      },
      "Sat": {
        "pinball_loss": 2.92,
        "bias": -1.05,
        "error_p90": 1.61,
        "n": 74514,
        "mae": 2.3,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 73.6
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.18,
        "bias": -1.38,
        "error_p90": 1.33,
        "n": 46827,
        "mae": 2.58,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 38.4
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 3.54,
        "bias": -1.18,
        "error_p90": 2.09,
        "n": 28314,
        "mae": 2.76,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 35.7
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.59,
        "bias": -0.74,
        "error_p90": 0.84,
        "n": 63030,
        "mae": 1.31,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 68.0
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 1.94,
        "bias": -0.88,
        "error_p90": 1.02,
        "n": 112398,
        "mae": 1.58,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 79.6
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.12,
        "bias": -0.97,
        "error_p90": 1.12,
        "n": 80355,
        "mae": 1.74,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 74.5
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 2.78,
        "bias": -1.17,
        "error_p90": 1.33,
        "n": 16124,
        "mae": 2.24,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 62.4
      },
      "4\u20136m": {
        "pinball_loss": 2.78,
        "bias": -1.17,
        "error_p90": 1.32,
        "n": 16124,
        "mae": 2.24,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 62.4
      },
      "6\u20138m": {
        "pinball_loss": 2.78,
        "bias": -1.17,
        "error_p90": 1.33,
        "n": 16124,
        "mae": 2.24,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 62.3
      },
      "8\u201310m": {
        "pinball_loss": 2.77,
        "bias": -1.17,
        "error_p90": 1.33,
        "n": 16124,
        "mae": 2.24,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 62.5
      },
      "10\u201314m": {
        "pinball_loss": 2.77,
        "bias": -1.17,
        "error_p90": 1.33,
        "n": 32248,
        "mae": 2.24,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 62.4
      },
      "14\u201320m": {
        "pinball_loss": 2.77,
        "bias": -1.16,
        "error_p90": 1.33,
        "n": 48372,
        "mae": 2.23,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 62.0
      },
      "20\u201330m": {
        "pinball_loss": 2.77,
        "bias": -1.16,
        "error_p90": 1.33,
        "n": 80620,
        "mae": 2.23,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 61.3
      },
      "30\u201345m": {
        "pinball_loss": 2.76,
        "bias": -1.15,
        "error_p90": 1.33,
        "n": 128992,
        "mae": 2.22,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 60.3
      },
      "45\u201360m": {
        "pinball_loss": 2.75,
        "bias": -1.14,
        "error_p90": 1.32,
        "n": 112868,
        "mae": 2.22,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 61.2
      },
      "60\u201390m": {
        "pinball_loss": 2.75,
        "bias": -1.13,
        "error_p90": 1.32,
        "n": 32248,
        "mae": 2.21,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 60.9
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.51,
        "bias": -1.16,
        "error_p90": 1.15,
        "n": 176352,
        "mae": 2.06,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 43.5
      },
      "ed-king (peak)": {
        "pinball_loss": 1.71,
        "bias": -0.78,
        "error_p90": 0.96,
        "n": 95271,
        "mae": 1.4,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 73.4
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.61,
        "bias": -1.34,
        "error_p90": 1.87,
        "n": 163119,
        "mae": 2.85,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 57.4
      },
      "sea-bi (peak)": {
        "pinball_loss": 2.82,
        "bias": -1.19,
        "error_p90": 1.43,
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
      "mean": 2.76,
      "std": 0.33
    },
    "bias": {
      "mean": -1.15,
      "std": 0.4
    },
    "error_p90": {
      "mean": 1.36,
      "std": 0.49
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
