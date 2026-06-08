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

    def test_no_docked_duration_without_eta_or_docked_since(self):
        """No docked_duration when both vessel_eta and vessel_docked_since are None."""
        from backend.display_processing import _format_vessel_status

        sailing = _make_sailing(30)
        sailing.vessel_at_dock = True
        sailing.vessel_eta = None
        sailing.vessel_docked_since = None

        result = _format_vessel_status(sailing)
        assert "docked_duration" not in result

    def test_docked_since_fallback_when_eta_is_null(self):
        """docked_duration computed from vessel_docked_since when eta is None."""
        from backend.display_processing import _format_vessel_status

        sailing = _make_sailing(30)
        sailing.vessel_at_dock = True
        sailing.vessel_eta = None
        sailing.vessel_docked_since = datetime.now(PT) - timedelta(minutes=20)

        result = _format_vessel_status(sailing)
        assert result["docked_duration"] in ("19m", "20m", "21m")
        assert "docked_at" in result

    def test_at_dock_null_eta_shows_scheduled_departure(self):
        """When at dock with null Eta and no docked_since, show scheduled departure."""
        from backend.display_processing import _format_vessel_status

        sailing = _make_sailing(30)
        sailing.vessel_at_dock = True
        sailing.vessel_eta = None
        sailing.vessel_docked_since = None

        result = _format_vessel_status(sailing)
        assert result["vessel_status_key"] == "at_dock"
        assert "docked_at" not in result
        # Should still show predicted_departure (falling back to scheduled time)
        assert "predicted_departure" in result

    def test_at_dock_null_eta_with_delay_shows_predicted_departure(self):
        """When at dock with null Eta but known delay, show adjusted departure."""
        from backend.display_processing import _format_vessel_status

        sailing = _make_sailing(30, delay=10)
        sailing.vessel_at_dock = True
        sailing.vessel_eta = None
        sailing.vessel_docked_since = None

        result = _format_vessel_status(sailing)
        assert result["vessel_status_key"] == "at_dock"
        assert "predicted_departure" in result
        # predicted_departure should be scheduled_time + 10min, not scheduled_time
        scheduled_str = sailing.scheduled_departure.strftime("%I:%M %p").lstrip("0")
        assert result["predicted_departure"] != scheduled_str


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

    def test_inbound_at_dock_shows_predicted_departure_when_delayed(self):
        """When inbound vessel is at dock with a delay, predicted_departure should reflect
        the adjusted time (scheduled + delay), not the raw scheduled departure."""
        now = datetime.now(PT)
        inbound_sched = now + timedelta(minutes=5)
        sailing = _make_sailing(60)
        sailing.inbound_vessel_name = "Wenatchee"
        sailing.inbound_vessel_at_dock = True
        sailing.inbound_vessel_from_terminal = "Bainbridge Island"
        sailing.inbound_vessel_scheduled_departure = inbound_sched
        sailing.inbound_vessel_delay_minutes = 15

        route = _make_route([sailing])
        result = process_routes_for_display([route])

        inbound_info = result[0]["schedules"][0]["sailings"][0]["inbound_info"]
        assert inbound_info is not None
        assert inbound_info["at_dock"] is True
        # predicted_departure should be scheduled + 15 min delay
        expected_predicted = (
            (inbound_sched + timedelta(minutes=15)).strftime("%I:%M %p").lstrip("0")
        )
        assert inbound_info["predicted_departure"] == expected_predicted
        # scheduled_departure should still be the raw scheduled time
        expected_scheduled = inbound_sched.strftime("%I:%M %p").lstrip("0")
        assert inbound_info["scheduled_departure"] == expected_scheduled

    def test_inbound_at_dock_no_delay_shows_scheduled_as_predicted(self):
        """When inbound vessel is at dock with no delay, predicted_departure is None
        and scheduled_departure provides the expected departure time."""
        now = datetime.now(PT)
        inbound_sched = now + timedelta(minutes=10)
        sailing = _make_sailing(60)
        sailing.inbound_vessel_name = "Wenatchee"
        sailing.inbound_vessel_at_dock = True
        sailing.inbound_vessel_from_terminal = "Bainbridge Island"
        sailing.inbound_vessel_scheduled_departure = inbound_sched

        route = _make_route([sailing])
        result = process_routes_for_display([route])

        inbound_info = result[0]["schedules"][0]["sailings"][0]["inbound_info"]
        assert inbound_info is not None
        assert inbound_info["predicted_departure"] is None
        expected_scheduled = inbound_sched.strftime("%I:%M %p").lstrip("0")
        assert inbound_info["scheduled_departure"] == expected_scheduled

    def test_inbound_at_dock_estimated_arrival_shown_in_detail_lines(self):
        """When an inbound at-dock vessel has an estimated arrival (computed from crossing
        time), inbound_detail_lines includes a line with the estimated arrival."""
        now = datetime.now(PT)
        inbound_sched = now + timedelta(minutes=10)
        estimated_arr = now + timedelta(minutes=45)  # 10 min dep + ~35 min crossing
        sailing = _make_sailing(60)
        sailing.inbound_vessel_name = "Wenatchee"
        sailing.inbound_vessel_at_dock = True
        sailing.inbound_vessel_from_terminal = "Bainbridge Island"
        sailing.inbound_vessel_scheduled_departure = inbound_sched
        sailing.inbound_vessel_estimated_arrival = estimated_arr

        route = _make_route([sailing])
        result = process_routes_for_display([route])

        displayed = result[0]["schedules"][0]["sailings"][0]
        lines = displayed["inbound_detail_lines"]
        assert len(lines) == 2
        assert "Bainbridge Island" in lines[0]["text"]
        # Second line: "Expected to arrive Seattle ~HH:MM (est.), expected departure HH:MM"
        estimated_arr_str = estimated_arr.strftime("%I:%M %p").lstrip("0")
        assert (
            f"Expected to arrive Seattle ~{estimated_arr_str} (est.)"
            in lines[1]["text"]
        )
        assert "expected departure" in lines[1]["text"]

    def test_inbound_at_dock_wsdot_eta_preferred_over_estimate(self):
        """When WSDOT provides an ETA, it is shown instead of the crossing-time estimate."""
        now = datetime.now(PT)
        inbound_sched = now + timedelta(minutes=10)
        estimated_arr = now + timedelta(minutes=45)
        wsdot_eta = now + timedelta(minutes=40)
        sailing = _make_sailing(60)
        sailing.inbound_vessel_name = "Wenatchee"
        sailing.inbound_vessel_at_dock = True
        sailing.inbound_vessel_from_terminal = "Bainbridge Island"
        sailing.inbound_vessel_scheduled_departure = inbound_sched
        sailing.inbound_vessel_estimated_arrival = estimated_arr
        sailing.inbound_vessel_eta = wsdot_eta

        route = _make_route([sailing])
        result = process_routes_for_display([route])

        displayed = result[0]["schedules"][0]["sailings"][0]
        lines = displayed["inbound_detail_lines"]
        assert len(lines) == 2
        # Should NOT contain "(est.)" since WSDOT eta is available
        assert "(est.)" not in lines[1]["text"]
        wsdot_eta_str = wsdot_eta.strftime("%I:%M %p").lstrip("0")
        assert wsdot_eta_str in lines[1]["text"]


