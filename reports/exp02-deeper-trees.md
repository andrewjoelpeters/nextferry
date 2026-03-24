# Backtest Report: exp02-deeper-trees

**Date:** 2026-03-22 22:49:08  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 1m 31s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.48× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.62 min** (PL/MAE = 1.48×) |
| MAE | 2.44 min |
| Bias | -0.08 min |
| p90 (tail risk) | +3.29 min |
| 70% Interval Coverage | 60.5% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 49.1% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.86 | +0.27 | +3.63 |
| 1 | 6448 | 3224 | 5.44 | +1.33 | +5.94 |
| 2 | 9672 | 3224 | 3.45 | -1.01 | +1.79 |
| 3 | 12896 | 3224 | 2.69 | -0.48 | +1.55 |
| 4 | 16120 | 3228 | 2.67 | -0.49 | +1.59 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.62 | ±1.02 |
| Bias | -0.08 | ±0.81 |
| p90 | 2.9 | ±1.71 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 3.11 | -0.07 | +2.84 | 271623 |
| sea-bi | 4.15 | -0.08 | +3.90 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 3.04 | +0.02 | +2.74 | 76527 |
| Mon | 3.6 | +0.14 | +3.60 | 81477 |
| Sat | 3.59 | +0.06 | +3.50 | 74514 |
| Sun | 5.25 | +0.13 | +5.53 | 71412 |
| Thu | 3.06 | -0.30 | +2.57 | 75306 |
| Tue | 2.95 | -0.19 | +2.62 | 77385 |
| Wed | 3.97 | -0.40 | +3.64 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.42 | +0.14 | +4.33 | 28314 |
| Early (5–7) | 4.05 | -0.26 | +3.07 | 46827 |
| Evening (19–22) | 3.46 | +0.26 | +4.62 | 80355 |
| Midday (10–15) | 1.88 | -0.20 | +1.40 | 63030 |
| PM Peak (15–19) | 2.77 | +0.02 | +2.65 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.62 | -0.10 | +3.27 | 16124 |
| 4–6m | 3.61 | -0.10 | +3.26 | 16124 |
| 6–8m | 3.61 | -0.10 | +3.27 | 16124 |
| 8–10m | 3.62 | -0.10 | +3.28 | 16124 |
| 10–14m | 3.62 | -0.09 | +3.27 | 32248 |
| 14–20m | 3.62 | -0.09 | +3.26 | 48372 |
| 20–30m | 3.62 | -0.08 | +3.28 | 80620 |
| 30–45m | 3.62 | -0.08 | +3.28 | 128992 |
| 45–60m | 3.63 | -0.07 | +3.29 | 112868 |
| 60–90m | 3.63 | -0.05 | +3.32 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.31 | -0.18 | +2.76 | 176352 |
| ed-king (peak) | 2.75 | +0.13 | +3.00 | 95271 |
| sea-bi (off-peak) | 4.44 | -0.11 | +4.18 | 163119 |
| sea-bi (peak) | 3.68 | -0.03 | +3.45 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.62,
    "overall_bias": -0.08,
    "overall_error_p90": 3.29,
    "n_test_samples": 532092,
    "overall_mae": 2.44,
    "overall_coverage_70pct": 60.5,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 49.1,
    "by_route": {
      "ed-king": {
        "pinball_loss": 3.11,
        "bias": -0.07,
        "error_p90": 2.84,
        "n": 271623,
        "mae": 2.1,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 39.5
      },
      "sea-bi": {
        "pinball_loss": 4.15,
        "bias": -0.08,
        "error_p90": 3.9,
        "n": 260469,
        "mae": 2.8,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 54.7
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 5.25,
        "bias": 0.13,
        "error_p90": 5.53,
        "n": 71412,
        "mae": 3.46,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 50.8
      },
      "Mon": {
        "pinball_loss": 3.6,
        "bias": 0.14,
        "error_p90": 3.6,
        "n": 81477,
        "mae": 2.35,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 31.1
      },
      "Tue": {
        "pinball_loss": 2.95,
        "bias": -0.19,
        "error_p90": 2.62,
        "n": 77385,
        "mae": 2.03,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 48.3
      },
      "Wed": {
        "pinball_loss": 3.97,
        "bias": -0.4,
        "error_p90": 3.64,
        "n": 75471,
        "mae": 2.78,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 24.4
      },
      "Thu": {
        "pinball_loss": 3.06,
        "bias": -0.3,
        "error_p90": 2.57,
        "n": 75306,
        "mae": 2.14,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 45.1
      },
      "Fri": {
        "pinball_loss": 3.04,
        "bias": 0.02,
        "error_p90": 2.74,
        "n": 76527,
        "mae": 2.02,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 54.7
      },
      "Sat": {
        "pinball_loss": 3.59,
        "bias": 0.06,
        "error_p90": 3.5,
        "n": 74514,
        "mae": 2.37,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 67.5
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 4.05,
        "bias": -0.26,
        "error_p90": 3.07,
        "n": 46827,
        "mae": 2.79,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 21.6
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.42,
        "bias": 0.14,
        "error_p90": 4.33,
        "n": 28314,
        "mae": 2.9,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 19.7
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.88,
        "bias": -0.2,
        "error_p90": 1.4,
        "n": 63030,
        "mae": 1.32,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 62.2
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.77,
        "bias": 0.02,
        "error_p90": 2.65,
        "n": 112398,
        "mae": 1.84,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 70.9
      },
      "Evening (19\u201322)": {
        "pinball_loss": 3.46,
        "bias": 0.26,
        "error_p90": 4.62,
        "n": 80355,
        "mae": 2.22,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 58.4
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.62,
        "bias": -0.1,
        "error_p90": 3.27,
        "n": 16124,
        "mae": 2.45,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 51.1
      },
      "4\u20136m": {
        "pinball_loss": 3.61,
        "bias": -0.1,
        "error_p90": 3.26,
        "n": 16124,
        "mae": 2.44,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 51.2
      },
      "6\u20138m": {
        "pinball_loss": 3.61,
        "bias": -0.1,
        "error_p90": 3.27,
        "n": 16124,
        "mae": 2.44,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 51.1
      },
      "8\u201310m": {
        "pinball_loss": 3.62,
        "bias": -0.1,
        "error_p90": 3.28,
        "n": 16124,
        "mae": 2.44,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 51.0
      },
      "10\u201314m": {
        "pinball_loss": 3.62,
        "bias": -0.09,
        "error_p90": 3.27,
        "n": 32248,
        "mae": 2.45,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 50.9
      },
      "14\u201320m": {
        "pinball_loss": 3.62,
        "bias": -0.09,
        "error_p90": 3.26,
        "n": 48372,
        "mae": 2.44,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 50.4
      },
      "20\u201330m": {
        "pinball_loss": 3.62,
        "bias": -0.08,
        "error_p90": 3.28,
        "n": 80620,
        "mae": 2.44,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 49.4
      },
      "30\u201345m": {
        "pinball_loss": 3.62,
        "bias": -0.08,
        "error_p90": 3.28,
        "n": 128992,
        "mae": 2.44,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 48.0
      },
      "45\u201360m": {
        "pinball_loss": 3.63,
        "bias": -0.07,
        "error_p90": 3.29,
        "n": 112868,
        "mae": 2.44,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 48.8
      },
      "60\u201390m": {
        "pinball_loss": 3.63,
        "bias": -0.05,
        "error_p90": 3.32,
        "n": 32248,
        "mae": 2.44,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 48.4
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.31,
        "bias": -0.18,
        "error_p90": 2.76,
        "n": 176352,
        "mae": 2.27,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 25.5
      },
      "ed-king (peak)": {
        "pinball_loss": 2.75,
        "bias": 0.13,
        "error_p90": 3.0,
        "n": 95271,
        "mae": 1.79,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 57.2
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.44,
        "bias": -0.11,
        "error_p90": 4.18,
        "n": 163119,
        "mae": 2.99,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 47.6
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.68,
        "bias": -0.03,
        "error_p90": 3.45,
        "n": 97350,
        "mae": 2.47,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 64.4
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.62,
      "std": 1.02
    },
    "bias": {
      "mean": -0.08,
      "std": 0.81
    },
    "error_p90": {
      "mean": 2.9,
      "std": 1.71
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
