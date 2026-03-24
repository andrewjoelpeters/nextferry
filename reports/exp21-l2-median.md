# Backtest Report: exp21-l2-median

**Date:** 2026-03-22 23:33:36  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 1s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.64× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **4.85 min** (PL/MAE = 1.64×) |
| MAE | 2.96 min |
| Bias | +0.82 min |
| p90 (tail risk) | +5.05 min |
| 70% Interval Coverage | 70.0% (target: 70%) |
| Baseline Pinball Loss | 7.11 min |
| Improvement vs baseline | 31.8% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 4.4 | +0.57 | +3.99 |
| 1 | 6448 | 3224 | 8.75 | +3.35 | +10.95 |
| 2 | 9672 | 3224 | 3.76 | -0.63 | +2.33 |
| 3 | 12896 | 3224 | 3.69 | +0.38 | +2.99 |
| 4 | 16120 | 3228 | 3.63 | +0.41 | +3.05 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 4.85 | ±1.97 |
| Bias | 0.82 | ±1.34 |
| p90 | 4.66 | ±3.19 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 4.32 | +0.82 | +4.61 | 271623 |
| sea-bi | 5.39 | +0.81 | +5.68 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 4.35 | +0.99 | +4.53 | 76527 |
| Mon | 5.73 | +1.51 | +8.43 | 81477 |
| Sat | 4.17 | +0.66 | +4.22 | 74514 |
| Sun | 6.47 | +1.07 | +7.40 | 71412 |
| Thu | 4.13 | +0.45 | +3.90 | 75306 |
| Tue | 4.14 | +0.64 | +4.18 | 77385 |
| Wed | 4.95 | +0.35 | +4.58 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 5.49 | +0.70 | +6.52 | 28314 |
| Early (5–7) | 5.75 | +0.97 | +5.94 | 46827 |
| Evening (19–22) | 4.06 | +0.81 | +5.10 | 80355 |
| Midday (10–15) | 2.54 | +0.24 | +2.16 | 63030 |
| PM Peak (15–19) | 3.59 | +0.63 | +3.64 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 4.85 | +0.80 | +4.98 | 16124 |
| 4–6m | 4.85 | +0.80 | +5.00 | 16124 |
| 6–8m | 4.85 | +0.80 | +5.01 | 16124 |
| 8–10m | 4.85 | +0.80 | +5.01 | 16124 |
| 10–14m | 4.85 | +0.80 | +5.00 | 32248 |
| 14–20m | 4.84 | +0.81 | +5.01 | 48372 |
| 20–30m | 4.85 | +0.81 | +5.01 | 80620 |
| 30–45m | 4.84 | +0.81 | +5.03 | 128992 |
| 45–60m | 4.84 | +0.82 | +5.07 | 112868 |
| 60–90m | 4.85 | +0.84 | +5.12 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 4.64 | +0.81 | +4.92 | 176352 |
| ed-king (peak) | 3.73 | +0.85 | +4.09 | 95271 |
| sea-bi (off-peak) | 5.93 | +0.97 | +6.56 | 163119 |
| sea-bi (peak) | 4.49 | +0.53 | +4.41 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 4.85,
    "overall_bias": 0.82,
    "overall_error_p90": 5.05,
    "n_test_samples": 532092,
    "overall_mae": 2.96,
    "overall_coverage_70pct": 70.0,
    "overall_baseline_pinball_loss": 7.11,
    "overall_improvement_pct": 31.8,
    "by_route": {
      "ed-king": {
        "pinball_loss": 4.32,
        "bias": 0.82,
        "error_p90": 4.61,
        "n": 271623,
        "mae": 2.61,
        "baseline_pinball_loss": 5.14,
        "improvement_pct": 15.9
      },
      "sea-bi": {
        "pinball_loss": 5.39,
        "bias": 0.81,
        "error_p90": 5.68,
        "n": 260469,
        "mae": 3.33,
        "baseline_pinball_loss": 9.17,
        "improvement_pct": 41.2
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 6.47,
        "bias": 1.07,
        "error_p90": 7.4,
        "n": 71412,
        "mae": 3.96,
        "baseline_pinball_loss": 10.68,
        "improvement_pct": 39.4
      },
      "Mon": {
        "pinball_loss": 5.73,
        "bias": 1.51,
        "error_p90": 8.43,
        "n": 81477,
        "mae": 3.32,
        "baseline_pinball_loss": 5.23,
        "improvement_pct": -9.7
      },
      "Tue": {
        "pinball_loss": 4.14,
        "bias": 0.64,
        "error_p90": 4.18,
        "n": 77385,
        "mae": 2.55,
        "baseline_pinball_loss": 5.71,
        "improvement_pct": 27.5
      },
      "Wed": {
        "pinball_loss": 4.95,
        "bias": 0.35,
        "error_p90": 4.58,
        "n": 75471,
        "mae": 3.19,
        "baseline_pinball_loss": 5.25,
        "improvement_pct": 5.8
      },
      "Thu": {
        "pinball_loss": 4.13,
        "bias": 0.45,
        "error_p90": 3.9,
        "n": 75306,
        "mae": 2.61,
        "baseline_pinball_loss": 5.57,
        "improvement_pct": 25.9
      },
      "Fri": {
        "pinball_loss": 4.35,
        "bias": 0.99,
        "error_p90": 4.53,
        "n": 76527,
        "mae": 2.57,
        "baseline_pinball_loss": 6.71,
        "improvement_pct": 35.1
      },
      "Sat": {
        "pinball_loss": 4.17,
        "bias": 0.66,
        "error_p90": 4.22,
        "n": 74514,
        "mae": 2.56,
        "baseline_pinball_loss": 11.05,
        "improvement_pct": 62.3
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 5.75,
        "bias": 0.97,
        "error_p90": 5.94,
        "n": 46827,
        "mae": 3.51,
        "baseline_pinball_loss": 5.16,
        "improvement_pct": -11.4
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 5.49,
        "bias": 0.7,
        "error_p90": 6.52,
        "n": 28314,
        "mae": 3.43,
        "baseline_pinball_loss": 5.51,
        "improvement_pct": 0.3
      },
      "Midday (10\u201315)": {
        "pinball_loss": 2.54,
        "bias": 0.24,
        "error_p90": 2.16,
        "n": 63030,
        "mae": 1.61,
        "baseline_pinball_loss": 4.97,
        "improvement_pct": 48.9
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 3.59,
        "bias": 0.63,
        "error_p90": 3.64,
        "n": 112398,
        "mae": 2.19,
        "baseline_pinball_loss": 9.51,
        "improvement_pct": 62.2
      },
      "Evening (19\u201322)": {
        "pinball_loss": 4.06,
        "bias": 0.81,
        "error_p90": 5.1,
        "n": 80355,
        "mae": 2.44,
        "baseline_pinball_loss": 8.33,
        "improvement_pct": 51.2
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 4.85,
        "bias": 0.8,
        "error_p90": 4.98,
        "n": 16124,
        "mae": 2.97,
        "baseline_pinball_loss": 7.4,
        "improvement_pct": 34.4
      },
      "4\u20136m": {
        "pinball_loss": 4.85,
        "bias": 0.8,
        "error_p90": 5.0,
        "n": 16124,
        "mae": 2.97,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 34.4
      },
      "6\u20138m": {
        "pinball_loss": 4.85,
        "bias": 0.8,
        "error_p90": 5.01,
        "n": 16124,
        "mae": 2.97,
        "baseline_pinball_loss": 7.38,
        "improvement_pct": 34.3
      },
      "8\u201310m": {
        "pinball_loss": 4.85,
        "bias": 0.8,
        "error_p90": 5.01,
        "n": 16124,
        "mae": 2.97,
        "baseline_pinball_loss": 7.39,
        "improvement_pct": 34.4
      },
      "10\u201314m": {
        "pinball_loss": 4.85,
        "bias": 0.8,
        "error_p90": 5.0,
        "n": 32248,
        "mae": 2.96,
        "baseline_pinball_loss": 7.37,
        "improvement_pct": 34.2
      },
      "14\u201320m": {
        "pinball_loss": 4.84,
        "bias": 0.81,
        "error_p90": 5.01,
        "n": 48372,
        "mae": 2.96,
        "baseline_pinball_loss": 7.3,
        "improvement_pct": 33.7
      },
      "20\u201330m": {
        "pinball_loss": 4.85,
        "bias": 0.81,
        "error_p90": 5.01,
        "n": 80620,
        "mae": 2.96,
        "baseline_pinball_loss": 7.16,
        "improvement_pct": 32.2
      },
      "30\u201345m": {
        "pinball_loss": 4.84,
        "bias": 0.81,
        "error_p90": 5.03,
        "n": 128992,
        "mae": 2.96,
        "baseline_pinball_loss": 6.96,
        "improvement_pct": 30.4
      },
      "45\u201360m": {
        "pinball_loss": 4.84,
        "bias": 0.82,
        "error_p90": 5.07,
        "n": 112868,
        "mae": 2.95,
        "baseline_pinball_loss": 7.08,
        "improvement_pct": 31.7
      },
      "60\u201390m": {
        "pinball_loss": 4.85,
        "bias": 0.84,
        "error_p90": 5.12,
        "n": 32248,
        "mae": 2.95,
        "baseline_pinball_loss": 7.04,
        "improvement_pct": 31.1
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 4.64,
        "bias": 0.81,
        "error_p90": 4.92,
        "n": 176352,
        "mae": 2.82,
        "baseline_pinball_loss": 4.45,
        "improvement_pct": -4.4
      },
      "ed-king (peak)": {
        "pinball_loss": 3.73,
        "bias": 0.85,
        "error_p90": 4.09,
        "n": 95271,
        "mae": 2.2,
        "baseline_pinball_loss": 6.42,
        "improvement_pct": 41.9
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 5.93,
        "bias": 0.97,
        "error_p90": 6.56,
        "n": 163119,
        "mae": 3.63,
        "baseline_pinball_loss": 8.48,
        "improvement_pct": 30.0
      },
      "sea-bi (peak)": {
        "pinball_loss": 4.49,
        "bias": 0.53,
        "error_p90": 4.41,
        "n": 97350,
        "mae": 2.81,
        "baseline_pinball_loss": 10.32,
        "improvement_pct": 56.5
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 4.85,
      "std": 1.97
    },
    "bias": {
      "mean": 0.82,
      "std": 1.34
    },
    "error_p90": {
      "mean": 4.66,
      "std": 3.19
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
