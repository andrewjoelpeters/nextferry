import os
from unittest import mock

import pytest

from backend.wsdot_client import (get_schedule_today, get_sailing_space,
                                  get_vessel_positions)


@pytest.fixture
def mock_api_key():
    """Mock the WSDOT_API_KEY environment variable."""
    with mock.patch.dict(os.environ, {"WSDOT_API_KEY": "test_api_key"}, clear=True):
        yield


def test_get_vessel_positions_no_api_key():
    """Test get_vessel_positions when WSDOT_API_KEY is not set."""
    with mock.patch.dict(os.environ, {}, clear=True):
        with pytest.raises(Exception) as excinfo:
            get_vessel_positions()
        assert "WSDOT_API_KEY environment variable is not set" in str(excinfo.value)


@mock.patch("backend.wsdot_client.requests.get")
def test_get_vessel_positions_success(mock_get, mock_api_key):
    """Test get_vessel_positions with a successful API response."""
    mock_response = mock.Mock()
    mock_response.ok = True
    mock_response.json.return_value = [
        {
            "VesselID": 1,
            "VesselName": "Test Ferry",
            "Mmsi": 123456789,
            "DepartingTerminalID": 1,
            "DepartingTerminalName": "Seattle",
            "DepartingTerminalAbbrev": "SEA",
            "ArrivingTerminalID": 2,
            "ArrivingTerminalName": "Bainbridge Island",
            "ArrivingTerminalAbbrev": "BAI",
            "Latitude": 47.6,
            "Longitude": -122.5,
            "Speed": 15.0,
            "Heading": 270,
            "InService": True,
            "AtDock": False,
            "LeftDock": "/Date(1678886400000-0700)/",
            "Eta": "/Date(1678887300000-0700)/",
            "ScheduledDeparture": "/Date(1678886400000-0700)/",
            "TimeStamp": "/Date(1678886400000-0700)/",
            "OpRouteAbbrev": ["SEA-BI"],
            "VesselPositionNum": 1,
        }
    ]
    mock_get.return_value = mock_response

    vessels = get_vessel_positions()

    assert len(vessels) == 1
    assert vessels[0].vessel_name == "Test Ferry"
    mock_get.assert_called_once_with(
        "https://www.wsdot.wa.gov/ferries/api/vessels/rest/vessellocations?apiaccesscode=test_api_key"
    )


@mock.patch("backend.wsdot_client.requests.get")
def test_get_schedule_today_success(mock_get, mock_api_key):
    """Test get_schedule_today with a successful API response."""
    mock_response = mock.Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "TerminalCombos": [
            {
                "DepartingTerminalID": 1,
                "DepartingTerminalName": "Seattle",
                "ArrivingTerminalID": 2,
                "ArrivingTerminalName": "Bainbridge Island",
                "SailingNotes": "",
                "Times": [
                    {
                        "DepartingTime": "/Date(1678886400000-0700)/",
                        "VesselName": "Test Ferry",
                        "VesselPositionNum": 1,
                    }
                ],
            }
        ]
    }
    mock_get.return_value = mock_response

    schedule = get_schedule_today(1)

    assert len(schedule) == 1
    assert schedule[0].departing_terminal_name == "Seattle"
    mock_get.assert_called_once_with(
        "https://www.wsdot.wa.gov/ferries/api/schedule/rest/scheduletoday/1/false?apiaccesscode=test_api_key"
    )


@mock.patch("backend.wsdot_client.requests.get")
def test_get_sailing_space_success(mock_get, mock_api_key):
    """Test get_sailing_space with a successful API response."""
    mock_response = mock.Mock()
    mock_response.ok = True
    mock_response.json.return_value = [
        {
            "TerminalID": 1,
            "TerminalName": "Seattle",
            "DepartingSpaces": [
                {
                    "Departure": "/Date(1678886400000-0700)/",
                    "IsCancelled": False,
                    "VesselID": 1,
                    "VesselName": "Test Ferry",
                    "MaxSpaceCount": 202,
                    "SpaceForArrivalTerminals": [
                        {
                            "TerminalID": 2,
                            "TerminalName": "Bainbridge Island",
                            "ReservableSpaceCount": 100,
                            "DriveUpSpaceCount": 102,
                            "MaxSpaceCount": 202,
                        }
                    ],
                }
            ],
        }
    ]
    mock_get.return_value = mock_response

    sailing_space = get_sailing_space()

    assert len(sailing_space) == 1
    assert sailing_space[0].terminal_name == "Seattle"
    mock_get.assert_called_once_with(
        "https://www.wsdot.wa.gov/ferries/api/terminals/rest/terminalsailingspace?apiaccesscode=test_api_key"
    )
