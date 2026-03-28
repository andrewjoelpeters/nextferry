"""Shared fixtures for integration tests.

Provides a mocked FastAPI TestClient that replaces all external calls
(WSDOT API, database, ML models) with fixture data, so tests run
without network access or a real database.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.next_sailings import CACHED_DELAYS
from backend.serializers import RawRouteSchedule, Vessel
from tests.fixtures.scenarios import (
    scenario_multi_route,
    scenario_null_fields,
    scenario_one_en_route_one_docked,
    scenario_two_boats_at_dock,
)


def _build_mock_vessels(vessel_dicts: list[dict]) -> list[Vessel]:
    """Convert raw WSDOT dicts to Vessel objects (same as wsdot_client does)."""
    return [Vessel(**v) for v in vessel_dicts]


def _build_schedule_response(schedule_dict: dict):
    """Parse a schedule dict into RawDirectionalSchedule list (same as wsdot_client)."""
    parsed = RawRouteSchedule(**schedule_dict)
    return parsed.terminal_combos


def _make_client(scenario: dict, ml_trained: bool = False, dock_trained: bool = False):
    """Create a TestClient with WSDOT API and models mocked for a given scenario.

    Args:
        scenario: Dict with 'vessels' and 'schedules' keys from scenarios.py
        ml_trained: Whether the en-route ML predictor should appear trained
        dock_trained: Whether the dock predictor should appear trained
    """
    vessels = _build_mock_vessels(scenario["vessels"])
    schedules = scenario["schedules"]

    def mock_get_vessel_positions():
        return list(vessels)

    def mock_get_schedule_today(route_id):
        if route_id in schedules:
            return _build_schedule_response(schedules[route_id])
        return []

    def mock_get_sailing_space():
        return []

    # Create mock predictors
    mock_ml = MagicMock()
    mock_ml.is_trained = ml_trained
    mock_ml.last_evaluation = None
    mock_ml.last_trained = None
    mock_ml.training_data_size = 0
    if ml_trained:
        mock_ml.predict.return_value = {
            "predicted_delay": 3,
            "lower_bound": 1,
            "upper_bound": 6,
        }
    else:
        mock_ml.predict.return_value = None

    mock_dock = MagicMock()
    mock_dock.is_trained = dock_trained
    mock_dock.last_evaluation = None
    mock_dock.last_trained = None
    mock_dock.training_data_size = 0
    if dock_trained:
        mock_dock.predict.return_value = {
            "predicted_delay": 2,
            "lower_bound": 0,
            "upper_bound": 5,
        }
    else:
        mock_dock.predict.return_value = None

    mock_fill = MagicMock()
    mock_fill.is_trained = False
    mock_fill.last_trained = None
    mock_fill.training_data_size = 0
    mock_fill.fill_rate = None
    mock_fill.predict.return_value = None
    mock_fill.load.return_value = None

    patches = [
        # Patch where the functions are imported (not at source) so the local
        # references in each module pick up the mock.
        patch("backend.next_sailings.get_vessel_positions", mock_get_vessel_positions),
        patch("backend.next_sailings.get_schedule_today", mock_get_schedule_today),
        patch("backend.sailing_space.get_sailing_space", mock_get_sailing_space),
        # Patch predictors at the module level where they're imported
        patch("backend.next_sailings.ml_predictor", mock_ml),
        patch("backend.next_sailings.dock_predictor", mock_dock),
        patch("backend.display_processing.fill_predictor", mock_fill),
        patch("backend.main.ml_predictor", mock_ml),
        patch("backend.main.dock_predictor", mock_dock),
        patch("backend.main.fill_predictor", mock_fill),
        # Stub out database calls that may happen during prediction
        patch("backend.next_sailings.get_previous_sailing_fullness", return_value=None),
        patch("backend.next_sailings.get_turnaround_minutes", return_value=None),
        patch(
            "backend.display_processing.get_departed_sailing_space", return_value=None
        ),
        # Stub database init and dashboard
        patch("backend.main.init_db"),
        patch("backend.main.get_dashboard_data", return_value={}),
        patch("backend.main.get_sailing_event_count", return_value=0),
        patch("backend.main.get_snapshot_count", return_value=0),
    ]

    for p in patches:
        p.start()

    # Clear module-level global state that leaks between tests
    CACHED_DELAYS.clear()

    from backend.next_sailings import _last_predictions

    _last_predictions.clear()

    # Import app AFTER patches are applied so lifespan doesn't run real tasks
    # We use TestClient without lifespan to avoid background tasks
    from backend.main import app

    client = TestClient(app, raise_server_exceptions=True)

    return client, patches, mock_ml, mock_dock


def _cleanup_patches(patches):
    for p in patches:
        p.stop()


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client_two_boats_docked():
    """Client with two boats docked at their respective terminals, no ML models."""
    client, patches, _, _ = _make_client(scenario_two_boats_at_dock())
    yield client
    _cleanup_patches(patches)


@pytest.fixture()
def client_en_route_delayed():
    """Client with one boat en route (delayed) and one docked, no ML models."""
    client, patches, _, _ = _make_client(scenario_one_en_route_one_docked())
    yield client
    _cleanup_patches(patches)


@pytest.fixture()
def client_null_fields():
    """Client with a vessel that has null scheduling fields."""
    client, patches, _, _ = _make_client(scenario_null_fields())
    yield client
    _cleanup_patches(patches)


@pytest.fixture()
def client_multi_route():
    """Client with vessels on two different routes."""
    client, patches, _, _ = _make_client(scenario_multi_route())
    yield client
    _cleanup_patches(patches)


@pytest.fixture()
def client_with_ml_models():
    """Client with both ML models trained (returns mock predictions)."""
    client, patches, mock_ml, mock_dock = _make_client(
        scenario_two_boats_at_dock(), ml_trained=True, dock_trained=True
    )
    yield client, mock_ml, mock_dock
    _cleanup_patches(patches)


@pytest.fixture()
def client_en_route_with_ml():
    """Client with en-route vessel + trained ML models."""
    client, patches, mock_ml, mock_dock = _make_client(
        scenario_one_en_route_one_docked(), ml_trained=True, dock_trained=True
    )
    yield client, mock_ml, mock_dock
    _cleanup_patches(patches)
