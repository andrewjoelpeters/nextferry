# Proposal: Simplified Prediction Pipeline — At-Dock Model + WSDOT ETA

## Motivation

The current two-model architecture (en-route model + dock model) independently
predicts delay for each future sailing. The en-route model uses vessel speed and
time-horizon features to guess how a delay will evolve — but WSDOT already tracks
vessel GPS and provides a real-time ETA. We're effectively trying to re-derive
something the source system already tells us.

**Proposed shift:** Replace the en-route ML model with WSDOT's ETA field, and
propagate delays forward using a chain of crossing times + at-dock predictions.
This is simpler, more grounded in physics, and eliminates the weakest part of our
prediction pipeline.

---

## Current Architecture

```
Vessel at dock:
  sailing[0] → dock model predicts delay
  sailing[1..N] → en-route model predicts delay independently per sailing

Vessel en route:
  sailing[0..N] → en-route model predicts delay independently per sailing
```

The en-route model takes `current_vessel_delay_minutes`, `vessel_speed`, and
`minutes_until_scheduled_departure` as key features. It learns a mapping from
"current state → predicted delay at future departure." This has two problems:

1. **Redundant with WSDOT ETA.** The API already tells us when the vessel will
   arrive. Our model is trying to infer arrival time from speed/delay, which is
   strictly less information than the GPS-derived ETA.
2. **Compounding error for future sailings.** For sailings 2+ out, the model
   uses the same snapshot features with only `minutes_until_scheduled_departure`
   varying. It can't account for what happens at intermediate turnarounds.

---

## Proposed Architecture

```
Vessel en route → WSDOT ETA gives arrival time
  ↓
Vessel arrives at dock → compute turnaround time
  ↓
At-dock model predicts departure delay for next sailing
  ↓
Estimated departure = scheduled_departure + predicted_delay
  ↓
Estimated arrival at opposite terminal = estimated_departure + crossing_time
  ↓
Repeat: compute turnaround → dock model → departure → crossing → ...
```

### Core Idea

Every prediction reduces to one question the dock model already answers well:
**"Given how long this vessel has been (or will be) at dock, what's the departure
delay?"** We chain these predictions forward using known crossing times.

---

## Components Changed

### 1. `backend/next_sailings.py` — Major Changes

**Remove `propigate_delays()` entirely.** Replace with a new
`propagate_via_chain()` function that:

1. Takes the vessel's current state (at dock or en route) and the full list of
   future sailings for that vessel.
2. Determines the vessel's next arrival time:
   - **If en route:** Use `vessel.eta` from WSDOT (fall back to
     `scheduled_arrival` estimate if ETA is null — see Gotchas below).
   - **If at dock:** Already arrived; `minutes_at_dock` is known.
