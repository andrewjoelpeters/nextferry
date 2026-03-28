"""Replay mode: serve the app with captured WSDOT API responses.

Captures are JSON files containing the raw WSDOT API responses for all three
endpoints (vessels, schedules, sailing space) plus the timestamp they were
collected at. In replay mode, the app serves this data instead of hitting the
live API, and datetime.now() is overridden to the capture time.

Scenarios may also contain a ``vessel_history`` array — a series of vessel
position snapshots captured over a time window before the final snapshot.
At replay startup the app fast-forwards through this history to pre-warm
the delay cache, matching production behavior where delays are observed
across many polling cycles.

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


def activate_replay(scenario_path: str) -> datetime:
    """Load a captured scenario and set replay time to its capture timestamp."""
    global _replay_time, _scenario_data

    path = Path(scenario_path)
    if not path.is_absolute():
        # Resolve relative to project root
        path = Path(__file__).parent.parent / path

    with open(path) as f:
        _scenario_data = json.load(f)

    _replay_time = datetime.fromisoformat(_scenario_data["captured_at"])
    if _replay_time.tzinfo is None:
        _replay_time = _replay_time.replace(tzinfo=PT)

    history = _scenario_data.get("vessel_history", [])
    logger.info(
        f"Replay mode: {path.name} (captured {_replay_time.isoformat()}, "
        f"{len(history)} history snapshots)"
    )
    return _replay_time


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
