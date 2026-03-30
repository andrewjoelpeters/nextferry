# Proposal: Remove CACHED_DELAYS In-Memory Cache

## Problem

`backend/next_sailings.py` maintains a global `CACHED_DELAYS = {}` dict that preserves vessel delay values across WSDOT API state transitions. This is mutable shared state that silently carries stale values. It works until it doesn't:

- **Process restarts** lose all cached delays, so vessels that are between the "en route" and "docked" states show no delay until the next departure.
- **Vessel reassignments** can leave stale delay values keyed to the old route/position, causing incorrect delay propagation.
- **Code paths that forget to clear entries** silently serve wrong data with no error signal.
- **It's a shadow copy** of data that already exists in the database, violating the principle that facts should be queried from their source of truth, not maintained in parallel.

## Current Behavior

When a vessel is en route, WSDOT provides `left_dock` and `scheduled_departure`, so the delay is computed as `left_dock - scheduled_departure`. When the vessel docks at the destination, WSDOT nulls out these fields.

To bridge this gap, `CACHED_DELAYS` (keyed by `route -> vessel_position_num -> timedelta`) preserves the last-known delay. Three functions manage this:

- `update_cached_delay()` — writes to the cache when live delay is available
- `get_cached_delay()` — reads from the cache when live delay is unavailable
- Used in `get_vessels_with_delays()` (lines 106-123), consumed by `propigate_delays()` and the display layer

## Proposed Change

Replace the in-memory cache with a database query against the `sailing_events` table, which already records `actual_departure` and `scheduled_departure` for every sailing once it departs.

### New function in `database.py`

```python
def get_last_departure_delay(vessel_id: int) -> timedelta | None:
    """Return the delay from the most recent departure for this vessel.

    Queries the sailing_events table for the vessel's last recorded sailing
    and computes actual_departure - scheduled_departure.
    Returns None if no sailing_events exist for this vessel.
    """
```

This is O(1) on the indexed `vessel_id` column.

### Changes to `next_sailings.py`

In `get_vessels_with_delays()`, replace the `get_cached_delay(v)` fallback with `get_last_departure_delay(v.vessel_id)`. Then delete `CACHED_DELAYS`, `update_cached_delay()`, and `get_cached_delay()`.

## Why This Is Better

1. **Survives restarts.** The DB has the delay from the moment it was recorded. No warm-up period, no lost state.
2. **Handles vessel reassignments.** The query is keyed by `vessel_id` and returns the most recent event, so a vessel moving to a different route automatically gets the correct delay.
3. **Single source of truth.** The `sailing_events` table already records departure facts. Querying it eliminates the parallel bookkeeping and the class of bugs where cache and reality diverge.
4. **No new infrastructure.** The table, the data, and the index already exist. This is removing code, not adding it.

Design principle: cache derived/computed values that are expensive to recompute. Query for facts that are already recorded. Don't maintain a shadow copy of data you already have.

## Risks

**Performance:** Low risk. The query hits a local WAL-mode SQLite DB with an index on `vessel_id`. It runs once per vessel per 30s refresh cycle (~10 vessels = ~10 queries). The `sailing_events` table has one row per sailing per day — it's small.

**Cold database:** On first deploy with a fresh DB (no `sailing_events` yet), the query returns `None` — identical to a cold cache today. The system gracefully degrades to showing no delay rather than a stale one.

**Replay mode:** In replay mode, the data collector is disabled so `sailing_events` won't be populated. The query returns `None`, matching current cold-cache behavior. If this matters for replay fidelity, the replay scenario loader could seed `sailing_events` from the captured snapshot.

## Migration Steps

1. Add `get_last_departure_delay(vessel_id)` to `backend/database.py` with a query against `sailing_events`.
2. Add a unit test for `get_last_departure_delay()` covering: vessel with recent departure, vessel with no events, and vessel whose last event is from a different route.
3. In `get_vessels_with_delays()`, replace the `get_cached_delay()` fallback with `get_last_departure_delay()`.
4. Remove `CACHED_DELAYS`, `update_cached_delay()`, and `get_cached_delay()` from `next_sailings.py`.
5. Run full test suite to confirm no regressions.
6. Verify in replay mode with a captured scenario that delay values display correctly during vessel state transitions.
