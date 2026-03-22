from datetime import datetime
from zoneinfo import ZoneInfo

from backend.serializers import DirectionalSailing, RouteSailing, Vessel

PT = ZoneInfo("America/Los_Angeles")


class TestVessel:
    def test_parse_wsdot_vessel(self):
        data = {
            "VesselID": 1,
            "VesselName": "Walla Walla",
            "DepartingTerminalID": 3,
            "DepartingTerminalName": "Seattle",
            "DepartingTerminalAbbrev": "SEA",
            "ArrivingTerminalID": 7,
            "ArrivingTerminalName": "Bainbridge Island",
            "ArrivingTerminalAbbrev": "BI",
            "Latitude": 47.6,
            "Longitude": -122.3,
            "Speed": 15.5,
            "Heading": 270,
            "InService": True,
            "AtDock": False,
            "LeftDock": "/Date(1700000000000-0800)/",
            "Eta": "/Date(1700003600000-0800)/",
            "ScheduledDeparture": "/Date(1699999800000-0800)/",
            "TimeStamp": "/Date(1700000100000-0800)/",
            "OpRouteAbbrev": ["sea-bi"],
            "VesselPositionNum": 1,
        }
        vessel = Vessel(**data)
        assert vessel.vessel_name == "Walla Walla"
        assert vessel.at_dock is False
        assert vessel.left_dock is not None
        assert isinstance(vessel.left_dock, datetime)
        assert vessel.route_name == ["sea-bi"]

    def test_vessel_with_null_fields(self):
        data = {
            "VesselID": 2,
            "VesselName": "Spokane",
            "DepartingTerminalID": None,
            "DepartingTerminalName": None,
            "DepartingTerminalAbbrev": None,
            "ArrivingTerminalID": None,
            "ArrivingTerminalName": None,
            "ArrivingTerminalAbbrev": None,
            "Latitude": None,
            "Longitude": None,
            "Speed": None,
            "Heading": None,
            "InService": True,
            "AtDock": True,
            "LeftDock": None,
            "Eta": None,
            "ScheduledDeparture": None,
            "TimeStamp": None,
            "OpRouteAbbrev": [],
            "VesselPositionNum": None,
        }
        vessel = Vessel(**data)
        assert vessel.vessel_name == "Spokane"
        assert vessel.left_dock is None
        assert vessel.scheduled_departure is None


class TestDirectionalSailing:
    def test_to_route_sailing(self):
        sailing = DirectionalSailing(
            departing_terminal_id=3,
            arriving_terminal_id=7,
            departing_terminal_name="Seattle",
            arriving_terminal_name="Bainbridge Island",
            scheduled_departure=datetime(2024, 1, 1, 12, 0, tzinfo=PT),
            vessel_name="Walla Walla",
            vessel_position_num=1,
            delay_in_minutes=5,
        )
        route_sailing = sailing.to_route_sailing()
        assert isinstance(route_sailing, RouteSailing)
        assert route_sailing.vessel_name == "Walla Walla"
        assert route_sailing.delay_in_minutes == 5
        assert not hasattr(route_sailing, "departing_terminal_id") or \
               "departing_terminal_id" not in route_sailing.model_fields
