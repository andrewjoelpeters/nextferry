from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.display_processing import process_routes_for_display
from backend.serializers import (DirectionalSchedule, RouteSailing,
                                 RouteSchedule)

PT = ZoneInfo("America/Los_Angeles")


def _make_sailing(minutes_from_now, vessel="TestVessel", delay=None):
    return RouteSailing(
        scheduled_departure=datetime.now(PT) + timedelta(minutes=minutes_from_now),
        vessel_name=vessel,
        vessel_position_num=1,
        delay_in_minutes=delay,
    )


def _make_route(sailings, departing="Seattle", arriving="Bainbridge"):
    return RouteSchedule(
        route_name=["Seattle - Bainbridge"],
        route_id=5,
        schedules=[
            DirectionalSchedule(
                departing_terminal_id=3,
                departing_terminal_name=departing,
                arriving_terminal_id=7,
                arriving_terminal_name=arriving,
                times=sailings,
            )
        ],
    )


class TestProcessRoutesForDisplay:
    def test_basic_processing(self):
        route = _make_route([_make_sailing(30)])
        result = process_routes_for_display([route])

        assert len(result) == 1
        assert result[0]["route_name"] == "Seattle - Bainbridge"
        assert len(result[0]["schedules"]) == 1

        sailings = result[0]["schedules"][0]["sailings"]
        assert len(sailings) == 1
        assert sailings[0]["time_until"] in ("29m", "30m")
        assert sailings[0]["status_class"] == "status-on-time"
        assert sailings[0]["vessel_name"] == "TestVessel"

    def test_limits_to_three_sailings(self):
        sailings = [_make_sailing(m) for m in [10, 20, 30, 40, 50]]
        route = _make_route(sailings)
        result = process_routes_for_display([route])

        displayed = result[0]["schedules"][0]["sailings"]
        assert len(displayed) == 3

    def test_delay_formatting(self):
        route = _make_route([_make_sailing(30, delay=5)])
        result = process_routes_for_display([route])

        sailing = result[0]["schedules"][0]["sailings"][0]
        assert sailing["has_delay"] is True
        assert sailing["delay_text"] == " (+5m)"
        assert sailing["status_class"] == "status-delayed"

    def test_no_delay(self):
        route = _make_route([_make_sailing(30)])
        result = process_routes_for_display([route])

        sailing = result[0]["schedules"][0]["sailings"][0]
        assert sailing["has_delay"] is False
        assert sailing["status_class"] == "status-on-time"

    def test_empty_schedules(self):
        route = _make_route([])
        result = process_routes_for_display([route])

        sailings = result[0]["schedules"][0]["sailings"]
        assert len(sailings) == 0

    def test_multiple_routes(self):
        route1 = _make_route([_make_sailing(10)])
        route2 = RouteSchedule(
            route_name=["Kingston - Edmonds"],
            route_id=6,
            schedules=[
                DirectionalSchedule(
                    departing_terminal_id=12,
                    departing_terminal_name="Kingston",
                    arriving_terminal_id=8,
                    arriving_terminal_name="Edmonds",
                    times=[_make_sailing(20)],
                )
            ],
        )
        result = process_routes_for_display([route1, route2])
        assert len(result) == 2
