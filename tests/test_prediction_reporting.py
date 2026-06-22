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
                            "delay": 7,
                            "trace": {
                                "source": "flat_propagation",
                                "reason": "at_dock_delay",
                                "predicted_departure": "2026-06-21T13:07:00-07:00",
                            },
                        },
                        {
                            "scheduled_departure": "2026-06-21T14:00:00-07:00",
                            "departing": "Bainbridge Island",
                            "arriving": "Seattle",
                            "delay": 5,
                            "trace": {
                                "source": "eta_bounded",
                                "predicted_arrival": "2026-06-21T14:38:00-07:00",
                                "arrival_source": "wsdot_eta",
                                "turnaround_minutes": 17,
                                "turnaround_source": "p75_ceiling",
                                "predicted_departure": "2026-06-21T14:55:00-07:00",
                                "delay_minutes": 5,
                                "arriving_terminal_name": "Seattle",
                            },
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
        assert context["matched_sailing"]["trace"]["source"] == "eta_bounded"
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
                    "matched_sailing": {
                        "trace": {"source": "eta_bounded", "delay_minutes": 8}
                    },
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

    def test_url_length_limit_drops_routes_when_body_too_large(self):
        """When the full context would exceed GitHub's URL limit the function
        falls back to dropping sailings_cache.routes so the URL stays short
        enough for GitHub to accept."""
        report_time = datetime(
            2026, 6, 21, 13, 5, tzinfo=ZoneInfo("America/Los_Angeles")
        )

        # Build a routes list large enough to push the URL over 8 000 chars.
        many_sailings = [
            {
                "scheduled_time": f"{hour}:00 PM",
                "vessel_name": "Tokitae",
                "delay_minutes": delay_idx,
            }
            for delay_idx, hour in enumerate(range(1, 21))
        ]
        large_routes = [
            {
                "route_name": f"Route {n} - Very Long Route Name Here",
                "schedules": [
                    {
                        "departing_terminal_name": f"Terminal {n}",
                        "arriving_terminal_name": f"Destination {n}",
                        "sailings": many_sailings,
                    }
                ],
            }
            for n in range(20)
        ]

        with (
            patch("backend.main.current_time", return_value=report_time),
            patch("backend.main.get_replay_time", return_value=None),
            patch("backend.main._find_prediction_report_context", return_value=None),
            patch.object(
                main,
                "_sailings_cache",
                {
                    "last_updated": "1:00:00 PM",
                    "cached_at": report_time,
                    "routes": large_routes,
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
                last_updated="1:00:00 PM",
            )

        assert len(issue_url) <= 8000
        parsed = urlparse(issue_url)
        assert parsed.scheme == "https"
        body = unquote(parse_qs(parsed.query)["body"][0])
        # Core context is still present even after trimming.
        assert '"displayed_time"' in body
        # Routes were omitted to stay within the limit.
        assert "routes_omitted" in body
