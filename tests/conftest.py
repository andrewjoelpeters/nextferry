"""Shared test fixtures for Next Ferry integration tests."""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def isolated_db_path():
    """Provide a temporary database path, restoring env after the test."""
    original = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
    temp_dir = tempfile.mkdtemp(prefix="nextferry_test_")
    try:
        yield Path(temp_dir)
    finally:
        # Restore env
        if original is None:
            os.environ.pop("RAILWAY_VOLUME_MOUNT_PATH", None)
        else:
            os.environ["RAILWAY_VOLUME_MOUNT_PATH"] = original
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def client(isolated_db_path):
    """FastAPI TestClient with an isolated temporary database."""
    from backend.database import init_db as _init_db

    def _get_db_path():
        p = isolated_db_path / "ferry.db"
        return p

    with patch("backend.database.get_db_path", _get_db_path):
        _init_db()
        from backend.main import app

        yield TestClient(app, raise_server_exceptions=False)
        _tmp = isolated_db_path / "ferry.db"
        _tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Replay-mode integration test fixture
# ---------------------------------------------------------------------------


def _reset_app_state():
    """Clear module-level state so each replay test starts fresh."""
    import backend.main as _main_mod
    import backend.next_sailings as _ns_mod
    import backend.replay as _replay_mod

    _replay_mod._replay_time = None
    _replay_mod._scenario_data = None
    _ns_mod.CACHED_DELAYS.clear()
    _ns_mod._last_predictions.clear()
    _main_mod._sailings_cache = None


@pytest.fixture
def replay_client(request, tmp_path, isolated_db_path):
    """FastAPI TestClient with replay mode activated for a scenario.

    Usage:
        @pytest.mark.parametrize("replay_client", [scenario_at_dock_overdue()], indirect=True)
        def test_something(replay_client):
            resp = replay_client.get("/ferry-data")

    The fixture writes the scenario dict to a temp JSON file, patches the DB
    path for isolation, and resets module-level state so each test is isolated.
    """
    scenario = request.param
    scenario_path = tmp_path / "scenario.json"
    with open(scenario_path, "w") as f:
        json.dump(scenario, f)

    os.environ["NEXTFERRY_SCENARIO"] = str(scenario_path)

    _reset_app_state()

    # Patch DB and then manually activate replay BEFORE creating the TestClient.
    # This avoids depending on lifespan to call activate_replay (which can race
    # with background tasks or the request lifecycle).
    from backend.replay import activate_replay

    activate_replay(str(scenario_path))

    def _get_db_path():
        return isolated_db_path / "ferry.db"

    with patch("backend.database.get_db_path", _get_db_path):
        from backend.main import app

        client = TestClient(app, raise_server_exceptions=False)
        yield client

    os.environ.pop("NEXTFERRY_SCENARIO", None)
    _reset_app_state()
