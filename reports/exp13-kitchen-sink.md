# Backtest Report: exp13-kitchen-sink

**Date:** 2026-03-22 23:11:53  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 24s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.45× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.4 min** (PL/MAE = 1.45×) |
| MAE | 2.34 min |
| Bias | -0.24 min |
| p90 (tail risk) | +2.68 min |
| 70% Interval Coverage | 60.4% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 52.2% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.77 | +0.18 | +3.39 |
| 1 | 6448 | 3224 | 4.45 | +0.77 | +3.80 |
| 2 | 9672 | 3224 | 3.31 | -1.16 | +1.59 |
| 3 | 12896 | 3224 | 2.76 | -0.46 | +1.69 |
| 4 | 16120 | 3228 | 2.69 | -0.52 | +1.63 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.4 | ±0.66 |
| Bias | -0.24 | ±0.66 |
| p90 | 2.42 | ±0.97 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 2.88 | -0.21 | +2.34 | 271623 |
| sea-bi | 3.94 | -0.27 | +3.13 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 2.86 | -0.10 | +2.45 | 76527 |
| Mon | 3.32 | -0.00 | +2.72 | 81477 |
| Sat | 3.39 | -0.15 | +2.82 | 74514 |
| Sun | 4.85 | -0.15 | +3.83 | 71412 |
| Thu | 2.94 | -0.39 | +2.16 | 75306 |
| Tue | 2.77 | -0.32 | +2.20 | 77385 |
| Wed | 3.75 | -0.56 | +2.79 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.31 | -0.05 | +4.19 | 28314 |
| Early (5–7) | 3.9 | -0.35 | +2.61 | 46827 |
| Evening (19–22) | 2.85 | -0.08 | +2.90 | 80355 |
| Midday (10–15) | 1.87 | -0.26 | +1.34 | 63030 |
| PM Peak (15–19) | 2.44 | -0.19 | +2.04 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.41 | -0.26 | +2.67 | 16124 |
| 4–6m | 3.4 | -0.26 | +2.66 | 16124 |
| 6–8m | 3.4 | -0.26 | +2.66 | 16124 |
| 8–10m | 3.4 | -0.25 | +2.67 | 16124 |
| 10–14m | 3.4 | -0.25 | +2.67 | 32248 |
| 14–20m | 3.4 | -0.25 | +2.67 | 48372 |
| 20–30m | 3.39 | -0.25 | +2.68 | 80620 |
| 30–45m | 3.39 | -0.24 | +2.68 | 128992 |
| 45–60m | 3.39 | -0.23 | +2.70 | 112868 |
| 60–90m | 3.39 | -0.22 | +2.70 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.16 | -0.28 | +2.45 | 176352 |
| ed-king (peak) | 2.35 | -0.08 | +2.13 | 95271 |
| sea-bi (off-peak) | 4.24 | -0.28 | +3.50 | 163119 |
| sea-bi (peak) | 3.42 | -0.24 | +2.67 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.4,
    "overall_bias": -0.24,
    "overall_error_p90": 2.68,
    "n_test_samples": 532092,
    "overall_mae": 2.34,
    "overall_coverage_70pct": 60.4,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 52.2,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.88,
        "bias": -0.21,
        "error_p90": 2.34,
        "n": 271623,
        "mae": 1.99,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 43.9
      },
      "sea-bi": {
        "pinball_loss": 3.94,
        "bias": -0.27,
        "error_p90": 3.13,
        "n": 260469,
        "mae": 2.71,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 57.0
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 4.85,
        "bias": -0.15,
        "error_p90": 3.83,
        "n": 71412,
        "mae": 3.29,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 54.6
      },
      "Mon": {
        "pinball_loss": 3.32,
        "bias": -0.0,
        "error_p90": 2.72,
        "n": 81477,
        "mae": 2.22,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 36.5
      },
      "Tue": {
        "pinball_loss": 2.77,
        "bias": -0.32,
        "error_p90": 2.2,
        "n": 77385,
        "mae": 1.96,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 51.5
      },
      "Wed": {
        "pinball_loss": 3.75,
        "bias": -0.56,
        "error_p90": 2.79,
        "n": 75471,
        "mae": 2.69,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 28.6
      },
      "Thu": {
        "pinball_loss": 2.94,
        "bias": -0.39,
        "error_p90": 2.16,
        "n": 75306,
        "mae": 2.09,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 47.2
      },
      "Fri": {
        "pinball_loss": 2.86,
        "bias": -0.1,
        "error_p90": 2.45,
        "n": 76527,
        "mae": 1.94,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 57.4
      },
      "Sat": {
        "pinball_loss": 3.39,
        "bias": -0.15,
        "error_p90": 2.82,
        "n": 74514,
        "mae": 2.31,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 69.3
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.9,
        "bias": -0.35,
        "error_p90": 2.61,
        "n": 46827,
        "mae": 2.71,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 24.5
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.31,
        "bias": -0.05,
        "error_p90": 4.19,
        "n": 28314,
        "mae": 2.89,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 21.7
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.87,
        "bias": -0.26,
        "error_p90": 1.34,
        "n": 63030,
        "mae": 1.33,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 62.4
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.44,
        "bias": -0.19,
        "error_p90": 2.04,
        "n": 112398,
        "mae": 1.69,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 74.3
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.85,
        "bias": -0.08,
        "error_p90": 2.9,
        "n": 80355,
        "mae": 1.93,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 65.8
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.41,
        "bias": -0.26,
        "error_p90": 2.67,
        "n": 16124,
        "mae": 2.36,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 53.9
      },
      "4\u20136m": {
        "pinball_loss": 3.4,
        "bias": -0.26,
        "error_p90": 2.66,
        "n": 16124,
        "mae": 2.35,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 54.0
      },
      "6\u20138m": {
        "pinball_loss": 3.4,
        "bias": -0.26,
        "error_p90": 2.66,
        "n": 16124,
        "mae": 2.35,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 53.9
      },
      "8\u201310m": {
        "pinball_loss": 3.4,
        "bias": -0.25,
        "error_p90": 2.67,
        "n": 16124,
        "mae": 2.35,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 54.0
      },
      "10\u201314m": {
        "pinball_loss": 3.4,
        "bias": -0.25,
        "error_p90": 2.67,
        "n": 32248,
        "mae": 2.35,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 53.9
      },
      "14\u201320m": {
        "pinball_loss": 3.4,
        "bias": -0.25,
        "error_p90": 2.67,
        "n": 48372,
        "mae": 2.35,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 53.4
      },
      "20\u201330m": {
        "pinball_loss": 3.39,
        "bias": -0.25,
        "error_p90": 2.68,
        "n": 80620,
        "mae": 2.34,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 52.6
      },
      "30\u201345m": {
        "pinball_loss": 3.39,
        "bias": -0.24,
        "error_p90": 2.68,
        "n": 128992,
        "mae": 2.34,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 51.3
      },
      "45\u201360m": {
        "pinball_loss": 3.39,
        "bias": -0.23,
        "error_p90": 2.7,
        "n": 112868,
        "mae": 2.34,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 52.1
      },
      "60\u201390m": {
        "pinball_loss": 3.39,
        "bias": -0.22,
        "error_p90": 2.7,
        "n": 32248,
        "mae": 2.33,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 51.9
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.16,
        "bias": -0.28,
        "error_p90": 2.45,
        "n": 176352,
        "mae": 2.2,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 28.9
      },
      "ed-king (peak)": {
        "pinball_loss": 2.35,
        "bias": -0.08,
        "error_p90": 2.13,
        "n": 95271,
        "mae": 1.59,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 63.4
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.24,
        "bias": -0.28,
        "error_p90": 3.5,
        "n": 163119,
        "mae": 2.92,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 50.0
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.42,
        "bias": -0.24,
        "error_p90": 2.67,
        "n": 97350,
        "mae": 2.36,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 66.9
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.4,
      "std": 0.66
    },
    "bias": {
      "mean": -0.24,
      "std": 0.66
    },
    "error_p90": {
      "mean": 2.42,
      "std": 0.97
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
