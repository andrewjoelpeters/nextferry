# Backtest Report: exp18-minutes-since-midnight

**Date:** 2026-03-22 23:25:23  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 23s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.46× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.49 min** (PL/MAE = 1.46×) |
| MAE | 2.39 min |
| Bias | -0.18 min |
| p90 (tail risk) | +3.14 min |
| 70% Interval Coverage | 59.4% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 50.9% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.77 | +0.18 | +3.38 |
| 1 | 6448 | 3224 | 4.9 | +1.04 | +4.73 |
| 2 | 9672 | 3224 | 3.31 | -1.16 | +1.55 |
| 3 | 12896 | 3224 | 2.75 | -0.46 | +1.72 |
| 4 | 16120 | 3228 | 2.71 | -0.48 | +1.72 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.49 | ±0.81 |
| Bias | -0.18 | ±0.74 |
| p90 | 2.62 | ±1.25 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 2.99 | -0.13 | +2.80 | 271623 |
| sea-bi | 4.01 | -0.22 | +3.53 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 3.0 | -0.00 | +2.85 | 76527 |
| Mon | 3.5 | +0.08 | +3.49 | 81477 |
| Sat | 3.46 | -0.10 | +3.21 | 74514 |
| Sun | 4.99 | -0.06 | +4.45 | 71412 |
| Thu | 3.01 | -0.34 | +2.53 | 75306 |
| Tue | 2.81 | -0.29 | +2.32 | 77385 |
| Wed | 3.76 | -0.55 | +3.15 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.25 | -0.06 | +3.93 | 28314 |
| Early (5–7) | 4.1 | -0.18 | +3.21 | 46827 |
| Evening (19–22) | 3.15 | +0.07 | +3.77 | 80355 |
| Midday (10–15) | 1.82 | -0.30 | +1.30 | 63030 |
| PM Peak (15–19) | 2.6 | -0.11 | +2.37 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.49 | -0.20 | +3.09 | 16124 |
| 4–6m | 3.48 | -0.20 | +3.09 | 16124 |
| 6–8m | 3.48 | -0.20 | +3.09 | 16124 |
| 8–10m | 3.49 | -0.20 | +3.09 | 16124 |
| 10–14m | 3.49 | -0.20 | +3.10 | 32248 |
| 14–20m | 3.49 | -0.19 | +3.11 | 48372 |
| 20–30m | 3.48 | -0.19 | +3.12 | 80620 |
| 30–45m | 3.48 | -0.18 | +3.15 | 128992 |
| 45–60m | 3.49 | -0.17 | +3.17 | 112868 |
| 60–90m | 3.5 | -0.15 | +3.18 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.22 | -0.22 | +2.87 | 176352 |
| ed-king (peak) | 2.56 | +0.02 | +2.68 | 95271 |
| sea-bi (off-peak) | 4.3 | -0.25 | +3.84 | 163119 |
| sea-bi (peak) | 3.52 | -0.18 | +3.04 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.49,
    "overall_bias": -0.18,
    "overall_error_p90": 3.14,
    "n_test_samples": 532092,
    "overall_mae": 2.39,
    "overall_coverage_70pct": 59.4,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 50.9,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.99,
        "bias": -0.13,
        "error_p90": 2.8,
        "n": 271623,
        "mae": 2.04,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 41.8
      },
      "sea-bi": {
        "pinball_loss": 4.01,
        "bias": -0.22,
        "error_p90": 3.53,
        "n": 260469,
        "mae": 2.75,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 56.3
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 4.99,
        "bias": -0.06,
        "error_p90": 4.45,
        "n": 71412,
        "mae": 3.35,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 53.3
      },
      "Mon": {
        "pinball_loss": 3.5,
        "bias": 0.08,
        "error_p90": 3.49,
        "n": 81477,
        "mae": 2.31,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 33.0
      },
      "Tue": {
        "pinball_loss": 2.81,
        "bias": -0.29,
        "error_p90": 2.32,
        "n": 77385,
        "mae": 1.97,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 50.8
      },
      "Wed": {
        "pinball_loss": 3.76,
        "bias": -0.55,
        "error_p90": 3.15,
        "n": 75471,
        "mae": 2.69,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 28.4
      },
      "Thu": {
        "pinball_loss": 3.01,
        "bias": -0.34,
        "error_p90": 2.53,
        "n": 75306,
        "mae": 2.12,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 46.0
      },
      "Fri": {
        "pinball_loss": 3.0,
        "bias": -0.0,
        "error_p90": 2.85,
        "n": 76527,
        "mae": 2.0,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 55.3
      },
      "Sat": {
        "pinball_loss": 3.46,
        "bias": -0.1,
        "error_p90": 3.21,
        "n": 74514,
        "mae": 2.34,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 68.7
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 4.1,
        "bias": -0.18,
        "error_p90": 3.21,
        "n": 46827,
        "mae": 2.79,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 20.6
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.25,
        "bias": -0.06,
        "error_p90": 3.93,
        "n": 28314,
        "mae": 2.85,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 22.8
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.82,
        "bias": -0.3,
        "error_p90": 1.3,
        "n": 63030,
        "mae": 1.31,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 63.4
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.6,
        "bias": -0.11,
        "error_p90": 2.37,
        "n": 112398,
        "mae": 1.77,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 72.7
      },
      "Evening (19\u201322)": {
        "pinball_loss": 3.15,
        "bias": 0.07,
        "error_p90": 3.77,
        "n": 80355,
        "mae": 2.08,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 62.2
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.49,
        "bias": -0.2,
        "error_p90": 3.09,
        "n": 16124,
        "mae": 2.39,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 52.8
      },
      "4\u20136m": {
        "pinball_loss": 3.48,
        "bias": -0.2,
        "error_p90": 3.09,
        "n": 16124,
        "mae": 2.39,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 52.9
      },
      "6\u20138m": {
        "pinball_loss": 3.48,
        "bias": -0.2,
        "error_p90": 3.09,
        "n": 16124,
        "mae": 2.39,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 52.8
      },
      "8\u201310m": {
        "pinball_loss": 3.49,
        "bias": -0.2,
        "error_p90": 3.09,
        "n": 16124,
        "mae": 2.39,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 52.8
      },
      "10\u201314m": {
        "pinball_loss": 3.49,
        "bias": -0.2,
        "error_p90": 3.1,
        "n": 32248,
        "mae": 2.39,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 52.7
      },
      "14\u201320m": {
        "pinball_loss": 3.49,
        "bias": -0.19,
        "error_p90": 3.11,
        "n": 48372,
        "mae": 2.39,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 52.2
      },
      "20\u201330m": {
        "pinball_loss": 3.48,
        "bias": -0.19,
        "error_p90": 3.12,
        "n": 80620,
        "mae": 2.38,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 51.4
      },
      "30\u201345m": {
        "pinball_loss": 3.48,
        "bias": -0.18,
        "error_p90": 3.15,
        "n": 128992,
        "mae": 2.38,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 50.0
      },
      "45\u201360m": {
        "pinball_loss": 3.49,
        "bias": -0.17,
        "error_p90": 3.17,
        "n": 112868,
        "mae": 2.38,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 50.7
      },
      "60\u201390m": {
        "pinball_loss": 3.5,
        "bias": -0.15,
        "error_p90": 3.18,
        "n": 32248,
        "mae": 2.38,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 50.3
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.22,
        "bias": -0.22,
        "error_p90": 2.87,
        "n": 176352,
        "mae": 2.22,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 27.6
      },
      "ed-king (peak)": {
        "pinball_loss": 2.56,
        "bias": 0.02,
        "error_p90": 2.68,
        "n": 95271,
        "mae": 1.7,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 60.1
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.3,
        "bias": -0.25,
        "error_p90": 3.84,
        "n": 163119,
        "mae": 2.95,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 49.3
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.52,
        "bias": -0.18,
        "error_p90": 3.04,
        "n": 97350,
        "mae": 2.4,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 65.9
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.49,
      "std": 0.81
    },
    "bias": {
      "mean": -0.18,
      "std": 0.74
    },
    "error_p90": {
      "mean": 2.62,
      "std": 1.25
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
