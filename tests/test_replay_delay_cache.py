"""Tests for replay vessel history, delay cache warming, and snapshot stepping."""

import json
import tempfile
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import backend.replay as replay_module
from backend.next_sailings import CACHED_DELAYS, warm_delay_cache
from backend.replay import (
    activate_replay,
    advance_snapshot,
    get_replay_time,
    get_snapshot_info,
    retreat_snapshot,
)

PT = ZoneInfo("America/Los_Angeles")


def _now():
    return datetime.now(PT)


def _dt_to_wsdot(dt):
    if dt is None:
        return None
    ms = int(dt.timestamp() * 1000)
    return f"/Date({ms}-0800)/"


def _make_raw_vessel(
    vessel_id=1,
    name="Walla Walla",
    position_num=1,
    route="sea-bi",
    at_dock=False,
    scheduled_departure=None,
    left_dock=None,
):
    """Build a raw WSDOT vessel dict (as it would appear in scenario JSON)."""
    return {
        "VesselID": vessel_id,
        "VesselName": name,
        "DepartingTerminalID": 3,
        "DepartingTerminalName": "Seattle",
        "DepartingTerminalAbbrev": "SEA",
        "ArrivingTerminalID": 7,
        "ArrivingTerminalName": "Bainbridge Island",
        "ArrivingTerminalAbbrev": "BI",
        "Latitude": 47.6,
        "Longitude": -122.3,
        "Speed": 12.0 if not at_dock else 0.0,
        "Heading": 270,
        "InService": True,
        "AtDock": at_dock,
        "LeftDock": _dt_to_wsdot(left_dock),
        "Eta": None,
        "ScheduledDeparture": _dt_to_wsdot(scheduled_departure),
        "TimeStamp": _dt_to_wsdot(_now()),
        "OpRouteAbbrev": [route],
        "VesselPositionNum": position_num,
    }


def _make_scenario_file(vessel_history=None):
    """Write a scenario JSON to a temp file and return the path."""
    now = _now()
    vessel = _make_raw_vessel(at_dock=True)

    scenario = {
        "captured_at": now.isoformat(),
        "vessels": [vessel],
        "schedules": {},
        "sailing_space": [],
    }
    if vessel_history is not None:
        scenario["vessel_history"] = vessel_history

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(scenario, f)
    return f.name


class TestWarmDelayCache:
    def setup_method(self):
        """Clear cache before each test."""
        CACHED_DELAYS.clear()

    def test_empty_history(self):
        count = warm_delay_cache([])
        assert count == 0
        assert CACHED_DELAYS == {}

    def test_caches_delay_from_history(self):
        """A vessel with left_dock and scheduled_departure should populate the cache."""
        sched = _now() - timedelta(minutes=20)
        left = sched + timedelta(minutes=5)  # 5 min delay

        history = [
            {
                "captured_at": _now().isoformat(),
                "vessels": [
                    _make_raw_vessel(
                        scheduled_departure=sched,
                        left_dock=left,
                        at_dock=False,
                    ),
                ],
            }
        ]

        warm_delay_cache(history)
        assert "sea-bi" in CACHED_DELAYS
        assert 1 in CACHED_DELAYS["sea-bi"]
        delay = CACHED_DELAYS["sea-bi"][1]
        # Should be ~5 minutes
        assert abs(delay.total_seconds() - 300) < 2

    def test_cache_persists_across_snapshots(self):
        """Delay cached in snapshot 1 survives when snapshot 2 has null fields."""
        sched = _now() - timedelta(minutes=20)
        left = sched + timedelta(minutes=7)  # 7 min delay

        # Snapshot 1: vessel en route with delay data
        snapshot1_vessel = _make_raw_vessel(
            scheduled_departure=sched,
            left_dock=left,
            at_dock=False,
        )

        # Snapshot 2: vessel at dock, WSDOT nulled out the departure fields
        snapshot2_vessel = _make_raw_vessel(
            scheduled_departure=None,
            left_dock=None,
            at_dock=True,
        )

        history = [
            {"captured_at": _now().isoformat(), "vessels": [snapshot1_vessel]},
            {"captured_at": _now().isoformat(), "vessels": [snapshot2_vessel]},
        ]

        warm_delay_cache(history)

        # The delay from snapshot 1 should still be cached
        assert "sea-bi" in CACHED_DELAYS
        delay = CACHED_DELAYS["sea-bi"][1]
        assert abs(delay.total_seconds() - 420) < 2  # ~7 minutes

    def test_skips_out_of_service_vessels(self):
        """Vessels with InService=False should be skipped."""
        sched = _now() - timedelta(minutes=10)
        left = sched + timedelta(minutes=3)

        vessel = _make_raw_vessel(scheduled_departure=sched, left_dock=left)
        vessel["InService"] = False

        history = [{"captured_at": _now().isoformat(), "vessels": [vessel]}]
        warm_delay_cache(history)
        assert CACHED_DELAYS == {}

    def test_multiple_vessels_and_routes(self):
        """Multiple vessels on different routes should all be cached."""
        sched = _now() - timedelta(minutes=15)

        history = [
            {
                "captured_at": _now().isoformat(),
                "vessels": [
                    _make_raw_vessel(
                        vessel_id=1,
                        name="Walla Walla",
                        position_num=1,
                        route="sea-bi",
                        scheduled_departure=sched,
                        left_dock=sched + timedelta(minutes=3),
                    ),
                    _make_raw_vessel(
                        vessel_id=2,
                        name="Spokane",
                        position_num=1,
                        route="ed-king",
                        scheduled_departure=sched,
                        left_dock=sched + timedelta(minutes=10),
                    ),
                ],
            }
        ]

        warm_delay_cache(history)
        assert "sea-bi" in CACHED_DELAYS
        assert "ed-king" in CACHED_DELAYS
        assert abs(CACHED_DELAYS["sea-bi"][1].total_seconds() - 180) < 2
        assert abs(CACHED_DELAYS["ed-king"][1].total_seconds() - 600) < 2


