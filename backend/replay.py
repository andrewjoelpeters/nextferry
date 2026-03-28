"""Replay mode: serve the app with captured WSDOT API responses.

Captures are JSON files containing the raw WSDOT API responses for all three
endpoints (vessels, schedules, sailing space) plus the timestamp they were
collected at. In replay mode, the app serves this data instead of hitting the
live API, and datetime.now() is overridden to the capture time.

Scenarios may also contain a ``vessel_history`` array — a series of vessel
position snapshots captured over a time window before the final snapshot.
At replay startup the user can step through snapshots with keyboard controls
(arrow keys), watching the delay cache accumulate naturally — matching
production behavior where delays are observed across many polling cycles.

Usage:
    # Capture a scenario from the live API right now
    uv run python -m scripts.capture_scenario

    # Start the app replaying that scenario
    NEXTFERRY_SCENARIO=scenarios/2025-12-16T17_30.json uvicorn backend.main:app --reload
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

PT = ZoneInfo("America/Los_Angeles")

# Global replay state
_replay_time: datetime | None = None
_scenario_data: dict | None = None
_snapshots: list[dict] = []  # [{captured_at, vessels}, ...]
_snapshot_index: int = 0


def activate_replay(scenario_path: str) -> datetime:
    """Load a captured scenario and set replay time to its capture timestamp."""
    global _replay_time, _scenario_data, _snapshots, _snapshot_index

    path = Path(scenario_path)
    if not path.is_absolute():
        # Resolve relative to project root
        path = Path(__file__).parent.parent / path

    with open(path) as f:
        _scenario_data = json.load(f)

    # Build ordered snapshot list: history first, then the final capture
    history = _scenario_data.get("vessel_history", [])
    final = {
        "captured_at": _scenario_data["captured_at"],
        "vessels": _scenario_data["vessels"],
    }
    _snapshots = history + [final]
    _snapshot_index = 0

    # Start at first snapshot
    _apply_snapshot(0)

    logger.info(
        f"Replay mode: {path.name} ({len(_snapshots)} snapshots, "
        f"starting at {_replay_time.isoformat()})"
    )
    return _replay_time


def _apply_snapshot(index: int) -> None:
    """Set replay time and vessel data from the snapshot at the given index."""
    global _replay_time, _snapshot_index

    _snapshot_index = index
    snap = _snapshots[index]

    _replay_time = datetime.fromisoformat(snap["captured_at"])
    if _replay_time.tzinfo is None:
        _replay_time = _replay_time.replace(tzinfo=PT)

    # Swap the vessel data that wsdot_client reads
    _scenario_data["vessels"] = snap["vessels"]


def advance_snapshot() -> dict | None:
    """Move to the next snapshot. Returns snapshot info, or None if at end."""
    if _snapshot_index >= len(_snapshots) - 1:
        return None
    _apply_snapshot(_snapshot_index + 1)
    return get_snapshot_info()


def retreat_snapshot() -> dict | None:
    """Move to the previous snapshot. Returns snapshot info, or None if at start."""
    if _snapshot_index <= 0:
        return None
    _apply_snapshot(_snapshot_index - 1)
    return get_snapshot_info()


def get_snapshot_info() -> dict:
    """Return current snapshot position and metadata."""
    return {
        "index": _snapshot_index,
        "total": len(_snapshots),
        "captured_at": _replay_time.isoformat() if _replay_time else None,
        "at_start": _snapshot_index == 0,
        "at_end": _snapshot_index >= len(_snapshots) - 1,
    }


def get_replay_time() -> datetime | None:
    return _replay_time


def get_scenario_data() -> dict | None:
    return _scenario_data


def get_vessel_history() -> list[dict]:
    """Return the vessel history snapshots, or empty list for legacy scenarios."""
    if _scenario_data is None:
        return []
    return _scenario_data.get("vessel_history", [])


def current_time() -> datetime:
    """Drop-in replacement for datetime.now() that respects replay mode."""
    if _replay_time:
        return _replay_time
    return datetime.now(tz=PT)
