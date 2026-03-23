# Backtest Report: exp11-shallow-many

**Date:** 2026-03-22 23:06:26  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 7s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.5× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.88 min** (PL/MAE = 1.5×) |
| MAE | 2.59 min |
| Bias | -0.01 min |
| p90 (tail risk) | +3.95 min |
| 70% Interval Coverage | 63.3% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 45.4% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.7 | +0.03 | +3.39 |
| 1 | 6448 | 3224 | 6.94 | +2.28 | +8.20 |
| 2 | 9672 | 3224 | 3.34 | -1.24 | +1.53 |
| 3 | 12896 | 3224 | 2.73 | -0.55 | +1.62 |
| 4 | 16120 | 3228 | 2.67 | -0.57 | +1.64 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.88 | ±1.58 |
| Bias | -0.01 | ±1.21 |
| p90 | 3.28 | ±2.56 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 3.38 | +0.04 | +3.51 | 271623 |
| sea-bi | 4.39 | -0.06 | +4.55 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 3.31 | +0.17 | +3.43 | 76527 |
| Mon | 3.87 | +0.16 | +5.20 | 81477 |
| Sat | 3.81 | +0.07 | +3.92 | 74514 |
| Sun | 5.34 | +0.01 | +6.54 | 71412 |
| Thu | 3.43 | -0.11 | +2.96 | 75306 |
| Tue | 3.24 | -0.04 | +3.06 | 77385 |
| Wed | 4.24 | -0.34 | +3.85 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.64 | +0.03 | +5.25 | 28314 |
| Early (5–7) | 4.19 | -0.30 | +3.87 | 46827 |
| Evening (19–22) | 3.98 | +0.53 | +6.81 | 80355 |
| Midday (10–15) | 1.85 | -0.30 | +1.33 | 63030 |
| PM Peak (15–19) | 2.93 | +0.06 | +2.47 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.88 | -0.04 | +3.90 | 16124 |
| 4–6m | 3.88 | -0.04 | +3.89 | 16124 |
| 6–8m | 3.88 | -0.04 | +3.90 | 16124 |
| 8–10m | 3.88 | -0.03 | +3.89 | 16124 |
| 10–14m | 3.88 | -0.03 | +3.89 | 32248 |
| 14–20m | 3.88 | -0.03 | +3.90 | 48372 |
| 20–30m | 3.87 | -0.02 | +3.93 | 80620 |
| 30–45m | 3.87 | -0.01 | +3.96 | 128992 |
| 45–60m | 3.88 | +0.00 | +3.98 | 112868 |
| 60–90m | 3.88 | +0.02 | +4.00 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 3.59 | -0.07 | +3.70 | 176352 |
| ed-king (peak) | 3.01 | +0.24 | +3.06 | 95271 |
| sea-bi (off-peak) | 4.69 | -0.08 | +4.91 | 163119 |
| sea-bi (peak) | 3.88 | -0.04 | +3.67 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.88,
    "overall_bias": -0.01,
    "overall_error_p90": 3.95,
    "n_test_samples": 532092,
    "overall_mae": 2.59,
    "overall_coverage_70pct": 63.3,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 45.4,
    "by_route": {
      "ed-king": {
        "pinball_loss": 3.38,
        "bias": 0.04,
        "error_p90": 3.51,
        "n": 271623,
        "mae": 2.24,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 34.2
      },
      "sea-bi": {
        "pinball_loss": 4.39,
        "bias": -0.06,
        "error_p90": 4.55,
        "n": 260469,
        "mae": 2.95,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 52.1
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 5.34,
        "bias": 0.01,
        "error_p90": 6.54,
        "n": 71412,
        "mae": 3.56,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 50.0
      },
      "Mon": {
        "pinball_loss": 3.87,
        "bias": 0.16,
        "error_p90": 5.2,
        "n": 81477,
        "mae": 2.53,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 25.9
      },
      "Tue": {
        "pinball_loss": 3.24,
        "bias": -0.04,
        "error_p90": 3.06,
        "n": 77385,
        "mae": 2.17,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 43.2
      },
      "Wed": {
        "pinball_loss": 4.24,
        "bias": -0.34,
        "error_p90": 3.85,
        "n": 75471,
        "mae": 2.94,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 19.3
      },
      "Thu": {
        "pinball_loss": 3.43,
        "bias": -0.11,
        "error_p90": 2.96,
        "n": 75306,
        "mae": 2.33,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 38.5
      },
      "Fri": {
        "pinball_loss": 3.31,
        "bias": 0.17,
        "error_p90": 3.43,
        "n": 76527,
        "mae": 2.15,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 50.6
      },
      "Sat": {
        "pinball_loss": 3.81,
        "bias": 0.07,
        "error_p90": 3.92,
        "n": 74514,
        "mae": 2.51,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 65.5
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 4.19,
        "bias": -0.3,
        "error_p90": 3.87,
        "n": 46827,
        "mae": 2.89,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 18.8
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.64,
        "bias": 0.03,
        "error_p90": 5.25,
        "n": 28314,
        "mae": 3.08,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 15.7
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.85,
        "bias": -0.3,
        "error_p90": 1.33,
        "n": 63030,
        "mae": 1.34,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 62.8
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.93,
        "bias": 0.06,
        "error_p90": 2.47,
        "n": 112398,
        "mae": 1.93,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 69.2
      },
      "Evening (19\u201322)": {
        "pinball_loss": 3.98,
        "bias": 0.53,
        "error_p90": 6.81,
        "n": 80355,
        "mae": 2.48,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 52.2
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.88,
        "bias": -0.04,
        "error_p90": 3.9,
        "n": 16124,
        "mae": 2.6,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 47.5
      },
      "4\u20136m": {
        "pinball_loss": 3.88,
        "bias": -0.04,
        "error_p90": 3.89,
        "n": 16124,
        "mae": 2.6,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 47.5
      },
      "6\u20138m": {
        "pinball_loss": 3.88,
        "bias": -0.04,
        "error_p90": 3.9,
        "n": 16124,
        "mae": 2.6,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 47.4
      },
      "8\u201310m": {
        "pinball_loss": 3.88,
        "bias": -0.03,
        "error_p90": 3.89,
        "n": 16124,
        "mae": 2.6,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 47.5
      },
      "10\u201314m": {
        "pinball_loss": 3.88,
        "bias": -0.03,
        "error_p90": 3.89,
        "n": 32248,
        "mae": 2.59,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 47.4
      },
      "14\u201320m": {
        "pinball_loss": 3.88,
        "bias": -0.03,
        "error_p90": 3.9,
        "n": 48372,
        "mae": 2.59,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 46.8
      },
      "20\u201330m": {
        "pinball_loss": 3.87,
        "bias": -0.02,
        "error_p90": 3.93,
        "n": 80620,
        "mae": 2.59,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 45.9
      },
      "30\u201345m": {
        "pinball_loss": 3.87,
        "bias": -0.01,
        "error_p90": 3.96,
        "n": 128992,
        "mae": 2.59,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 44.4
      },
      "45\u201360m": {
        "pinball_loss": 3.88,
        "bias": 0.0,
        "error_p90": 3.98,
        "n": 112868,
        "mae": 2.58,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 45.2
      },
      "60\u201390m": {
        "pinball_loss": 3.88,
        "bias": 0.02,
        "error_p90": 4.0,
        "n": 32248,
        "mae": 2.58,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 44.9
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 3.59,
        "bias": -0.07,
        "error_p90": 3.7,
        "n": 176352,
        "mae": 2.41,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 19.2
      },
      "ed-king (peak)": {
        "pinball_loss": 3.01,
        "bias": 0.24,
        "error_p90": 3.06,
        "n": 95271,
        "mae": 1.93,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 53.1
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.69,
        "bias": -0.08,
        "error_p90": 4.91,
        "n": 163119,
        "mae": 3.16,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 44.7
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.88,
        "bias": -0.04,
        "error_p90": 3.67,
        "n": 97350,
        "mae": 2.6,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 62.4
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.88,
      "std": 1.58
    },
    "bias": {
      "mean": -0.01,
      "std": 1.21
    },
    "error_p90": {
      "mean": 3.28,
      "std": 2.56
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
