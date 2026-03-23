# Backtest Report: exp10-very-slow

**Date:** 2026-03-22 23:04:09  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 4m 9s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.48× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.6 min** (PL/MAE = 1.48×) |
| MAE | 2.44 min |
| Bias | -0.12 min |
| p90 (tail risk) | +3.34 min |
| 70% Interval Coverage | 61.0% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 49.4% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.74 | +0.14 | +3.36 |
| 1 | 6448 | 3224 | 5.56 | +1.45 | +5.57 |
| 2 | 9672 | 3224 | 3.29 | -1.18 | +1.55 |
| 3 | 12896 | 3224 | 2.71 | -0.49 | +1.66 |
| 4 | 16120 | 3228 | 2.69 | -0.50 | +1.66 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.6 | ±1.06 |
| Bias | -0.12 | ±0.89 |
| p90 | 2.76 | ±1.56 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 3.13 | -0.07 | +2.96 | 271623 |
| sea-bi | 4.09 | -0.16 | +3.78 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 3.11 | +0.05 | +2.97 | 76527 |
| Mon | 3.62 | +0.16 | +3.84 | 81477 |
| Sat | 3.53 | -0.05 | +3.35 | 74514 |
| Sun | 5.1 | -0.01 | +4.94 | 71412 |
| Thu | 3.11 | -0.28 | +2.60 | 75306 |
| Tue | 2.89 | -0.22 | +2.50 | 77385 |
| Wed | 3.94 | -0.46 | +3.52 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.51 | +0.13 | +5.09 | 28314 |
| Early (5–7) | 4.02 | -0.27 | +3.34 | 46827 |
| Evening (19–22) | 3.3 | +0.17 | +4.24 | 80355 |
| Midday (10–15) | 1.93 | -0.21 | +1.56 | 63030 |
| PM Peak (15–19) | 2.77 | +0.02 | +2.68 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.61 | -0.14 | +3.34 | 16124 |
| 4–6m | 3.6 | -0.14 | +3.34 | 16124 |
| 6–8m | 3.6 | -0.14 | +3.34 | 16124 |
| 8–10m | 3.6 | -0.13 | +3.34 | 16124 |
| 10–14m | 3.6 | -0.13 | +3.34 | 32248 |
| 14–20m | 3.6 | -0.13 | +3.34 | 48372 |
| 20–30m | 3.59 | -0.13 | +3.34 | 80620 |
| 30–45m | 3.6 | -0.12 | +3.34 | 128992 |
| 45–60m | 3.6 | -0.10 | +3.35 | 112868 |
| 60–90m | 3.6 | -0.09 | +3.35 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.31 | -0.20 | +2.89 | 176352 |
| ed-king (peak) | 2.79 | +0.17 | +3.00 | 95271 |
| sea-bi (off-peak) | 4.36 | -0.22 | +4.10 | 163119 |
| sea-bi (peak) | 3.64 | -0.07 | +3.39 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.6,
    "overall_bias": -0.12,
    "overall_error_p90": 3.34,
    "n_test_samples": 532092,
    "overall_mae": 2.44,
    "overall_coverage_70pct": 61.0,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 49.4,
    "by_route": {
      "ed-king": {
        "pinball_loss": 3.13,
        "bias": -0.07,
        "error_p90": 2.96,
        "n": 271623,
        "mae": 2.11,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 39.1
      },
      "sea-bi": {
        "pinball_loss": 4.09,
        "bias": -0.16,
        "error_p90": 3.78,
        "n": 260469,
        "mae": 2.78,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 55.4
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 5.1,
        "bias": -0.01,
        "error_p90": 4.94,
        "n": 71412,
        "mae": 3.4,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 52.2
      },
      "Mon": {
        "pinball_loss": 3.62,
        "bias": 0.16,
        "error_p90": 3.84,
        "n": 81477,
        "mae": 2.36,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 30.7
      },
      "Tue": {
        "pinball_loss": 2.89,
        "bias": -0.22,
        "error_p90": 2.5,
        "n": 77385,
        "mae": 2.0,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 49.4
      },
      "Wed": {
        "pinball_loss": 3.94,
        "bias": -0.46,
        "error_p90": 3.52,
        "n": 75471,
        "mae": 2.78,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 25.0
      },
      "Thu": {
        "pinball_loss": 3.11,
        "bias": -0.28,
        "error_p90": 2.6,
        "n": 75306,
        "mae": 2.16,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 44.2
      },
      "Fri": {
        "pinball_loss": 3.11,
        "bias": 0.05,
        "error_p90": 2.97,
        "n": 76527,
        "mae": 2.06,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 53.6
      },
      "Sat": {
        "pinball_loss": 3.53,
        "bias": -0.05,
        "error_p90": 3.35,
        "n": 74514,
        "mae": 2.37,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 68.1
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 4.02,
        "bias": -0.27,
        "error_p90": 3.34,
        "n": 46827,
        "mae": 2.77,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 22.1
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.51,
        "bias": 0.13,
        "error_p90": 5.09,
        "n": 28314,
        "mae": 2.97,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 18.1
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.93,
        "bias": -0.21,
        "error_p90": 1.56,
        "n": 63030,
        "mae": 1.36,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 61.2
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.77,
        "bias": 0.02,
        "error_p90": 2.68,
        "n": 112398,
        "mae": 1.84,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 70.9
      },
      "Evening (19\u201322)": {
        "pinball_loss": 3.3,
        "bias": 0.17,
        "error_p90": 4.24,
        "n": 80355,
        "mae": 2.14,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 60.4
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.61,
        "bias": -0.14,
        "error_p90": 3.34,
        "n": 16124,
        "mae": 2.45,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 51.2
      },
      "4\u20136m": {
        "pinball_loss": 3.6,
        "bias": -0.14,
        "error_p90": 3.34,
        "n": 16124,
        "mae": 2.45,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 51.3
      },
      "6\u20138m": {
        "pinball_loss": 3.6,
        "bias": -0.14,
        "error_p90": 3.34,
        "n": 16124,
        "mae": 2.45,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 51.2
      },
      "8\u201310m": {
        "pinball_loss": 3.6,
        "bias": -0.13,
        "error_p90": 3.34,
        "n": 16124,
        "mae": 2.45,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 51.3
      },
      "10\u201314m": {
        "pinball_loss": 3.6,
        "bias": -0.13,
        "error_p90": 3.34,
        "n": 32248,
        "mae": 2.45,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 51.2
      },
      "14\u201320m": {
        "pinball_loss": 3.6,
        "bias": -0.13,
        "error_p90": 3.34,
        "n": 48372,
        "mae": 2.44,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 50.7
      },
      "20\u201330m": {
        "pinball_loss": 3.59,
        "bias": -0.13,
        "error_p90": 3.34,
        "n": 80620,
        "mae": 2.44,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 49.8
      },
      "30\u201345m": {
        "pinball_loss": 3.6,
        "bias": -0.12,
        "error_p90": 3.34,
        "n": 128992,
        "mae": 2.44,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 48.2
      },
      "45\u201360m": {
        "pinball_loss": 3.6,
        "bias": -0.1,
        "error_p90": 3.35,
        "n": 112868,
        "mae": 2.43,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 49.2
      },
      "60\u201390m": {
        "pinball_loss": 3.6,
        "bias": -0.09,
        "error_p90": 3.35,
        "n": 32248,
        "mae": 2.43,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 48.9
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.31,
        "bias": -0.2,
        "error_p90": 2.89,
        "n": 176352,
        "mae": 2.27,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 25.5
      },
      "ed-king (peak)": {
        "pinball_loss": 2.79,
        "bias": 0.17,
        "error_p90": 3.0,
        "n": 95271,
        "mae": 1.8,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 56.5
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.36,
        "bias": -0.22,
        "error_p90": 4.1,
        "n": 163119,
        "mae": 2.98,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 48.6
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.64,
        "bias": -0.07,
        "error_p90": 3.39,
        "n": 97350,
        "mae": 2.45,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 64.7
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.6,
      "std": 1.06
    },
    "bias": {
      "mean": -0.12,
      "std": 0.89
    },
    "error_p90": {
      "mean": 2.76,
      "std": 1.56
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
