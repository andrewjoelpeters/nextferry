# ETA + Turnaround Deep Dive: sea-bi & ed-king

**Date:** 2026-04-04 20:29:33
**Routes:** ed-king, sea-bi

## 1. Data Coverage

- **ed-king:** 9893 events, 9866 with arrival (99.7%)
- **sea-bi:** 9429 events, 9365 with arrival (99.3%)
- **Total:** 19322 events, 19231 with arrival

## 2. ETA Accuracy (en-route snapshots)

> Positive = ETA predicted later than actual. Negative = ETA predicted earlier.

### ed-king

| Metric | Value |
|--------|-------|
| N snapshots | 40895 |
| MAE | 3.42 min |
| Bias | -2.64 min |
| Median error | -2.68 min |
| p10 / p90 | -5.23 / -0.15 min |
| Within ±1 min | 18.4% |
| Within ±2 min | 36.3% |
| Within ±5 min | 87.2% |

**By minutes to arrival:**

| Proximity | N | MAE | Bias | Within ±2m |
|-----------|---|-----|------|------------|
| 0–5m | 303 | 0.74 | -0.56 | 96.4% |
| 5–10m | 9977 | 2.91 | -2.07 | 39.5% |
| 10–15m | 10065 | 3.13 | -2.21 | 38.2% |
| 15–20m | 10016 | 3.13 | -2.33 | 39.3% |
| 20–30m | 10175 | 3.85 | -3.24 | 27.6% |
| 30+m | 359 | 24.60 | -23.93 | 0.8% |

### sea-bi

| Metric | Value |
|--------|-------|
| N snapshots | 57845 |
| MAE | 3.88 min |
| Bias | -2.52 min |
| Median error | -2.63 min |
| p10 / p90 | -5.55 / +0.30 min |
| Within ±1 min | 17.8% |
| Within ±2 min | 35.4% |
| Within ±5 min | 84.0% |

**By minutes to arrival:**

| Proximity | N | MAE | Bias | Within ±2m |
|-----------|---|-----|------|------------|
| 0–5m | 217 | 0.69 | -0.44 | 99.1% |
| 5–10m | 9435 | 3.21 | -1.97 | 39.0% |
| 10–15m | 9503 | 3.46 | -1.99 | 37.9% |
| 15–20m | 9497 | 3.23 | -2.51 | 37.3% |
| 20–30m | 18937 | 3.69 | -2.31 | 37.0% |
| 30+m | 10256 | 5.89 | -3.99 | 23.8% |

## 3. Turnaround Patterns

### ed-king

| Metric | Value |
|--------|-------|
| N | 9351 |
| Median | 21.4 min |
| Mean | 21.6 min |
| Std | 5.6 min |
| p10 / p90 | 14.8 / 28.8 min |
| IQR | 18.4 – 24.6 min |

**By hour of day:**

| Hour | N | Median | Std |
|------|---|--------|-----|
| 0:00 | 550 | 20.2 | 4.2 |
| 1:00 | 428 | 20.6 | 4.0 |
| 2:00 | 610 | 19.3 | 4.9 |
| 3:00 | 613 | 17.9 | 4.0 |
| 4:00 | 395 | 16.9 | 5.3 |
| 5:00 | 377 | 16.3 | 4.4 |
| 6:00 | 213 | 15.5 | 5.5 |
| 7:00 | 97 | 10.8 | 2.2 |
| 11:00 | 76 | 23.5 | 2.5 |
| 12:00 | 246 | 24.0 | 5.4 |
| 13:00 | 342 | 20.7 | 4.4 |
| 14:00 | 565 | 21.8 | 5.2 |
| 15:00 | 676 | 24.5 | 5.9 |
| 16:00 | 427 | 22.3 | 5.4 |
| 17:00 | 426 | 20.8 | 3.4 |
| 18:00 | 613 | 22.4 | 4.1 |
| 19:00 | 682 | 24.4 | 3.3 |
| 20:00 | 432 | 26.5 | 3.9 |
| 21:00 | 431 | 27.6 | 4.9 |
| 22:00 | 516 | 21.4 | 5.0 |
| 23:00 | 636 | 20.7 | 4.7 |

### sea-bi

| Metric | Value |
|--------|-------|
| N | 8549 |
| Median | 16.8 min |
| Mean | 17.3 min |
| Std | 6.4 min |
| p10 / p90 | 9.3 / 25.2 min |
| IQR | 13.2 – 20.9 min |

**By hour of day:**

