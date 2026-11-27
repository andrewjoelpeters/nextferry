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


def test_poll_interval_follows_service_across_midnight():
    from datetime import datetime, timedelta
    from types import SimpleNamespace

    from backend.collector import poll_interval
    from backend.config import ROUTES
    from backend.replay import PT

    now = datetime(2026, 11, 27, 23, 50, tzinfo=PT)
    departure = SimpleNamespace(scheduled_departure=now + timedelta(minutes=45))
    schedules = {
        route["route_id"]: [
            SimpleNamespace(departing_terminal_id=t, times=[departure])
            for t in route["terminals"]
        ]
        for route in ROUTES
    }

    def interval(at, vessels):
        return poll_interval(at, vessels, schedules, at)

    assert interval(now, []) == 600
    assert interval(now + timedelta(minutes=33), []) == 120
    assert interval(now + timedelta(minutes=35), []) == 60
    assert interval(now + timedelta(minutes=50), []) == 60

    late = SimpleNamespace(route_name=["ed-king"], at_dock=False)
    assert interval(now + timedelta(hours=2), [late]) == 60
    late.route_name = ["muk-cl"]
    assert interval(now, [late]) == 60
    late.route_name = []
    assert interval(now, [late]) == 60
    late.route_name = ["ed-king"]
    late.at_dock = True
    late.scheduled_departure = now
    late.left_dock = None
    assert interval(now + timedelta(hours=2), [late]) == 60

    # The current timetable ends before the next service day's first trip.
    assert interval(now.replace(hour=2, minute=48), []) == 120
    before_rollover = now.replace(hour=2, minute=59, second=59)
    assert (
        poll_interval(
            before_rollover + timedelta(seconds=2), [], schedules, before_rollover
        )
        == 60
    )
    schedules[6] = []
    assert interval(now, []) == 60


def test_history_uses_elapsed_time_through_idle_and_active_polls(monkeypatch, tmp_path):
    from backend import collector

    elapsed = 0
    attempts = []
    intervals = iter([600, 60, 60, 60, 60, 60, 60])

    def cycle(due):
        attempts.append((elapsed, due))
        return (
            {"meta.json": {"route_count": 2, "vessel_count": 1}},
            next(intervals),
            due,
        )

    def sleep(seconds):
        nonlocal elapsed
        elapsed += seconds
        if elapsed > 900:
            raise StopIteration

    monkeypatch.delenv("NEXTFERRY_SCENARIO", raising=False)
    monkeypatch.setattr(collector, "_collect_cycle", cycle)
    monkeypatch.setattr(collector, "write_local", lambda *_: None)
    monkeypatch.setattr(collector, "init_db", lambda: None)
    monkeypatch.setattr(collector.fill_predictor, "load", lambda: None)
    monkeypatch.setattr(collector.time, "monotonic", lambda: elapsed)
    monkeypatch.setattr(collector.time, "sleep", sleep)
    with pytest.raises(StopIteration):
        collector.main(["--no-upload"])
    assert [seconds for seconds, due in attempts if due] == [0, 600, 900]
