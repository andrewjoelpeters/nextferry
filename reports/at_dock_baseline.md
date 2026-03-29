# Backtest Report: at_dock_baseline

> Flat delay baseline (option C): predict departure delay = previous vessel delay

**Date:** 2026-03-26 22:13:30  
**Sailing events:** 19289  
**Walk-forward folds:** 5  
**Training time:** 0.1s

## Top-Line Results

> **Pinball Loss** is an asymmetric MAE (α=2): overprediction is penalized 2× more than underprediction.  
> PL / MAE = 1.48× — closer to 1.0 means errors are mostly safe (underprediction); closer to 2.0 means mostly dangerous.

| Metric | Value |
|--------|-------|
| **Pinball Loss** | **4.92 min** (PL/MAE = 1.48×) |
| MAE | 3.32 min |
| Bias | -0.13 min |
| p90 (tail risk) | +3.53 min |
| 70% Interval Coverage | 0.3% (target: 70%) |
| Baseline Pinball Loss | 4.92 min |
| Improvement vs baseline | -0.0% |

## Walk-Forward Stability

| Fold | Train | Test | Pinball Loss | Bias | p90 |
|------|-------|------|--------------|------|-----|
| 0 | 3214 | 3214 | 5.55 | +0.24 | +4.08 |
| 1 | 6428 | 3214 | 4.55 | +0.09 | +2.98 |
| 2 | 9642 | 3214 | 5.9 | -0.12 | +4.25 |
| 3 | 12856 | 3214 | 4.42 | -0.54 | +3.02 |
| 4 | 16070 | 3219 | 4.15 | -0.31 | +3.15 |

| Metric | Mean | Std Dev |
|--------|------|---------|
| Pinball Loss | 4.91 | ±0.68 |
| Bias | -0.13 | ±0.28 |
| p90 | 3.5 | ±0.55 |

## By Route

| Route | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| ed-king | 3.71 | -0.87 | +2.23 | 47924 |
| sea-bi | 6.41 | +0.78 | +5.30 | 38967 |

## By Day of Week

| Day | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| Fri | 4.24 | -0.14 | +3.09 | 12150 |
| Mon | 4.51 | +0.24 | +3.05 | 12546 |
| Sat | 4.25 | +0.37 | +4.58 | 13330 |
| Sun | 8.36 | +1.09 | +6.32 | 12763 |
| Thu | 3.92 | -1.13 | +1.93 | 12205 |
| Tue | 3.31 | -0.81 | +2.03 | 12107 |
| Wed | 5.76 | -0.66 | +3.92 | 11790 |

## By Time of Day

| Period | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| AM Peak (7–10) | 6.04 | +0.48 | +3.13 | 2226 |
| Early (5–7) | 3.31 | -0.61 | +2.52 | 5405 |
| Evening (19–22) | 2.63 | -0.45 | +2.08 | 11944 |
| Midday (10–15) | 6.48 | +0.69 | +5.55 | 20839 |
| PM Peak (15–19) | 5.39 | +0.41 | +4.07 | 19329 |

## By Prediction Horizon

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 3.44 | +0.15 | +2.86 | 5727 |
| 4–6m | 3.35 | +0.07 | +2.90 | 5919 |
| 6–8m | 3.48 | +0.09 | +2.84 | 5547 |
| 8–10m | 3.08 | +0.01 | +2.57 | 5246 |
| 10–14m | 3.2 | +0.07 | +2.52 | 10297 |
| 14–20m | 2.93 | -0.09 | +2.08 | 11332 |
| 20–30m | 3.61 | +0.08 | +1.90 | 6463 |
| 30–45m | 7.92 | +1.14 | +7.13 | 2286 |
| 45–60m | 7.82 | +0.99 | +7.13 | 1985 |
| 60–90m | 7.86 | +1.03 | +7.78 | 3950 |

## Raw Results (JSON)

<details>
<summary>Click to expand</summary>

