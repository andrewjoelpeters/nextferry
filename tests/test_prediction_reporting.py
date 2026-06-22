from datetime import datetime
from unittest.mock import patch
from urllib.parse import parse_qs, unquote, urlparse
from zoneinfo import ZoneInfo

from backend import main


class TestPredictionReporting:
    def test_finds_matching_prediction_context(self):
        with patch(
            "backend.main.get_last_predictions",
            return_value={
                101: {
                    "vessel_id": 101,
                    "vessel_name": "Tacoma",
                    "sailings": [
                        {
                            "scheduled_departure": "2026-06-21T13:00:00-07:00",
                            "departing": "Seattle",
                            "arriving": "Bainbridge Island",
                            "source": "flat_propagation",
                            "inputs": {"current_vessel_delay_minutes": 7},
                            "delay": 7,
                        },
                        {
                            "scheduled_departure": "2026-06-21T14:00:00-07:00",
                            "departing": "Bainbridge Island",
                            "arriving": "Seattle",
                            "source": "eta_bounded",
                            "inputs": {"current_vessel_delay_minutes": 7},
                            "delay": 5,
                        },
                    ],
                }
            },
        ):
            context = main._find_prediction_report_context(
                vessel_name="Tacoma",
                scheduled_departure="2026-06-21T14:00:00-07:00",
                departing_terminal="Bainbridge Island",
                arriving_terminal="Seattle",
            )

        assert context is not None
        assert context["vessel_id"] == 101
        assert context["matched_sailing"]["source"] == "eta_bounded"
        assert len(context["all_vessel_sailings"]) == 2

    def test_builds_github_issue_url_with_captured_context(self):
        report_time = datetime(
            2026, 6, 21, 13, 5, tzinfo=ZoneInfo("America/Los_Angeles")
        )

        with (
            patch("backend.main.current_time", return_value=report_time),
            patch("backend.main.get_replay_time", return_value=None),
            patch(
                "backend.main._find_prediction_report_context",
                return_value={
                    "vessel_id": 808,
                    "vessel_name": "Walla Walla",
                    "matched_sailing": {"source": "eta_bounded", "delay": 8},
                    "all_vessel_sailings": [],
                },
            ),
            patch.object(
                main,
                "_sailings_cache",
                {
                    "last_updated": "1:02:03 PM",
                    "cached_at": report_time,
                    "routes": [
                        {
                            "route_name": "Seattle - Bainbridge Island",
                            "schedules": [
                                {
                                    "departing_terminal_name": "Seattle",
                                    "arriving_terminal_name": "Bainbridge Island",
                                    "sailings": [
                                        {
                                            "scheduled_time": "1:10 PM",
                                            "vessel_name": "Walla Walla",
                                            "delay_minutes": 8,
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                },
            ),
        ):
            issue_url = main._build_prediction_report_url(
                route_name="sea-bi",
                departing_terminal="Seattle",
                arriving_terminal="Bainbridge Island",
                scheduled_departure="2026-06-21T13:10:00-07:00",
                displayed_time="1:10 PM → 1:18 PM",
                time_until="13 min",
                last_updated="1:02:03 PM",
                vessel_name="Walla Walla",
                delay_text="+8m late",
                referrer="https://nextferry.example/",
            )

        parsed = urlparse(issue_url)
        params = parse_qs(parsed.query)
        body = unquote(params["body"][0])

        assert parsed.scheme == "https"
        assert parsed.netloc == "github.com"
        assert "Prediction error: sea-bi Seattle" in params["title"][0]
        assert '"vessel_id": 808' in body
        assert '"displayed_time": "1:10 PM → 1:18 PM"' in body
        assert '"referrer": "https://nextferry.example/"' in body
        assert '"routes"' in body
        assert '"Seattle - Bainbridge Island"' in body
