# ETA Deep Dive: Next-Sailing Prediction Experiments

**Date:** 2026-04-05 09:41:25  
**Routes:** sea-bi, ed-king  
**Prediction pairs:** 17873

## Summary

| Experiment | MAE | Bias | ±3min | ±5min | Missed | Howlers |
|---|---|---|---|---|---|---|
| **Flat propagation** | 2.4 | -0.1 | 77.7% | 87.7% | 6.6% | 894 (5.0%) |
| **Clamped (p10 TA)** | 2.39 | +0.0 | 77.6% | 87.7% | 6.3% | 0 (0.0%) |
| **Cond ceil med (>10)** | 2.33 | -0.6 | 77.3% | 87.8% | 8.6% | 0 (0.0%) |
| **Cond ceil med (>15)** | 2.34 | -0.4 | 77.3% | 87.5% | 7.8% | 0 (0.0%) |
| **Cond ceil p75 (>10)** | 2.26 | -0.3 | 78.3% | 88.5% | 6.8% | 0 (0.0%) |
| **Cond ceil p75 (>15)** | 2.29 | -0.2 | 77.9% | 88.1% | 6.7% | 0 (0.0%) |
| **Cond ceil p75 (>20)** | 2.32 | -0.1 | 77.7% | 87.9% | 6.6% | 0 (0.0%) |

### sea-bi

| Experiment | MAE | Bias | ±3min | Howlers |
|---|---|---|---|---|
| Flat propagation (sea-bi) | 2.71 | -0.4 | 74.2% | 491 |
| Clamped (p10 TA) (sea-bi) | 2.69 | -0.2 | 74.3% | 0 |
| Cond ceil med (>10) (sea-bi) | 2.67 | -1.1 | 73.4% | 0 |
| Cond ceil med (>15) (sea-bi) | 2.66 | -0.9 | 73.5% | 0 |
| Cond ceil p75 (>10) (sea-bi) | 2.52 | -0.6 | 75.0% | 0 |
| Cond ceil p75 (>15) (sea-bi) | 2.55 | -0.5 | 74.8% | 0 |
| Cond ceil p75 (>20) (sea-bi) | 2.57 | -0.5 | 74.4% | 0 |

### ed-king

| Experiment | MAE | Bias | ±3min | Howlers |
|---|---|---|---|---|
| Flat propagation (ed-king) | 2.12 | +0.1 | 81.0% | 403 |
| Clamped (p10 TA) (ed-king) | 2.13 | +0.2 | 80.5% | 0 |
| Cond ceil med (>10) (ed-king) | 2.01 | -0.2 | 80.9% | 0 |
| Cond ceil med (>15) (ed-king) | 2.05 | +0.0 | 80.8% | 0 |
| Cond ceil p75 (>10) (ed-king) | 2.02 | +0.1 | 81.2% | 0 |
| Cond ceil p75 (>15) (ed-king) | 2.06 | +0.1 | 80.9% | 0 |
| Cond ceil p75 (>20) (ed-king) | 2.08 | +0.1 | 80.7% | 0 |

## By Actual Next-Sailing Delay

### On-time (≤1)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (on_time) | 1.68 | +1.6 | 96.5% |
| Clamped (p10 TA) (on_time) | 1.79 | +1.8 | 96.3% |
| Cond ceil med (>10) (on_time) | 1.61 | +1.6 | 97.0% |
| Cond ceil med (>15) (on_time) | 1.65 | +1.6 | 96.7% |
| Cond ceil p75 (>10) (on_time) | 1.64 | +1.6 | 96.8% |
| Cond ceil p75 (>15) (on_time) | 1.66 | +1.6 | 96.6% |
| Cond ceil p75 (>20) (on_time) | 1.68 | +1.6 | 96.5% |

### Minor (1–5)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (minor) | 1.45 | +0.5 | 95.4% |
| Clamped (p10 TA) (minor) | 1.5 | +0.5 | 95.2% |
| Cond ceil med (>10) (minor) | 1.32 | +0.3 | 96.5% |
| Cond ceil med (>15) (minor) | 1.39 | +0.4 | 95.5% |
| Cond ceil p75 (>10) (minor) | 1.37 | +0.4 | 95.9% |
| Cond ceil p75 (>15) (minor) | 1.42 | +0.5 | 95.4% |
| Cond ceil p75 (>20) (minor) | 1.43 | +0.5 | 95.3% |

### Moderate (5–15)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (moderate) | 4.11 | -1.1 | 71.3% |
| Clamped (p10 TA) (moderate) | 4.05 | -0.8 | 71.9% |
| Cond ceil med (>10) (moderate) | 3.79 | -2.2 | 72.9% |
| Cond ceil med (>15) (moderate) | 3.67 | -1.5 | 74.3% |
| Cond ceil p75 (>10) (moderate) | 3.74 | -1.4 | 74.0% |
| Cond ceil p75 (>15) (moderate) | 3.79 | -1.2 | 73.3% |
| Cond ceil p75 (>20) (moderate) | 3.88 | -1.1 | 72.2% |

### Major (15+)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (major) | 6.78 | -4.3 | 53.1% |
| Clamped (p10 TA) (major) | 6.45 | -3.9 | 54.0% |
| Cond ceil med (>10) (major) | 7.57 | -6.5 | 43.5% |
| Cond ceil med (>15) (major) | 7.36 | -6.3 | 45.6% |
| Cond ceil p75 (>10) (major) | 6.53 | -4.7 | 53.8% |
| Cond ceil p75 (>15) (major) | 6.5 | -4.7 | 54.2% |
| Cond ceil p75 (>20) (major) | 6.47 | -4.6 | 54.5% |

## Howler Analysis

A **howler** is when we predict the boat will depart before the inbound vessel can physically arrive and turn around (ETA + p10 turnaround).

Flat propagation produces **894 howlers** out of 17873 predictions (5.0%).

- **Clamped (p10 TA)**: zero howlers ✓
- **Cond ceil med (>10)**: zero howlers ✓
- **Cond ceil med (>15)**: zero howlers ✓
- **Cond ceil p75 (>10)**: zero howlers ✓
- **Cond ceil p75 (>15)**: zero howlers ✓
- **Cond ceil p75 (>20)**: zero howlers ✓
