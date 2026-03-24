# Backtest Report: exp05-delay-x-horizon

**Date:** 2026-03-22 22:53:50  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 50.1s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.48× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.74 min** (PL/MAE = 1.48×) |
| MAE | 2.52 min |
| Bias | -0.08 min |
| p90 (tail risk) | +3.49 min |
| 70% Interval Coverage | 62.8% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 47.4% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.7 | -0.01 | +3.30 |
| 1 | 6448 | 3224 | 6.31 | +1.82 | +7.87 |
| 2 | 9672 | 3224 | 3.27 | -1.17 | +1.54 |
| 3 | 12896 | 3224 | 2.73 | -0.51 | +1.64 |
| 4 | 16120 | 3228 | 2.7 | -0.52 | +1.71 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.74 | ±1.34 |
| Bias | -0.08 | ±1.02 |
| p90 | 3.21 | ±2.42 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 3.29 | -0.01 | +2.94 | 271623 |
| sea-bi | 4.21 | -0.15 | +4.12 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 3.22 | +0.11 | +2.91 | 76527 |
| Mon | 3.86 | +0.20 | +4.16 | 81477 |
| Sat | 3.6 | -0.03 | +3.55 | 74514 |
| Sun | 5.23 | -0.03 | +5.99 | 71412 |
| Thu | 3.23 | -0.25 | +2.45 | 75306 |
| Tue | 3.09 | -0.15 | +2.70 | 77385 |
| Wed | 4.07 | -0.43 | +3.68 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.49 | +0.08 | +5.11 | 28314 |
| Early (5–7) | 4.02 | -0.32 | +3.52 | 46827 |
| Evening (19–22) | 3.91 | +0.46 | +6.35 | 80355 |
| Midday (10–15) | 1.94 | -0.26 | +1.47 | 63030 |
| PM Peak (15–19) | 2.94 | +0.06 | +2.65 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.75 | -0.10 | +3.47 | 16124 |
| 4–6m | 3.74 | -0.10 | +3.46 | 16124 |
| 6–8m | 3.74 | -0.10 | +3.46 | 16124 |
| 8–10m | 3.74 | -0.10 | +3.46 | 16124 |
| 10–14m | 3.74 | -0.10 | +3.46 | 32248 |
| 14–20m | 3.74 | -0.09 | +3.47 | 48372 |
| 20–30m | 3.74 | -0.09 | +3.48 | 80620 |
| 30–45m | 3.74 | -0.08 | +3.49 | 128992 |
| 45–60m | 3.74 | -0.07 | +3.51 | 112868 |
| 60–90m | 3.73 | -0.06 | +3.55 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.4 | -0.17 | +2.80 | 176352 |
| ed-king (peak) | 3.09 | +0.29 | +3.30 | 95271 |
| sea-bi (off-peak) | 4.49 | -0.18 | +4.39 | 163119 |
| sea-bi (peak) | 3.74 | -0.09 | +3.79 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.74,
    "overall_bias": -0.08,
    "overall_error_p90": 3.49,
    "n_test_samples": 532092,
    "overall_mae": 2.52,
    "overall_coverage_70pct": 62.8,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 47.4,
    "by_route": {
      "ed-king": {
        "pinball_loss": 3.29,
        "bias": -0.01,
        "error_p90": 2.94,
        "n": 271623,
        "mae": 2.2,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 36.0
      },
      "sea-bi": {
        "pinball_loss": 4.21,
        "bias": -0.15,
        "error_p90": 4.12,
        "n": 260469,
        "mae": 2.86,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 54.1
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 5.23,
        "bias": -0.03,
        "error_p90": 5.99,
        "n": 71412,
        "mae": 3.49,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 51.0
      },
      "Mon": {
        "pinball_loss": 3.86,
        "bias": 0.2,
        "error_p90": 4.16,
        "n": 81477,
        "mae": 2.5,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 26.1
      },
      "Tue": {
        "pinball_loss": 3.09,
        "bias": -0.15,
        "error_p90": 2.7,
        "n": 77385,
        "mae": 2.11,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 45.9
      },
      "Wed": {
        "pinball_loss": 4.07,
        "bias": -0.43,
        "error_p90": 3.68,
        "n": 75471,
        "mae": 2.86,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 22.5
      },
      "Thu": {
        "pinball_loss": 3.23,
        "bias": -0.25,
        "error_p90": 2.45,
        "n": 75306,
        "mae": 2.23,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 42.0
      },
      "Fri": {
        "pinball_loss": 3.22,
        "bias": 0.11,
        "error_p90": 2.91,
        "n": 76527,
        "mae": 2.11,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 52.0
      },
      "Sat": {
        "pinball_loss": 3.6,
        "bias": -0.03,
        "error_p90": 3.55,
        "n": 74514,
        "mae": 2.41,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 67.4
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 4.02,
        "bias": -0.32,
        "error_p90": 3.52,
        "n": 46827,
        "mae": 2.78,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 22.1
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.49,
        "bias": 0.08,
        "error_p90": 5.11,
        "n": 28314,
        "mae": 2.96,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 18.5
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.94,
        "bias": -0.26,
        "error_p90": 1.47,
        "n": 63030,
        "mae": 1.38,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 61.0
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.94,
        "bias": 0.06,
        "error_p90": 2.65,
        "n": 112398,
        "mae": 1.94,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 69.1
      },
      "Evening (19\u201322)": {
        "pinball_loss": 3.91,
        "bias": 0.46,
        "error_p90": 6.35,
        "n": 80355,
        "mae": 2.45,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 53.0
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.75,
        "bias": -0.1,
        "error_p90": 3.47,
        "n": 16124,
        "mae": 2.53,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 49.3
      },
      "4\u20136m": {
        "pinball_loss": 3.74,
        "bias": -0.1,
        "error_p90": 3.46,
        "n": 16124,
        "mae": 2.53,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 49.4
      },
      "6\u20138m": {
        "pinball_loss": 3.74,
        "bias": -0.1,
        "error_p90": 3.46,
        "n": 16124,
        "mae": 2.53,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 49.3
      },
      "8\u201310m": {
        "pinball_loss": 3.74,
        "bias": -0.1,
        "error_p90": 3.46,
        "n": 16124,
        "mae": 2.53,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 49.4
      },
      "10\u201314m": {
        "pinball_loss": 3.74,
        "bias": -0.1,
        "error_p90": 3.46,
        "n": 32248,
        "mae": 2.53,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 49.3
      },
      "14\u201320m": {
        "pinball_loss": 3.74,
        "bias": -0.09,
        "error_p90": 3.47,
        "n": 48372,
        "mae": 2.53,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 48.7
      },
      "20\u201330m": {
        "pinball_loss": 3.74,
        "bias": -0.09,
        "error_p90": 3.48,
        "n": 80620,
        "mae": 2.52,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 47.7
      },
      "30\u201345m": {
        "pinball_loss": 3.74,
        "bias": -0.08,
        "error_p90": 3.49,
        "n": 128992,
        "mae": 2.52,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 46.2
      },
      "45\u201360m": {
        "pinball_loss": 3.74,
        "bias": -0.07,
        "error_p90": 3.51,
        "n": 112868,
        "mae": 2.52,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 47.2
      },
      "60\u201390m": {
        "pinball_loss": 3.73,
        "bias": -0.06,
        "error_p90": 3.55,
        "n": 32248,
        "mae": 2.51,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 47.0
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.4,
        "bias": -0.17,
        "error_p90": 2.8,
        "n": 176352,
        "mae": 2.33,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 23.5
      },
      "ed-king (peak)": {
        "pinball_loss": 3.09,
        "bias": 0.29,
        "error_p90": 3.3,
        "n": 95271,
        "mae": 1.96,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 51.9
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.49,
        "bias": -0.18,
        "error_p90": 4.39,
        "n": 163119,
        "mae": 3.05,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 47.0
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.74,
        "bias": -0.09,
        "error_p90": 3.79,
        "n": 97350,
        "mae": 2.52,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 63.8
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.74,
      "std": 1.34
    },
    "bias": {
      "mean": -0.08,
      "std": 1.02
    },
    "error_p90": {
      "mean": 3.21,
      "std": 2.42
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
