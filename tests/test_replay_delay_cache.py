"""Tests for replay vessel history and delay cache warming."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.next_sailings import CACHED_DELAYS, warm_delay_cache

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
