# Proposal: Data Flow Improvements

## Problem

The sailing data pipeline passes through ~5 transformation stages, and several structural issues make the code harder to maintain and more fragile than necessary:

1. **Information is destroyed mid-pipeline and immediately needed again.** `to_route_sailing()` strips terminal IDs from `DirectionalSailing`, then `display_processing.py` reaches up to the parent `schedule` object to get them back (lines 110, 130, 132).

2. **Parallel data paths are joined by fragile keys.** Schedule data and capacity data are fetched independently and stitched together via `(terminal_id, "%Y-%m-%d %H:%M")` string keys. If the two APIs disagree on seconds, or formatting drifts, the join silently fails — no error, no logging, capacity just disappears.

3. **Route config lookups are duplicated everywhere.** At least three places do `for route in ROUTES: if terminal_id in route["terminals"]` — `display_processing.py:13`, `next_sailings.py:110`, and `data_collector.py:59`.

## Current pipeline

```
WSDOT APIs (3 calls: vessels, schedule, sailing_space)
  → Pydantic models (Vessel, RawDirectionalSchedule, TerminalSpace)
  → next_sailings.py: filter by vessel state, mutate delays, annotate vessel info
  → serializers.py: DirectionalSailing → RouteSailing (terminal IDs stripped)
  → display_processing.py: format for templates, re-lookup terminal IDs from parent
  → plain dicts → Jinja2 templates
```

The capacity data flows separately:
```
WSDOT sailing_space API
  → sailing_space.py: build SpaceLookup dict keyed by (terminal_id, time_string)
  → display_processing.py: joined to sailings by matching the string key
```

## Proposed changes

### 1. Eliminate `RouteSailing` — use `DirectionalSailing` everywhere

**Problem:** `RouteSailing` exists only as a stripped-down version of `DirectionalSailing` with terminal IDs removed. `DirectionalSchedule.times` is `List[RouteSailing]`. But `display_processing.py` needs terminal IDs for every sailing — to look up capacity, compute route abbreviations, and run fill predictions — so it reaches through to `schedule.departing_terminal_id`.

**Fix:** Delete `RouteSailing`. Change `DirectionalSchedule.times` to `List[DirectionalSailing]`. Delete `to_route_sailing()`. Each sailing carries its own identity through the entire pipeline.

**Diff sketch:**

In `serializers.py`:
```python
# Delete RouteSailing class entirely
# Delete DirectionalSailing.to_route_sailing() method

class DirectionalSchedule(BaseModel):
    departing_terminal_id: int
    departing_terminal_name: str
    arriving_terminal_id: int
    arriving_terminal_name: str
    times: List[DirectionalSailing]  # was List[RouteSailing]
```

In `next_sailings.py`, `get_directional_schedules()`:
```python
# Before:
direction_groups[direction_meta].append(sailing)
# ...
times=sorted(
    [sailing.to_route_sailing() for sailing in sailings],
    key=lambda x: x.scheduled_departure,
),

# After:
direction_groups[direction_meta].append(sailing)
# ...
times=sorted(sailings, key=lambda x: x.scheduled_departure),
```

In `display_processing.py`, sailing-level lookups become direct:
```python
# Before:
space_lookup.get((schedule.departing_terminal_id, time_key))
_get_route_abbrev(schedule.departing_terminal_id)

# After:
space_lookup.get((sailing.departing_terminal_id, time_key))
_get_route_abbrev(sailing.departing_terminal_id)
```

**Risk:** Low. This is a simplification — fewer classes, fewer conversions, no behavior change.

### 2. Centralize route config lookups

**Problem:** The pattern `for route in ROUTES: if terminal_id in route["terminals"]` appears in:
- `display_processing.py:13` (`_get_route_abbrev`)
- `next_sailings.py:110` (inside `propigate_delays`)
- `next_sailings.py:64` (`get_route_vessels`, different pattern but same config)

**Fix:** Add a single lookup function in `config.py`:

```python
# Precompute terminal → route mapping
_TERMINAL_TO_ROUTE = {}
for _route in ROUTES:
    for _tid in _route["terminals"]:
        _TERMINAL_TO_ROUTE[_tid] = _route


def get_route_for_terminal(terminal_id: int) -> Optional[dict]:
    """Look up route config by terminal ID. O(1)."""
    return _TERMINAL_TO_ROUTE.get(terminal_id)


def get_route_abbrev(terminal_id: int) -> str:
    """Get route abbreviation for a terminal, or 'unknown'."""
    route = _TERMINAL_TO_ROUTE.get(terminal_id)
    return route["route_name"] if route else "unknown"
```

Delete `_get_route_abbrev` from `display_processing.py` and the inline loop in `propigate_delays`. Import from config instead.

**Risk:** None. Pure deduplication.

### 3. Unify the capacity join key with `sailing_id`

**Problem:** `sailing_space.py` builds a lookup keyed by `(terminal_id, departure_time.strftime("%Y-%m-%d %H:%M"))`. `display_processing.py` reconstructs this key from `sailing.scheduled_departure.strftime("%Y-%m-%d %H:%M")`. This works because both happen to format the same datetime the same way — but it's a string-based join with no type safety and silent failure on mismatch.

**Fix (after canonical sailing IDs land):** Key the space lookup by `sailing_id` instead of a formatted time string:

```python
# sailing_space.py
from .sailing_id import make_sailing_id

def get_sailing_space_lookup() -> SpaceLookup:
    for terminal in terminals:
        for sailing in terminal.departing_spaces:
            if not sailing.departure:
                continue
            hhmm = sailing.departure.strftime("%H%M")
            for arrival in sailing.space_for_arrival_terminals:
                sid = make_sailing_id(hhmm, terminal.terminal_id, arrival.terminal_id)
                lookup[sid] = {
                    "drive_up_space_count": arrival.drive_up_space_count,
                    "max_space_count": arrival.max_space_count,
                }
```

```python
# display_processing.py
capacity = None
if space_lookup and sailing.sailing_id:
    space_info = space_lookup.get(sailing.sailing_id)
    # ...
```

The join becomes a single key lookup with no string formatting at the call site, and a failed match is trivially loggable.

**Risk:** Low, but depends on proposal 1 (sailing needs terminal IDs) and the canonical ID proposal landing first.

## What this does NOT change

- **Vessel-to-sailing matching logic** in `next_sailings.py` — the at-dock/en-route/unknown branching stays. That complexity is inherent to the problem (live vessel state is messy).
- **Mutation pattern** in `next_sailings.py` — sailings are still enriched in-place with delay/vessel state. This is a real code smell but the blast radius of fixing it is larger and the current code works. Worth revisiting but not in this PR.
- **Display processing structure** — the big loop in `process_routes_for_display` is straightforward formatting. Not broken, doesn't need redesigning.

## Implementation order

| Item | Depends on | Effort | Priority |
|------|-----------|--------|----------|
| Eliminate `RouteSailing`, use `DirectionalSailing` throughout | Nothing | Small | P0 |
| Centralize route config lookups in `config.py` | Nothing | Small | P0 |
| Unify space lookup key to `sailing_id` | Canonical ID proposal | Small | P1 |

Items 1 and 2 can be done independently and immediately — they don't depend on the canonical sailing ID proposal. Item 3 is a natural follow-on once sailing IDs exist.
