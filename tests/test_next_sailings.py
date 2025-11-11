from datetime import datetime, timedelta
from unittest import mock

import pytest
from backend.next_sailings import (get_next_sailings_for_route,
                                     propigate_delays)
from backend.serializers import (DirectionalSailing, RawDeparture,
                                   RawDirectionalSchedule, Vessel)


@pytest.fixture
def mock_vessel_data():
    """Returns a list of mock Vessel objects."""
    now_ms = int(datetime.now().timestamp() * 1000)
    return [
        Vessel.model_validate(
            {
                "VesselID": 1,
                "VesselName": "Test Ferry 1",
                "OpRouteAbbrev": ["SEA-BI"],
                "InService": True,
                "AtDock": True,
                "ScheduledDeparture": f"/Date({now_ms}-0700)/",
                "VesselPositionNum": 1,
                "DepartingTerminalID": 1,
                "DepartingTerminalName": "Seattle",
                "DepartingTerminalAbbrev": "SEA",
                "ArrivingTerminalID": 2,
                "ArrivingTerminalName": "Bainbridge Island",
                "ArrivingTerminalAbbrev": "BAI",
                "Latitude": 47.6,
                "Longitude": -122.5,
                "Speed": 0,
                "Heading": 0,
                "LeftDock": None,
                "Eta": None,
                "TimeStamp": f"/Date({now_ms}-0700)/",
            }
        ),
        Vessel.model_validate(
            {
                "VesselID": 2,
                "VesselName": "Test Ferry 2",
                "OpRouteAbbrev": ["SEA-BI"],
                "InService": True,
                "AtDock": False,
                "ScheduledDeparture": f"/Date({now_ms - 600000}-0700)/",
                "LeftDock": f"/Date({now_ms - 300000}-0700)/",
                "VesselPositionNum": 2,
                "DepartingTerminalID": 1,
                "DepartingTerminalName": "Seattle",
                "DepartingTerminalAbbrev": "SEA",
                "ArrivingTerminalID": 2,
                "ArrivingTerminalName": "Bainbridge Island",
                "ArrivingTerminalAbbrev": "BAI",
                "Latitude": 47.6,
                "Longitude": -122.5,
                "Speed": 15,
                "Heading": 270,
                "Eta": f"/Date({now_ms + 600000}-0700)/",
                "TimeStamp": f"/Date({now_ms}-0700)/",
            }
        ),
    ]


@pytest.fixture
def mock_schedule_data():
    """Returns a list of mock RawDirectionalSchedule objects."""
    now_ms = int(datetime.now().timestamp() * 1000)
    return [
        RawDirectionalSchedule(
            DepartingTerminalID=1,
            DepartingTerminalName="Seattle",
            ArrivingTerminalID=2,
            ArrivingTerminalName="Bainbridge Island",
            SailingNotes="",
            Times=[
                RawDeparture.model_validate(
                    {
                        "DepartingTime": f"/Date({now_ms + 1800000}-0700)/",
                        "VesselName": "Test Ferry 1",
                        "VesselPositionNum": 1,
                    }
                ),
                RawDeparture.model_validate(
                    {
                        "DepartingTime": f"/Date({now_ms + 3600000}-0700)/",
                        "VesselName": "Test Ferry 2",
                        "VesselPositionNum": 2,
                    }
                ),
            ],
        )
    ]


@mock.patch("backend.next_sailings.get_schedule_today")
@mock.patch("backend.next_sailings.get_vessel_positions")
def test_get_next_sailings_for_route(
    mock_get_vessel_positions, mock_get_schedule_today, mock_vessel_data, mock_schedule_data
):
    """Test get_next_sailings_for_route."""
    mock_get_vessel_positions.return_value = mock_vessel_data
    mock_get_schedule_today.return_value = mock_schedule_data
    route_config = {"route_id": 1, "route_name": "SEA-BI", "name": "Seattle - Bainbridge Island"}

    next_sailings = get_next_sailings_for_route(mock_vessel_data, route_config)

    assert len(next_sailings) == 1
    assert len(next_sailings[0].times) == 2


def test_propigate_delays():
    """Test the propigate_delays function."""
    sailings = [
        DirectionalSailing(
            departing_terminal_id=1,
            arriving_terminal_id=2,
            departing_terminal_name="Seattle",
            arriving_terminal_name="Bainbridge Island",
            scheduled_departure=datetime.now(),
            vessel_name="Test Ferry",
            vessel_position_num=1,
        )
    ]
    delay = timedelta(minutes=15)
    delayed_sailings = propigate_delays(delay, sailings)
    assert delayed_sailings[0].delay_in_minutes == 15
