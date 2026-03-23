# Backtest Report: exp16-weekend

**Date:** 2026-03-22 23:19:46  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 14s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.43× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.27 min** (PL/MAE = 1.43×) |
| MAE | 2.29 min |
| Bias | -0.35 min |
| p90 (tail risk) | +2.34 min |
| 70% Interval Coverage | 59.9% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 54.0% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.75 | +0.12 | +3.41 |
| 1 | 6448 | 3224 | 3.84 | +0.31 | +3.07 |
| 2 | 9672 | 3224 | 3.33 | -1.17 | +1.57 |
| 3 | 12896 | 3224 | 2.73 | -0.49 | +1.64 |
| 4 | 16120 | 3228 | 2.7 | -0.50 | +1.70 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.27 | ±0.48 |
| Bias | -0.35 | ±0.52 |
| p90 | 2.28 | ±0.79 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 2.7 | -0.33 | +2.04 | 271623 |
| sea-bi | 3.86 | -0.37 | +2.83 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 2.81 | -0.16 | +2.27 | 76527 |
| Mon | 3.16 | -0.13 | +2.40 | 81477 |
| Sat | 3.36 | -0.24 | +2.45 | 74514 |
| Sun | 4.61 | -0.36 | +3.33 | 71412 |
| Thu | 2.78 | -0.49 | +1.97 | 75306 |
| Tue | 2.65 | -0.40 | +1.98 | 77385 |
| Wed | 3.61 | -0.66 | +2.42 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.33 | +0.00 | +4.22 | 28314 |
| Early (5–7) | 3.97 | -0.34 | +2.77 | 46827 |
| Evening (19–22) | 2.67 | -0.22 | +2.27 | 80355 |
| Midday (10–15) | 1.87 | -0.27 | +1.34 | 63030 |
| PM Peak (15–19) | 2.35 | -0.25 | +1.83 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.26 | -0.38 | +2.32 | 16124 |
| 4–6m | 3.25 | -0.38 | +2.32 | 16124 |
| 6–8m | 3.26 | -0.37 | +2.32 | 16124 |
| 8–10m | 3.26 | -0.37 | +2.32 | 16124 |
| 10–14m | 3.26 | -0.37 | +2.32 | 32248 |
| 14–20m | 3.27 | -0.36 | +2.33 | 48372 |
| 20–30m | 3.26 | -0.36 | +2.33 | 80620 |
| 30–45m | 3.27 | -0.35 | +2.34 | 128992 |
| 45–60m | 3.28 | -0.33 | +2.35 | 112868 |
| 60–90m | 3.28 | -0.32 | +2.35 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.95 | -0.42 | +2.14 | 176352 |
| ed-king (peak) | 2.24 | -0.15 | +1.87 | 95271 |
| sea-bi (off-peak) | 4.16 | -0.41 | +3.19 | 163119 |
| sea-bi (peak) | 3.36 | -0.28 | +2.39 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.27,
    "overall_bias": -0.35,
    "overall_error_p90": 2.34,
    "n_test_samples": 532092,
    "overall_mae": 2.29,
    "overall_coverage_70pct": 59.9,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 54.0,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.7,
        "bias": -0.33,
        "error_p90": 2.04,
        "n": 271623,
        "mae": 1.91,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 47.5
      },
      "sea-bi": {
        "pinball_loss": 3.86,
        "bias": -0.37,
        "error_p90": 2.83,
        "n": 260469,
        "mae": 2.69,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 57.9
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 4.61,
        "bias": -0.36,
        "error_p90": 3.33,
        "n": 71412,
        "mae": 3.19,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 56.8
      },
      "Mon": {
        "pinball_loss": 3.16,
        "bias": -0.13,
        "error_p90": 2.4,
        "n": 81477,
        "mae": 2.15,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 39.5
      },
      "Tue": {
        "pinball_loss": 2.65,
        "bias": -0.4,
        "error_p90": 1.98,
        "n": 77385,
        "mae": 1.9,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 53.6
      },
      "Wed": {
        "pinball_loss": 3.61,
        "bias": -0.66,
        "error_p90": 2.42,
        "n": 75471,
        "mae": 2.63,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 31.3
      },
      "Thu": {
        "pinball_loss": 2.78,
        "bias": -0.49,
        "error_p90": 1.97,
        "n": 75306,
        "mae": 2.02,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 50.1
      },
      "Fri": {
        "pinball_loss": 2.81,
        "bias": -0.16,
        "error_p90": 2.27,
        "n": 76527,
        "mae": 1.93,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 58.1
      },
      "Sat": {
        "pinball_loss": 3.36,
        "bias": -0.24,
        "error_p90": 2.45,
        "n": 74514,
        "mae": 2.32,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 69.6
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.97,
        "bias": -0.34,
        "error_p90": 2.77,
        "n": 46827,
        "mae": 2.76,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 23.1
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.33,
        "bias": 0.0,
        "error_p90": 4.22,
        "n": 28314,
        "mae": 2.89,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 21.4
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.87,
        "bias": -0.27,
        "error_p90": 1.34,
        "n": 63030,
        "mae": 1.33,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 62.4
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.35,
        "bias": -0.25,
        "error_p90": 1.83,
        "n": 112398,
        "mae": 1.65,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 75.3
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.67,
        "bias": -0.22,
        "error_p90": 2.27,
        "n": 80355,
        "mae": 1.86,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 67.9
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.26,
        "bias": -0.38,
        "error_p90": 2.32,
        "n": 16124,
        "mae": 2.3,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 55.9
      },
      "4\u20136m": {
        "pinball_loss": 3.25,
        "bias": -0.38,
        "error_p90": 2.32,
        "n": 16124,
        "mae": 2.29,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 56.0
      },
      "6\u20138m": {
        "pinball_loss": 3.26,
        "bias": -0.37,
        "error_p90": 2.32,
        "n": 16124,
        "mae": 2.3,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 55.8
      },
      "8\u201310m": {
        "pinball_loss": 3.26,
        "bias": -0.37,
        "error_p90": 2.32,
        "n": 16124,
        "mae": 2.3,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 55.9
      },
      "10\u201314m": {
        "pinball_loss": 3.26,
        "bias": -0.37,
        "error_p90": 2.32,
        "n": 32248,
        "mae": 2.3,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 55.8
      },
      "14\u201320m": {
        "pinball_loss": 3.27,
        "bias": -0.36,
        "error_p90": 2.33,
        "n": 48372,
        "mae": 2.3,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 55.2
      },
      "20\u201330m": {
        "pinball_loss": 3.26,
        "bias": -0.36,
        "error_p90": 2.33,
        "n": 80620,
        "mae": 2.3,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 54.4
      },
      "30\u201345m": {
        "pinball_loss": 3.27,
        "bias": -0.35,
        "error_p90": 2.34,
        "n": 128992,
        "mae": 2.29,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 53.0
      },
      "45\u201360m": {
        "pinball_loss": 3.28,
        "bias": -0.33,
        "error_p90": 2.35,
        "n": 112868,
        "mae": 2.29,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 53.7
      },
      "60\u201390m": {
        "pinball_loss": 3.28,
        "bias": -0.32,
        "error_p90": 2.35,
        "n": 32248,
        "mae": 2.29,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 53.4
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.95,
        "bias": -0.42,
        "error_p90": 2.14,
        "n": 176352,
        "mae": 2.11,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 33.6
      },
      "ed-king (peak)": {
        "pinball_loss": 2.24,
        "bias": -0.15,
        "error_p90": 1.87,
        "n": 95271,
        "mae": 1.55,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 65.1
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.16,
        "bias": -0.41,
        "error_p90": 3.19,
        "n": 163119,
        "mae": 2.91,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 50.9
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.36,
        "bias": -0.28,
        "error_p90": 2.39,
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
      "mean": 3.27,
      "std": 0.48
    },
    "bias": {
      "mean": -0.35,
      "std": 0.52
    },
    "error_p90": {
      "mean": 2.28,
      "std": 0.79
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
