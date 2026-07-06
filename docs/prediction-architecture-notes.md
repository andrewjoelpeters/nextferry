# Prediction Architecture Notes

*Generated from conversation on 2026-07-03*

## Current Design (Option A / ETA-Bounded)

The prediction has two modes:

**ETA-bounded** (used when vessel is en-route with ETA and the next sailing is opposite-direction):
```python
eta_floor = max(0, (ETA + p10 - scheduled_dep) / 60)
eta_ceiling = max(0, (ETA + p75 - scheduled_dep) / 60)
return max(floor, min(current_delay, ceiling))
```
Result: ETA acts as a **cap** on current delay. If ETA says "arrive early," the ceiling drops to 0, discarding current delay entirely.

**Flat propagation** (used when at dock or no ETA):
```python
return current_delay
```
Result: carries forward whatever delay the vessel is currently experiencing.

## Why ETA-bounded Is Wrong

The ETA from WSDOT is for the *current* crossing, but the prediction is for a sailing 2-3 crossings later. Intermediate sailings cause cascade growth that the ETA doesn't capture.

**Tacoma example (2026-06-27 16:40):**
Vessel is 28m late crossing Seattle→BI at 14:43. WSDOT ETA says arrival at 15:11. ETA + 35min turnaround = 15:46, still 54min before 16:40 departure. Option A computes ceiling=0, predicts 0m. Actual: 60m.

The ceiling formula `min(current_delay, eta_ceiling)` actively erases current delay when ETA is optimistic.

## UX Constraint

**Underprediction is safe** — telling you 5m delay when it's 60m means you wait, but you catch the boat. Overprediction (60m when it's 5m) means you miss the ferry. The prediction should err toward underprediction.

## Chosen Approach

1. **Flat propagation becomes the default** for all predictions. Observable current delay is the ground truth.
2. **ETA is surfaced as an informational note** when it would predict an earlier departure than flat prop. User sees: "Currently showing Nm delay based on observed sailing patterns. WSDOT expects departure at HH:MM."

This retains the safe bias, doesn't discard information, and lets users make their own judgment about ETA reliability.

## Physical Recovery Constraint

A vessel can't reduce delay by more than ~25% of crossing time during a crossing. For sea-bi (35min): max recovery ≈ 9min. Any prediction that assumes more recovery than that is unrealistic. This could be used as a floor: `max(option_a_prediction, current_delay - max_recovery)`.

## Error Analysis Tooling

The analysis pipeline (`scripts/analyze_prediction_outliers.py`) reconstructs predictions from historical vessel snapshots and compares to actual delays. The viewer (`reports/prediction_viewer.html`) provides an interactive step-through interface with map and timeline.

Key metrics:
- MAE (Mean Absolute Error) by horizon
- ±3min / ±5min accuracy
- Bias (systematic under/overprediction)
- Missed delays (predicted ≤3min, actual >10min)
- Big overpredictions (predicted >10min, actual ≤3min)

## Previous Work

- Feb-Mar 2026: ML models (quantile GBT) + at-dock model active
- Apr 9: Replaced with pure ETA-bounded prediction (commit #67)
- Jun 21: Inbound vessel prediction fix (#77)
- Jun 24: Null-field fix (#82)
- Jun 27: Impossible pre-ETA anchoring fix (#84)
