# Proposal: Current Vessel Load Feature for Delay Prediction

## Problem

The time it takes a vessel to unload and reload at a terminal directly affects turnaround time and departure delays. A vessel carrying 200 cars takes significantly longer to unload than one carrying 5. The model currently has no feature representing the actual vehicle load on the vessel for its current trip.

The existing `previous_sailing_fullness` feature is related but captures something different: it measures how full the *last boat that arrived at the departing terminal* was, as a proxy for terminal-level demand. It does not tell the model how many vehicles the *current vessel* is carrying on its inbound trip, which is what drives unload time.

## Current state

**`previous_sailing_fullness`** (the closest existing feature):
- Source: `sailing_space_snapshots` table
- Computed as: `1.0 - drive_up_space_count / max_space_count` for the most recent sailing that arrived at the *departing terminal*
- Joined via `merge_asof` on `arriving_terminal_id` matching `departing_terminal_id` of the predicted sailing
- Purpose: demand/congestion proxy — "is this terminal busy?"

**`turnaround_minutes`** captures actual dock-to-departure time from historical snapshots, but at prediction time it's computed from when the vessel first appears at dock, not from the expected unload duration.

Neither feature answers: "how loaded is the vessel that's about to arrive and unload?"

## Proposed changes

### New feature

Add to `FEATURE_COLS`:

**`current_vessel_fullness`** — The capacity utilization of the predicted vessel on its *inbound* trip (the trip arriving at the departing terminal just before the predicted sailing). Computed as `1.0 - drive_up_space_count / max_space_count` from `sailing_space_snapshots`, matched to the vessel's current or most recent inbound sailing.

### Training data construction (`ml_predictor.py`)

Add a query that:

1. For each sailing event, identifies the vessel's *previous* trip — the inbound sailing that brought the vessel to the departing terminal.
2. Looks up the fullness of that inbound trip from `sailing_space_snapshots`, matching on `vessel_id` and the departure time of the inbound sailing.
3. Joins via `merge_asof` with `direction="backward"` to get the most recent space snapshot for that inbound trip before the prediction time.

This differs from the existing `previous_sailing_fullness` join in that it follows the *vessel*, not the *terminal*. The current feature asks "how full was the last boat to arrive here (regardless of which vessel)?" while this asks "how full was *this specific vessel* on its way in?"

### Inference path

At prediction time, the inbound sailing's space data is available from the WSDOT sailing space API (already fetched and cached). The predict call site in `next_sailings.py` would look up the vessel's current or most recent inbound trip and pass its fullness to the feature dict.

### Relationship to `previous_sailing_fullness`

Both features should coexist — they capture different signals:

| Feature | Question answered | Signal |
|---|---|---|
| `previous_sailing_fullness` | How full was the last boat to arrive at this terminal? | Terminal demand level |
| `current_vessel_fullness` | How full is this vessel on its inbound trip? | Expected unload duration |

The model can learn that high `current_vessel_fullness` → longer unload → more turnaround time needed, independent of overall terminal demand.

## Risks and considerations

- **Space data availability:** `sailing_space_snapshots` may not have data for every inbound trip (collection gaps, API failures). Default to `NaN` and let the HistGradientBoosting model handle missing values natively (it supports this).
- **Timing:** Space snapshots are point-in-time. The fullness of an inbound sailing can change as the vessel approaches (late drive-up reservations updating). Use the most recent snapshot before the prediction horizon.
- **Routes with reservation-heavy traffic:** On routes where most vehicles are reserved, `drive_up_space_count` may not fully reflect total load. If `total_space_count` or reservation data becomes available, the feature could be refined.

## Expected impact

Medium. This adds a direct signal for unload duration that the model currently lacks. The impact will be strongest for sailings where the vessel has an unusually high or low load compared to the route's typical pattern — those are exactly the cases where turnaround time deviates from the historical average the model has learned.
