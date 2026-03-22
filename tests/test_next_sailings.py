from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.next_sailings import (
    get_directional_schedules,
    get_next_sailings_by_boat,
    get_route_schedule_by_boat,
    get_route_vessels,
)
from backend.serializers import (
    DirectionalSailing,
    RawDeparture,
    RawDirectionalSchedule,
    Vessel,
)

PT = ZoneInfo("America/Los_Angeles")


def _now():
    return datetime.now(PT)


def _dt_to_wsdot(dt):
    """Convert a datetime to WSDOT /Date(...)/ format for the Vessel validator."""
    if dt is None:
        return None
    ms = int(dt.timestamp() * 1000)
    return f"/Date({ms}-0800)/"


def _make_vessel(
    position_num=1,
    at_dock=True,
    scheduled_departure=None,
    route="sea-bi",
    name="Walla Walla",
):
    return Vessel(
        VesselID=1,
        VesselName=name,
        DepartingTerminalID=3,
        DepartingTerminalName="Seattle",
        DepartingTerminalAbbrev="SEA",
        ArrivingTerminalID=7,
        ArrivingTerminalName="Bainbridge Island",
        ArrivingTerminalAbbrev="BI",
        Latitude=47.6,
        Longitude=-122.3,
        Speed=0.0,
        Heading=0,
        InService=True,
        AtDock=at_dock,
        LeftDock=None,
        Eta=None,
        ScheduledDeparture=_dt_to_wsdot(scheduled_departure),
        TimeStamp=_dt_to_wsdot(_now()),
        OpRouteAbbrev=[route],
        VesselPositionNum=position_num,
    )


def _make_directional_sailing(minutes_from_now, position_num=1, vessel="Walla Walla"):
    return DirectionalSailing(
        departing_terminal_id=3,
        arriving_terminal_id=7,
        departing_terminal_name="Seattle",
        arriving_terminal_name="Bainbridge Island",
        scheduled_departure=_now() + timedelta(minutes=minutes_from_now),
        vessel_name=vessel,
        vessel_position_num=position_num,
    )


class TestGetRouteVessels:
    def test_filters_by_route(self):
        v1 = _make_vessel(route="sea-bi")
        v2 = _make_vessel(route="ed-king", position_num=2, name="Spokane")
        route_config = {"route_name": "sea-bi"}

        result = get_route_vessels([v1, v2], route_config)
        assert len(result) == 1
        assert result[0].vessel_name == "Walla Walla"


class TestGetRouteScheduleByBoat:
    def test_groups_by_vessel(self):
        schedules = [
            RawDirectionalSchedule(
                DepartingTerminalID=3,
                DepartingTerminalName="Seattle",
                ArrivingTerminalID=7,
                ArrivingTerminalName="Bainbridge Island",
                SailingNotes="",
                Times=[
                    RawDeparture(
                        DepartingTime=_dt_to_wsdot(_now() + timedelta(hours=1)),
                        VesselName="Walla Walla",
                        VesselPositionNum=1,
                    ),
                    RawDeparture(
                        DepartingTime=_dt_to_wsdot(_now() + timedelta(hours=3)),
                        VesselName="Walla Walla",
                        VesselPositionNum=1,
                    ),
                ],
            )
        ]
        result = get_route_schedule_by_boat(schedules)
        assert 1 in result
        assert len(result[1]) == 2

    def test_sorts_by_departure(self):
        later = _now() + timedelta(hours=5)
        earlier = _now() + timedelta(hours=1)
        schedules = [
            RawDirectionalSchedule(
                DepartingTerminalID=3,
                DepartingTerminalName="Seattle",
                ArrivingTerminalID=7,
                ArrivingTerminalName="Bainbridge Island",
                SailingNotes="",
                Times=[
                    RawDeparture(
                        DepartingTime=_dt_to_wsdot(later),
                        VesselName="Walla Walla",
                        VesselPositionNum=1,
                    ),
                    RawDeparture(
                        DepartingTime=_dt_to_wsdot(earlier),
                        VesselName="Walla Walla",
                        VesselPositionNum=1,
                    ),
                ],
            )
        ]
        result = get_route_schedule_by_boat(schedules)
        assert result[1][0].scheduled_departure < result[1][1].scheduled_departure


