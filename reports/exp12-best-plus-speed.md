# Backtest Report: exp12-best-plus-speed

**Date:** 2026-03-22 23:09:13  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 32s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.43× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **3.3 min** (PL/MAE = 1.43×) |
| MAE | 2.31 min |
| Bias | -0.33 min |
| p90 (tail risk) | +2.34 min |
| 70% Interval Coverage | 59.9% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 53.6% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 3.76 | +0.13 | +3.39 |
| 1 | 6448 | 3224 | 3.95 | +0.39 | +3.18 |
| 2 | 9672 | 3224 | 3.33 | -1.17 | +1.57 |
| 3 | 12896 | 3224 | 2.75 | -0.48 | +1.66 |
| 4 | 16120 | 3228 | 2.69 | -0.52 | +1.64 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 3.3 | ±0.51 |
| Bias | -0.33 | ±0.55 |
| p90 | 2.29 | ±0.82 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 2.73 | -0.31 | +2.03 | 271623 |
| sea-bi | 3.88 | -0.35 | +2.85 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 2.79 | -0.18 | +2.23 | 76527 |
| Mon | 3.19 | -0.11 | +2.37 | 81477 |
| Sat | 3.38 | -0.20 | +2.59 | 74514 |
| Sun | 4.75 | -0.29 | +3.48 | 71412 |
| Thu | 2.77 | -0.49 | +1.93 | 75306 |
| Tue | 2.68 | -0.39 | +1.92 | 77385 |
| Wed | 3.61 | -0.66 | +2.39 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 4.29 | -0.02 | +4.29 | 28314 |
| Early (5–7) | 3.98 | -0.33 | +2.60 | 46827 |
| Evening (19–22) | 2.67 | -0.21 | +2.25 | 80355 |
| Midday (10–15) | 1.86 | -0.27 | +1.32 | 63030 |
| PM Peak (15–19) | 2.36 | -0.25 | +1.82 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.29 | -0.36 | +2.32 | 16124 |
| 4–6m | 3.29 | -0.36 | +2.31 | 16124 |
| 6–8m | 3.29 | -0.35 | +2.31 | 16124 |
| 8–10m | 3.3 | -0.35 | +2.32 | 16124 |
| 10–14m | 3.29 | -0.35 | +2.31 | 32248 |
| 14–20m | 3.3 | -0.34 | +2.32 | 48372 |
| 20–30m | 3.29 | -0.34 | +2.32 | 80620 |
| 30–45m | 3.29 | -0.33 | +2.33 | 128992 |
| 45–60m | 3.3 | -0.32 | +2.35 | 112868 |
| 60–90m | 3.29 | -0.31 | +2.36 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.99 | -0.40 | +2.12 | 176352 |
| ed-king (peak) | 2.25 | -0.15 | +1.86 | 95271 |
| sea-bi (off-peak) | 4.18 | -0.40 | +3.21 | 163119 |
| sea-bi (peak) | 3.38 | -0.28 | +2.40 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 3.3,
    "overall_bias": -0.33,
    "overall_error_p90": 2.34,
    "n_test_samples": 532092,
    "overall_mae": 2.31,
    "overall_coverage_70pct": 59.9,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 53.6,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.73,
        "bias": -0.31,
        "error_p90": 2.03,
        "n": 271623,
        "mae": 1.93,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 46.9
      },
      "sea-bi": {
        "pinball_loss": 3.88,
        "bias": -0.35,
        "error_p90": 2.85,
        "n": 260469,
        "mae": 2.7,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 57.7
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 4.75,
        "bias": -0.29,
        "error_p90": 3.48,
        "n": 71412,
        "mae": 3.26,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 55.5
      },
      "Mon": {
        "pinball_loss": 3.19,
        "bias": -0.11,
        "error_p90": 2.37,
        "n": 81477,
        "mae": 2.17,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": 39.0
      },
      "Tue": {
        "pinball_loss": 2.68,
        "bias": -0.39,
        "error_p90": 1.92,
        "n": 77385,
        "mae": 1.92,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 53.1
      },
      "Wed": {
        "pinball_loss": 3.61,
        "bias": -0.66,
        "error_p90": 2.39,
        "n": 75471,
        "mae": 2.63,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 31.3
      },
      "Thu": {
        "pinball_loss": 2.77,
        "bias": -0.49,
        "error_p90": 1.93,
        "n": 75306,
        "mae": 2.01,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 50.3
      },
      "Fri": {
        "pinball_loss": 2.79,
        "bias": -0.18,
        "error_p90": 2.23,
        "n": 76527,
        "mae": 1.92,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 58.4
      },
      "Sat": {
        "pinball_loss": 3.38,
        "bias": -0.2,
        "error_p90": 2.59,
        "n": 74514,
        "mae": 2.32,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 69.4
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.98,
        "bias": -0.33,
        "error_p90": 2.6,
        "n": 46827,
        "mae": 2.77,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": 22.9
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 4.29,
        "bias": -0.02,
        "error_p90": 4.29,
        "n": 28314,
        "mae": 2.87,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 22.1
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.86,
        "bias": -0.27,
        "error_p90": 1.32,
        "n": 63030,
        "mae": 1.33,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 62.6
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.36,
        "bias": -0.25,
        "error_p90": 1.82,
        "n": 112398,
        "mae": 1.65,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 75.2
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.67,
        "bias": -0.21,
        "error_p90": 2.25,
        "n": 80355,
        "mae": 1.85,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 67.9
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.29,
        "bias": -0.36,
        "error_p90": 2.32,
        "n": 16124,
        "mae": 2.32,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 55.5
      },
      "4\u20136m": {
        "pinball_loss": 3.29,
        "bias": -0.36,
        "error_p90": 2.31,
        "n": 16124,
        "mae": 2.31,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 55.5
      },
      "6\u20138m": {
        "pinball_loss": 3.29,
        "bias": -0.35,
        "error_p90": 2.31,
        "n": 16124,
        "mae": 2.31,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 55.4
      },
      "8\u201310m": {
        "pinball_loss": 3.3,
        "bias": -0.35,
        "error_p90": 2.32,
        "n": 16124,
        "mae": 2.31,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 55.3
      },
      "10\u201314m": {
        "pinball_loss": 3.29,
        "bias": -0.35,
        "error_p90": 2.31,
        "n": 32248,
        "mae": 2.31,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 55.4
      },
      "14\u201320m": {
        "pinball_loss": 3.3,
        "bias": -0.34,
        "error_p90": 2.32,
        "n": 48372,
        "mae": 2.31,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 54.8
      },
      "20\u201330m": {
        "pinball_loss": 3.29,
        "bias": -0.34,
        "error_p90": 2.32,
        "n": 80620,
        "mae": 2.31,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 54.0
      },
      "30\u201345m": {
        "pinball_loss": 3.29,
        "bias": -0.33,
        "error_p90": 2.33,
        "n": 128992,
        "mae": 2.3,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 52.7
      },
      "45\u201360m": {
        "pinball_loss": 3.3,
        "bias": -0.32,
        "error_p90": 2.35,
        "n": 112868,
        "mae": 2.3,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 53.4
      },
      "60\u201390m": {
        "pinball_loss": 3.29,
        "bias": -0.31,
        "error_p90": 2.36,
        "n": 32248,
        "mae": 2.3,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 53.3
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.99,
        "bias": -0.4,
        "error_p90": 2.12,
        "n": 176352,
        "mae": 2.13,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": 32.7
      },
      "ed-king (peak)": {
        "pinball_loss": 2.25,
        "bias": -0.15,
        "error_p90": 1.86,
        "n": 95271,
        "mae": 1.55,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 65.0
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 4.18,
        "bias": -0.4,
        "error_p90": 3.21,
        "n": 163119,
        "mae": 2.92,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 50.7
      },
      "sea-bi (peak)": {
        "pinball_loss": 3.38,
        "bias": -0.28,
        "error_p90": 2.4,
        "n": 97350,
        "mae": 2.34,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 67.3
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 3.3,
      "std": 0.51
    },
    "bias": {
      "mean": -0.33,
      "std": 0.55
    },
    "error_p90": {
      "mean": 2.29,
      "std": 0.82
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
