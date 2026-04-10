# ETA + Turnaround Backtest Report

> Can WSDOT's real-time ETA + turnaround model replace the current en-route delay predictor?

**Date:** 2026-04-04 19:52:19

## 1. Data Coverage

- **Total sailing events:** 87348
- **Events with derived arrival:** 86588
- **Arrival coverage:** 99.1%
- **En-route snapshots (total):** 464463
- **Snapshots with ETA:** 409291
- **Null ETA rate:** 11.9%

## 2. ETA Accuracy

> Positive error = ETA was later than actual arrival. Negative = ETA was earlier.

### Overall

| Metric | Value |
|--------|-------|
| N | 403050 |
| MAE | 5.72 min |
| Bias | -1.16 min |
| Std Dev | 50.66 min |
| p10 | -5.80 min |
| p50 (median) | -2.63 min |
| p90 | +0.60 min |

### By Minutes to Arrival

| Proximity | N | MAE | Bias | p90 |
|---|---|---|---|---|
| 0–5m | 2365 | 4.64 | 3.24 | 0.43 |
| 5–10m | 86847 | 3.92 | -1.27 | -0.10 |
| 10–15m | 84089 | 4.19 | -1.48 | 0.17 |
| 15–20m | 60586 | 5.07 | -1.47 | 0.23 |
| 20–30m | 75409 | 5.60 | -1.37 | 0.55 |
| 30–45m | 57580 | 7.15 | -0.44 | 2.13 |
| 45–60m | 29239 | 9.38 | -0.44 | 2.17 |

### By Route

| Route | N | MAE | Bias | p90 |
|---|---|---|---|---|
| ana-sj | 106458 | 8.91 | 1.86 | 1.68 |
| ed-king | 40895 | 3.42 | -2.64 | -0.15 |
| f-v-s | 51864 | 4.47 | -2.76 | 0.08 |
| muk-cl | 38229 | 4.40 | -2.40 | -0.12 |
| pd-tal | 17500 | 9.24 | -4.85 | 0.20 |
| pt-cou | 23846 | 3.96 | -1.90 | 0.07 |
| sea-bi | 57845 | 3.88 | -2.52 | 0.30 |
| sea-br | 66407 | 5.09 | -0.67 | 1.12 |

## 3. Turnaround Patterns

- **Valid turnaround observations:** 75776
- **Variance explained by route+hour:** 24.1%

### Turnaround by Route

| Route | N | Median | Mean | Std | p10 | p90 |
|---|---|---|---|---|---|---|
| ana-sj | 11093 | 16.40 | 18.40 | 10.60 | 6.70 | 32.80 |
| ed-king | 9351 | 21.40 | 21.60 | 5.60 | 14.80 | 28.80 |
| f-v-s | 16408 | 10.50 | 12.00 | 6.90 | 6.20 | 18.30 |
| muk-cl | 13590 | 12.70 | 13.10 | 4.50 | 8.80 | 16.80 |
| pd-tal | 7155 | 12.60 | 13.50 | 5.70 | 8.60 | 18.20 |
| pt-cou | 4225 | 15.60 | 16.50 | 5.20 | 11.80 | 22.00 |
| sea-bi | 8549 | 16.80 | 17.30 | 6.40 | 9.30 | 25.20 |
| sea-br | 5404 | 13.80 | 15.30 | 6.70 | 8.70 | 24.10 |

## 4. Crossing Time Patterns

| Route | N | Median | Mean | Std | p10 | p90 |
|---|---|---|---|---|---|---|
| ana-sj | 14748 | 43.10 | 40.00 | 18.80 | 12.60 | 67.40 |
| ed-king | 9866 | 24.50 | 24.60 | 3.10 | 22.00 | 27.10 |
| f-v-s | 19925 | 16.40 | 17.30 | 5.50 | 12.90 | 22.20 |
| muk-cl | 14369 | 17.40 | 17.70 | 3.60 | 14.80 | 20.10 |
| pd-tal | 7882 | 14.80 | 16.20 | 9.00 | 12.30 | 17.50 |
| pt-cou | 4528 | 29.60 | 29.80 | 3.20 | 27.10 | 32.70 |
| sea-bi | 9365 | 34.70 | 34.90 | 3.60 | 32.00 | 37.80 |
| sea-br | 5904 | 59.00 | 59.10 | 4.40 | 55.40 | 63.00 |

