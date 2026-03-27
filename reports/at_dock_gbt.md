# Backtest Report: at_dock

> At-dock GBT model: predicts departure delay for vessels currently at dock

**Date:** 2026-03-26 22:14:16  
**Sailing events:** 19289  
**Walk-forward folds:** 5  
**Training time:** 19.8s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.21× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **2.58 min** (PL/MAE = 1.21×) |
| MAE | 2.13 min |
| Bias | -1.24 min |
| p90 (tail risk) | +1.27 min |
| 70% Interval Coverage | 71.0% (target: 70%) |
| Baseline Pinball Loss | 4.92 min |
| Improvement vs baseline | 47.5% |

## Comparison vs Previous Run

| Metric | Previous | Current | Delta |
|--------|----------|---------|-------|
| Pinball Loss | 4.92 min | 2.58 min | -2.34 (better) |
| MAE | 3.32 min | 2.13 min | -1.19 (better) |
| p90 | 3.53 min | 1.27 min | -2.26 (better) |
| Coverage | 0.3% | 71.0% | +70.70 (better) |
| Improvement % | -0.0% | 47.5% | +47.50 (better) |

### Per-Route Comparison

| Route | Prev PL | Curr PL | Prev p90 | Curr p90 | PL Delta |
|-------|---------|---------|----------|----------|----------|
| ed-king | 3.71 | 2.48 | +2.23 | +1.17 | -1.23 (better) |
| sea-bi | 6.41 | 2.7 | +5.30 | +1.38 | -3.71 (better) |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3214 | 3214 | 2.87 | -1.11 | +1.63 |
| 1 | 6428 | 3214 | 2.26 | -0.96 | +1.33 |
| 2 | 9642 | 3214 | 2.96 | -1.69 | +1.19 |
| 3 | 12856 | 3214 | 2.62 | -1.37 | +1.21 |
| 4 | 16070 | 3219 | 2.16 | -1.07 | +1.00 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 2.57 | ±0.32 |
| Bias | -1.24 | ±0.26 |
| p90 | 1.27 | ±0.21 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 2.48 | -1.28 | +1.17 | 47924 |
| sea-bi | 2.7 | -1.20 | +1.38 | 38967 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 2.37 | -0.87 | +1.31 | 12150 |
| Mon | 2.07 | -0.99 | +1.02 | 12546 |
| Sat | 2.11 | -0.67 | +1.43 | 13330 |
| Sun | 3.35 | -1.60 | +1.74 | 12763 |
| Thu | 2.65 | -1.51 | +1.01 | 12205 |
| Tue | 2.28 | -1.24 | +0.99 | 12107 |
| Wed | 3.27 | -1.89 | +1.31 | 11790 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 3.05 | -1.62 | +1.02 | 2226 |
| Early (5–7) | 2.59 | -1.50 | +0.91 | 5405 |
| Evening (19–22) | 2.03 | -0.84 | +1.16 | 11944 |
| Midday (10–15) | 2.22 | -1.01 | +1.29 | 20839 |
| PM Peak (15–19) | 2.2 | -1.07 | +1.14 | 19329 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 1.86 | -0.91 | +1.00 | 5727 |
| 4–6m | 1.89 | -0.81 | +1.12 | 5919 |
| 6–8m | 1.9 | -0.90 | +1.02 | 5547 |
| 8–10m | 1.72 | -0.75 | +1.05 | 5246 |
| 10–14m | 1.7 | -0.78 | +0.98 | 10297 |
| 14–20m | 1.61 | -0.73 | +0.95 | 11332 |
| 20–30m | 1.62 | -0.75 | +0.90 | 6463 |
| 30–45m | 2.54 | -1.25 | +1.39 | 2286 |
| 45–60m | 2.52 | -1.18 | +1.41 | 1985 |
| 60–90m | 2.48 | -1.19 | +1.35 | 3950 |

## Feature Importance (Permutation)

