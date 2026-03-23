# Backtest Report: exp06-drop-is-peak

**Date:** 2026-03-22 22:54:55  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 48.8s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.48× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.66 min** (PL/MAE = 1.48×) |
| MAE | 2.47 min |
| Bias | -0.09 min |
| p90 (tail risk) | +3.42 min |
| 70% Interval Coverage | 61.8% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 48.5% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.7 | +0.08 | +3.36 |
| 1 | 6448 | 3224 | 5.88 | +1.67 | +6.67 |
| 2 | 9672 | 3224 | 3.34 | -1.21 | +1.55 |
| 3 | 12896 | 3224 | 2.69 | -0.51 | +1.62 |
| 4 | 16120 | 3228 | 2.71 | -0.48 | +1.65 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.66 | ±1.17 |
| Bias | -0.09 | ±0.97 |
| p90 | 2.97 | ±1.97 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 3.16 | -0.06 | +2.84 | 271623 |
| sea-bi | 4.19 | -0.13 | +4.15 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 3.15 | +0.08 | +3.07 | 76527 |
| Mon | 3.68 | +0.13 | +3.84 | 81477 |
| Sat | 3.62 | +0.02 | +3.53 | 74514 |
| Sun | 5.1 | -0.04 | +5.43 | 71412 |
| Thu | 3.13 | -0.27 | +2.55 | 75306 |
| Tue | 3.01 | -0.16 | +2.51 | 77385 |
| Wed | 4.07 | -0.42 | +3.69 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.29 | -0.07 | +3.97 | 28314 |
| Early (5–7) | 3.94 | -0.37 | +2.90 | 46827 |
| Evening (19–22) | 3.57 | +0.33 | +5.24 | 80355 |
| Midday (10–15) | 1.88 | -0.25 | +1.40 | 63030 |
| PM Peak (15–19) | 2.78 | +0.00 | +2.44 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.67 | -0.11 | +3.36 | 16124 |
| 4–6m | 3.67 | -0.11 | +3.34 | 16124 |
| 6–8m | 3.67 | -0.11 | +3.36 | 16124 |
| 8–10m | 3.67 | -0.11 | +3.36 | 16124 |
| 10–14m | 3.67 | -0.11 | +3.38 | 32248 |
| 14–20m | 3.67 | -0.10 | +3.39 | 48372 |
| 20–30m | 3.66 | -0.10 | +3.40 | 80620 |
| 30–45m | 3.66 | -0.09 | +3.45 | 128992 |
| 45–60m | 3.66 | -0.08 | +3.47 | 112868 |
| 60–90m | 3.66 | -0.07 | +3.49 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.38 | -0.16 | +2.90 | 176352 |
| ed-king (peak) | 2.76 | +0.14 | +2.70 | 95271 |
| sea-bi (off-peak) | 4.5 | -0.14 | +4.43 | 163119 |
| sea-bi (peak) | 3.66 | -0.11 | +3.51 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.66,
    "overall_bias": -0.09,
    "overall_error_p90": 3.42,
    "n_test_samples": 532092,
    "overall_mae": 2.47,
    "overall_coverage_70pct": 61.8,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 48.5,
    "by_route": {
      "ed-king": {
        "pinball_loss": 3.16,
        "bias": -0.06,
        "error_p90": 2.84,
        "n": 271623,
        "mae": 2.13,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 38.5
      },
      "sea-bi": {
        "pinball_loss": 4.19,
        "bias": -0.13,
        "error_p90": 4.15,
        "n": 260469,
        "mae": 2.84,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 54.3
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 5.1,
        "bias": -0.04,
        "error_p90": 5.43,
        "n": 71412,
        "mae": 3.41,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 52.2
      },
      "Mon": {
        "pinball_loss": 3.68,
        "bias": 0.13,
        "error_p90": 3.84,
        "n": 81477,
        "mae": 2.41,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 29.6
      },
      "Tue": {
        "pinball_loss": 3.01,
        "bias": -0.16,
        "error_p90": 2.51,
        "n": 77385,
        "mae": 2.06,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 47.3
      },
      "Wed": {
        "pinball_loss": 4.07,
        "bias": -0.42,
        "error_p90": 3.69,
        "n": 75471,
        "mae": 2.85,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 22.5
      },
      "Thu": {
        "pinball_loss": 3.13,
        "bias": -0.27,
        "error_p90": 2.55,
        "n": 75306,
        "mae": 2.18,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 43.8
      },
      "Fri": {
        "pinball_loss": 3.15,
        "bias": 0.08,
        "error_p90": 3.07,
        "n": 76527,
        "mae": 2.07,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 53.0
      },
      "Sat": {
        "pinball_loss": 3.62,
        "bias": 0.02,
        "error_p90": 3.53,
        "n": 74514,
        "mae": 2.41,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 67.3
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.94,
        "bias": -0.37,
        "error_p90": 2.9,
        "n": 46827,
        "mae": 2.75,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 23.7
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.29,
        "bias": -0.07,
        "error_p90": 3.97,
        "n": 28314,
        "mae": 2.89,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 22.1
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.88,
        "bias": -0.25,
        "error_p90": 1.4,
        "n": 63030,
        "mae": 1.34,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 62.2
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.78,
        "bias": 0.0,
        "error_p90": 2.44,
        "n": 112398,
        "mae": 1.85,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 70.8
      },
      "Evening (19\u201322)": {
        "pinball_loss": 3.57,
        "bias": 0.33,
        "error_p90": 5.24,
        "n": 80355,
        "mae": 2.27,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 57.1
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.67,
        "bias": -0.11,
        "error_p90": 3.36,
        "n": 16124,
        "mae": 2.49,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 50.4
      },
      "4\u20136m": {
        "pinball_loss": 3.67,
        "bias": -0.11,
        "error_p90": 3.34,
        "n": 16124,
        "mae": 2.48,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 50.3
      },
      "6\u20138m": {
        "pinball_loss": 3.67,
        "bias": -0.11,
        "error_p90": 3.36,
        "n": 16124,
        "mae": 2.48,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 50.3
      },
      "8\u201310m": {
        "pinball_loss": 3.67,
        "bias": -0.11,
        "error_p90": 3.36,
        "n": 16124,
        "mae": 2.48,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 50.3
      },
      "10\u201314m": {
        "pinball_loss": 3.67,
        "bias": -0.11,
        "error_p90": 3.38,
        "n": 32248,
        "mae": 2.48,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 50.2
      },
      "14\u201320m": {
        "pinball_loss": 3.67,
        "bias": -0.1,
        "error_p90": 3.39,
        "n": 48372,
        "mae": 2.48,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 49.7
      },
      "20\u201330m": {
        "pinball_loss": 3.66,
        "bias": -0.1,
        "error_p90": 3.4,
        "n": 80620,
        "mae": 2.47,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 48.8
      },
      "30\u201345m": {
        "pinball_loss": 3.66,
        "bias": -0.09,
        "error_p90": 3.45,
        "n": 128992,
        "mae": 2.47,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 47.4
      },
      "45\u201360m": {
        "pinball_loss": 3.66,
        "bias": -0.08,
        "error_p90": 3.47,
        "n": 112868,
        "mae": 2.47,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 48.3
      },
      "60\u201390m": {
        "pinball_loss": 3.66,
        "bias": -0.07,
        "error_p90": 3.49,
        "n": 32248,
        "mae": 2.46,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 48.0
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.38,
        "bias": -0.16,
        "error_p90": 2.9,
        "n": 176352,
        "mae": 2.3,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 24.0
      },
      "ed-king (peak)": {
        "pinball_loss": 2.76,
        "bias": 0.14,
        "error_p90": 2.7,
        "n": 95271,
        "mae": 1.79,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 57.0
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.5,
        "bias": -0.14,
        "error_p90": 4.43,
        "n": 163119,
        "mae": 3.05,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 46.9
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.66,
        "bias": -0.11,
        "error_p90": 3.51,
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
      "mean": 3.66,
      "std": 1.17
    },
    "bias": {
      "mean": -0.09,
      "std": 0.97
    },
    "error_p90": {
      "mean": 2.97,
      "std": 1.97
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
