# Proposal: Canonical Sailing IDs

## Problem

Sailings are identified by different composite keys depending on context:

| Context | Key | Location |
|---------|-----|----------|
| DB sailing events | `(vessel_id, scheduled_departure)` | `database.py:74` |
| Capacity lookup | `(departing_terminal_id, "%Y-%m-%d %H:%M")` | `sailing_space.py:29` |
| Vessel grouping | `vessel_position_num` | `next_sailings.py:73` |
| Direction grouping | `(dep_term_id, dep_name, arr_term_id, arr_name)` | `next_sailings.py:231` |
| Vessel state match | `scheduled_departure == vessel.scheduled_departure` | `next_sailings.py:178` |
| Display key | `scheduled_departure_iso` string | `display_processing.py:184` |

There's no single, stable identifier for "the 2:35 PM Seattle→Bainbridge sailing." Every piece of code that needs to find, match, or query a sailing reinvents its own lookup. Historical queries require ad-hoc joins across multiple columns.

## Proposal

Introduce a **canonical sailing ID** — a string that uniquely identifies a recurring schedule slot:

```
{HHMM}-{departing_terminal_id}-{arriving_terminal_id}
```

**Example:** `1435-7-3` = the 2:35 PM sailing from Seattle (terminal 7) to Bainbridge (terminal 3).

### Design decisions

- **Time-first ordering** so IDs sort chronologically across all routes.
- **Date is excluded** from the ID. The ID represents the schedule slot, not a specific instance. A specific instance is `(sailing_id, date)`. This makes historical queries natural — "give me the last 30 days of sailing `1435-7-3`" is a single WHERE clause.
- **Vessel-agnostic.** The sailing identity is the terminal pair + time, not which boat happens to run it. Vessel swaps don't change the sailing ID.

### Operations this enables

| Operation | How |
|-----------|-----|
| Look up this sailing's delay yesterday | `SELECT delay_minutes FROM sailing_events WHERE sailing_id = '1435-7-3' AND date(scheduled_departure) = date('now', '-1 day')` |
| Last 30 days of this sailing | `SELECT * FROM sailing_events WHERE sailing_id = '1435-7-3' AND scheduled_departure >= date('now', '-30 days')` |
| Incoming boat's delay | Swap terminal segments: `1435-7-3` → scan for latest `*-3-7` before 14:35 — i.e. the most recent sailing from Bainbridge→Seattle that arrived before this departure |
| All sailings on a route today | `WHERE sailing_id LIKE '%-7-3' OR sailing_id LIKE '%-3-7'` |

## Implementation

### Step 1: Add `sailing_id` property to `DirectionalSailing`

In `backend/serializers.py`, add a computed property:

```python
class DirectionalSailing(RouteSailing):
    departing_terminal_id: int
    arriving_terminal_id: int
    departing_terminal_name: str
    arriving_terminal_name: str

    @property
    def sailing_id(self) -> Optional[str]:
        if self.scheduled_departure is None:
            return None
        time_part = self.scheduled_departure.strftime("%H%M")
        return f"{time_part}-{self.departing_terminal_id}-{self.arriving_terminal_id}"
```

This is a pure derivation from existing fields — no new data to carry around.

### Step 2: Add `sailing_id` column to `sailing_events` table

In `backend/database.py`, update the schema:

```sql
CREATE TABLE IF NOT EXISTS sailing_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vessel_id INTEGER NOT NULL,
    vessel_name TEXT NOT NULL,
    route_abbrev TEXT,
    departing_terminal_id INTEGER,
    arriving_terminal_id INTEGER,
    scheduled_departure TEXT NOT NULL,
    actual_departure TEXT NOT NULL,
    delay_minutes REAL NOT NULL,
    day_of_week INTEGER NOT NULL,
    hour_of_day INTEGER NOT NULL,
    sailing_id TEXT,
    UNIQUE(vessel_id, scheduled_departure)
);
```

- Add `sailing_id TEXT` column (nullable for backward compat with existing rows).
- Add an index: `CREATE INDEX IF NOT EXISTS idx_sailing_events_sailing_id ON sailing_events(sailing_id)`.
- Populate on insert in `extract_sailing_events()`: compute from `scheduled_departure`, `departing_terminal_id`, `arriving_terminal_id`.
- Backfill existing rows: `UPDATE sailing_events SET sailing_id = printf('%02d%02d', cast(strftime('%H', scheduled_departure) as int), cast(strftime('%M', scheduled_departure) as int)) || '-' || departing_terminal_id || '-' || arriving_terminal_id WHERE sailing_id IS NULL`.