| Feature | Importance | |
|---|---|---|
| current_vessel_delay_minutes | 1.9354 | ████████████████████ |
| minutes_until_scheduled_departure | 1.4466 | ██████████████ |
| minutes_at_dock | 0.6604 | ██████ |
| hour_of_day | 0.4660 | ████ |
| incoming_vehicle_fullness | 0.3860 | ███ |
| day_of_week | 0.2274 | ██ |
| departing_terminal_id | 0.0991 | █ |
| vessel_id | 0.0916 |  |
| route_abbrev | 0.0503 |  |
| current_fullness | 0.0090 |  |
| is_weekend | 0.0018 |  |

### By Route

| Feature | ed-king | sea-bi |
|---|---|---|
| current_vessel_delay_minutes | 1.1132 | 3.0993 |
| minutes_until_scheduled_departure | 0.6769 | 2.0554 |
| minutes_at_dock | 0.4434 | 0.6260 |
| hour_of_day | 0.3589 | 0.5542 |
| incoming_vehicle_fullness | 0.3734 | 0.3821 |
| day_of_week | 0.3187 | 0.2503 |
| departing_terminal_id | 0.0277 | 0.1289 |
| vessel_id | 0.0571 | 0.0689 |
| route_abbrev | 0.0000 | 0.0000 |
| current_fullness | 0.0075 | 0.0087 |
| is_weekend | 0.0081 | 0.0051 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 2.58,
    "overall_bias": -1.24,
    "overall_error_p90": 1.27,
    "n_test_samples": 86891,
    "overall_mae": 2.13,
    "overall_coverage_70pct": 71.0,
    "overall_baseline_pinball_loss": 4.92,
    "overall_improvement_pct": 47.5,
    "by_route": {
      "ed-king": {
        "pinball_loss": 2.48,
        "bias": -1.28,
        "error_p90": 1.17,
        "n": 47924,
        "mae": 2.08,
        "baseline_pinball_loss": 3.71,
        "improvement_pct": 33.1
      },
      "sea-bi": {
        "pinball_loss": 2.7,
        "bias": -1.2,
        "error_p90": 1.38,
        "n": 38967,
        "mae": 2.2,
        "baseline_pinball_loss": 6.41,
        "improvement_pct": 57.9
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 3.35,
        "bias": -1.6,
        "error_p90": 1.74,
        "n": 12763,
        "mae": 2.77,
        "baseline_pinball_loss": 8.36,
        "improvement_pct": 59.9
      },
      "Mon": {
        "pinball_loss": 2.07,
        "bias": -0.99,
        "error_p90": 1.02,
        "n": 12546,
        "mae": 1.71,
        "baseline_pinball_loss": 4.51,
        "improvement_pct": 54.1
      },
      "Tue": {
        "pinball_loss": 2.28,
        "bias": -1.24,
        "error_p90": 0.99,
        "n": 12107,
        "mae": 1.93,
        "baseline_pinball_loss": 3.31,
        "improvement_pct": 31.2
      },
      "Wed": {
        "pinball_loss": 3.27,
        "bias": -1.89,
        "error_p90": 1.31,
        "n": 11790,
        "mae": 2.81,
        "baseline_pinball_loss": 5.76,
        "improvement_pct": 43.3
      },
      "Thu": {
        "pinball_loss": 2.65,
        "bias": -1.51,
        "error_p90": 1.01,
        "n": 12205,
        "mae": 2.27,
        "baseline_pinball_loss": 3.92,
        "improvement_pct": 32.4
      },
      "Fri": {
        "pinball_loss": 2.37,
        "bias": -0.87,
        "error_p90": 1.31,
        "n": 12150,
        "mae": 1.87,
        "baseline_pinball_loss": 4.24,
        "improvement_pct": 44.1
      },
      "Sat": {
        "pinball_loss": 2.11,
        "bias": -0.67,
        "error_p90": 1.43,
        "n": 13330,
        "mae": 1.63,
        "baseline_pinball_loss": 4.25,
        "improvement_pct": 50.4
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 2.59,
        "bias": -1.5,
        "error_p90": 0.91,
        "n": 5405,
        "mae": 2.22,
        "baseline_pinball_loss": 3.31,
        "improvement_pct": 21.8
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 3.05,
        "bias": -1.62,
        "error_p90": 1.02,
        "n": 2226,
        "mae": 2.57,
        "baseline_pinball_loss": 6.04,
        "improvement_pct": 49.5
      },
      "Midday (10\u201315)": {
        "pinball_loss": 2.22,
        "bias": -1.01,
        "error_p90": 1.29,
        "n": 20839,
        "mae": 1.81,
        "baseline_pinball_loss": 6.48,
        "improvement_pct": 65.7
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 2.2,
        "bias": -1.07,
        "error_p90": 1.14,
        "n": 19329,
        "mae": 1.82,
        "baseline_pinball_loss": 5.39,
        "improvement_pct": 59.2
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.03,
        "bias": -0.84,
        "error_p90": 1.16,
        "n": 11944,
        "mae": 1.64,
        "baseline_pinball_loss": 2.63,
        "improvement_pct": 22.7
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 1.86,
        "bias": -0.91,
        "error_p90": 1.0,
        "n": 5727,
        "mae": 1.54,
        "baseline_pinball_loss": 3.44,
        "improvement_pct": 46.0
      },
      "4\u20136m": {
        "pinball_loss": 1.89,
        "bias": -0.81,
        "error_p90": 1.12,
        "n": 5919,
        "mae": 1.53,
        "baseline_pinball_loss": 3.35,
        "improvement_pct": 43.6
      },
      "6\u20138m": {
        "pinball_loss": 1.9,
        "bias": -0.9,
        "error_p90": 1.02,
        "n": 5547,
        "mae": 1.56,
        "baseline_pinball_loss": 3.48,
        "improvement_pct": 45.3
      },
      "8\u201310m": {
        "pinball_loss": 1.72,
        "bias": -0.75,
        "error_p90": 1.05,
        "n": 5246,
        "mae": 1.4,
        "baseline_pinball_loss": 3.08,
        "improvement_pct": 44.1
      },
      "10\u201314m": {
        "pinball_loss": 1.7,
        "bias": -0.78,
        "error_p90": 0.98,
        "n": 10297,
        "mae": 1.39,
        "baseline_pinball_loss": 3.2,
        "improvement_pct": 46.9
      },
      "14\u201320m": {
        "pinball_loss": 1.61,
        "bias": -0.73,
        "error_p90": 0.95,
        "n": 11332,
        "mae": 1.31,
        "baseline_pinball_loss": 2.93,
        "improvement_pct": 45.0
      },
      "20\u201330m": {
        "pinball_loss": 1.62,
        "bias": -0.75,
        "error_p90": 0.9,
        "n": 6463,
        "mae": 1.33,
        "baseline_pinball_loss": 3.61,
        "improvement_pct": 55.2
      },
      "30\u201345m": {
        "pinball_loss": 2.54,
        "bias": -1.25,
        "error_p90": 1.39,
        "n": 2286,
        "mae": 2.11,
        "baseline_pinball_loss": 7.92,
        "improvement_pct": 67.9
      },
      "45\u201360m": {
        "pinball_loss": 2.52,
        "bias": -1.18,
        "error_p90": 1.41,
        "n": 1985,
        "mae": 2.07,
        "baseline_pinball_loss": 7.82,
        "improvement_pct": 67.8
      },
      "60\u201390m": {
        "pinball_loss": 2.48,
        "bias": -1.19,
        "error_p90": 1.35,
        "n": 3950,
        "mae": 2.05,
        "baseline_pinball_loss": 7.86,
        "improvement_pct": 68.4
      }
    },
    "n_test_events": 16075,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 2.57,
      "std": 0.32
    },
    "bias": {
      "mean": -1.24,
      "std": 0.26
    },
    "error_p90": {
      "mean": 1.27,
      "std": 0.21
    }
  },
  "n_total_events": 19289,
  "n_folds": 5
}
```

</details>