class TestBuildVesselDetailLines:
    def test_at_dock_formats_single_line(self):
        from backend.display_processing import _build_vessel_detail_lines

        vessel_info = {
            "vessel_status_key": "at_dock",
            "docked_at": "9:55 AM",
            "docked_duration": "15m",
            "predicted_departure": "10:20 AM",
        }
        lines = _build_vessel_detail_lines(
            vessel_info, "Seattle", "Bainbridge Island", False
        )
        assert len(lines) == 1
        assert "9:55 AM" in lines[0]["text"]
        assert "15m" in lines[0]["text"]
        assert "Seattle" in lines[0]["text"]
        assert "10:20 AM" in lines[0]["text"]

    def test_overdue_shows_three_lines(self):
        from backend.display_processing import _build_vessel_detail_lines

        vessel_info = {
            "vessel_status_key": "at_dock",
            "docked_at": "9:55 AM",
            "docked_duration": "30m",
            "predicted_departure": "10:05 AM",
            "overdue": True,
            "minutes_overdue": 20,
        }
        lines = _build_vessel_detail_lines(
            vessel_info, "Seattle", "Bainbridge Island", False
        )
        assert len(lines) == 3
        assert lines[1]["css_class"] == "detail-overdue"
        assert lines[2]["css_class"] == "overdue-alert"
        assert "20m ago" in lines[2]["text"]

    def test_en_route_names_arriving_terminal(self):
        from backend.display_processing import _build_vessel_detail_lines

        vessel_info = {
            "vessel_status_key": "en_route",
            "left_dock": "9:30 AM",
            "departure_delay": "+5m late",
        }
        lines = _build_vessel_detail_lines(
            vessel_info, "Seattle", "Bainbridge Island", False
        )
        assert len(lines) == 1
        assert "Bainbridge Island" in lines[0]["text"]
        assert "+5m late" in lines[0]["text"]

    def test_empty_vessel_info_returns_no_lines(self):
        from backend.display_processing import _build_vessel_detail_lines

        lines = _build_vessel_detail_lines({}, "Seattle", "Bainbridge Island", False)
        assert lines == []


