# Backtest Report: exp15-month

**Date:** 2026-03-22 23:17:07  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 16s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.45× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.49 min** (PL/MAE = 1.45×) |
| MAE | 2.41 min |
| Bias | -0.25 min |
| p90 (tail risk) | +3.03 min |
| 70% Interval Coverage | 60.0% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 50.9% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.58 | -0.09 | +3.10 |
| 1 | 6448 | 3224 | 4.73 | +0.87 | +4.91 |
| 2 | 9672 | 3224 | 3.27 | -1.29 | +1.50 |
| 3 | 12896 | 3224 | 3.09 | -0.26 | +1.90 |
| 4 | 16120 | 3228 | 2.79 | -0.49 | +1.81 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.49 | ±0.67 |
| Bias | -0.25 | ±0.7 |
| p90 | 2.64 | ±1.26 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 2.9 | -0.26 | +2.30 | 271623 |
| sea-bi | 4.11 | -0.25 | +3.77 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 2.97 | -0.10 | +2.64 | 76527 |
| Mon | 3.56 | +0.08 | +3.59 | 81477 |
| Sat | 3.46 | -0.25 | +2.89 | 74514 |
| Sun | 5.03 | -0.14 | +4.55 | 71412 |
| Thu | 3.0 | -0.37 | +2.30 | 75306 |
| Tue | 2.75 | -0.39 | +2.07 | 77385 |
| Wed | 3.77 | -0.62 | +3.03 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.41 | -0.04 | +4.20 | 28314 |
| Early (5–7) | 4.05 | -0.31 | +2.73 | 46827 |
| Evening (19–22) | 3.21 | +0.08 | +3.96 | 80355 |
| Midday (10–15) | 1.83 | -0.28 | +1.33 | 63030 |
| PM Peak (15–19) | 2.56 | -0.14 | +2.04 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.49 | -0.28 | +2.97 | 16124 |
| 4–6m | 3.48 | -0.28 | +2.96 | 16124 |
| 6–8m | 3.49 | -0.28 | +2.97 | 16124 |
| 8–10m | 3.49 | -0.28 | +2.98 | 16124 |
| 10–14m | 3.49 | -0.27 | +2.98 | 32248 |
| 14–20m | 3.49 | -0.27 | +3.01 | 48372 |
| 20–30m | 3.49 | -0.26 | +3.01 | 80620 |
| 30–45m | 3.49 | -0.25 | +3.02 | 128992 |
| 45–60m | 3.49 | -0.24 | +3.05 | 112868 |
| 60–90m | 3.5 | -0.23 | +3.07 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.13 | -0.38 | +2.36 | 176352 |
| ed-king (peak) | 2.47 | -0.03 | +2.18 | 95271 |
| sea-bi (off-peak) | 4.41 | -0.30 | +4.00 | 163119 |
| sea-bi (peak) | 3.6 | -0.16 | +3.23 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.49,
    "overall_bias": -0.25,
    "overall_error_p90": 3.03,
    "n_test_samples": 532092,
    "overall_mae": 2.41,
    "overall_coverage_70pct": 60.0,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 50.9,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.9,
        "bias": -0.26,
        "error_p90": 2.3,
        "n": 271623,
        "mae": 2.02,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 43.6
      },
      "sea-bi": {
        "pinball_loss": 4.11,
        "bias": -0.25,
        "error_p90": 3.77,
        "n": 260469,
        "mae": 2.82,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 55.2
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 5.03,
        "bias": -0.14,
        "error_p90": 4.55,
        "n": 71412,
        "mae": 3.4,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 52.9
      },
      "Mon": {
        "pinball_loss": 3.56,
        "bias": 0.08,
        "error_p90": 3.59,
        "n": 81477,
        "mae": 2.34,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 31.9
      },
      "Tue": {
        "pinball_loss": 2.75,
        "bias": -0.39,
        "error_p90": 2.07,
        "n": 77385,
        "mae": 1.96,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 51.8
      },
      "Wed": {
        "pinball_loss": 3.77,
        "bias": -0.62,
        "error_p90": 3.03,
        "n": 75471,
        "mae": 2.72,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 28.3
      },
      "Thu": {
        "pinball_loss": 3.0,
        "bias": -0.37,
        "error_p90": 2.3,
        "n": 75306,
        "mae": 2.12,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 46.2
      },
      "Fri": {
        "pinball_loss": 2.97,
        "bias": -0.1,
        "error_p90": 2.64,
        "n": 76527,
        "mae": 2.02,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 55.7
      },
      "Sat": {
        "pinball_loss": 3.46,
        "bias": -0.25,
        "error_p90": 2.89,
        "n": 74514,
        "mae": 2.39,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 68.7
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 4.05,
        "bias": -0.31,
        "error_p90": 2.73,
        "n": 46827,
        "mae": 2.8,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 21.6
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.41,
        "bias": -0.04,
        "error_p90": 4.2,
        "n": 28314,
        "mae": 2.95,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 19.9
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.83,
        "bias": -0.28,
        "error_p90": 1.33,
        "n": 63030,
        "mae": 1.31,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 63.2
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.56,
        "bias": -0.14,
        "error_p90": 2.04,
        "n": 112398,
        "mae": 1.75,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 73.1
      },
      "Evening (19\u201322)": {
        "pinball_loss": 3.21,
        "bias": 0.08,
        "error_p90": 3.96,
        "n": 80355,
        "mae": 2.11,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 61.4
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.49,
        "bias": -0.28,
        "error_p90": 2.97,
        "n": 16124,
        "mae": 2.42,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 52.8
      },
      "4\u20136m": {
        "pinball_loss": 3.48,
        "bias": -0.28,
        "error_p90": 2.96,
        "n": 16124,
        "mae": 2.42,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 52.9
      },
      "6\u20138m": {
        "pinball_loss": 3.49,
        "bias": -0.28,
        "error_p90": 2.97,
        "n": 16124,
        "mae": 2.42,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 52.7
      },
      "8\u201310m": {
        "pinball_loss": 3.49,
        "bias": -0.28,
        "error_p90": 2.98,
        "n": 16124,
        "mae": 2.42,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 52.8
      },
      "10\u201314m": {
        "pinball_loss": 3.49,
        "bias": -0.27,
        "error_p90": 2.98,
        "n": 32248,
        "mae": 2.42,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 52.7
      },
      "14\u201320m": {
        "pinball_loss": 3.49,
        "bias": -0.27,
        "error_p90": 3.01,
        "n": 48372,
        "mae": 2.42,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 52.2
      },
      "20\u201330m": {
        "pinball_loss": 3.49,
        "bias": -0.26,
        "error_p90": 3.01,
        "n": 80620,
        "mae": 2.41,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 51.2
      },
      "30\u201345m": {
        "pinball_loss": 3.49,
        "bias": -0.25,
        "error_p90": 3.02,
        "n": 128992,
        "mae": 2.41,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 49.8
      },
      "45\u201360m": {
        "pinball_loss": 3.49,
        "bias": -0.24,
        "error_p90": 3.05,
        "n": 112868,
        "mae": 2.41,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 50.7
      },
      "60\u201390m": {
        "pinball_loss": 3.5,
        "bias": -0.23,
        "error_p90": 3.07,
        "n": 32248,
        "mae": 2.41,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 50.3
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.13,
        "bias": -0.38,
        "error_p90": 2.36,
        "n": 176352,
        "mae": 2.21,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 29.6
      },
      "ed-king (peak)": {
        "pinball_loss": 2.47,
        "bias": -0.03,
        "error_p90": 2.18,
        "n": 95271,
        "mae": 1.66,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 61.5
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.41,
        "bias": -0.3,
        "error_p90": 4.0,
        "n": 163119,
        "mae": 3.04,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 48.0
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.6,
        "bias": -0.16,
        "error_p90": 3.23,
        "n": 97350,
        "mae": 2.45,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 65.1
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.49,
      "std": 0.67
    },
    "bias": {
      "mean": -0.25,
      "std": 0.7
    },
    "error_p90": {
      "mean": 2.64,
      "std": 1.26
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