## 5. Head-to-Head: ETA+Turnaround vs Current Model

**ETA+Turnaround predictions:** 86453

> Note: ETA+turnaround predicts the *next* sailing's delay from en-route observations. The current model predicts the *current* sailing's delay from pre-departure observations. These are complementary, not directly comparable — but we can evaluate each on the sailings they cover.

### ETA+Turnaround (next-sailing prediction)

| Metric | Value |
|--------|-------|
| Pinball Loss | 38.3 min |
| MAE | 19.66 min |
| Bias | +17.61 min |
| p90 | +48.83 min |
| 70% Coverage | 28.6% |

### ETA+Turnaround by Route

| Route | Pinball Loss | Bias | p90 | Interval Width | N |
|---|---|---|---|---|---|
| ana-sj | 79.63 | +39.11 | +68.52 | 20.95 | 14708 |
| ed-king | 39.44 | +18.40 | +44.71 | 8.06 | 9854 |
| f-v-s | 26.86 | +12.35 | +25.03 | 8.91 | 19894 |
| muk-cl | 25.81 | +11.27 | +29.43 | 4.74 | 14346 |
| pd-tal | 7.56 | +0.27 | +2.68 | 3.87 | 7865 |
| pt-cou | 11.01 | +3.37 | +6.94 | 4.45 | 4525 |
| sea-bi | 41.53 | +18.96 | +49.53 | 9.68 | 9358 |
| sea-br | 59.08 | +27.77 | +69.71 | 8.97 | 5903 |

### ETA+Turnaround by Horizon (minutes to next departure)

| Horizon | Pinball Loss | Bias | p90 | N |
|---|---|---|---|---|
| 2–4m | 25.71 | +11.03 | +27.31 | 1829 |
| 4–6m | 22.93 | +9.72 | +25.19 | 1938 |
| 6–8m | 19.1 | +7.40 | +21.89 | 1804 |
| 8–10m | 13.92 | +4.83 | +17.20 | 1981 |
| 10–14m | 10.04 | +2.66 | +10.88 | 4780 |
| 14–20m | 7.79 | +1.10 | +7.07 | 9668 |
| 20–30m | 6.2 | +0.62 | +6.05 | 13460 |
| 30–45m | 5.1 | -0.34 | +2.92 | 6473 |
| 45–60m | 6.3 | -0.74 | +4.31 | 799 |
| 60–90m | 5.94 | -5.44 | -0.33 | 200 |

### Current GBT Model (walk-forward)

| Metric | Value |
|--------|-------|
| Pinball Loss | 2.47 min |
| MAE | 1.98 min |
| Bias | -0.98 min |
| p90 | +1.29 min |
| 70% Coverage | 72.3% |

## 6. Propagation (Chained Predictions)

> Predicting forward: sailing+1, +2, +3 using arrival → turnaround → crossing chain.

| Hop | N | Pinball Loss | MAE | Bias | p90 |
|-----|---|---|---|---|---|
| +1 | 86563 | 40.16 | 20.41 | +19.07 | +51.57 |
| +2 | 86563 | 77.57 | 39.01 | +38.12 | +77.82 |
| +3 | 86563 | 115.51 | 57.98 | +57.07 | +129.41 |

## 7. Recommendation

**ETA quality is poor** (MAE=5.72 min). WSDOT ETA is not accurate enough to build reliable turnaround predictions on.

**Propagation:** Error grows 2.8× from +1 to +3 sailings. 
Chaining 2 sailings ahead is reasonable; 3+ degrades quickly.

**ETA+Turnaround pinball loss:** 38.3 min (for next-sailing prediction).

**Next steps:** The ETA+turnaround approach operates at a different point in the sailing lifecycle (en-route → next departure) than the current model (pre-departure → current departure). Consider using both: the GBT model for near-term predictions, and ETA+turnaround for propagation to the next sailing.
