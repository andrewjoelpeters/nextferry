# Backtest Report: exp22-q40-asymmetric

**Date:** 2026-03-22 23:36:20  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 22s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.35× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.09 min** (PL/MAE = 1.35×) |
| MAE | 2.29 min |
| Bias | -0.70 min |
| p90 (tail risk) | +2.07 min |
| 70% Interval Coverage | 70.0% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 56.5% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.4 | -0.34 | +2.71 |
| 1 | 6448 | 3224 | 3.86 | +0.26 | +3.21 |
| 2 | 9672 | 3224 | 3.16 | -1.60 | +1.17 |
| 3 | 12896 | 3224 | 2.51 | -0.90 | +1.27 |
| 4 | 16120 | 3228 | 2.5 | -0.92 | +1.23 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.09 | ±0.53 |
| Bias | -0.7 | ±0.62 |
| p90 | 1.92 | ±0.87 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 2.61 | -0.59 | +1.89 | 271623 |
| sea-bi | 3.58 | -0.83 | +2.27 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 2.55 | -0.47 | +1.86 | 76527 |
| Mon | 2.99 | -0.50 | +2.12 | 81477 |
| Sat | 3.13 | -0.64 | +2.25 | 74514 |
| Sun | 4.4 | -0.89 | +2.93 | 71412 |
| Thu | 2.64 | -0.78 | +1.70 | 75306 |
| Tue | 2.51 | -0.67 | +1.80 | 77385 |
| Wed | 3.48 | -0.99 | +2.12 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 3.89 | -0.63 | +3.20 | 28314 |
| Early (5–7) | 3.66 | -0.80 | +2.42 | 46827 |
| Evening (19–22) | 2.42 | -0.56 | +1.82 | 80355 |
| Midday (10–15) | 1.69 | -0.57 | +1.05 | 63030 |
| PM Peak (15–19) | 2.07 | -0.61 | +1.38 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.09 | -0.73 | +2.05 | 16124 |
| 4–6m | 3.09 | -0.73 | +2.05 | 16124 |
| 6–8m | 3.09 | -0.73 | +2.04 | 16124 |
| 8–10m | 3.09 | -0.72 | +2.05 | 16124 |
| 10–14m | 3.09 | -0.72 | +2.06 | 32248 |
| 14–20m | 3.09 | -0.72 | +2.06 | 48372 |
| 20–30m | 3.08 | -0.71 | +2.06 | 80620 |
| 30–45m | 3.09 | -0.70 | +2.07 | 128992 |
| 45–60m | 3.08 | -0.69 | +2.09 | 112868 |
| 60–90m | 3.08 | -0.68 | +2.09 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.97 | -0.65 | +2.19 | 176352 |
| ed-king (peak) | 1.96 | -0.48 | +1.48 | 95271 |
| sea-bi (off-peak) | 3.92 | -0.85 | +2.58 | 163119 |
| sea-bi (peak) | 3.02 | -0.78 | +1.91 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.09,
    "overall_bias": -0.7,
    "overall_error_p90": 2.07,
    "n_test_samples": 532092,
    "overall_mae": 2.29,
    "overall_coverage_70pct": 70.0,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 56.5,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.61,
        "bias": -0.59,
        "error_p90": 1.89,
        "n": 271623,
        "mae": 1.94,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 49.2
      },
      "sea-bi": {
        "pinball_loss": 3.58,
        "bias": -0.83,
        "error_p90": 2.27,
        "n": 260469,
        "mae": 2.66,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 60.9
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 4.4,
        "bias": -0.89,
        "error_p90": 2.93,
        "n": 71412,
        "mae": 3.23,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 58.8
      },
      "Mon": {
        "pinball_loss": 2.99,
        "bias": -0.5,
        "error_p90": 2.12,
        "n": 81477,
        "mae": 2.16,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 42.8
      },
      "Tue": {
        "pinball_loss": 2.51,
        "bias": -0.67,
        "error_p90": 1.8,
        "n": 77385,
        "mae": 1.9,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 56.0
      },
      "Wed": {
        "pinball_loss": 3.48,
        "bias": -0.99,
        "error_p90": 2.12,
        "n": 75471,
        "mae": 2.65,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 33.8
      },
      "Thu": {
        "pinball_loss": 2.64,
        "bias": -0.78,
        "error_p90": 1.7,
        "n": 75306,
        "mae": 2.02,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 52.6
      },
      "Fri": {
        "pinball_loss": 2.55,
        "bias": -0.47,
        "error_p90": 1.86,
        "n": 76527,
        "mae": 1.86,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 62.0
      },
      "Sat": {
        "pinball_loss": 3.13,
        "bias": -0.64,
        "error_p90": 2.25,
        "n": 74514,
        "mae": 2.3,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 71.7
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.66,
        "bias": -0.8,
        "error_p90": 2.42,
        "n": 46827,
        "mae": 2.71,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 29.1
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 3.89,
        "bias": -0.63,
        "error_p90": 3.2,
        "n": 28314,
        "mae": 2.8,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 29.4
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.69,
        "bias": -0.57,
        "error_p90": 1.05,
        "n": 63030,
        "mae": 1.31,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 66.0
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.07,
        "bias": -0.61,
        "error_p90": 1.38,
        "n": 112398,
        "mae": 1.58,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 78.2
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.42,
        "bias": -0.56,
        "error_p90": 1.82,
        "n": 80355,
        "mae": 1.8,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 70.9
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.09,
        "bias": -0.73,
        "error_p90": 2.05,
        "n": 16124,
        "mae": 2.31,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 58.2
      },
      "4\u20136m": {
        "pinball_loss": 3.09,
        "bias": -0.73,
        "error_p90": 2.05,
        "n": 16124,
        "mae": 2.3,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 58.2
      },
      "6\u20138m": {
        "pinball_loss": 3.09,
        "bias": -0.73,
        "error_p90": 2.04,
        "n": 16124,
        "mae": 2.3,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 58.1
      },
      "8\u201310m": {
        "pinball_loss": 3.09,
        "bias": -0.72,
        "error_p90": 2.05,
        "n": 16124,
        "mae": 2.3,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 58.2
      },
      "10\u201314m": {
        "pinball_loss": 3.09,
        "bias": -0.72,
        "error_p90": 2.06,
        "n": 32248,
        "mae": 2.3,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 58.1
      },
      "14\u201320m": {
        "pinball_loss": 3.09,
        "bias": -0.72,
        "error_p90": 2.06,
        "n": 48372,
        "mae": 2.3,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 57.6
      },
      "20\u201330m": {
        "pinball_loss": 3.08,
        "bias": -0.71,
        "error_p90": 2.06,
        "n": 80620,
        "mae": 2.29,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 57.0
      },
      "30\u201345m": {
        "pinball_loss": 3.09,
        "bias": -0.7,
        "error_p90": 2.07,
        "n": 128992,
        "mae": 2.29,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 55.6
      },
      "45\u201360m": {
        "pinball_loss": 3.08,
        "bias": -0.69,
        "error_p90": 2.09,
        "n": 112868,
        "mae": 2.29,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 56.5
      },
      "60\u201390m": {
        "pinball_loss": 3.08,
        "bias": -0.68,
        "error_p90": 2.09,
        "n": 32248,
        "mae": 2.28,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 56.3
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.97,
        "bias": -0.65,
        "error_p90": 2.19,
        "n": 176352,
        "mae": 2.19,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 33.2
      },
      "ed-king (peak)": {
        "pinball_loss": 1.96,
        "bias": -0.48,
        "error_p90": 1.48,
        "n": 95271,
        "mae": 1.46,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 69.5
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.92,
        "bias": -0.85,
        "error_p90": 2.58,
        "n": 163119,
        "mae": 2.89,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 53.8
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.02,
        "bias": -0.78,
        "error_p90": 1.91,
        "n": 97350,
        "mae": 2.27,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 70.7
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.09,
      "std": 0.53
    },
    "bias": {
      "mean": -0.7,
      "std": 0.62
    },
    "error_p90": {
      "mean": 1.92,
      "std": 0.87
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
