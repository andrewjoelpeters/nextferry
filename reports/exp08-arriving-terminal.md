# Backtest Report: exp08-arriving-terminal

**Date:** 2026-03-22 22:57:04  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 50.2s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.49× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.72 min** (PL/MAE = 1.49×) |
| MAE | 2.5 min |
| Bias | -0.05 min |
| p90 (tail risk) | +3.61 min |
| 70% Interval Coverage | 62.1% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 47.7% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.67 | +0.04 | +3.30 |
| 1 | 6448 | 3224 | 6.26 | +1.86 | +7.59 |
| 2 | 9672 | 3224 | 3.3 | -1.17 | +1.57 |
| 3 | 12896 | 3224 | 2.71 | -0.51 | +1.62 |
| 4 | 16120 | 3228 | 2.68 | -0.50 | +1.64 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.72 | ±1.32 |
| Bias | -0.06 | ±1.03 |
| p90 | 3.14 | ±2.32 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 3.29 | +0.02 | +3.26 | 271623 |
| sea-bi | 4.17 | -0.13 | +4.19 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 3.2 | +0.10 | +3.05 | 76527 |
| Mon | 3.74 | +0.16 | +4.11 | 81477 |
| Sat | 3.68 | +0.06 | +3.76 | 74514 |
| Sun | 5.24 | +0.07 | +6.34 | 71412 |
| Thu | 3.2 | -0.23 | +2.59 | 75306 |
| Tue | 3.05 | -0.13 | +2.70 | 77385 |
| Wed | 4.05 | -0.42 | +3.65 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.43 | +0.02 | +4.25 | 28314 |
| Early (5–7) | 3.96 | -0.41 | +2.92 | 46827 |
| Evening (19–22) | 3.83 | +0.46 | +6.22 | 80355 |
| Midday (10–15) | 1.84 | -0.27 | +1.32 | 63030 |
| PM Peak (15–19) | 2.83 | +0.03 | +2.35 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.73 | -0.08 | +3.59 | 16124 |
| 4–6m | 3.73 | -0.08 | +3.59 | 16124 |
| 6–8m | 3.73 | -0.08 | +3.59 | 16124 |
| 8–10m | 3.73 | -0.07 | +3.59 | 16124 |
| 10–14m | 3.73 | -0.07 | +3.59 | 32248 |
| 14–20m | 3.72 | -0.07 | +3.59 | 48372 |
| 20–30m | 3.72 | -0.06 | +3.60 | 80620 |
| 30–45m | 3.72 | -0.06 | +3.61 | 128992 |
| 45–60m | 3.72 | -0.05 | +3.62 | 112868 |
| 60–90m | 3.72 | -0.03 | +3.65 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.49 | -0.08 | +3.35 | 176352 |
| ed-king (peak) | 2.91 | +0.20 | +2.96 | 95271 |
| sea-bi (off-peak) | 4.46 | -0.16 | +4.56 | 163119 |
| sea-bi (peak) | 3.7 | -0.08 | +3.55 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.72,
    "overall_bias": -0.05,
    "overall_error_p90": 3.61,
    "n_test_samples": 532092,
    "overall_mae": 2.5,
    "overall_coverage_70pct": 62.1,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 47.7,
    "by_route": {
      "ed-king": {
        "pinball_loss": 3.29,
        "bias": 0.02,
        "error_p90": 3.26,
        "n": 271623,
        "mae": 2.19,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 36.0
      },
      "sea-bi": {
        "pinball_loss": 4.17,
        "bias": -0.13,
        "error_p90": 4.19,
        "n": 260469,
        "mae": 2.83,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 54.5
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 5.24,
        "bias": 0.07,
        "error_p90": 6.34,
        "n": 71412,
        "mae": 3.47,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 50.9
      },
      "Mon": {
        "pinball_loss": 3.74,
        "bias": 0.16,
        "error_p90": 4.11,
        "n": 81477,
        "mae": 2.44,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 28.4
      },
      "Tue": {
        "pinball_loss": 3.05,
        "bias": -0.13,
        "error_p90": 2.7,
        "n": 77385,
        "mae": 2.08,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 46.6
      },
      "Wed": {
        "pinball_loss": 4.05,
        "bias": -0.42,
        "error_p90": 3.65,
        "n": 75471,
        "mae": 2.84,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 22.9
      },
      "Thu": {
        "pinball_loss": 3.2,
        "bias": -0.23,
        "error_p90": 2.59,
        "n": 75306,
        "mae": 2.21,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 42.6
      },
      "Fri": {
        "pinball_loss": 3.2,
        "bias": 0.1,
        "error_p90": 3.05,
        "n": 76527,
        "mae": 2.1,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 52.3
      },
      "Sat": {
        "pinball_loss": 3.68,
        "bias": 0.06,
        "error_p90": 3.76,
        "n": 74514,
        "mae": 2.43,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 66.7
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.96,
        "bias": -0.41,
        "error_p90": 2.92,
        "n": 46827,
        "mae": 2.78,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 23.3
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.43,
        "bias": 0.02,
        "error_p90": 4.25,
        "n": 28314,
        "mae": 2.95,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 19.6
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.84,
        "bias": -0.27,
        "error_p90": 1.32,
        "n": 63030,
        "mae": 1.32,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 63.0
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.83,
        "bias": 0.03,
        "error_p90": 2.35,
        "n": 112398,
        "mae": 1.88,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 70.2
      },
      "Evening (19\u201322)": {
        "pinball_loss": 3.83,
        "bias": 0.46,
        "error_p90": 6.22,
        "n": 80355,
        "mae": 2.4,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 54.0
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.73,
        "bias": -0.08,
        "error_p90": 3.59,
        "n": 16124,
        "mae": 2.51,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 49.6
      },
      "4\u20136m": {
        "pinball_loss": 3.73,
        "bias": -0.08,
        "error_p90": 3.59,
        "n": 16124,
        "mae": 2.51,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 49.5
      },
      "6\u20138m": {
        "pinball_loss": 3.73,
        "bias": -0.08,
        "error_p90": 3.59,
        "n": 16124,
        "mae": 2.51,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 49.5
      },
      "8\u201310m": {
        "pinball_loss": 3.73,
        "bias": -0.07,
        "error_p90": 3.59,
        "n": 16124,
        "mae": 2.51,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 49.5
      },
      "10\u201314m": {
        "pinball_loss": 3.73,
        "bias": -0.07,
        "error_p90": 3.59,
        "n": 32248,
        "mae": 2.51,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 49.4
      },
      "14\u201320m": {
        "pinball_loss": 3.72,
        "bias": -0.07,
        "error_p90": 3.59,
        "n": 48372,
        "mae": 2.51,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 49.0
      },
      "20\u201330m": {
        "pinball_loss": 3.72,
        "bias": -0.06,
        "error_p90": 3.6,
        "n": 80620,
        "mae": 2.5,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 48.0
      },
      "30\u201345m": {
        "pinball_loss": 3.72,
        "bias": -0.06,
        "error_p90": 3.61,
        "n": 128992,
        "mae": 2.5,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 46.5
      },
      "45\u201360m": {
        "pinball_loss": 3.72,
        "bias": -0.05,
        "error_p90": 3.62,
        "n": 112868,
        "mae": 2.49,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 47.5
      },
      "60\u201390m": {
        "pinball_loss": 3.72,
        "bias": -0.03,
        "error_p90": 3.65,
        "n": 32248,
        "mae": 2.49,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 47.2
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.49,
        "bias": -0.08,
        "error_p90": 3.35,
        "n": 176352,
        "mae": 2.36,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 21.5
      },
      "ed-king (peak)": {
        "pinball_loss": 2.91,
        "bias": 0.2,
        "error_p90": 2.96,
        "n": 95271,
        "mae": 1.87,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 54.7
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.46,
        "bias": -0.16,
        "error_p90": 4.56,
        "n": 163119,
        "mae": 3.02,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 47.4
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.7,
        "bias": -0.08,
        "error_p90": 3.55,
        "n": 97350,
        "mae": 2.5,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 64.2
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.72,
      "std": 1.32
    },
    "bias": {
      "mean": -0.06,
      "std": 1.03
    },
    "error_p90": {
      "mean": 3.14,
      "std": 2.32
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