3. For each sailing in sequence:
   a. Compute `estimated_turnaround` = time from arrival to `scheduled_departure`.
   b. If `arrival_time > scheduled_departure`, the sailing is inherently late:
      `min_delay = arrival_time - scheduled_departure`.
   c. Call the dock model with the estimated turnaround to predict departure delay.
   d. Clamp prediction: `delay >= min_delay` (can't depart before arriving).
   e. `estimated_departure = scheduled_departure + predicted_delay`.
   f. `estimated_arrival = estimated_departure + route_crossing_time`.
   g. Feed `estimated_arrival` into the next iteration.

**Remove `_build_en_route_features()`.** No longer needed.

**Simplify `get_next_sailings_by_boat()`.** No need to hold back the first
sailing or branch between dock/en-route models. Every sailing goes through the
same chain.

### 2. `backend/ml_predictor.py` — Remove En-Route Model

- Remove the en-route `QuantileGBTModel` instance.
- Keep the dock model (rename from `dock_predictor` to just `predictor` or
  `departure_predictor`).
- The dock model's feature set stays the same: `route_abbrev`,
  `departing_terminal_id`, `vessel_id`, `day_of_week`, `hour_of_day`,
  `minutes_at_dock`, `incoming_vehicle_fullness`, `current_vessel_delay_minutes`.
- **New capability needed:** The model must accept *estimated* turnaround times
  for future sailings (not just observed `minutes_at_dock`). This is already how
  the feature works — it's just minutes, whether observed or projected.

### 3. `backend/crossing_times.py` — New Module

A small module providing average crossing times per route. Two options:

**Option A — Static config (start here):**
```python
# Median crossing times from historical sailing_events data
CROSSING_TIMES: dict[str, float] = {
    "sea-bi": 35.0,   # minutes
    "ed-king": 30.0,
}
```

**Option B — Dynamic (future enhancement):**
Query `sailing_events` for recent median crossing times per route/direction.
Update daily alongside model retraining.

**Recommendation:** Start with Option A (static). Crossing times are very
consistent for a given route. We can compute initial values from historical data
and revisit if needed.

### 4. `backend/model_training/backtest_model.py` — Simplify

- Remove en-route feature definitions and training pipeline.
- Keep dock-model feature definitions as-is.
- The `FEATURE_COLS` list becomes the dock model's features only.

### 5. `backend/main.py` — Minor Changes

- Remove the en-route model loading/training from lifespan startup.
- Simplify the daily retrain task to only retrain one model.
- The `dock_predictor` singleton becomes the sole predictor.

### 6. `backend/display_processing.py` — No Structural Changes

Display processing already consumes `delay_in_minutes`, `delay_lower_bound`,
and `delay_upper_bound` generically per sailing. The source of these values
changes (chain propagation instead of independent prediction), but the display
contract stays the same.

### 7. `backend/data_collector.py` — No Changes

We still collect vessel snapshots and sailing events. The training data for the
dock model comes from the same `sailing_events` + `vessel_snapshots` tables.

---

## New State Management

### Crossing Time State

The chain propagation needs to know how long each crossing takes. This is **route-level
configuration**, not per-request state. A static dict (or daily-computed cache) is
sufficient.

### No New Per-Request State

The chain is computed fresh on every cache update cycle (every 30 seconds), using:
- Current vessel position (from WSDOT API)
- Current WSDOT ETA (from WSDOT API)
- Schedule (from WSDOT API)
- Dock model (loaded singleton)
- Crossing times (static config)

There is **no accumulating state** between cache cycles. Each 30-second update
recomputes the full chain from scratch using the latest vessel data.

### Cached Delay Fallback

The existing `CACHED_DELAYS` dict (vessel's last-known delay) is still useful as
a fallback when WSDOT ETA is null. Keep it.

---

## Delay Propagation: Detailed Walkthrough

### Example: Seattle–Bainbridge, vessel M/V Wenatchee

**State:** En route from Bainbridge to Seattle, ETA 10:05 AM.

**Schedule (Wenatchee's remaining sailings):**
| # | Depart | From | To |
|---|--------|------|-----|
| 1 | 10:20 AM | Seattle | Bainbridge |
| 2 | 11:10 AM | Bainbridge | Seattle |
| 3 | 12:00 PM | Seattle | Bainbridge |

**Chain computation:**

1. **Arrival at Seattle:** ETA = 10:05 AM (from WSDOT).
2. **Sailing 1 (SEA→BI, sched 10:20):**
   - Turnaround = 10:20 - 10:05 = 15 min.
   - Dock model predicts with `minutes_at_dock=15`: delay = +3 min.
   - Estimated departure = 10:23 AM.
   - Estimated arrival at Bainbridge = 10:23 + 35 min crossing = 10:58 AM.
3. **Sailing 2 (BI→SEA, sched 11:10):**
   - Turnaround = 11:10 - 10:58 = 12 min.
   - Dock model predicts with `minutes_at_dock=12`: delay = +5 min.
   - Estimated departure = 11:15 AM.
   - Estimated arrival at Seattle = 11:15 + 35 = 11:50 AM.
4. **Sailing 3 (SEA→BI, sched 12:00):**
   - Turnaround = 12:00 - 11:50 = 10 min.
   - Dock model predicts with `minutes_at_dock=10`: delay = +7 min.
   - Estimated departure = 12:07 PM.

Notice how delays **naturally compound**: a short turnaround (because the vessel
arrived late) produces a larger predicted delay, which pushes the next arrival
later, compressing the next turnaround further. This is physically correct and
something the current en-route model cannot capture.

### Edge Case: Vessel Already Late

If ETA is 10:25 AM but the scheduled departure is 10:20 AM:
- Turnaround = 10:20 - 10:25 = **-5 min** (negative → vessel hasn't arrived yet).
- `min_delay = 5 min` (can't depart before arriving).
- Dock model gets `minutes_at_dock=0` (just arrived).
- Predicted delay = max(model_prediction, 5 min + minimum_loading_time).

---

## Handling WSDOT ETA Gaps

Per the CLAUDE.md gotcha: *"WSDOT vessel data can have null fields even when the
vessel is moving."* The `eta` field can be null.

**Fallback strategy when `vessel.eta` is null:**

1. **Vessel en route (`at_dock=False`, `speed > 0`):** Estimate arrival from
   `left_dock + route_crossing_time`. If `left_dock` is also null, use
   `CACHED_DELAYS` flat propagation as today.
2. **Vessel at dock (`at_dock=True`):** ETA is the docked-since time (already
   handled via `vessel.eta` or `sailing.vessel_docked_since`).
3. **Vessel state unknown:** Fall back to flat propagation (no change from current
   behavior).

---

## Confidence Intervals

The dock model already produces quantile predictions (q15/q50/q85). In the chain:

- **Sailing 1:** Confidence bounds come directly from the dock model.
- **Sailing 2+:** Uncertainty compounds. Two options:
  - **Simple (recommended):** Widen bounds by a fixed factor per hop (e.g., ±2 min
    per additional sailing in the chain). This is honest about decreasing
    certainty further out.
  - **Monte Carlo (future):** Sample from the dock model's distribution at each
    step and propagate. More accurate but computationally heavier.

**Recommendation:** Start with the simple widening approach. The current en-route
model's confidence bounds for sailing 3+ aren't well-calibrated anyway, so even a
heuristic widening is an improvement in honesty.

---

## Migration Plan

### Phase 1: Add Crossing Times + Chain Propagation (behind flag)
1. Create `backend/crossing_times.py` with static crossing times.
2. Compute initial values from `sailing_events` historical data.
3. Implement `propagate_via_chain()` in `next_sailings.py`.
4. Add a feature flag (`USE_CHAIN_PROPAGATION = True/False`) to toggle between
   old and new pipeline.
5. Tests: Unit test chain propagation with mock dock model and known crossing times.

### Phase 2: Validate with Replay Mode
1. Capture several scenarios spanning different delay conditions.
2. Run both pipelines on the same scenarios.
3. Compare prediction accuracy (predicted vs actual departure delay).
4. Verify edge cases: null ETA, late arrivals, cancelled sailings.

### Phase 3: Remove En-Route Model
1. Remove en-route model training from `ml_predictor.py`.
2. Remove `_build_en_route_features()` from `next_sailings.py`.
3. Remove en-route model loading from `main.py` lifespan.
4. Clean up `backtest_model.py` feature definitions.
5. Remove feature flag, make chain propagation the only path.

### Phase 4: Tune (Optional)
1. Switch to dynamic crossing times if route conditions vary.
2. Implement Monte Carlo confidence propagation if simple widening proves
   insufficient.

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| WSDOT ETA is null frequently | Chain can't start | Fallback to `left_dock + crossing_time`, then flat propagation |
| Crossing times vary (weather, tides) | Chain accumulates error | Start static, switch to rolling median if needed |
| Dock model accuracy at low turnaround times | May underpredict delay when vessel is very late | Enforce `delay >= arrival_overshoot + min_loading_time` floor |
| Removing en-route model loses some signal | Predictions for en-route vessels may be less nuanced in the short-term | WSDOT ETA is more accurate for the immediate crossing than our speed-based model |

---

## Summary

| Aspect | Current | Proposed |
|--------|---------|----------|
| En-route prediction | ML model (speed, delay, horizon) | WSDOT ETA (GPS-derived) |
| At-dock prediction | Dock ML model | Same dock ML model |
| Future sailing propagation | Independent per-sailing prediction | Chained: arrival → turnaround → dock model → departure → crossing → repeat |
| Delay compounding | Not modeled (each sailing predicted in isolation) | Naturally emerges from chain |
| Models to maintain | 2 (en-route + dock) | 1 (dock only) |
| New dependencies | None | Route crossing times (static config) |
| Confidence intervals | Quantile model per sailing | Quantile model + uncertainty widening per hop |
