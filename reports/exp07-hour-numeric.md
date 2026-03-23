# Backtest Report: exp07-hour-numeric

**Date:** 2026-03-22 22:55:56  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 48.7s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.49× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.67 min** (PL/MAE = 1.49×) |
| MAE | 2.47 min |
| Bias | -0.07 min |
| p90 (tail risk) | +3.40 min |
| 70% Interval Coverage | 61.4% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 48.4% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.78 | +0.13 | +3.40 |
| 1 | 6448 | 3224 | 5.84 | +1.62 | +6.88 |
| 2 | 9672 | 3224 | 3.33 | -1.12 | +1.63 |
| 3 | 12896 | 3224 | 2.73 | -0.49 | +1.64 |
| 4 | 16120 | 3228 | 2.69 | -0.51 | +1.68 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.67 | ±1.16 |
| Bias | -0.07 | ±0.93 |
| p90 | 3.05 | ±2.03 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 3.17 | -0.06 | +2.71 | 271623 |
| sea-bi | 4.19 | -0.09 | +4.19 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 3.12 | +0.06 | +2.91 | 76527 |
| Mon | 3.68 | +0.15 | +4.05 | 81477 |
| Sat | 3.55 | -0.02 | +3.28 | 74514 |
| Sun | 5.33 | +0.10 | +6.03 | 71412 |
| Thu | 3.17 | -0.23 | +2.50 | 75306 |
| Tue | 3.0 | -0.13 | +2.68 | 77385 |
| Wed | 3.98 | -0.47 | +3.57 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.25 | -0.09 | +3.55 | 28314 |
| Early (5–7) | 3.9 | -0.39 | +3.00 | 46827 |
| Evening (19–22) | 3.66 | +0.37 | +5.48 | 80355 |
| Midday (10–15) | 1.88 | -0.26 | +1.46 | 63030 |
| PM Peak (15–19) | 2.84 | +0.02 | +2.44 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.69 | -0.09 | +3.37 | 16124 |
| 4–6m | 3.68 | -0.09 | +3.36 | 16124 |
| 6–8m | 3.68 | -0.09 | +3.36 | 16124 |
| 8–10m | 3.68 | -0.09 | +3.36 | 16124 |
| 10–14m | 3.68 | -0.09 | +3.37 | 32248 |
| 14–20m | 3.68 | -0.09 | +3.38 | 48372 |
| 20–30m | 3.67 | -0.08 | +3.39 | 80620 |
| 30–45m | 3.67 | -0.08 | +3.40 | 128992 |
| 45–60m | 3.67 | -0.07 | +3.41 | 112868 |
| 60–90m | 3.67 | -0.05 | +3.42 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.34 | -0.18 | +2.74 | 176352 |
| ed-king (peak) | 2.86 | +0.18 | +2.67 | 95271 |
| sea-bi (off-peak) | 4.5 | -0.09 | +4.55 | 163119 |
| sea-bi (peak) | 3.68 | -0.09 | +3.35 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.67,
    "overall_bias": -0.07,
    "overall_error_p90": 3.4,
    "n_test_samples": 532092,
    "overall_mae": 2.47,
    "overall_coverage_70pct": 61.4,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 48.4,
    "by_route": {
      "ed-king": {
        "pinball_loss": 3.17,
        "bias": -0.06,
        "error_p90": 2.71,
        "n": 271623,
        "mae": 2.13,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 38.3
      },
      "sea-bi": {
        "pinball_loss": 4.19,
        "bias": -0.09,
        "error_p90": 4.19,
        "n": 260469,
        "mae": 2.83,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 54.3
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 5.33,
        "bias": 0.1,
        "error_p90": 6.03,
        "n": 71412,
        "mae": 3.52,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 50.1
      },
      "Mon": {
        "pinball_loss": 3.68,
        "bias": 0.15,
        "error_p90": 4.05,
        "n": 81477,
        "mae": 2.4,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 29.6
      },
      "Tue": {
        "pinball_loss": 3.0,
        "bias": -0.13,
        "error_p90": 2.68,
        "n": 77385,
        "mae": 2.04,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 47.5
      },
      "Wed": {
        "pinball_loss": 3.98,
        "bias": -0.47,
        "error_p90": 3.57,
        "n": 75471,
        "mae": 2.81,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 24.3
      },
      "Thu": {
        "pinball_loss": 3.17,
        "bias": -0.23,
        "error_p90": 2.5,
        "n": 75306,
        "mae": 2.19,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 43.1
      },
      "Fri": {
        "pinball_loss": 3.12,
        "bias": 0.06,
        "error_p90": 2.91,
        "n": 76527,
        "mae": 2.06,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 53.5
      },
      "Sat": {
        "pinball_loss": 3.55,
        "bias": -0.02,
        "error_p90": 3.28,
        "n": 74514,
        "mae": 2.37,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 67.9
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.9,
        "bias": -0.39,
        "error_p90": 3.0,
        "n": 46827,
        "mae": 2.73,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 24.5
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.25,
        "bias": -0.09,
        "error_p90": 3.55,
        "n": 28314,
        "mae": 2.86,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 22.8
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.88,
        "bias": -0.26,
        "error_p90": 1.46,
        "n": 63030,
        "mae": 1.34,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 62.2
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.84,
        "bias": 0.02,
        "error_p90": 2.44,
        "n": 112398,
        "mae": 1.89,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 70.1
      },
      "Evening (19\u201322)": {
        "pinball_loss": 3.66,
        "bias": 0.37,
        "error_p90": 5.48,
        "n": 80355,
        "mae": 2.32,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 56.0
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.69,
        "bias": -0.09,
        "error_p90": 3.37,
        "n": 16124,
        "mae": 2.49,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 50.1
      },
      "4\u20136m": {
        "pinball_loss": 3.68,
        "bias": -0.09,
        "error_p90": 3.36,
        "n": 16124,
        "mae": 2.48,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 50.2
      },
      "6\u20138m": {
        "pinball_loss": 3.68,
        "bias": -0.09,
        "error_p90": 3.36,
        "n": 16124,
        "mae": 2.48,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 50.1
      },
      "8\u201310m": {
        "pinball_loss": 3.68,
        "bias": -0.09,
        "error_p90": 3.36,
        "n": 16124,
        "mae": 2.48,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 50.2
      },
      "10\u201314m": {
        "pinball_loss": 3.68,
        "bias": -0.09,
        "error_p90": 3.37,
        "n": 32248,
        "mae": 2.48,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 50.1
      },
      "14\u201320m": {
        "pinball_loss": 3.68,
        "bias": -0.09,
        "error_p90": 3.38,
        "n": 48372,
        "mae": 2.48,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 49.6
      },
      "20\u201330m": {
        "pinball_loss": 3.67,
        "bias": -0.08,
        "error_p90": 3.39,
        "n": 80620,
        "mae": 2.48,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 48.7
      },
      "30\u201345m": {
        "pinball_loss": 3.67,
        "bias": -0.08,
        "error_p90": 3.4,
        "n": 128992,
        "mae": 2.47,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 47.2
      },
      "45\u201360m": {
        "pinball_loss": 3.67,
        "bias": -0.07,
        "error_p90": 3.41,
        "n": 112868,
        "mae": 2.47,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 48.2
      },
      "60\u201390m": {
        "pinball_loss": 3.67,
        "bias": -0.05,
        "error_p90": 3.42,
        "n": 32248,
        "mae": 2.46,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 47.9
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.34,
        "bias": -0.18,
        "error_p90": 2.74,
        "n": 176352,
        "mae": 2.29,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 24.9
      },
      "ed-king (peak)": {
        "pinball_loss": 2.86,
        "bias": 0.18,
        "error_p90": 2.67,
        "n": 95271,
        "mae": 1.85,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 55.5
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.5,
        "bias": -0.09,
        "error_p90": 4.55,
        "n": 163119,
        "mae": 3.03,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 46.9
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.68,
        "bias": -0.09,
        "error_p90": 3.35,
        "n": 97350,
        "mae": 2.48,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 64.4
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.67,
      "std": 1.16
    },
    "bias": {
      "mean": -0.07,
      "std": 0.93
    },
    "error_p90": {
      "mean": 3.05,
      "std": 2.03
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
