# ETA Deep Dive: Next-Sailing Prediction Experiments

**Date:** 2026-04-05 10:50:32  
**Routes:** sea-bi, ed-king  
**Prediction pairs:** 17873

## Summary

| Experiment | MAE | Bias | ±3min | ±5min | Missed | Howlers |
|---|---|---|---|---|---|---|
| **Flat propagation** | 2.4 | -0.1 | 77.7% | 87.7% | 6.6% | 894 (5.0%) |
| **Clamped (p10 TA)** | 2.39 | +0.0 | 77.6% | 87.7% | 6.3% | 0 (0.0%) |
| **Cond ceil p75 (>10)** | 2.26 | -0.3 | 78.3% | 88.5% | 6.8% | 0 (0.0%) |
| **Cond ceil LINEAR (>10)** | 2.37 | -0.7 | 77.5% | 87.8% | 9.0% | 0 (0.0%) |
| **Cond ceil GBT (>10)** | 2.2 | -0.5 | 79.2% | 89.4% | 7.4% | 0 (0.0%) |

## Turnaround Model Diagnostics

**Training rows:** 17871
**Linear R²:** 0.387

**Linear model coefficients:**

| Feature | Coefficient | Interpretation |
|---|---|---|
| arriving_fullness | +4.029 | min added per 100% fullness increase (cars to unload) |
| outbound_fullness | +0.689 | min added per 100% fullness increase (cars to load) |
| minutes_until_next_scheduled | +0.303 | min added per min of schedule gap |
| route_code | -1.498 | min added for sea-bi vs ed-king |
| ta_hour_of_day | +0.094 | min added per hour of day |
| (intercept) | 12.58 | |

**Residual quantiles (for turnaround bounds):**

| Route | p10 (floor offset) | p75 (ceiling offset) |
|---|---|---|
| ed-king | -4.5 min | +2.1 min |
| sea-bi | -5.8 min | +2.4 min |

### sea-bi

| Experiment | MAE | Bias | ±3min | Howlers |
|---|---|---|---|---|
| Flat propagation (sea-bi) | 2.71 | -0.4 | 74.2% | 491 |
| Clamped (p10 TA) (sea-bi) | 2.69 | -0.2 | 74.3% | 0 |
| Cond ceil p75 (>10) (sea-bi) | 2.52 | -0.6 | 75.0% | 0 |
| Cond ceil LINEAR (>10) (sea-bi) | 2.77 | -1.1 | 73.7% | 0 |
| Cond ceil GBT (>10) (sea-bi) | 2.48 | -0.8 | 76.0% | 0 |

### ed-king

| Experiment | MAE | Bias | ±3min | Howlers |
|---|---|---|---|---|
| Flat propagation (ed-king) | 2.12 | +0.1 | 81.0% | 403 |
| Clamped (p10 TA) (ed-king) | 2.13 | +0.2 | 80.5% | 0 |
| Cond ceil p75 (>10) (ed-king) | 2.02 | +0.1 | 81.2% | 0 |
| Cond ceil LINEAR (>10) (ed-king) | 2.0 | -0.2 | 81.0% | 0 |
| Cond ceil GBT (>10) (ed-king) | 1.94 | -0.2 | 82.0% | 0 |

## By Actual Next-Sailing Delay

### On-time (≤1)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (on_time) | 1.68 | +1.6 | 96.5% |
| Clamped (p10 TA) (on_time) | 1.79 | +1.8 | 96.3% |
| Cond ceil p75 (>10) (on_time) | 1.64 | +1.6 | 96.8% |
| Cond ceil LINEAR (>10) (on_time) | 1.63 | +1.6 | 96.9% |
| Cond ceil GBT (>10) (on_time) | 1.64 | +1.6 | 96.9% |

### Minor (1–5)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (minor) | 1.45 | +0.5 | 95.4% |
| Clamped (p10 TA) (minor) | 1.5 | +0.5 | 95.2% |
| Cond ceil p75 (>10) (minor) | 1.37 | +0.4 | 95.9% |
| Cond ceil LINEAR (>10) (minor) | 1.34 | +0.4 | 96.3% |
| Cond ceil GBT (>10) (minor) | 1.31 | +0.3 | 96.7% |

### Moderate (5–15)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (moderate) | 4.11 | -1.1 | 71.3% |
| Clamped (p10 TA) (moderate) | 4.05 | -0.8 | 71.9% |
| Cond ceil p75 (>10) (moderate) | 3.74 | -1.4 | 74.0% |
| Cond ceil LINEAR (>10) (moderate) | 3.5 | -1.9 | 77.4% |
| Cond ceil GBT (>10) (moderate) | 3.57 | -2.1 | 76.7% |

### Major (15+)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (major) | 6.78 | -4.3 | 53.1% |
| Clamped (p10 TA) (major) | 6.45 | -3.9 | 54.0% |
| Cond ceil p75 (>10) (major) | 6.53 | -4.7 | 53.8% |
| Cond ceil LINEAR (>10) (major) | 8.34 | -7.9 | 37.2% |
| Cond ceil GBT (>10) (major) | 6.61 | -5.4 | 53.4% |

## Howler Analysis

A **howler** is when we predict the boat will depart before the inbound vessel can physically arrive and turn around (ETA + p10 turnaround).

Flat propagation produces **894 howlers** out of 17873 predictions (5.0%).

- **Clamped (p10 TA)**: zero howlers ✓
- **Cond ceil p75 (>10)**: zero howlers ✓
- **Cond ceil LINEAR (>10)**: zero howlers ✓
- **Cond ceil GBT (>10)**: zero howlers ✓
