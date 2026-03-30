# Backtest Report: exp42-drop-speed

> Ablation: drop vessel_speed

**Date:** 2026-03-29 23:26:44  
**Sailing events:** 19348  
**Walk-forward folds:** 5  
**Training time:** 2m 22s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.2× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.44 min** (PL/MAE = 1.2×) |
| MAE | 2.04 min |
| Bias | -1.25 min |
| p90 (tail risk) | +1.06 min |
| 70% Interval Coverage | 70.2% (target: 70%) |
| Interval Width (mean) | 4.86 min |
| Interval Width (median) | 3.5 min |
| Baseline Pinball Loss | 4.39 min |
| Improvement vs baseline | 44.4% |

## Comparison vs Previous Run

| Metric | Previous | Current | Delta |
|--------|----------|---------|-------|
| Pinball Loss | 2.48 min | 2.44 min | -0.04 (better) |
| MAE | 1.97 min | 2.04 min | +0.07 (worse) |
| p90 | 1.33 min | 1.06 min | -0.27 (better) |
| Coverage | 70.0% | 70.2% | +0.20 (better) |
| Interval Width | 4.81 min | 4.86 min | +0.05 (worse) |
| Improvement % | 43.5% | 44.4% | +0.90 (better) |

### Per-Route Comparison

| Route | Prev PL | Curr PL | Prev p90 | Curr p90 | PL Delta |
|-------|---------|---------|----------|----------|----------|
| ed-king | 2.09 | 2.04 | +1.09 | +0.86 | -0.05 (better) |
| sea-bi | 2.9 | 2.86 | +1.65 | +1.33 | -0.04 (better) |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3224 | 3224 | 2.88 | -1.12 | +1.58 |
| 1 | 6448 | 3224 | 2.09 | -0.93 | +1.11 |
| 2 | 9672 | 3224 | 2.87 | -1.78 | +0.90 |
| 3 | 12896 | 3224 | 2.24 | -1.25 | +0.89 |
| 4 | 16120 | 3228 | 2.12 | -1.18 | +0.81 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.44 | ±0.36 |
| Bias | -1.25 | ±0.28 |
| p90 | 1.06 | ±0.28 |

## By Route

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ed-king | 2.04 | -1.13 | +0.86 | 4.17 | 271623 |
| sea-bi | 2.86 | -1.38 | +1.33 | 5.57 | 260469 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| Fri | 2.2 | -0.91 | +1.14 | 4.32 | 76527 |
| Mon | 2.17 | -1.07 | +0.93 | 4.82 | 81477 |
| Sat | 2.36 | -1.10 | +1.15 | 5.06 | 74514 |
| Sun | 3.35 | -1.67 | +1.48 | 6.48 | 71412 |
| Thu | 2.28 | -1.25 | +0.95 | 4.28 | 75306 |
| Tue | 1.95 | -1.17 | +0.77 | 4.3 | 77385 |
| Wed | 2.87 | -1.65 | +1.07 | 4.85 | 75471 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 2.68 | -1.31 | +1.00 | 28314 |
| Early (5–7) | 2.68 | -1.71 | +0.86 | 46827 |
| Evening (19–22) | 2.0 | -0.95 | +1.00 | 80355 |
| Midday (10–15) | 1.51 | -0.89 | +0.68 | 63030 |
| PM Peak (15–19) | 1.88 | -0.93 | +0.95 | 112398 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 2.36 | -1.15 | +1.07 | 16124 |
| 4–6m | 2.36 | -1.16 | +1.07 | 16124 |
| 6–8m | 2.36 | -1.17 | +1.07 | 16124 |
| 8–10m | 2.36 | -1.17 | +1.07 | 16124 |
| 10–14m | 2.37 | -1.18 | +1.07 | 32248 |
| 14–20m | 2.38 | -1.20 | +1.07 | 48372 |
| 20–30m | 2.41 | -1.21 | +1.07 | 80620 |
| 30–45m | 2.44 | -1.27 | +1.06 | 128992 |
| 45–60m | 2.48 | -1.30 | +1.05 | 112868 |
| 60–90m | 2.51 | -1.32 | +1.06 | 32248 |

## Route x Peak vs Off-Peak