| Hour | N | Median | Std |
|------|---|--------|-----|
| 0:00 | 403 | 18.7 | 5.7 |
| 1:00 | 398 | 17.2 | 4.2 |
| 2:00 | 395 | 14.7 | 4.4 |
| 3:00 | 396 | 15.9 | 7.4 |
| 4:00 | 422 | 17.0 | 10.6 |
| 5:00 | 338 | 11.5 | 11.1 |
| 6:00 | 221 | 10.4 | 6.3 |
| 7:00 | 228 | 8.4 | 6.7 |
| 8:00 | 168 | 7.0 | 6.6 |
| 9:00 | 30 | 7.9 | 2.5 |
| 11:00 | 63 | 10.4 | 2.1 |
| 12:00 | 233 | 13.1 | 2.8 |
| 13:00 | 356 | 15.3 | 3.4 |
| 14:00 | 524 | 15.4 | 3.9 |
| 15:00 | 611 | 15.5 | 4.6 |
| 16:00 | 415 | 17.0 | 5.1 |
| 17:00 | 421 | 20.6 | 5.5 |
| 18:00 | 424 | 20.1 | 4.5 |
| 19:00 | 422 | 18.9 | 3.9 |
| 20:00 | 421 | 17.4 | 3.8 |
| 21:00 | 483 | 19.4 | 5.2 |
| 22:00 | 611 | 20.4 | 5.6 |
| 23:00 | 566 | 18.8 | 5.0 |

## 4. Error Decomposition

> Breaks total prediction error into ETA error and turnaround error components.

| Route | N | Total MAE | Total Bias | ETA MAE | ETA Bias | TA MAE | TA Bias | Clamp % | Unclamped MAE |
|---|---|---|---|---|---|---|---|---|---|
| ed-king | 9849 | 3.01 | -1.15 | 3.35 | -2.42 | 31.01 | -27.88 | 46.3% | 3.46 |
| sea-bi | 9349 | 3.38 | -1.53 | 3.51 | -2.68 | 33.1 | -29.59 | 42.5% | 3.72 |

## 5. Oracle: Perfect ETA + Turnaround Lookup

> If we had a perfect ETA (actual arrival), how well would turnaround prediction alone do?

| Metric | Value |
|--------|-------|
| Pinball Loss | 4.78 min |
| MAE | 3.13 min |
| Bias | +0.19 min |
| 70% Coverage | 65.3% |

**By route:**

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ed-king | 4.46 | +0.25 | +4.92 | 6.43 | 9860 |
| sea-bi | 5.13 | +0.13 | +5.60 | 7.8 | 9355 |

## 6. Head-to-Head

### ETA + Turnaround (next-sailing prediction)

| Metric | Value |
|--------|-------|
| Pinball Loss | 4.12 min |
| MAE | 3.19 min |
| Bias | -1.33 min |
| p90 | +2.42 min |
| 70% Coverage | 60.9% |

**By route:**

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ed-king | 3.94 | -1.15 | +2.12 | 4.93 | 9849 |
| sea-bi | 4.3 | -1.53 | +2.73 | 6.58 | 9349 |

### Current GBT Model (walk-forward)

| Metric | Value |
|--------|-------|
| Pinball Loss | 2.47 min |
| MAE | 1.98 min |
| Bias | -0.98 min |
| p90 | +1.29 min |
| 70% Coverage | 72.3% |

**By route:**

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ed-king | 2.09 | -0.88 | +1.07 | 4.37 | 271623 |
| sea-bi | 2.87 | -1.09 | +1.55 | 5.84 | 260469 |

## 7. User Impact Analysis

> How do errors translate to rider experience?

| Route | N | Delay Rate | Within 2m | Within 5m | Dangerous Miss | False Alarm | Delayed MAE | Delayed Bias |
|---|---|---|---|---|---|---|---|---|
| ed-king | 9849 | 30.9% | 57.5% | 88.1% | 6.7% | 4.1% | 5.31 | -3.09 |
| sea-bi | 9349 | 43.1% | 46.8% | 83.4% | 6.8% | 3.3% | 5.23 | -2.94 |

**Key:**
- **Delay Rate**: % of sailings actually delayed >3 min
- **Dangerous Miss**: predicted ≤3 min delay, actual >5 min (rider might miss)
- **False Alarm**: predicted >5 min delay, actual ≤3 min (rider arrives too early)

## 8. Analysis & Recommendations

### ed-king

- **Turnaround is the dominant error source** (TA MAE=31.01 vs ETA MAE=3.35). Improving turnaround prediction matters more than better ETAs.
- **Dangerous miss rate is 6.7%** — too high for production use.

### sea-bi

- **Turnaround is the dominant error source** (TA MAE=33.1 vs ETA MAE=3.51). Improving turnaround prediction matters more than better ETAs.
- **Dangerous miss rate is 6.8%** — too high for production use.
