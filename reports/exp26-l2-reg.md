# Backtest Report: exp26-l2-reg

**Date:** 2026-03-22 23:50:24  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 3m 26s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.25× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.79 min** (PL/MAE = 1.25×) |
| MAE | 2.24 min |
| Bias | -1.14 min |
| p90 (tail risk) | +1.37 min |
| 70% Interval Coverage | 70.0% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 60.8% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.23 | -0.69 | +2.28 |
| 1 | 6448 | 3224 | 2.69 | -0.74 | +1.67 |
| 2 | 9672 | 3224 | 3.13 | -1.86 | +0.95 |
| 3 | 12896 | 3224 | 2.42 | -1.20 | +1.04 |
| 4 | 16120 | 3228 | 2.45 | -1.21 | +1.02 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.78 | ±0.34 |
| Bias | -1.14 | ±0.42 |
| p90 | 1.39 | ±0.51 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 2.24 | -1.00 | +1.11 | 271623 |
| sea-bi | 3.35 | -1.29 | +1.72 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 2.3 | -0.83 | +1.30 | 76527 |
| Mon | 2.64 | -0.99 | +1.31 | 81477 |
| Sat | 2.92 | -1.06 | +1.55 | 74514 |
| Sun | 4.04 | -1.58 | +1.89 | 71412 |
| Thu | 2.39 | -1.10 | +1.14 | 75306 |
| Tue | 2.2 | -1.05 | +1.05 | 77385 |
| Wed | 3.11 | -1.41 | +1.42 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 3.48 | -1.24 | +1.98 | 28314 |
| Early (5–7) | 3.15 | -1.43 | +1.33 | 46827 |
| Evening (19–22) | 2.21 | -0.90 | +1.30 | 80355 |
| Midday (10–15) | 1.6 | -0.77 | +0.81 | 63030 |
| PM Peak (15–19) | 1.95 | -0.85 | +1.05 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 2.8 | -1.16 | +1.35 | 16124 |
| 4–6m | 2.8 | -1.16 | +1.35 | 16124 |
| 6–8m | 2.8 | -1.16 | +1.36 | 16124 |
| 8–10m | 2.8 | -1.16 | +1.36 | 16124 |
| 10–14m | 2.8 | -1.15 | +1.36 | 32248 |
| 14–20m | 2.79 | -1.15 | +1.36 | 48372 |
| 20–30m | 2.79 | -1.15 | +1.37 | 80620 |
| 30–45m | 2.78 | -1.14 | +1.37 | 128992 |
| 45–60m | 2.78 | -1.13 | +1.39 | 112868 |
| 60–90m | 2.77 | -1.12 | +1.38 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.53 | -1.13 | +1.20 | 176352 |
| ed-king (peak) | 1.72 | -0.74 | +0.99 | 95271 |
| sea-bi (off-peak) | 3.66 | -1.35 | +1.93 | 163119 |
| sea-bi (peak) | 2.82 | -1.20 | +1.45 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.79,
    "overall_bias": -1.14,
    "overall_error_p90": 1.37,
    "n_test_samples": 532092,
    "overall_mae": 2.24,
    "overall_coverage_70pct": 70.0,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 60.8,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.24,
        "bias": -1.0,
        "error_p90": 1.11,
        "n": 271623,
        "mae": 1.83,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 56.4
      },
      "sea-bi": {
        "pinball_loss": 3.35,
        "bias": -1.29,
        "error_p90": 1.72,
        "n": 260469,
        "mae": 2.66,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 63.5
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 4.04,
        "bias": -1.58,
        "error_p90": 1.89,
        "n": 71412,
        "mae": 3.22,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 62.2
      },
      "Mon": {
        "pinball_loss": 2.64,
        "bias": -0.99,
        "error_p90": 1.31,
        "n": 81477,
        "mae": 2.09,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 49.5
      },
      "Tue": {
        "pinball_loss": 2.2,
        "bias": -1.05,
        "error_p90": 1.05,
        "n": 77385,
        "mae": 1.82,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 61.5
      },
      "Wed": {
        "pinball_loss": 3.11,
        "bias": -1.41,
        "error_p90": 1.42,
        "n": 75471,
        "mae": 2.54,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 40.8
      },
      "Thu": {
        "pinball_loss": 2.39,
        "bias": -1.1,
        "error_p90": 1.14,
        "n": 75306,
        "mae": 1.96,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 57.1
      },
      "Fri": {
        "pinball_loss": 2.3,
        "bias": -0.83,
        "error_p90": 1.3,
        "n": 76527,
        "mae": 1.81,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 65.7
      },
      "Sat": {
        "pinball_loss": 2.92,
        "bias": -1.06,
        "error_p90": 1.55,
        "n": 74514,
        "mae": 2.3,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 73.6
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.15,
        "bias": -1.43,
        "error_p90": 1.33,
        "n": 46827,
        "mae": 2.58,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 39.0
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 3.48,
        "bias": -1.24,
        "error_p90": 1.98,
        "n": 28314,
        "mae": 2.73,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 36.8
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.6,
        "bias": -0.77,
        "error_p90": 0.81,
        "n": 63030,
        "mae": 1.32,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 67.8
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 1.95,
        "bias": -0.85,
        "error_p90": 1.05,
        "n": 112398,
        "mae": 1.58,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 79.5
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.21,
        "bias": -0.9,
        "error_p90": 1.3,
        "n": 80355,
        "mae": 1.77,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 73.5
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 2.8,
        "bias": -1.16,
        "error_p90": 1.35,
        "n": 16124,
        "mae": 2.25,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 62.1
      },
      "4\u20136m": {
        "pinball_loss": 2.8,
        "bias": -1.16,
        "error_p90": 1.35,
        "n": 16124,
        "mae": 2.25,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 62.1
      },
      "6\u20138m": {
        "pinball_loss": 2.8,
        "bias": -1.16,
        "error_p90": 1.36,
        "n": 16124,
        "mae": 2.25,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 62.1
      },
      "8\u201310m": {
        "pinball_loss": 2.8,
        "bias": -1.16,
        "error_p90": 1.36,
        "n": 16124,
        "mae": 2.25,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 62.1
      },
      "10\u201314m": {
        "pinball_loss": 2.8,
        "bias": -1.15,
        "error_p90": 1.36,
        "n": 32248,
        "mae": 2.25,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 62.0
      },
      "14\u201320m": {
        "pinball_loss": 2.79,
        "bias": -1.15,
        "error_p90": 1.36,
        "n": 48372,
        "mae": 2.25,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 61.8
      },
      "20\u201330m": {
        "pinball_loss": 2.79,
        "bias": -1.15,
        "error_p90": 1.37,
        "n": 80620,
        "mae": 2.24,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 61.0
      },
      "30\u201345m": {
        "pinball_loss": 2.78,
        "bias": -1.14,
        "error_p90": 1.37,
        "n": 128992,
        "mae": 2.24,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 60.0
      },
      "45\u201360m": {
        "pinball_loss": 2.78,
        "bias": -1.13,
        "error_p90": 1.39,
        "n": 112868,
        "mae": 2.23,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 60.8
      },
      "60\u201390m": {
        "pinball_loss": 2.77,
        "bias": -1.12,
        "error_p90": 1.38,
        "n": 32248,
        "mae": 2.22,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 60.7
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.53,
        "bias": -1.13,
        "error_p90": 1.2,
        "n": 176352,
        "mae": 2.06,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 43.1
      },
      "ed-king (peak)": {
        "pinball_loss": 1.72,
        "bias": -0.74,
        "error_p90": 0.99,
        "n": 95271,
        "mae": 1.4,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 73.2
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.66,
        "bias": -1.35,
        "error_p90": 1.93,
        "n": 163119,
        "mae": 2.89,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 56.8
      },
      "sea-bi (peak)": {
        "pinball_loss": 2.82,
        "bias": -1.2,
        "error_p90": 1.45,
        "n": 97350,
        "mae": 2.28,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 72.7
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 2.78,
      "std": 0.34
    },
    "bias": {
      "mean": -1.14,
      "std": 0.42
    },
    "error_p90": {
      "mean": 1.39,
      "std": 0.51
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
