# Backtest Report: exp09-slow-and-deep

**Date:** 2026-03-22 22:59:50  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 30s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.46× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.48 min** (PL/MAE = 1.46×) |
| MAE | 2.38 min |
| Bias | -0.20 min |
| p90 (tail risk) | +3.10 min |
| 70% Interval Coverage | 60.6% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 51.1% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.76 | +0.15 | +3.38 |
| 1 | 6448 | 3224 | 4.84 | +1.04 | +4.55 |
| 2 | 9672 | 3224 | 3.31 | -1.21 | +1.54 |
| 3 | 12896 | 3224 | 2.76 | -0.48 | +1.67 |
| 4 | 16120 | 3228 | 2.7 | -0.49 | +1.69 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.47 | ±0.79 |
| Bias | -0.2 | ±0.75 |
| p90 | 2.57 | ±1.2 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 3.0 | -0.13 | +2.77 | 271623 |
| sea-bi | 3.97 | -0.26 | +3.51 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 2.97 | -0.04 | +2.70 | 76527 |
| Mon | 3.42 | +0.04 | +3.24 | 81477 |
| Sat | 3.46 | -0.10 | +3.08 | 74514 |
| Sun | 4.92 | -0.11 | +4.25 | 71412 |
| Thu | 2.94 | -0.38 | +2.37 | 75306 |
| Tue | 2.9 | -0.26 | +2.58 | 77385 |
| Wed | 3.82 | -0.53 | +3.26 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.32 | -0.04 | +4.13 | 28314 |
| Early (5–7) | 3.91 | -0.37 | +2.85 | 46827 |
| Evening (19–22) | 3.09 | +0.05 | +3.57 | 80355 |
| Midday (10–15) | 1.85 | -0.27 | +1.29 | 63030 |
| PM Peak (15–19) | 2.59 | -0.10 | +2.27 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.48 | -0.22 | +3.07 | 16124 |
| 4–6m | 3.47 | -0.22 | +3.06 | 16124 |
| 6–8m | 3.48 | -0.22 | +3.07 | 16124 |
| 8–10m | 3.48 | -0.22 | +3.07 | 16124 |
| 10–14m | 3.48 | -0.21 | +3.08 | 32248 |
| 14–20m | 3.48 | -0.21 | +3.08 | 48372 |
| 20–30m | 3.47 | -0.21 | +3.09 | 80620 |
| 30–45m | 3.47 | -0.20 | +3.11 | 128992 |
| 45–60m | 3.47 | -0.19 | +3.13 | 112868 |
| 60–90m | 3.47 | -0.17 | +3.15 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.24 | -0.22 | +2.83 | 176352 |
| ed-king (peak) | 2.55 | +0.04 | +2.66 | 95271 |
| sea-bi (off-peak) | 4.26 | -0.30 | +3.75 | 163119 |
| sea-bi (peak) | 3.49 | -0.20 | +3.13 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.48,
    "overall_bias": -0.2,
    "overall_error_p90": 3.1,
    "n_test_samples": 532092,
    "overall_mae": 2.38,
    "overall_coverage_70pct": 60.6,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 51.1,
    "by_route": {
      "ed-king": {
        "pinball_loss": 3.0,
        "bias": -0.13,
        "error_p90": 2.77,
        "n": 271623,
        "mae": 2.04,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 41.6
      },
      "sea-bi": {
        "pinball_loss": 3.97,
        "bias": -0.26,
        "error_p90": 3.51,
        "n": 260469,
        "mae": 2.74,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 56.7
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 4.92,
        "bias": -0.11,
        "error_p90": 4.25,
        "n": 71412,
        "mae": 3.32,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 53.9
      },
      "Mon": {
        "pinball_loss": 3.42,
        "bias": 0.04,
        "error_p90": 3.24,
        "n": 81477,
        "mae": 2.27,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 34.5
      },
      "Tue": {
        "pinball_loss": 2.9,
        "bias": -0.26,
        "error_p90": 2.58,
        "n": 77385,
        "mae": 2.02,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 49.2
      },
      "Wed": {
        "pinball_loss": 3.82,
        "bias": -0.53,
        "error_p90": 3.26,
        "n": 75471,
        "mae": 2.72,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 27.3
      },
      "Thu": {
        "pinball_loss": 2.94,
        "bias": -0.38,
        "error_p90": 2.37,
        "n": 75306,
        "mae": 2.09,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 47.2
      },
      "Fri": {
        "pinball_loss": 2.97,
        "bias": -0.04,
        "error_p90": 2.7,
        "n": 76527,
        "mae": 2.0,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 55.7
      },
      "Sat": {
        "pinball_loss": 3.46,
        "bias": -0.1,
        "error_p90": 3.08,
        "n": 74514,
        "mae": 2.34,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 68.7
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.91,
        "bias": -0.37,
        "error_p90": 2.85,
        "n": 46827,
        "mae": 2.73,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 24.3
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.32,
        "bias": -0.04,
        "error_p90": 4.13,
        "n": 28314,
        "mae": 2.89,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 21.6
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.85,
        "bias": -0.27,
        "error_p90": 1.29,
        "n": 63030,
        "mae": 1.33,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 62.8
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.59,
        "bias": -0.1,
        "error_p90": 2.27,
        "n": 112398,
        "mae": 1.76,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 72.8
      },
      "Evening (19\u201322)": {
        "pinball_loss": 3.09,
        "bias": 0.05,
        "error_p90": 3.57,
        "n": 80355,
        "mae": 2.04,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 62.9
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.48,
        "bias": -0.22,
        "error_p90": 3.07,
        "n": 16124,
        "mae": 2.39,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 52.9
      },
      "4\u20136m": {
        "pinball_loss": 3.47,
        "bias": -0.22,
        "error_p90": 3.06,
        "n": 16124,
        "mae": 2.39,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 53.0
      },
      "6\u20138m": {
        "pinball_loss": 3.48,
        "bias": -0.22,
        "error_p90": 3.07,
        "n": 16124,
        "mae": 2.39,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 52.8
      },
      "8\u201310m": {
        "pinball_loss": 3.48,
        "bias": -0.22,
        "error_p90": 3.07,
        "n": 16124,
        "mae": 2.39,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 52.9
      },
      "10\u201314m": {
        "pinball_loss": 3.48,
        "bias": -0.21,
        "error_p90": 3.08,
        "n": 32248,
        "mae": 2.39,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 52.8
      },
      "14\u201320m": {
        "pinball_loss": 3.48,
        "bias": -0.21,
        "error_p90": 3.08,
        "n": 48372,
        "mae": 2.39,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 52.3
      },
      "20\u201330m": {
        "pinball_loss": 3.47,
        "bias": -0.21,
        "error_p90": 3.09,
        "n": 80620,
        "mae": 2.38,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 51.5
      },
      "30\u201345m": {
        "pinball_loss": 3.47,
        "bias": -0.2,
        "error_p90": 3.11,
        "n": 128992,
        "mae": 2.38,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 50.1
      },
      "45\u201360m": {
        "pinball_loss": 3.47,
        "bias": -0.19,
        "error_p90": 3.13,
        "n": 112868,
        "mae": 2.38,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 51.0
      },
      "60\u201390m": {
        "pinball_loss": 3.47,
        "bias": -0.17,
        "error_p90": 3.15,
        "n": 32248,
        "mae": 2.37,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 50.7
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.24,
        "bias": -0.22,
        "error_p90": 2.83,
        "n": 176352,
        "mae": 2.24,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 27.1
      },
      "ed-king (peak)": {
        "pinball_loss": 2.55,
        "bias": 0.04,
        "error_p90": 2.66,
        "n": 95271,
        "mae": 1.69,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 60.3
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.26,
        "bias": -0.3,
        "error_p90": 3.75,
        "n": 163119,
        "mae": 2.94,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 49.7
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.49,
        "bias": -0.2,
        "error_p90": 3.13,
        "n": 97350,
        "mae": 2.39,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 66.2
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.47,
      "std": 0.79
    },
    "bias": {
      "mean": -0.2,
      "std": 0.75
    },
    "error_p90": {
      "mean": 2.57,
      "std": 1.2
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