class TestGetNextSailingsByBoat:
    def test_no_vessel_info_filters_to_future(self):
        """When no vessel info is available, only future sailings are returned.

        Note: uses a vessel with no scheduled_departure to trigger the
        'no vessel info' branch while avoiding the None.delay bug when
        current_vessel is truly None.
        """
        vessel = _make_vessel(position_num=1, scheduled_departure=None)
        sailings = {
            1: [
                _make_directional_sailing(-30),  # past
                _make_directional_sailing(30),  # future
                _make_directional_sailing(60),  # future
            ]
        }
        result = get_next_sailings_by_boat(sailings, [vessel])
        assert len(result[1]) == 2

    def test_at_dock_includes_current(self):
        # Use a round timestamp so WSDOT parse round-trip is exact
        departure_time = _now().replace(second=0, microsecond=0) + timedelta(minutes=5)
        vessel = _make_vessel(
            at_dock=True, scheduled_departure=departure_time
        )
        # The vessel's scheduled_departure went through WSDOT date parsing,
        # so use the parsed value for the sailing to ensure exact match
        parsed_departure = vessel.scheduled_departure
        sailings = {
            1: [
                _make_directional_sailing(-30),
                DirectionalSailing(
                    departing_terminal_id=3,
                    arriving_terminal_id=7,
                    departing_terminal_name="Seattle",
                    arriving_terminal_name="Bainbridge Island",
                    scheduled_departure=parsed_departure,
                    vessel_name="Walla Walla",
                    vessel_position_num=1,
                ),
                _make_directional_sailing(60),
            ]
        }
        result = get_next_sailings_by_boat(sailings, [vessel])
        # Should include the current sailing (at dock) + future
        assert len(result[1]) == 2

    def test_en_route_excludes_current(self):
        departure_time = _now().replace(second=0, microsecond=0) - timedelta(minutes=5)
        vessel = _make_vessel(
            at_dock=False, scheduled_departure=departure_time
        )
        parsed_departure = vessel.scheduled_departure
        sailings = {
            1: [
                DirectionalSailing(
                    departing_terminal_id=3,
                    arriving_terminal_id=7,
                    departing_terminal_name="Seattle",
                    arriving_terminal_name="Bainbridge Island",
                    scheduled_departure=parsed_departure,
                    vessel_name="Walla Walla",
                    vessel_position_num=1,
                ),
                _make_directional_sailing(60),
            ]
        }
        result = get_next_sailings_by_boat(sailings, [vessel])
        # En route: includes the just-departed sailing (marked departed) + future
        assert len(result[1]) == 2
        assert result[1][0].departed is True
        assert result[1][1].departed is False


class TestGetDirectionalSchedules:
    def test_groups_by_direction(self):
        sailings_by_boat = {
            1: [
                _make_directional_sailing(30, position_num=1),
                _make_directional_sailing(90, position_num=1),
            ]
        }
        result = get_directional_schedules(sailings_by_boat)
        assert len(result) == 1
        assert len(result[0].times) == 2

    def test_multiple_directions(self):
        s1 = _make_directional_sailing(30, position_num=1)
        s2 = DirectionalSailing(
            departing_terminal_id=7,
            arriving_terminal_id=3,
            departing_terminal_name="Bainbridge Island",
            arriving_terminal_name="Seattle",
            scheduled_departure=_now() + timedelta(minutes=60),
            vessel_name="Spokane",
            vessel_position_num=2,
        )
        result = get_directional_schedules({1: [s1], 2: [s2]})
        assert len(result) == 2

    def test_times_sorted_by_departure(self):
        s1 = _make_directional_sailing(60, position_num=1)
        s2 = _make_directional_sailing(30, position_num=1, vessel="Spokane")
        result = get_directional_schedules({1: [s1, s2]})
        times = result[0].times
        assert times[0].scheduled_departure < times[1].scheduled_departure