### Step 3: Add helper to parse/manipulate sailing IDs

In a new file `backend/sailing_id.py`:

```python
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SailingIdParts:
    time: str          # "HHMM"
    dep_terminal: int
    arr_terminal: int

    @property
    def hour(self) -> int:
        return int(self.time[:2])

    @property
    def minute(self) -> int:
        return int(self.time[2:])

    def incoming(self) -> "SailingIdParts":
        """The reverse-direction sailing (swap terminals)."""
        return SailingIdParts(
            time=self.time,
            dep_terminal=self.arr_terminal,
            arr_terminal=self.dep_terminal,
        )

    def __str__(self) -> str:
        return f"{self.time}-{self.dep_terminal}-{self.arr_terminal}"


def parse_sailing_id(sailing_id: str) -> Optional[SailingIdParts]:
    """Parse a sailing ID string like '1435-7-3' into its components."""
    parts = sailing_id.split("-")
    if len(parts) != 3:
        return None
    return SailingIdParts(
        time=parts[0],
        dep_terminal=int(parts[1]),
        arr_terminal=int(parts[2]),
    )


def make_sailing_id(hhmm: str, dep_terminal_id: int, arr_terminal_id: int) -> str:
    """Construct a sailing ID from components."""
    return f"{hhmm}-{dep_terminal_id}-{arr_terminal_id}"
```

### Step 4: Refactor historical DB queries

Replace ad-hoc composite key lookups with `sailing_id`-based queries:

**`get_previous_sailing_fullness()`** (`database.py:313-343`): Currently queries `sailing_space_snapshots` by `arriving_terminal_id` and `departure_time <=`. Refactor to compute the incoming sailing ID (swap terminals), then query by `sailing_id` on the target date.

**`get_vessel_delay_at_time()`** (`database.py:280-310`): Currently queries `vessel_snapshots` by `vessel_id` and time range. This one is vessel-specific (looking at the same physical boat's prior delay), so `sailing_id` doesn't directly replace it — but could augment it for "same slot, yesterday" queries.

**New query — `get_sailing_delay_history()`**: Return delay history for a `sailing_id` over a date range. This doesn't exist today and would be trivial with the new column.

### Step 5 (future): Add `sailing_id` to `sailing_space_snapshots`

The capacity table currently uses `(departing_terminal_id, arriving_terminal_id, departure_time)` as part of its unique constraint. Adding `sailing_id` here would unify the lookup key with `sailing_events`, enabling joins like "for sailing `1435-7-3` on March 22, what was the capacity AND the delay?"

Not required for the initial change but a natural follow-on.

## What this does NOT change

- **Live vessel-to-sailing matching** in `next_sailings.py` — the conditional logic for at-dock vs en-route, direction validation, null field handling stays the same. The sailing ID doesn't simplify real-time state matching.
- **Display processing** — formatting times, computing "time until departure", capacity bars. These operate on the sailing object, not on IDs.
- **ML feature engineering** — features are derived from raw fields (day_of_week, hour_of_day, etc.), not from IDs.

## Risks and edge cases

- **Schedule changes across seasons.** The `1435-7-3` slot might not exist on every day. This is fine — queries for nonexistent dates simply return no rows. Historical trend queries should filter to dates where the slot was active.
- **Minute-level collisions.** Could two different sailings depart the same terminal pair at the same HHMM? In practice, no — WSF doesn't schedule two boats from the same terminal to the same destination at the same minute. If this ever happened, we'd need to revisit.
- **Overnight schedule boundaries.** Sailings near midnight (e.g. `2350-7-3`) sort correctly since HHMM is zero-padded. A "next day" query just changes the date filter.

## Scope

| Item | Effort | Priority |
|------|--------|----------|
| `sailing_id` property on `DirectionalSailing` | Small | P0 |
| `sailing_id` column + index on `sailing_events` | Small | P0 |
| `sailing_id.py` parse/construct helpers | Small | P0 |
| Backfill existing `sailing_events` rows | Small | P0 |
| Populate `sailing_id` in `extract_sailing_events()` | Small | P0 |
| Refactor `get_previous_sailing_fullness()` | Medium | P1 |
| New `get_sailing_delay_history()` query | Small | P1 |
| Add `sailing_id` to `sailing_space_snapshots` | Medium | P2 |
| Unify `SpaceLookup` key to use `sailing_id` | Medium | P2 |
