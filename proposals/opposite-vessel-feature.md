# Proposal: Opposite Vessel State Feature for Delay Prediction

## Problem

The delay prediction model is entirely single-vessel — it only considers the delay, speed, and turnaround of the vessel assigned to the sailing being predicted. It has no visibility into the state of the other vessel operating on the same route.

This creates a blind spot: **dock-blocking delays**. If Vessel A is delayed and still occupying the dock at Seattle, and Vessel B is inbound to Seattle on time, Vessel B will be delayed because it cannot berth until Vessel A departs. The model currently sees Vessel B with `current_vessel_delay_minutes ≈ 0` and normal `vessel_speed`, so it predicts an on-time arrival — missing a delay that is essentially guaranteed.

This pattern is common on two-boat routes (e.g., Seattle–Bainbridge, Edmonds–Kingston) where vessels share a single slip at one or both terminals.

## Current state

The 11 features in `FEATURE_COLS` (`backend/model_training/backtest_model.py`) include no information about the opposite vessel:

- `current_vessel_delay_minutes` — delay of the predicted vessel only
- `vessel_speed` — speed of the predicted vessel only
- `turnaround_minutes` — dock time of the predicted vessel only

The `vessel_snapshots` table already stores position, speed, delay, and dock status for all vessels on all routes, so the data needed to compute opposite-vessel features is already being collected.

## Proposed changes

### New features

Add to `FEATURE_COLS`:

1. **`opposite_vessel_delay_minutes`** — The most recent `current_vessel_delay_minutes` for the other vessel on the same route at the time of prediction. Computed from `vessel_snapshots` the same way `current_vessel_delay_minutes` is, but for the paired vessel instead.

2. **`opposite_vessel_at_dock`** — Binary flag: is the opposite vessel currently at the dock the predicted vessel is heading toward? This directly captures the dock-blocking scenario. Derived from `vessel_snapshots.at_dock` where the opposite vessel's `departing_terminal_id` matches the predicted vessel's `arriving_terminal_id`.

### Training data construction (`ml_predictor.py`)

Add a new bulk query section (after the existing turnaround query) that:

1. For each sailing event, identifies the other vessel operating on the same route. Route-to-vessel mapping is already available via `route_abbrev` and `vessel_id` in the training data — group by route, find the other vessel.
2. Joins `vessel_snapshots` for the opposite vessel using `merge_asof` on timestamp (same pattern used for `previous_sailing_fullness`), matching the most recent opposite-vessel snapshot before each prediction horizon.
3. Extracts delay and at-dock status from the matched snapshot.

### Inference path (`ml_predictor.py` predict methods)

At prediction time, the opposite vessel's state is available from `_sailings_cache` in `main.py`, which already contains vessel data for all active routes. The predict call site in `next_sailings.py` would need to pass the opposite vessel's current state alongside the existing feature dict.

### Identifying the opposite vessel

On two-boat routes, the "opposite vessel" is simply the other vessel assigned to the same route. For routes with more than two vessels (rare but possible during peak season), use the vessel most recently seen heading in the opposite direction on the same route.

## Risks and considerations

- **Single-boat routes:** When a route is running with one vessel (e.g., maintenance period), there is no opposite vessel. These should default to `opposite_vessel_delay_minutes = 0.0` and `opposite_vessel_at_dock = 0`.
- **Vessel swaps:** Vessels occasionally change route assignments. The training data join should use the route at the time of the snapshot, not a static mapping.
- **Feature leakage:** Ensure the opposite vessel snapshot used in training is from *before* the prediction horizon, not after. The `merge_asof` with `direction="backward"` handles this naturally.

## Expected impact

High. Dock-blocking is a direct causal mechanism for delays that the model currently cannot detect. On two-boat routes, the opposite vessel's state is one of the strongest predictors of whether the predicted vessel will experience a cascading delay.