class TestSnapshotStepping:
    def test_activate_builds_snapshot_list(self):
        """History snapshots + final snapshot should be in order."""
        t1 = (_now() - timedelta(minutes=2)).isoformat()
        t2 = (_now() - timedelta(minutes=1)).isoformat()
        vessel = _make_raw_vessel(at_dock=True)

        history = [
            {"captured_at": t1, "vessels": [vessel]},
            {"captured_at": t2, "vessels": [vessel]},
        ]
        path = _make_scenario_file(vessel_history=history)
        activate_replay(path)

        # 2 history + 1 final = 3 snapshots
        assert len(replay_module._snapshots) == 3
        info = get_snapshot_info()
        assert info["index"] == 0
        assert info["total"] == 3
        assert info["at_start"] is True
        assert info["at_end"] is False

    def test_activate_legacy_scenario(self):
        """A scenario without vessel_history should have exactly 1 snapshot."""
        path = _make_scenario_file(vessel_history=None)
        activate_replay(path)

        assert len(replay_module._snapshots) == 1
        info = get_snapshot_info()
        assert info["total"] == 1
        assert info["at_start"] is True
        assert info["at_end"] is True

    def test_advance_and_retreat(self):
        t1 = (_now() - timedelta(minutes=1)).isoformat()
        vessel = _make_raw_vessel(at_dock=True)
        history = [{"captured_at": t1, "vessels": [vessel]}]
        path = _make_scenario_file(vessel_history=history)
        activate_replay(path)

        # Start at 0, advance to 1
        result = advance_snapshot()
        assert result is not None
        assert result["index"] == 1
        assert result["at_end"] is True

        # Can't advance past end
        assert advance_snapshot() is None

        # Retreat back to 0
        result = retreat_snapshot()
        assert result is not None
        assert result["index"] == 0
        assert result["at_start"] is True

        # Can't retreat past start
        assert retreat_snapshot() is None

    def test_advance_updates_replay_time(self):
        """Each step should update the replay time to match the snapshot."""
        t1 = (_now() - timedelta(minutes=5)).isoformat()
        t2 = (_now() - timedelta(minutes=3)).isoformat()
        vessel = _make_raw_vessel(at_dock=True)

        history = [
            {"captured_at": t1, "vessels": [vessel]},
            {"captured_at": t2, "vessels": [vessel]},
        ]
        path = _make_scenario_file(vessel_history=history)
        activate_replay(path)

        # At snapshot 0 (t1)
        time_at_0 = get_replay_time()
        assert time_at_0 == datetime.fromisoformat(t1)

        # Advance to snapshot 1 (t2)
        advance_snapshot()
        time_at_1 = get_replay_time()
        assert time_at_1 == datetime.fromisoformat(t2)
        assert time_at_1 > time_at_0

    def test_advance_swaps_vessel_data(self):
        """Advancing should change which vessel data is served."""
        vessel_a = _make_raw_vessel(name="Walla Walla", at_dock=True)
        vessel_b = _make_raw_vessel(name="Spokane", at_dock=False)

        t1 = (_now() - timedelta(minutes=1)).isoformat()
        history = [{"captured_at": t1, "vessels": [vessel_a]}]

        # Final snapshot has vessel_b
        now = _now()
        scenario = {
            "captured_at": now.isoformat(),
            "vessels": [vessel_b],
            "schedules": {},
            "sailing_space": [],
            "vessel_history": history,
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(scenario, f)

        activate_replay(f.name)

        # At snapshot 0: should see vessel_a
        from backend.replay import get_scenario_data

        assert get_scenario_data()["vessels"][0]["VesselName"] == "Walla Walla"

        # Advance to final: should see vessel_b
        advance_snapshot()
        assert get_scenario_data()["vessels"][0]["VesselName"] == "Spokane"