class TestBuildInboundDetailLines:
    def test_at_dock_no_eta_no_estimate_shows_two_lines(self):
        from backend.display_processing import _build_inbound_detail_lines

        inbound_info = {
            "at_dock": True,
            "from_terminal": "Bainbridge Island",
            "scheduled_departure": "9:45 AM",
            "predicted_departure": None,
            "eta": None,
            "estimated_arrival": None,
        }
        lines = _build_inbound_detail_lines(inbound_info, "Seattle", "10:45 AM", False)
        assert len(lines) == 2
        assert "Bainbridge Island" in lines[0]["text"]
        assert "9:45 AM" in lines[0]["text"]
        assert "Seattle" in lines[1]["text"]
        assert "10:45 AM" in lines[1]["text"]

    def test_at_dock_with_estimated_arrival_shows_est(self):
        from backend.display_processing import _build_inbound_detail_lines

        inbound_info = {
            "at_dock": True,
            "from_terminal": "Bainbridge Island",
            "scheduled_departure": "9:45 AM",
            "predicted_departure": None,
            "eta": None,
            "estimated_arrival": "10:20 AM",
        }
        lines = _build_inbound_detail_lines(inbound_info, "Seattle", "10:45 AM", False)
        assert len(lines) == 2
        assert "(est.)" in lines[1]["text"]
        assert "10:20 AM" in lines[1]["text"]
        assert "10:45 AM" in lines[1]["text"]

    def test_at_dock_with_wsdot_eta_no_est_label(self):
        from backend.display_processing import _build_inbound_detail_lines

        inbound_info = {
            "at_dock": True,
            "from_terminal": "Bainbridge Island",
            "scheduled_departure": "9:45 AM",
            "predicted_departure": None,
            "eta": "10:15 AM",
            "estimated_arrival": "10:20 AM",  # ignored when eta is present
        }
        lines = _build_inbound_detail_lines(inbound_info, "Seattle", "10:45 AM", False)
        assert len(lines) == 2
        assert "(est.)" not in lines[1]["text"]
        assert "10:15 AM" in lines[1]["text"]

    def test_en_route_single_line(self):
        from backend.display_processing import _build_inbound_detail_lines

        inbound_info = {
            "at_dock": False,
            "from_terminal": "Bainbridge Island",
            "vessel_name": "Wenatchee",
            "left_dock": "9:30 AM",
            "eta": "10:05 AM",
            "estimated_arrival": None,
        }
        lines = _build_inbound_detail_lines(inbound_info, "Seattle", "10:45 AM", False)
        assert len(lines) == 1
        assert "Wenatchee" in lines[0]["text"]
        assert "Bainbridge Island" in lines[0]["text"]
        assert "9:30 AM" in lines[0]["text"]
        assert "Seattle" in lines[0]["text"]
        assert "10:05 AM" in lines[0]["text"]
