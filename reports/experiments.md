# Experiments

Tracking model experiments, ideas, and results. Each entry describes the model configuration, what changed, and key metrics. Full evaluation reports are linked.

## Experiment Log

### 1. Baseline — QuantileGBT v2 (2026-03-22)

**Report:** [baseline_2026-03-22.md](baseline_2026-03-22.md)

**Model:** 3× `HistGradientBoostingRegressor` (quantiles q15/q50/q85)
**Hyperparameters:** max_iter=200, max_depth=6, learning_rate=0.1
**Training time:** 49.8s (5-fold walk-forward, 19,348 events)

**Features (9):**
| Feature | Type | Description |
|---------|------|-------------|
| route_abbrev | categorical | sea-bi, ed-king |
| departing_terminal_id | categorical | Terminal ID |
| day_of_week | categorical | 0–6 (Sun–Sat) |
| hour_of_day | categorical | 5–21 |
| minutes_until_scheduled_departure | numeric | Prediction horizon (2–120 min) |
| current_vessel_delay_minutes | numeric | Latest observed vessel delay |
| is_peak_hour | binary | 1 if hour in [6–9, 15–19] |
| previous_sailing_fullness | numeric | Drive-up capacity usage of prior sailing |
| turnaround_minutes | numeric | Time from dock arrival to next scheduled departure |

**Results:**
| Metric | Value |
|--------|-------|
| Pinball Loss | 3.83 min |
| MAE | 2.54 min |
| Bias | +0.04 min |
| 70% Coverage | 61.6% (target: 70%) |
| vs Naive Baseline | 46.1% improvement |

**Observations:**
- Model is nearly unbiased overall (+0.04 min), strong 46% improvement over naive "current delay = future delay" baseline.
- Coverage is under-calibrated (61.6% vs 70% target) — prediction intervals are too narrow.
- Fold 1 is a clear outlier (PL=6.7 vs mean 3.83) — likely a period with unusual delay patterns and limited training data.
- Performance varies more by time-of-day than by route: Midday is excellent (PL=1.84), AM Peak struggles (PL=4.61).
- Sundays are the hardest day (PL=5.4), likely due to less regular schedule patterns.
- Prediction horizon has almost no effect on accuracy (all ~3.83) — the model isn't leveraging horizon-specific signal.
- Sea-bi off-peak is the weakest route×period slice (PL=4.58).

---

*Add new experiments above this line.*
