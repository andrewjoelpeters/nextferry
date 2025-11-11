import asyncio
from datetime import datetime
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from backend.main import app, lifespan
from backend.serializers import Vessel


@pytest.fixture
def client():
    """Returns a TestClient instance."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def mock_background_tasks():
    """Mock the background tasks."""
    with mock.patch("backend.main.update_sailings_cache") as mock_update_cache, mock.patch(
        "backend.main.collect_data"
    ) as mock_collect_data:
        yield mock_update_cache, mock_collect_data


def test_home(client):
    """Test the home page."""
    response = client.get("/")
    assert response.status_code == 200


@mock.patch("backend.main.get_next_sailings")
def test_get_next_sailings_html(mock_get_next_sailings, client):
    """Test the /next-sailings endpoint."""
    mock_get_next_sailings.return_value = [
        {
            "route_name": ["Seattle - Bainbridge Island"],
            "route_id": 1,
            "schedules": [],
        }
    ]
    response = client.get("/next-sailings")
    assert response.status_code == 200


@mock.patch("backend.main.get_vessel_positions")
def test_get_ferry_positions(mock_get_vessel_positions, client):
    """Test the /ferry-data endpoint."""
    now_ms = int(datetime.now().timestamp() * 1000)
    mock_get_vessel_positions.return_value = [
        Vessel.model_validate(
            {
                "VesselID": 1,
                "VesselName": "Test Ferry",
                "OpRouteAbbrev": ["SEA-BI"],
                "InService": True,
                "AtDock": False,
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
                "Speed": 15,
                "Heading": 270,
                "LeftDock": f"/Date({now_ms}-0700)/",
                "Eta": f"/Date({now_ms + 600000}-0700)/",
                "TimeStamp": f"/Date({now_ms}-0700)/",
            }
        )
    ]
    response = client.get("/ferry-data")
    assert response.status_code == 200
    assert len(response.json()) == 1


@mock.patch(
    "backend.main._sailings_cache",
    {
        "status": "Cache active",
        "cached_at": datetime.now(),
        "last_updated": "now",
        "routes": [],
    },
)
def test_cache_status(client):
    """Test the /debug/cache-status endpoint."""
    response = client.get("/debug/cache-status")
    assert response.status_code == 200
    assert response.json()["status"] == "Cache active"


@pytest.mark.asyncio
async def test_lifespan():
    """Test the lifespan context manager."""
    with mock.patch("backend.main.asyncio.create_task") as mock_create_task:
        f = asyncio.Future()
        f.set_result(None)
        mock_create_task.return_value = f
        async with lifespan(app):
            pass
        assert mock_create_task.call_count == 2