```json
{
  "aggregate": {
    "overall_pinball_loss": 4.92,
    "overall_bias": -0.13,
    "overall_error_p90": 3.53,
    "n_test_samples": 86891,
    "overall_mae": 3.32,
    "overall_coverage_70pct": 0.3,
    "overall_baseline_pinball_loss": 4.92,
    "overall_improvement_pct": -0.0,
    "by_route": {
      "ed-king": {
        "pinball_loss": 3.71,
        "bias": -0.87,
        "error_p90": 2.23,
        "n": 47924,
        "mae": 2.76,
        "baseline_pinball_loss": 3.71,
        "improvement_pct": -0.0
      },
      "sea-bi": {
        "pinball_loss": 6.41,
        "bias": 0.78,
        "error_p90": 5.3,
        "n": 38967,
        "mae": 4.01,
        "baseline_pinball_loss": 6.41,
        "improvement_pct": -0.0
      }
    },
    "by_day_of_week": {
      "Sun": {
        "pinball_loss": 8.36,
        "bias": 1.09,
        "error_p90": 6.32,
        "n": 12763,
        "mae": 5.21,
        "baseline_pinball_loss": 8.36,
        "improvement_pct": 0.0
      },
      "Mon": {
        "pinball_loss": 4.51,
        "bias": 0.24,
        "error_p90": 3.05,
        "n": 12546,
        "mae": 2.92,
        "baseline_pinball_loss": 4.51,
        "improvement_pct": -0.1
      },
      "Tue": {
        "pinball_loss": 3.31,
        "bias": -0.81,
        "error_p90": 2.03,
        "n": 12107,
        "mae": 2.48,
        "baseline_pinball_loss": 3.31,
        "improvement_pct": 0.1
      },
      "Wed": {
        "pinball_loss": 5.76,
        "bias": -0.66,
        "error_p90": 3.92,
        "n": 11790,
        "mae": 4.06,
        "baseline_pinball_loss": 5.76,
        "improvement_pct": 0.0
      },
      "Thu": {
        "pinball_loss": 3.92,
        "bias": -1.13,
        "error_p90": 1.93,
        "n": 12205,
        "mae": 2.99,
        "baseline_pinball_loss": 3.92,
        "improvement_pct": -0.0
      },
      "Fri": {
        "pinball_loss": 4.24,
        "bias": -0.14,
        "error_p90": 3.09,
        "n": 12150,
        "mae": 2.87,
        "baseline_pinball_loss": 4.24,
        "improvement_pct": 0.1
      },
      "Sat": {
        "pinball_loss": 4.25,
        "bias": 0.37,
        "error_p90": 4.58,
        "n": 13330,
        "mae": 2.71,
        "baseline_pinball_loss": 4.25,
        "improvement_pct": 0.1
      }
    },
    "by_time_of_day": {
      "Early (5\u20137)": {
        "pinball_loss": 3.31,
        "bias": -0.61,
        "error_p90": 2.52,
        "n": 5405,
        "mae": 2.41,
        "baseline_pinball_loss": 3.31,
        "improvement_pct": 0.1
      },
      "AM Peak (7\u201310)": {
        "pinball_loss": 6.04,
        "bias": 0.48,
        "error_p90": 3.13,
        "n": 2226,
        "mae": 3.87,
        "baseline_pinball_loss": 6.04,
        "improvement_pct": 0.1
      },
      "Midday (10\u201315)": {
        "pinball_loss": 6.48,
        "bias": 0.69,
        "error_p90": 5.55,
        "n": 20839,
        "mae": 4.09,
        "baseline_pinball_loss": 6.48,
        "improvement_pct": -0.0
      },
      "PM Peak (15\u201319)": {
        "pinball_loss": 5.39,
        "bias": 0.41,
        "error_p90": 4.07,
        "n": 19329,
        "mae": 3.46,
        "baseline_pinball_loss": 5.39,
        "improvement_pct": -0.0
      },
      "Evening (19\u201322)": {
        "pinball_loss": 2.63,
        "bias": -0.45,
        "error_p90": 2.08,
        "n": 11944,
        "mae": 1.9,
        "baseline_pinball_loss": 2.63,
        "improvement_pct": -0.1
      }
    },
    "by_horizon": {
      "2\u20134m": {
        "pinball_loss": 3.44,
        "bias": 0.15,
        "error_p90": 2.86,
        "n": 5727,
        "mae": 2.24,
        "baseline_pinball_loss": 3.44,
        "improvement_pct": 0.0
      },
      "4\u20136m": {
        "pinball_loss": 3.35,
        "bias": 0.07,
        "error_p90": 2.9,
        "n": 5919,
        "mae": 2.21,
        "baseline_pinball_loss": 3.35,
        "improvement_pct": 0.1
      },
      "6\u20138m": {
        "pinball_loss": 3.48,
        "bias": 0.09,
        "error_p90": 2.84,
        "n": 5547,
        "mae": 2.29,
        "baseline_pinball_loss": 3.48,
        "improvement_pct": -0.1
      },
      "8\u201310m": {
        "pinball_loss": 3.08,
        "bias": 0.01,
        "error_p90": 2.57,
        "n": 5246,
        "mae": 2.05,
        "baseline_pinball_loss": 3.08,
        "improvement_pct": -0.0
      },
      "10\u201314m": {
        "pinball_loss": 3.2,
        "bias": 0.07,
        "error_p90": 2.52,
        "n": 10297,
        "mae": 2.11,
        "baseline_pinball_loss": 3.2,
        "improvement_pct": 0.1
      },
      "14\u201320m": {
        "pinball_loss": 2.93,
        "bias": -0.09,
        "error_p90": 2.08,
        "n": 11332,
        "mae": 1.98,
        "baseline_pinball_loss": 2.93,
        "improvement_pct": -0.1
      },
      "20\u201330m": {
        "pinball_loss": 3.61,
        "bias": 0.08,
        "error_p90": 1.9,
        "n": 6463,
        "mae": 2.38,
        "baseline_pinball_loss": 3.61,
        "improvement_pct": 0.1
      },
      "30\u201345m": {
        "pinball_loss": 7.92,
        "bias": 1.14,
        "error_p90": 7.13,
        "n": 2286,
        "mae": 4.9,
        "baseline_pinball_loss": 7.92,
        "improvement_pct": -0.0
      },
      "45\u201360m": {
        "pinball_loss": 7.82,
        "bias": 0.99,
        "error_p90": 7.13,
        "n": 1985,
        "mae": 4.89,
        "baseline_pinball_loss": 7.82,
        "improvement_pct": 0.0
      },
      "60\u201390m": {
        "pinball_loss": 7.86,
        "bias": 1.03,
        "error_p90": 7.78,
        "n": 3950,
        "mae": 4.89,
        "baseline_pinball_loss": 7.86,
        "improvement_pct": -0.0
      }
    },
    "n_test_events": 16075,
    "n_folds": 5
  },
  "stability": {
    "pinball_loss": {
      "mean": 4.91,
      "std": 0.68
    },
    "bias": {
      "mean": -0.13,
      "std": 0.28
    },
    "error_p90": {
      "mean": 3.5,
      "std": 0.55
    }
  },
  "n_total_events": 19289,
  "n_folds": 5
}
```

</details>
