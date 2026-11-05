"""Tests for the static live-data collector."""

import json

import pytest

from backend import replay
from backend.collector import R2Publisher, collect_once, write_local
from backend.database import get_snapshot_count, init_db
from backend.next_sailings import CACHED_DELAYS, _last_predictions
from tests.scenarios import scenario_at_dock_overdue


class FakeR2Client:
    def __init__(self):
        self.objects = {}

    def put_object(self, **kwargs):
        self.objects[kwargs["Key"]] = kwargs


@pytest.fixture
def replay_collector(tmp_path, isolated_db_path, monkeypatch):
    scenario_path = tmp_path / "scenario.json"
    scenario_path.write_text(json.dumps(scenario_at_dock_overdue()))

    monkeypatch.setenv("NEXTFERRY_SCENARIO", str(scenario_path))
    replay.activate_replay(str(scenario_path))
    monkeypatch.setattr(
        "backend.database.get_db_path",
        lambda: isolated_db_path / "ferry.db",
    )
    init_db()

    yield scenario_path

    replay._replay_time = None
    replay._scenario_data = None
    CACHED_DELAYS.clear()
    _last_predictions.clear()


@pytest.fixture
def artifacts(replay_collector):
    return collect_once(persist_history=False)


def test_collect_once_builds_live_artifacts(artifacts, replay_collector):
    vessels = artifacts["ferry-data.json"]
    html = artifacts["next-sailings.html"]
    meta = artifacts["meta.json"]

    assert len(vessels) == 2
    assert any(v["VesselName"] == "Walla Walla" for v in vessels)
    assert "Walla Walla" in html
    assert "Last updated:" in html
    assert meta["vessel_count"] == 2
    assert meta["route_count"] == 2
    assert (
        meta["generated_at"] == json.loads(replay_collector.read_text())["captured_at"]
    )


def test_write_local_writes_all_objects(artifacts, tmp_path):
    output_dir = tmp_path / "live"

    write_local(artifacts, output_dir)

    assert (output_dir / "ferry-data.json").is_file()
    assert (output_dir / "next-sailings.html").is_file()
    assert (output_dir / "meta.json").is_file()
    assert "Walla Walla" in (output_dir / "next-sailings.html").read_text()


def test_r2_publisher_uploads_live_objects(artifacts):
    client = FakeR2Client()
    publisher = R2Publisher(bucket="test-bucket", prefix="live", client=client)

    publisher.publish(artifacts)

    assert set(client.objects) == {
        "live/ferry-data.json",
        "live/next-sailings.html",
        "live/meta.json",
    }
    assert client.objects["live/next-sailings.html"]["ContentType"] == (
        "text/html; charset=utf-8"
    )


def test_collect_once_persists_history(replay_collector):
    collect_once(persist_history=True)

    assert get_snapshot_count() == 2
