"""Tests for user metrics tracking."""

from unittest.mock import patch

from backend.database import get_metrics_data, init_db, insert_page_view
from backend.metrics import _hash_visitor, _should_track, track_request


def _setup_test_db(tmp_path):
    """Point the database at a temporary path and initialize it."""
    db_path = tmp_path / "test.db"
    with patch("backend.database._db_path", db_path):
        init_db()
    return db_path


class TestShouldTrack:
    def test_skips_static_assets(self):
        assert _should_track("/static/style.css") is False
        assert _should_track("/static/alerts.js") is False

    def test_skips_polling_endpoints(self):
        assert _should_track("/ferry-data") is False
        assert _should_track("/next-sailings") is False

    def test_skips_debug(self):
        assert _should_track("/debug/cache-status") is False

    def test_skips_sw(self):
        assert _should_track("/sw.js") is False

    def test_tracks_main_pages(self):
        assert _should_track("/") is True
        assert _should_track("/sailings-tab") is True
        assert _should_track("/map-tab") is True
        assert _should_track("/predictions-tab") is True
        assert _should_track("/metrics-tab") is True


class TestHashVisitor:
    def test_deterministic(self):
        h1 = _hash_visitor("1.2.3.4", "Mozilla/5.0")
        h2 = _hash_visitor("1.2.3.4", "Mozilla/5.0")
        assert h1 == h2

    def test_different_ips_differ(self):
        h1 = _hash_visitor("1.2.3.4", "Mozilla/5.0")
        h2 = _hash_visitor("5.6.7.8", "Mozilla/5.0")
        assert h1 != h2

    def test_length(self):
        h = _hash_visitor("1.2.3.4", "Mozilla/5.0")
        assert len(h) == 16


class TestInsertAndQuery:
    def test_insert_and_retrieve(self, tmp_path):
        db_path = _setup_test_db(tmp_path)
        with patch("backend.database._db_path", db_path):
            insert_page_view(
                timestamp="2026-03-26T10:00:00-07:00",
                path="/",
                visitor_hash="abc123",
                device_type="Mobile",
                browser="Safari",
                os="iOS",
                referrer=None,
            )
            insert_page_view(
                timestamp="2026-03-26T10:05:00-07:00",
                path="/sailings-tab",
                visitor_hash="abc123",
                device_type="Mobile",
                browser="Safari",
                os="iOS",
                referrer=None,
            )
            insert_page_view(
                timestamp="2026-03-26T11:00:00-07:00",
                path="/",
                visitor_hash="def456",
                device_type="Desktop",
                browser="Chrome",
                os="Windows",
                referrer="https://google.com",
            )

            metrics = get_metrics_data(days=30)

            assert metrics["total_views"] == 3
            assert metrics["unique_visitors"] == 2
            assert len(metrics["views_by_path"]) == 2
            assert len(metrics["device_breakdown"]) == 2
            assert len(metrics["browser_breakdown"]) == 2


class TestTrackRequest:
    def test_skips_bots(self, tmp_path):
        db_path = _setup_test_db(tmp_path)
        with patch("backend.database._db_path", db_path):
            track_request(
                path="/",
                client_ip="1.2.3.4",
                user_agent_str="Googlebot/2.1 (+http://www.google.com/bot.html)",
                referrer=None,
            )
            metrics = get_metrics_data(days=30)
            assert metrics["total_views"] == 0

    def test_tracks_real_browser(self, tmp_path):
        db_path = _setup_test_db(tmp_path)
        with patch("backend.database._db_path", db_path):
            track_request(
                path="/",
                client_ip="1.2.3.4",
                user_agent_str="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                referrer=None,
            )
            metrics = get_metrics_data(days=30)
            assert metrics["total_views"] == 1
            assert metrics["device_breakdown"][0]["device_type"] == "Mobile"

    def test_skips_filtered_paths(self, tmp_path):
        db_path = _setup_test_db(tmp_path)
        with patch("backend.database._db_path", db_path):
            track_request(
                path="/ferry-data",
                client_ip="1.2.3.4",
                user_agent_str="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                referrer=None,
            )
            metrics = get_metrics_data(days=30)
            assert metrics["total_views"] == 0