| Route (period) | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king (off-peak) | 2.24 | -1.27 | +0.91 | 176352 |
| ed-king (peak) | 1.65 | -0.87 | +0.80 | 95271 |
| sea-bi (off-peak) | 3.13 | -1.46 | +1.50 | 163119 |
| sea-bi (peak) | 2.42 | -1.26 | +1.10 | 97350 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.44,
    "overall_bias": -1.25,
    "overall_error_p90": 1.06,
    "n_test_samples": 532092,
    "overall_mae": 2.04,
    "overall_coverage_70pct": 70.2,
    "overall_mean_interval_width": 4.86,
    "overall_median_interval_width": 3.5,
    "overall_baseline_pinball_loss": 4.39,
    "overall_improvement_pct": 44.4,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.04,
        "bias": -1.13,
        "error_p90": 0.86,
        "n": 271623,
        "mae": 1.73,
        "mean_interval_width": 4.17,
        "median_interval_width": 3.18,
        "baseline_pinball_loss": 3.77,
        "improvement_pct": 45.9
      },
      "sea-bi": {
        "pinball_loss": 2.86,
        "bias": -1.38,
        "error_p90": 1.33,
        "n": 260469,
        "mae": 2.37,
        "mean_interval_width": 5.57,
        "median_interval_width": 3.99,
        "baseline_pinball_loss": 5.03,
        "improvement_pct": 43.2
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 3.35,
        "bias": -1.67,
        "error_p90": 1.48,
        "n": 71412,
        "mae": 2.79,
        "mean_interval_width": 6.48,
        "median_interval_width": 4.17,
        "baseline_pinball_loss": 6.0,
        "improvement_pct": 44.2
      },
      "Mon": {
        "pinball_loss": 2.17,
        "bias": -1.07,
        "error_p90": 0.93,
        "n": 81477,
        "mae": 1.8,
        "mean_interval_width": 4.82,
        "median_interval_width": 3.13,
        "baseline_pinball_loss": 4.21,
        "improvement_pct": 48.5
      },
      "Tue": {
        "pinball_loss": 1.95,
        "bias": -1.17,
        "error_p90": 0.77,
        "n": 77385,
        "mae": 1.69,
        "mean_interval_width": 4.3,
        "median_interval_width": 3.36,
        "baseline_pinball_loss": 3.28,
        "improvement_pct": 40.5
      },
      "Wed": {
        "pinball_loss": 2.87,
        "bias": -1.65,
        "error_p90": 1.07,
        "n": 75471,
        "mae": 2.46,
        "mean_interval_width": 4.85,
        "median_interval_width": 3.73,
        "baseline_pinball_loss": 5.6,
        "improvement_pct": 48.7
      },
      "Thu": {
        "pinball_loss": 2.28,
        "bias": -1.25,
        "error_p90": 0.95,
        "n": 75306,
        "mae": 1.94,
        "mean_interval_width": 4.28,
        "median_interval_width": 3.21,
        "baseline_pinball_loss": 3.48,
        "improvement_pct": 34.5
      },
      "Fri": {
        "pinball_loss": 2.2,
        "bias": -0.91,
        "error_p90": 1.14,
        "n": 76527,
        "mae": 1.77,
        "mean_interval_width": 4.32,
        "median_interval_width": 3.39,
        "baseline_pinball_loss": 4.26,
        "improvement_pct": 48.3
      },
      "Sat": {
        "pinball_loss": 2.36,
        "bias": -1.1,
        "error_p90": 1.15,
        "n": 74514,
        "mae": 1.94,
        "mean_interval_width": 5.06,
        "median_interval_width": 3.87,
        "baseline_pinball_loss": 4.03,
        "improvement_pct": 41.4
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 2.68,
        "bias": -1.71,
        "error_p90": 0.86,
        "n": 46827,
        "mae": 2.36,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 36.6
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 2.68,
        "bias": -1.31,
        "error_p90": 1.0,
        "n": 28314,
        "mae": 2.22,
        "baseline_pinball_loss": 5.63,
        "improvement_pct": 52.4
      },
      "Midday (10\u201315)": {
        "pinball_loss": 1.51,
        "bias": -0.89,
        "error_p90": 0.68,
        "n": 63030,
        "mae": 1.31,
        "baseline_pinball_loss": 4.83,
        "improvement_pct": 68.7
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 1.88,
        "bias": -0.93,
        "error_p90": 0.95,
        "n": 112398,
        "mae": 1.56,
        "baseline_pinball_loss": 3.49,
        "improvement_pct": 46.2
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.0,
        "bias": -0.95,
        "error_p90": 1.0,
        "n": 80355,
        "mae": 1.65,
        "baseline_pinball_loss": 2.94,
        "improvement_pct": 32.0
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 2.36,
        "bias": -1.15,
        "error_p90": 1.07,
        "n": 16124,
        "mae": 1.95,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 39.9
      },
      "4\u20136m": {
        "pinball_loss": 2.36,
        "bias": -1.16,
        "error_p90": 1.07,
        "n": 16124,
        "mae": 1.96,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 40.0
      },
      "6\u20138m": {
        "pinball_loss": 2.36,
        "bias": -1.17,
        "error_p90": 1.07,
        "n": 16124,
        "mae": 1.96,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 39.9
      },
      "8\u201310m": {
        "pinball_loss": 2.36,
        "bias": -1.17,
        "error_p90": 1.07,
        "n": 16124,
        "mae": 1.97,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 40.0
      },
      "10\u201314m": {
        "pinball_loss": 2.37,
        "bias": -1.18,
        "error_p90": 1.07,
        "n": 32248,
        "mae": 1.97,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 39.7
      },
      "14\u201320m": {
        "pinball_loss": 2.38,
        "bias": -1.2,
        "error_p90": 1.07,
        "n": 48372,
        "mae": 1.99,
        "baseline_pinball_loss": 3.93,
        "improvement_pct": 39.4
      },
      "20\u201330m": {
        "pinball_loss": 2.41,
        "bias": -1.21,
        "error_p90": 1.07,
        "n": 80620,
        "mae": 2.01,
        "baseline_pinball_loss": 3.94,
        "improvement_pct": 38.9
      },
      "30\u201345m": {
        "pinball_loss": 2.44,
        "bias": -1.27,
        "error_p90": 1.06,
        "n": 128992,
        "mae": 2.05,
        "baseline_pinball_loss": 4.23,
        "improvement_pct": 42.3
      },
      "45\u201360m": {
        "pinball_loss": 2.48,
        "bias": -1.3,
        "error_p90": 1.05,
        "n": 112868,
        "mae": 2.09,
        "baseline_pinball_loss": 4.94,
        "improvement_pct": 49.8
      },
      "60\u201390m": {
        "pinball_loss": 2.51,
        "bias": -1.32,
        "error_p90": 1.06,
        "n": 32248,
        "mae": 2.12,
        "baseline_pinball_loss": 5.02,
        "improvement_pct": 50.0
      }
    },
    "by_route_x_peak": {
      "ed-king (off-peak)": {
        "pinball_loss": 2.24,
        "bias": -1.27,
        "error_p90": 0.91,
        "n": 176352,
        "mae": 1.92,
        "baseline_pinball_loss": 4.15,
        "improvement_pct": 46.0
      },
      "ed-king (peak)": {
        "pinball_loss": 1.65,
        "bias": -0.87,
        "error_p90": 0.8,
        "n": 95271,
        "mae": 1.39,
        "baseline_pinball_loss": 3.07,
        "improvement_pct": 46.2
      },
      "sea-bi (off-peak)": {
        "pinball_loss": 3.13,
        "bias": -1.46,
        "error_p90": 1.5,
        "n": 163119,
        "mae": 2.57,
        "baseline_pinball_loss": 5.37,
        "improvement_pct": 41.7
      },
      "sea-bi (peak)": {
        "pinball_loss": 2.42,
        "bias": -1.26,
        "error_p90": 1.1,
        "n": 97350,
        "mae": 2.03,
        "baseline_pinball_loss": 4.48,
        "improvement_pct": 45.9
      }
    },
    "n_test_events": 16124,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 2.44,
      "std": 0.36
    },
    "bias": {
      "mean": -1.25,
      "std": 0.28
    },
    "error_p90": {
      "mean": 1.06,
      "std": 0.28
    }
  },
  "n_total_events": 19348,
  "n_folds": 5
}
```

</details>
