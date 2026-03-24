# Backtest Report: exp04-vessel-speed

**Date:** 2026-03-22 22:52:33  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 50.3s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.48× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.68 min** (PL/MAE = 1.48×) |
| MAE | 2.48 min |
| Bias | -0.09 min |
| p90 (tail risk) | +3.69 min |
| 70% Interval Coverage | 60.8% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 48.2% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.71 | +0.07 | +3.33 |
| 1 | 6448 | 3224 | 5.98 | +1.73 | +6.29 |
| 2 | 9672 | 3224 | 3.31 | -1.24 | +1.50 |
| 3 | 12896 | 3224 | 2.72 | -0.50 | +1.66 |
| 4 | 16120 | 3228 | 2.67 | -0.53 | +1.63 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.68 | ±1.21 |
| Bias | -0.09 | ±1.0 |
| p90 | 2.88 | ±1.83 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 3.22 | -0.03 | +3.23 | 271623 |
| sea-bi | 4.15 | -0.16 | +4.14 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 3.13 | +0.07 | +2.95 | 76527 |
| Mon | 3.77 | +0.19 | +4.53 | 81477 |
| Sat | 3.55 | -0.02 | +3.66 | 74514 |
| Sun | 5.16 | -0.02 | +5.27 | 71412 |
| Thu | 3.2 | -0.26 | +2.77 | 75306 |
| Tue | 3.03 | -0.16 | +2.77 | 77385 |
| Wed | 4.0 | -0.47 | +3.63 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.57 | +0.13 | +4.95 | 28314 |
| Early (5–7) | 4.12 | -0.26 | +3.51 | 46827 |
| Evening (19–22) | 3.47 | +0.28 | +4.77 | 80355 |
| Midday (10–15) | 1.87 | -0.27 | +1.33 | 63030 |
| PM Peak (15–19) | 2.81 | +0.01 | +2.53 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.7 | -0.11 | +3.68 | 16124 |
| 4–6m | 3.69 | -0.11 | +3.68 | 16124 |
| 6–8m | 3.69 | -0.11 | +3.68 | 16124 |
| 8–10m | 3.69 | -0.11 | +3.69 | 16124 |
| 10–14m | 3.69 | -0.11 | +3.69 | 32248 |
| 14–20m | 3.68 | -0.11 | +3.68 | 48372 |
| 20–30m | 3.67 | -0.10 | +3.68 | 80620 |
| 30–45m | 3.67 | -0.09 | +3.68 | 128992 |
| 45–60m | 3.67 | -0.08 | +3.70 | 112868 |
| 60–90m | 3.67 | -0.07 | +3.74 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.43 | -0.14 | +3.39 | 176352 |
| ed-king (peak) | 2.84 | +0.16 | +3.04 | 95271 |
| sea-bi (off-peak) | 4.41 | -0.21 | +4.38 | 163119 |
| sea-bi (peak) | 3.71 | -0.07 | +3.62 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.68,
    "overall_bias": -0.09,
    "overall_error_p90": 3.69,
    "n_test_samples": 532092,
    "overall_mae": 2.48,
    "overall_coverage_70pct": 60.8,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 48.2,
    "by_route": {
      "ed-king": {
        "pinball_loss": 3.22,
        "bias": -0.03,
        "error_p90": 3.23,
        "n": 271623,
        "mae": 2.16,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 37.3
      },
      "sea-bi": {
        "pinball_loss": 4.15,
        "bias": -0.16,
        "error_p90": 4.14,
        "n": 260469,
        "mae": 2.82,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 54.7
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 5.16,
        "bias": -0.02,
        "error_p90": 5.27,
        "n": 71412,
        "mae": 3.45,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 51.7
      },
      "Mon": {
        "pinball_loss": 3.77,
        "bias": 0.19,
        "error_p90": 4.53,
        "n": 81477,
        "mae": 2.45,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 27.9
      },
      "Tue": {
        "pinball_loss": 3.03,
        "bias": -0.16,
        "error_p90": 2.77,
        "n": 77385,
        "mae": 2.07,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 46.9
      },
      "Wed": {
        "pinball_loss": 4.0,
        "bias": -0.47,
        "error_p90": 3.63,
        "n": 75471,
        "mae": 2.83,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 23.9
      },
      "Thu": {
        "pinball_loss": 3.2,
        "bias": -0.26,
        "error_p90": 2.77,
        "n": 75306,
        "mae": 2.22,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 42.6
      },
      "Fri": {
        "pinball_loss": 3.13,
        "bias": 0.07,
        "error_p90": 2.95,
        "n": 76527,
        "mae": 2.06,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 53.3
      },
      "Sat": {
        "pinball_loss": 3.55,
        "bias": -0.02,
        "error_p90": 3.66,
        "n": 74514,
        "mae": 2.37,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 67.9
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 4.12,
        "bias": -0.26,
        "error_p90": 3.51,
        "n": 46827,
        "mae": 2.83,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 20.2
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.57,
        "bias": 0.13,
        "error_p90": 4.95,
        "n": 28314,
        "mae": 3.01,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 17.0
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.87,
        "bias": -0.27,
        "error_p90": 1.33,
        "n": 63030,
        "mae": 1.33,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 62.4
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.81,
        "bias": 0.01,
        "error_p90": 2.53,
        "n": 112398,
        "mae": 1.87,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 70.4
      },
      "Evening (19\u201322)": {
        "pinball_loss": 3.47,
        "bias": 0.28,
        "error_p90": 4.77,
        "n": 80355,
        "mae": 2.22,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 58.3
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.7,
        "bias": -0.11,
        "error_p90": 3.68,
        "n": 16124,
        "mae": 2.5,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 50.0
      },
      "4\u20136m": {
        "pinball_loss": 3.69,
        "bias": -0.11,
        "error_p90": 3.68,
        "n": 16124,
        "mae": 2.5,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 50.1
      },
      "6\u20138m": {
        "pinball_loss": 3.69,
        "bias": -0.11,
        "error_p90": 3.68,
        "n": 16124,
        "mae": 2.5,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 50.0
      },
      "8\u201310m": {
        "pinball_loss": 3.69,
        "bias": -0.11,
        "error_p90": 3.69,
        "n": 16124,
        "mae": 2.5,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 50.1
      },
      "10\u201314m": {
        "pinball_loss": 3.69,
        "bias": -0.11,
        "error_p90": 3.69,
        "n": 32248,
        "mae": 2.49,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 49.9
      },
      "14\u201320m": {
        "pinball_loss": 3.68,
        "bias": -0.11,
        "error_p90": 3.68,
        "n": 48372,
        "mae": 2.49,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 49.6
      },
      "20\u201330m": {
        "pinball_loss": 3.67,
        "bias": -0.1,
        "error_p90": 3.68,
        "n": 80620,
        "mae": 2.48,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 48.7
      },
      "30\u201345m": {
        "pinball_loss": 3.67,
        "bias": -0.09,
        "error_p90": 3.68,
        "n": 128992,
        "mae": 2.48,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 47.2
      },
      "45\u201360m": {
        "pinball_loss": 3.67,
        "bias": -0.08,
        "error_p90": 3.7,
        "n": 112868,
        "mae": 2.48,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 48.2
      },
      "60\u201390m": {
        "pinball_loss": 3.67,
        "bias": -0.07,
        "error_p90": 3.74,
        "n": 32248,
        "mae": 2.47,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 47.9
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.43,
        "bias": -0.14,
        "error_p90": 3.39,
        "n": 176352,
        "mae": 2.33,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 22.8
      },
      "ed-king (peak)": {
        "pinball_loss": 2.84,
        "bias": 0.16,
        "error_p90": 3.04,
        "n": 95271,
        "mae": 1.84,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 55.8
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.41,
        "bias": -0.21,
        "error_p90": 4.38,
        "n": 163119,
        "mae": 3.01,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 48.0
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.71,
        "bias": -0.07,
        "error_p90": 3.62,
        "n": 97350,
        "mae": 2.5,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 64.1
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.68,
      "std": 1.21
    },
    "bias": {
      "mean": -0.09,
      "std": 1.0
    },
    "error_p90": {
      "mean": 2.88,
      "std": 1.83
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
