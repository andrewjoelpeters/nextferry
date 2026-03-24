# Backtest Report: exp03-vessel-id

**Date:** 2026-03-22 22:51:27  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 50.2s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.47× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.62 min** (PL/MAE = 1.47×) |
| MAE | 2.46 min |
| Bias | -0.15 min |
| p90 (tail risk) | +3.16 min |
| 70% Interval Coverage | 62.7% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 49.1% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.73 | +0.05 | +3.37 |
| 1 | 6448 | 3224 | 5.65 | +1.39 | +7.24 |
| 2 | 9672 | 3224 | 3.28 | -1.18 | +1.57 |
| 3 | 12896 | 3224 | 2.72 | -0.51 | +1.63 |
| 4 | 16120 | 3228 | 2.7 | -0.51 | +1.67 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.62 | ±1.09 |
| Bias | -0.15 | ±0.86 |
| p90 | 3.1 | ±2.18 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 3.13 | -0.10 | +2.60 | 271623 |
| sea-bi | 4.12 | -0.21 | +3.87 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 3.12 | +0.04 | +2.66 | 76527 |
| Mon | 3.68 | +0.11 | +3.68 | 81477 |
| Sat | 3.54 | -0.07 | +3.33 | 74514 |
| Sun | 5.07 | -0.15 | +5.74 | 71412 |
| Thu | 3.14 | -0.29 | +2.33 | 75306 |
| Tue | 2.95 | -0.23 | +2.48 | 77385 |
| Wed | 3.93 | -0.51 | +3.44 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.36 | +0.02 | +4.48 | 28314 |
| Early (5–7) | 3.78 | -0.46 | +2.82 | 46827 |
| Evening (19–22) | 3.78 | +0.39 | +6.00 | 80355 |
| Midday (10–15) | 1.89 | -0.25 | +1.42 | 63030 |
| PM Peak (15–19) | 2.85 | +0.02 | +2.49 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.63 | -0.18 | +3.13 | 16124 |
| 4–6m | 3.62 | -0.18 | +3.12 | 16124 |
| 6–8m | 3.62 | -0.18 | +3.12 | 16124 |
| 8–10m | 3.62 | -0.17 | +3.13 | 16124 |
| 10–14m | 3.62 | -0.17 | +3.13 | 32248 |
| 14–20m | 3.62 | -0.17 | +3.14 | 48372 |
| 20–30m | 3.62 | -0.16 | +3.15 | 80620 |
| 30–45m | 3.61 | -0.15 | +3.17 | 128992 |
| 45–60m | 3.62 | -0.14 | +3.19 | 112868 |
| 60–90m | 3.61 | -0.13 | +3.19 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.24 | -0.27 | +2.41 | 176352 |
| ed-king (peak) | 2.94 | +0.21 | +2.80 | 95271 |
| sea-bi (off-peak) | 4.4 | -0.25 | +4.14 | 163119 |
| sea-bi (peak) | 3.65 | -0.13 | +3.45 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.62,
    "overall_bias": -0.15,
    "overall_error_p90": 3.16,
    "n_test_samples": 532092,
    "overall_mae": 2.46,
    "overall_coverage_70pct": 62.7,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 49.1,
    "by_route": {
      "ed-king": {
        "pinball_loss": 3.13,
        "bias": -0.1,
        "error_p90": 2.6,
        "n": 271623,
        "mae": 2.12,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 39.1
      },
      "sea-bi": {
        "pinball_loss": 4.12,
        "bias": -0.21,
        "error_p90": 3.87,
        "n": 260469,
        "mae": 2.82,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 55.1
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 5.07,
        "bias": -0.15,
        "error_p90": 5.74,
        "n": 71412,
        "mae": 3.43,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 52.5
      },
      "Mon": {
        "pinball_loss": 3.68,
        "bias": 0.11,
        "error_p90": 3.68,
        "n": 81477,
        "mae": 2.41,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 29.6
      },
      "Tue": {
        "pinball_loss": 2.95,
        "bias": -0.23,
        "error_p90": 2.48,
        "n": 77385,
        "mae": 2.04,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 48.3
      },
      "Wed": {
        "pinball_loss": 3.93,
        "bias": -0.51,
        "error_p90": 3.44,
        "n": 75471,
        "mae": 2.79,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 25.2
      },
      "Thu": {
        "pinball_loss": 3.14,
        "bias": -0.29,
        "error_p90": 2.33,
        "n": 75306,
        "mae": 2.19,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 43.7
      },
      "Fri": {
        "pinball_loss": 3.12,
        "bias": 0.04,
        "error_p90": 2.66,
        "n": 76527,
        "mae": 2.06,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 53.5
      },
      "Sat": {
        "pinball_loss": 3.54,
        "bias": -0.07,
        "error_p90": 3.33,
        "n": 74514,
        "mae": 2.39,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 68.0
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.78,
        "bias": -0.46,
        "error_p90": 2.82,
        "n": 46827,
        "mae": 2.67,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 26.8
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.36,
        "bias": 0.02,
        "error_p90": 4.48,
        "n": 28314,
        "mae": 2.9,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 20.8
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.89,
        "bias": -0.25,
        "error_p90": 1.42,
        "n": 63030,
        "mae": 1.35,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 62.0
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.85,
        "bias": 0.02,
        "error_p90": 2.49,
        "n": 112398,
        "mae": 1.89,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 70.0
      },
      "Evening (19\u201322)": {
        "pinball_loss": 3.78,
        "bias": 0.39,
        "error_p90": 6.0,
        "n": 80355,
        "mae": 2.39,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 54.6
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.63,
        "bias": -0.18,
        "error_p90": 3.13,
        "n": 16124,
        "mae": 2.48,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 50.9
      },
      "4\u20136m": {
        "pinball_loss": 3.62,
        "bias": -0.18,
        "error_p90": 3.12,
        "n": 16124,
        "mae": 2.47,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 51.0
      },
      "6\u20138m": {
        "pinball_loss": 3.62,
        "bias": -0.18,
        "error_p90": 3.12,
        "n": 16124,
        "mae": 2.47,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 50.9
      },
      "8\u201310m": {
        "pinball_loss": 3.62,
        "bias": -0.17,
        "error_p90": 3.13,
        "n": 16124,
        "mae": 2.47,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 51.0
      },
      "10\u201314m": {
        "pinball_loss": 3.62,
        "bias": -0.17,
        "error_p90": 3.13,
        "n": 32248,
        "mae": 2.47,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 50.9
      },
      "14\u201320m": {
        "pinball_loss": 3.62,
        "bias": -0.17,
        "error_p90": 3.14,
        "n": 48372,
        "mae": 2.47,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 50.4
      },
      "20\u201330m": {
        "pinball_loss": 3.62,
        "bias": -0.16,
        "error_p90": 3.15,
        "n": 80620,
        "mae": 2.46,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 49.4
      },
      "30\u201345m": {
        "pinball_loss": 3.61,
        "bias": -0.15,
        "error_p90": 3.17,
        "n": 128992,
        "mae": 2.46,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 48.1
      },
      "45\u201360m": {
        "pinball_loss": 3.62,
        "bias": -0.14,
        "error_p90": 3.19,
        "n": 112868,
        "mae": 2.46,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 48.9
      },
      "60\u201390m": {
        "pinball_loss": 3.61,
        "bias": -0.13,
        "error_p90": 3.19,
        "n": 32248,
        "mae": 2.45,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 48.7
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.24,
        "bias": -0.27,
        "error_p90": 2.41,
        "n": 176352,
        "mae": 2.25,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 27.1
      },
      "ed-king (peak)": {
        "pinball_loss": 2.94,
        "bias": 0.21,
        "error_p90": 2.8,
        "n": 95271,
        "mae": 1.89,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 54.2
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.4,
        "bias": -0.25,
        "error_p90": 4.14,
        "n": 163119,
        "mae": 3.02,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 48.1
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.65,
        "bias": -0.13,
        "error_p90": 3.45,
        "n": 97350,
        "mae": 2.48,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 64.6
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.62,
      "std": 1.09
    },
    "bias": {
      "mean": -0.15,
      "std": 0.86
    },
    "error_p90": {
      "mean": 3.1,
      "std": 2.18
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
