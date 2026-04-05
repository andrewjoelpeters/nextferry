# ETA Deep Dive: Next-Sailing Prediction Experiments

**Date:** 2026-04-05 09:42:54  
**Routes:** sea-bi, ed-king  
**Prediction pairs:** 17873

## Summary

| Experiment | MAE | Bias | ±3min | ±5min | Missed | Howlers |
|---|---|---|---|---|---|---|
| **Flat propagation** | 2.4 | -0.1 | 77.7% | 87.7% | 6.6% | 894 (5.0%) |
| **Clamped (p10 TA)** | 2.39 | +0.0 | 77.6% | 87.7% | 6.3% | 0 (0.0%) |
| **Cond ceil p75 (>10)** | 2.26 | -0.3 | 78.3% | 88.5% | 6.8% | 0 (0.0%) |
| **Late ETA (70%/>10)** | 2.47 | -0.3 | 76.3% | 86.7% | 8.0% | 0 (0.0%) |
| **Late ETA (50%/>10)** | 2.46 | -0.4 | 76.4% | 86.8% | 8.1% | 0 (0.0%) |
| **Late ETA p75 (70%/>10)** | 2.47 | +0.3 | 77.2% | 87.1% | 5.3% | 0 (0.0%) |
| **Late ETA p75 (50%/>10)** | 2.48 | +0.3 | 77.2% | 87.1% | 5.3% | 0 (0.0%) |

### sea-bi

| Experiment | MAE | Bias | ±3min | Howlers |
|---|---|---|---|---|
| Flat propagation (sea-bi) | 2.71 | -0.4 | 74.2% | 491 |
| Clamped (p10 TA) (sea-bi) | 2.69 | -0.2 | 74.3% | 0 |
| Cond ceil p75 (>10) (sea-bi) | 2.52 | -0.6 | 75.0% | 0 |
| Late ETA (70%/>10) (sea-bi) | 2.86 | -0.7 | 71.7% | 0 |
| Late ETA (50%/>10) (sea-bi) | 2.85 | -0.7 | 71.9% | 0 |
| Late ETA p75 (70%/>10) (sea-bi) | 2.79 | +0.2 | 73.6% | 0 |
| Late ETA p75 (50%/>10) (sea-bi) | 2.78 | +0.2 | 73.8% | 0 |

### ed-king

| Experiment | MAE | Bias | ±3min | Howlers |
|---|---|---|---|---|
| Flat propagation (ed-king) | 2.12 | +0.1 | 81.0% | 403 |
| Clamped (p10 TA) (ed-king) | 2.13 | +0.2 | 80.5% | 0 |
| Cond ceil p75 (>10) (ed-king) | 2.02 | +0.1 | 81.2% | 0 |
| Late ETA (70%/>10) (ed-king) | 2.11 | +0.0 | 80.5% | 0 |
| Late ETA (50%/>10) (ed-king) | 2.1 | -0.0 | 80.5% | 0 |
| Late ETA p75 (70%/>10) (ed-king) | 2.18 | +0.3 | 80.4% | 0 |
| Late ETA p75 (50%/>10) (ed-king) | 2.2 | +0.4 | 80.4% | 0 |

## By Actual Next-Sailing Delay

### On-time (≤1)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (on_time) | 1.68 | +1.6 | 96.5% |
| Clamped (p10 TA) (on_time) | 1.79 | +1.8 | 96.3% |
| Cond ceil p75 (>10) (on_time) | 1.64 | +1.6 | 96.8% |
| Late ETA (70%/>10) (on_time) | 1.74 | +1.7 | 96.5% |
| Late ETA (50%/>10) (on_time) | 1.73 | +1.7 | 96.5% |
| Late ETA p75 (70%/>10) (on_time) | 1.75 | +1.7 | 96.3% |
| Late ETA p75 (50%/>10) (on_time) | 1.75 | +1.7 | 96.4% |

### Minor (1–5)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (minor) | 1.45 | +0.5 | 95.4% |
| Clamped (p10 TA) (minor) | 1.5 | +0.5 | 95.2% |
| Cond ceil p75 (>10) (minor) | 1.37 | +0.4 | 95.9% |
| Late ETA (70%/>10) (minor) | 1.43 | +0.5 | 95.8% |
| Late ETA (50%/>10) (minor) | 1.41 | +0.4 | 96.0% |
| Late ETA p75 (70%/>10) (minor) | 1.47 | +0.5 | 95.5% |
| Late ETA p75 (50%/>10) (minor) | 1.46 | +0.5 | 95.6% |

### Moderate (5–15)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (moderate) | 4.11 | -1.1 | 71.3% |
| Clamped (p10 TA) (moderate) | 4.05 | -0.8 | 71.9% |
| Cond ceil p75 (>10) (moderate) | 3.74 | -1.4 | 74.0% |
| Late ETA (70%/>10) (moderate) | 4.08 | -1.7 | 70.6% |
| Late ETA (50%/>10) (moderate) | 4.07 | -1.8 | 70.8% |
| Late ETA p75 (70%/>10) (moderate) | 4.45 | -0.5 | 67.4% |
| Late ETA p75 (50%/>10) (moderate) | 4.48 | -0.5 | 67.2% |

### Major (15+)

| Experiment | MAE | Bias | ±5min |
|---|---|---|---|
| Flat propagation (major) | 6.78 | -4.3 | 53.1% |
| Clamped (p10 TA) (major) | 6.45 | -3.9 | 54.0% |
| Cond ceil p75 (>10) (major) | 6.53 | -4.7 | 53.8% |
| Late ETA (70%/>10) (major) | 7.7 | -5.3 | 40.7% |
| Late ETA (50%/>10) (major) | 7.73 | -5.5 | 40.5% |
| Late ETA p75 (70%/>10) (major) | 6.86 | -1.3 | 52.4% |
| Late ETA p75 (50%/>10) (major) | 6.91 | -1.2 | 52.2% |

## Howler Analysis

A **howler** is when we predict the boat will depart before the inbound vessel can physically arrive and turn around (ETA + p10 turnaround).

Flat propagation produces **894 howlers** out of 17873 predictions (5.0%).

- **Clamped (p10 TA)**: zero howlers ✓
- **Cond ceil p75 (>10)**: zero howlers ✓
- **Late ETA (70%/>10)**: zero howlers ✓
- **Late ETA (50%/>10)**: zero howlers ✓
- **Late ETA p75 (70%/>10)**: zero howlers ✓
- **Late ETA p75 (50%/>10)**: zero howlers ✓
