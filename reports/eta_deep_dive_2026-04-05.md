# ETA Deep Dive: Next-Sailing Prediction Experiments

**Date:** 2026-04-05 09:36:22  
**Routes:** sea-bi, ed-king  
**Prediction pairs:** 17873

## Summary

| Experiment | MAE | Bias | ±3min | ±5min | Missed | Howlers |
|---|---|---|---|---|---|---|
| **Flat propagation** | 2.4 | -0.1 | 77.7% | 87.7% | 6.6% | 894 (5.0%) |
| **ETA + median TA** | 3.24 | -1.1 | 66.1% | 81.1% | 10.2% | 0 (0.0%) |
| **Clamped (p10 TA)** | 2.39 | +0.0 | 77.6% | 87.7% | 6.3% | 0 (0.0%) |
| **Clamped (p25 TA)** | 2.47 | +0.2 | 75.4% | 87.1% | 6.1% | 0 (0.0%) |
| **Clamped (median TA)** | 2.84 | +0.8 | 69.9% | 82.4% | 5.1% | 0 (0.0%) |
| **Blend (median TA)** | 2.92 | -0.7 | 69.6% | 83.3% | 8.7% | 5 (0.0%) |
| **Blend (p25 TA)** | 3.12 | -2.2 | 70.7% | 83.0% | 15.1% | 15 (0.1%) |

### sea-bi

| Experiment | MAE | Bias | ±3min | Howlers |
|---|---|---|---|---|
| Flat propagation (sea-bi) | 2.71 | -0.4 | 74.2% | 491 |
| ETA + median TA (sea-bi) | 3.64 | -1.2 | 60.4% | 0 |
| Clamped (p10 TA) (sea-bi) | 2.69 | -0.2 | 74.3% | 0 |
| Clamped (p25 TA) (sea-bi) | 2.75 | -0.0 | 72.4% | 0 |
| Clamped (median TA) (sea-bi) | 3.19 | +0.8 | 65.2% | 0 |
| Blend (median TA) (sea-bi) | 3.35 | -0.9 | 63.8% | 1 |
| Blend (p25 TA) (sea-bi) | 3.72 | -2.9 | 65.0% | 5 |

### ed-king

| Experiment | MAE | Bias | ±3min | Howlers |
|---|---|---|---|---|
| Flat propagation (ed-king) | 2.12 | +0.1 | 81.0% | 403 |
| ETA + median TA (ed-king) | 2.87 | -0.9 | 71.4% | 0 |
| Clamped (p10 TA) (ed-king) | 2.13 | +0.2 | 80.5% | 0 |
| Clamped (p25 TA) (ed-king) | 2.21 | +0.3 | 78.3% | 0 |
| Clamped (median TA) (ed-king) | 2.51 | +0.8 | 74.1% | 0 |
| Blend (median TA) (ed-king) | 2.53 | -0.6 | 75.0% | 4 |
| Blend (p25 TA) (ed-king) | 2.58 | -1.7 | 75.9% | 10 |

## By Actual Next-Sailing Delay

### On-time (≤1)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (on_time) | 1.68 | +1.6 | 96.5% |
| ETA + median TA (on_time) | 2.01 | +1.3 | 86.1% |
| Clamped (p10 TA) (on_time) | 1.79 | +1.8 | 96.3% |
| Clamped (p25 TA) (on_time) | 2.02 | +2.0 | 93.9% |
| Clamped (median TA) (on_time) | 2.78 | +2.8 | 83.7% |
| Blend (median TA) (on_time) | 1.79 | +1.5 | 87.5% |
| Blend (p25 TA) (on_time) | 0.92 | +0.4 | 97.7% |

### Minor (1–5)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (minor) | 1.45 | +0.5 | 95.4% |
| ETA + median TA (minor) | 2.38 | -0.4 | 92.8% |
| Clamped (p10 TA) (minor) | 1.5 | +0.5 | 95.2% |
| Clamped (p25 TA) (minor) | 1.59 | +0.7 | 94.6% |
| Clamped (median TA) (minor) | 2.02 | +1.2 | 89.5% |
| Blend (median TA) (minor) | 2.07 | -0.1 | 93.5% |
| Blend (p25 TA) (minor) | 1.9 | -1.2 | 98.5% |

### Moderate (5–15)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (moderate) | 4.11 | -1.1 | 71.3% |
| ETA + median TA (moderate) | 4.9 | -2.4 | 53.1% |
| Clamped (p10 TA) (moderate) | 4.05 | -0.8 | 71.9% |
| Clamped (p25 TA) (moderate) | 4.06 | -0.6 | 72.1% |
| Clamped (median TA) (moderate) | 4.18 | +0.2 | 70.1% |
| Blend (median TA) (moderate) | 4.56 | -1.9 | 61.1% |
| Blend (p25 TA) (moderate) | 5.73 | -4.4 | 42.3% |

### Major (15+)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (major) | 6.78 | -4.3 | 53.1% |
| ETA + median TA (major) | 7.58 | -5.4 | 41.9% |
| Clamped (p10 TA) (major) | 6.45 | -3.9 | 54.0% |
| Clamped (p25 TA) (major) | 6.34 | -3.6 | 54.1% |
| Clamped (median TA) (major) | 6.31 | -2.6 | 52.4% |
| Blend (median TA) (major) | 7.14 | -4.9 | 45.5% |
| Blend (p25 TA) (major) | 9.34 | -8.5 | 28.9% |

## Howler Analysis

A **howler** is when we predict the boat will depart before the inbound vessel can physically arrive and turn around (ETA + p10 turnaround).

Flat propagation produces **894 howlers** out of 17873 predictions (5.0%).

- **ETA + median TA**: zero howlers ✓
- **Clamped (p10 TA)**: zero howlers ✓
- **Clamped (p25 TA)**: zero howlers ✓
- **Clamped (median TA)**: zero howlers ✓
