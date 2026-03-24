from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from backend.display_processing import process_routes_for_display
from backend.serializers import DirectionalSchedule, RouteSailing, RouteSchedule

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


class TestFormatVesselStatus:
    def test_docked_duration_shown_when_at_dock(self):
        """When a vessel is at dock, docked_duration should be computed from vessel_eta."""
        from backend.display_processing import _format_vessel_status

        sailing = _make_sailing(30)
        sailing.vessel_at_dock = True
        sailing.vessel_eta = datetime.now(PT) - timedelta(minutes=15)

        result = _format_vessel_status(sailing)
        assert result["vessel_status_key"] == "at_dock"
        assert result["docked_duration"] in ("14m", "15m", "16m")

    def test_docked_duration_hours(self):
        """Docked duration should show hours when >= 60 minutes."""
        from backend.display_processing import _format_vessel_status

        sailing = _make_sailing(30)
        sailing.vessel_at_dock = True
        sailing.vessel_eta = datetime.now(PT) - timedelta(minutes=75)

        result = _format_vessel_status(sailing)
        assert "1h" in result["docked_duration"]

    def test_no_docked_duration_without_eta(self):
        """No docked_duration when vessel_eta is None."""
        from backend.display_processing import _format_vessel_status

        sailing = _make_sailing(30)
        sailing.vessel_at_dock = True
        sailing.vessel_eta = None

        result = _format_vessel_status(sailing)
        assert "docked_duration" not in result


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

    @patch("backend.display_processing.get_departed_sailing_space")
    def test_departed_sailing_shows_actual_capacity(self, mock_get_space):
        mock_get_space.return_value = {
            "max_space_count": 200,
            "drive_up_space_count": 50,
        }
        sailing = _make_sailing(-10)  # departed 10 min ago
        sailing.departed = True
        route = _make_route([sailing])
        result = process_routes_for_display([route])

        displayed = result[0]["schedules"][0]["sailings"][0]
        assert displayed["capacity"] is not None
        assert displayed["capacity"]["cars_on_board"] == 150
        assert displayed["capacity"]["total"] == 200
        assert displayed["capacity"]["percent"] == 75
        assert displayed["departed"] is True

    @patch("backend.display_processing.get_departed_sailing_space")
    def test_departed_sailing_no_snapshot_has_no_capacity(self, mock_get_space):
        mock_get_space.return_value = None
        sailing = _make_sailing(-10)
        sailing.departed = True
        route = _make_route([sailing])
        result = process_routes_for_display([route])

        displayed = result[0]["schedules"][0]["sailings"][0]
        assert displayed["capacity"] is None

    @patch("backend.display_processing.get_departed_sailing_space")
    def test_departed_sailing_skips_fill_risk(self, mock_get_space):
        mock_get_space.return_value = {
            "max_space_count": 200,
            "drive_up_space_count": 50,
        }
        sailing = _make_sailing(-10)
        sailing.departed = True
        route = _make_route([sailing])
        result = process_routes_for_display([route])

        displayed = result[0]["schedules"][0]["sailings"][0]
        assert displayed["fill_risk"] is None
