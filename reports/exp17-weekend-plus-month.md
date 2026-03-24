# Backtest Report: exp17-weekend-plus-month

**Date:** 2026-03-22 23:22:29  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 30s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.45× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.52 min** (PL/MAE = 1.45×) |
| MAE | 2.42 min |
| Bias | -0.22 min |
| p90 (tail risk) | +3.02 min |
| 70% Interval Coverage | 59.9% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 50.5% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.58 | -0.10 | +3.07 |
| 1 | 6448 | 3224 | 4.71 | +0.86 | +4.88 |
| 2 | 9672 | 3224 | 3.27 | -1.29 | +1.50 |
| 3 | 12896 | 3224 | 3.26 | -0.09 | +2.02 |
| 4 | 16120 | 3228 | 2.79 | -0.49 | +1.81 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.52 | ±0.65 |
| Bias | -0.22 | ±0.7 |
| p90 | 2.66 | ±1.23 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 2.92 | -0.23 | +2.34 | 271623 |
| sea-bi | 4.14 | -0.21 | +3.77 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 3.0 | -0.08 | +2.64 | 76527 |
| Mon | 3.57 | +0.11 | +3.57 | 81477 |
| Sat | 3.49 | -0.22 | +2.89 | 74514 |
| Sun | 5.13 | -0.05 | +4.63 | 71412 |
| Thu | 3.01 | -0.35 | +2.33 | 75306 |
| Tue | 2.77 | -0.37 | +2.12 | 77385 |
| Wed | 3.78 | -0.61 | +3.03 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.43 | -0.01 | +4.11 | 28314 |
| Early (5–7) | 4.08 | -0.27 | +2.74 | 46827 |
| Evening (19–22) | 3.27 | +0.13 | +3.96 | 80355 |
| Midday (10–15) | 1.85 | -0.26 | +1.33 | 63030 |
| PM Peak (15–19) | 2.57 | -0.13 | +2.04 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.52 | -0.25 | +2.96 | 16124 |
| 4–6m | 3.51 | -0.25 | +2.96 | 16124 |
| 6–8m | 3.52 | -0.25 | +2.97 | 16124 |
| 8–10m | 3.52 | -0.25 | +2.98 | 16124 |
| 10–14m | 3.52 | -0.24 | +2.98 | 32248 |
| 14–20m | 3.52 | -0.24 | +3.00 | 48372 |
| 20–30m | 3.52 | -0.23 | +3.02 | 80620 |
| 30–45m | 3.52 | -0.22 | +3.02 | 128992 |
| 45–60m | 3.52 | -0.21 | +3.04 | 112868 |
| 60–90m | 3.53 | -0.20 | +3.06 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.16 | -0.35 | +2.41 | 176352 |
| ed-king (peak) | 2.49 | -0.01 | +2.18 | 95271 |
| sea-bi (off-peak) | 4.45 | -0.26 | +4.00 | 163119 |
| sea-bi (peak) | 3.63 | -0.13 | +3.23 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.52,
    "overall_bias": -0.22,
    "overall_error_p90": 3.02,
    "n_test_samples": 532092,
    "overall_mae": 2.42,
    "overall_coverage_70pct": 59.9,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 50.5,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.92,
        "bias": -0.23,
        "error_p90": 2.34,
        "n": 271623,
        "mae": 2.03,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 43.2
      },
      "sea-bi": {
        "pinball_loss": 4.14,
        "bias": -0.21,
        "error_p90": 3.77,
        "n": 260469,
        "mae": 2.83,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 54.8
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 5.13,
        "bias": -0.05,
        "error_p90": 4.63,
        "n": 71412,
        "mae": 3.44,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 52.0
      },
      "Mon": {
        "pinball_loss": 3.57,
        "bias": 0.11,
        "error_p90": 3.57,
        "n": 81477,
        "mae": 2.35,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 31.7
      },
      "Tue": {
        "pinball_loss": 2.77,
        "bias": -0.37,
        "error_p90": 2.12,
        "n": 77385,
        "mae": 1.97,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 51.5
      },
      "Wed": {
        "pinball_loss": 3.78,
        "bias": -0.61,
        "error_p90": 3.03,
        "n": 75471,
        "mae": 2.72,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 28.1
      },
      "Thu": {
        "pinball_loss": 3.01,
        "bias": -0.35,
        "error_p90": 2.33,
        "n": 75306,
        "mae": 2.12,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 46.0
      },
      "Fri": {
        "pinball_loss": 3.0,
        "bias": -0.08,
        "error_p90": 2.64,
        "n": 76527,
        "mae": 2.03,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 55.3
      },
      "Sat": {
        "pinball_loss": 3.49,
        "bias": -0.22,
        "error_p90": 2.89,
        "n": 74514,
        "mae": 2.4,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 68.4
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 4.08,
        "bias": -0.27,
        "error_p90": 2.74,
        "n": 46827,
        "mae": 2.81,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 21.0
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.43,
        "bias": -0.01,
        "error_p90": 4.11,
        "n": 28314,
        "mae": 2.96,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 19.6
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.85,
        "bias": -0.26,
        "error_p90": 1.33,
        "n": 63030,
        "mae": 1.32,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 62.8
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.57,
        "bias": -0.13,
        "error_p90": 2.04,
        "n": 112398,
        "mae": 1.75,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 73.0
      },
      "Evening (19\u201322)": {
        "pinball_loss": 3.27,
        "bias": 0.13,
        "error_p90": 3.96,
        "n": 80355,
        "mae": 2.14,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 60.7
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.52,
        "bias": -0.25,
        "error_p90": 2.96,
        "n": 16124,
        "mae": 2.43,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 52.4
      },
      "4\u20136m": {
        "pinball_loss": 3.51,
        "bias": -0.25,
        "error_p90": 2.96,
        "n": 16124,
        "mae": 2.43,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 52.5
      },
      "6\u20138m": {
        "pinball_loss": 3.52,
        "bias": -0.25,
        "error_p90": 2.97,
        "n": 16124,
        "mae": 2.43,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 52.3
      },
      "8\u201310m": {
        "pinball_loss": 3.52,
        "bias": -0.25,
        "error_p90": 2.98,
        "n": 16124,
        "mae": 2.43,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 52.4
      },
      "10\u201314m": {
        "pinball_loss": 3.52,
        "bias": -0.24,
        "error_p90": 2.98,
        "n": 32248,
        "mae": 2.43,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 52.3
      },
      "14\u201320m": {
        "pinball_loss": 3.52,
        "bias": -0.24,
        "error_p90": 3.0,
        "n": 48372,
        "mae": 2.43,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 51.8
      },
      "20\u201330m": {
        "pinball_loss": 3.52,
        "bias": -0.23,
        "error_p90": 3.02,
        "n": 80620,
        "mae": 2.42,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 50.8
      },
      "30\u201345m": {
        "pinball_loss": 3.52,
        "bias": -0.22,
        "error_p90": 3.02,
        "n": 128992,
        "mae": 2.42,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 49.4
      },
      "45\u201360m": {
        "pinball_loss": 3.52,
        "bias": -0.21,
        "error_p90": 3.04,
        "n": 112868,
        "mae": 2.42,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 50.3
      },
      "60\u201390m": {
        "pinball_loss": 3.53,
        "bias": -0.2,
        "error_p90": 3.06,
        "n": 32248,
        "mae": 2.42,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 49.9
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.16,
        "bias": -0.35,
        "error_p90": 2.41,
        "n": 176352,
        "mae": 2.22,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 28.9
      },
      "ed-king (peak)": {
        "pinball_loss": 2.49,
        "bias": -0.01,
        "error_p90": 2.18,
        "n": 95271,
        "mae": 1.66,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 61.2
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.45,
        "bias": -0.26,
        "error_p90": 4.0,
        "n": 163119,
        "mae": 3.05,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 47.5
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.63,
        "bias": -0.13,
        "error_p90": 3.23,
        "n": 97350,
        "mae": 2.47,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 64.8
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.52,
      "std": 0.65
    },
    "bias": {
      "mean": -0.22,
      "std": 0.7
    },
    "error_p90": {
      "mean": 2.66,
      "std": 1.23
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
