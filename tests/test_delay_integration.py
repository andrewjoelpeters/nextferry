"""Integration tests that verify delay calculation and display accuracy.

Uses replay-mode scenarios (synthetic WSDOT JSON data loaded via
NEXTFERRY_SCENARIO) so the full pipeline runs without mocks or
network access.  Every test is deterministic — the scenario fixes
the "current time" so delay values are predictable.

Agent workflow:
    uv run pytest tests/test_delay_integration.py -v
"""

import pytest

from tests.scenarios import (
    scenario_at_dock_overdue,
    scenario_en_route_delayed,
    scenario_just_departed,
    scenario_multi_route,
    scenario_normal_ops,
    scenario_null_fields,
)


def _find_vessel(data: list[dict], name: str) -> dict | None:
    return next((v for v in data if v["VesselName"] == name), None)


# ===================================================================
# Scenario: At-dock vessel overdue
# ===================================================================


@pytest.mark.parametrize("replay_client", [scenario_at_dock_overdue()], indirect=True)
class TestAtDockOverdue:
    def test_ferry_data_overdue_delay(self, replay_client):
        """Overdue vessel should have DelayMinutes = minutes since scheduled departure."""
        data = replay_client.get("/ferry-data").json()
        walla = _find_vessel(data, "Walla Walla")
        assert walla is not None
        # scheduled 13:10, replay time 14:00 → 50 min overdue
        assert walla["DelayMinutes"] == 50, f"Expected 50, got {walla['DelayMinutes']}"
        assert walla["PredictedDeparture"] is not None

    def test_ferry_data_at_dock_status(self, replay_client):
        """At-dock vessel should show AtDock=true and zero speed."""
        data = replay_client.get("/ferry-data").json()
        walla = _find_vessel(data, "Walla Walla")
        assert walla["AtDock"] is True
        assert walla["Speed"] == 0.0

    def test_second_vessel_no_delay(self, replay_client):
        """Second vessel (Spokane) has future scheduled departure → no overdue."""
        data = replay_client.get("/ferry-data").json()
        spokane = _find_vessel(data, "Spokane")
        assert spokane is not None
        assert spokane["DelayMinutes"] is None
        assert spokane["AtDock"] is True

    def test_sailings_endpoint_ok(self, replay_client):
        assert replay_client.get("/next-sailings").status_code == 200

    def test_sailings_contains_vessels(self, replay_client):
        html = replay_client.get("/next-sailings").text
        assert "Walla Walla" in html
        assert "Spokane" in html

    def test_all_endpoints_200(self, replay_client):
        endpoints = [
            "/ferry-data",
            "/next-sailings",
            "/",
            "/debug/cache-status",
        ]
        for ep in endpoints:
            resp = replay_client.get(ep)
            assert resp.status_code == 200, f"{ep} returned {resp.status_code}"


# ===================================================================
# Scenario: En route with 5-minute delay
# ===================================================================


@pytest.mark.parametrize("replay_client", [scenario_en_route_delayed()], indirect=True)
class TestEnRouteDelayed:
    def test_en_route_delay_computed(self, replay_client):
        """Delay should be LeftDock(13:15) - ScheduledDeparture(13:10) = 5 min."""
        data = replay_client.get("/ferry-data").json()
        walla = _find_vessel(data, "Walla Walla")
        assert walla is not None
        assert walla["DelayMinutes"] == 5, f"Expected 5, got {walla['DelayMinutes']}"
        assert walla["AtDock"] is False
        assert walla["Speed"] > 0

    def test_en_route_has_eta(self, replay_client):
        data = replay_client.get("/ferry-data").json()
        walla = _find_vessel(data, "Walla Walla")
        assert walla["Eta"] is not None

    def test_second_vessel_at_dock(self, replay_client):
        data = replay_client.get("/ferry-data").json()
        spokane = _find_vessel(data, "Spokane")
        assert spokane is not None
        assert spokane["AtDock"] is True
        assert spokane["DelayMinutes"] is None

    def test_sailings_renders(self, replay_client):
        html = replay_client.get("/next-sailings").text
        assert "Walla Walla" in html
        assert "Spokane" in html

    def test_predictions_debug(self, replay_client):
        replay_client.get("/next-sailings")  # trigger computation
        pred = replay_client.get("/debug/predictions").json()
        assert len(pred) > 0
        vessel_preds = list(pred.values())
        sailings = vessel_preds[0].get("sailings", [])
        if sailings:
            assert "trace" in sailings[0]
            assert sailings[0]["trace"]["source"] in (
                "flat_propagation",
                "eta_bounded",
                "re_propagated",
            )


# ===================================================================
# Scenario: Just departed (0 delay)
# ===================================================================


@pytest.mark.parametrize("replay_client", [scenario_just_departed()], indirect=True)
class TestJustDeparted:
    def test_zero_delay(self, replay_client):
        """On-time departure → DelayMinutes = 0."""
        data = replay_client.get("/ferry-data").json()
        walla = _find_vessel(data, "Walla Walla")
        assert walla is not None
        assert walla["DelayMinutes"] == 0, f"Expected 0, got {walla['DelayMinutes']}"

    def test_just_departed_status(self, replay_client):
        data = replay_client.get("/ferry-data").json()
        walla = _find_vessel(data, "Walla Walla")
        assert walla["AtDock"] is False

    def test_sailings_endpoint_200(self, replay_client):
        assert replay_client.get("/next-sailings").status_code == 200


# ===================================================================
# Scenario: Null fields (WSDOT gotcha)
# ===================================================================


@pytest.mark.parametrize("replay_client", [scenario_null_fields()], indirect=True)
class TestNullFields:
    def test_null_fields_dont_crash(self, replay_client):
        data = replay_client.get("/ferry-data").json()
        assert isinstance(data, list)
        walla = _find_vessel(data, "Walla Walla")
        assert walla is not None

    def test_null_fields_no_delay(self, replay_client):
        """No LeftDock/ScheduledDeparture → no delay."""
        data = replay_client.get("/ferry-data").json()
        walla = _find_vessel(data, "Walla Walla")
        assert walla["DelayMinutes"] is None
        assert walla["PredictedDeparture"] is None

    def test_null_fields_second_vessel_ok(self, replay_client):
        data = replay_client.get("/ferry-data").json()
        spokane = _find_vessel(data, "Spokane")
        assert spokane is not None
        assert spokane["AtDock"] is True

    def test_null_fields_sailings_ok(self, replay_client):
        assert replay_client.get("/next-sailings").status_code == 200

    def test_null_fields_errors_ok(self, replay_client):
        for ep in ["/ferry-data", "/next-sailings"]:
            assert replay_client.get(ep).status_code == 200


# ===================================================================
# Scenario: Normal ops (two boats at dock)
# ===================================================================


@pytest.mark.parametrize("replay_client", [scenario_normal_ops()], indirect=True)
class TestNormalOps:
    def test_vessels_present(self, replay_client):
        data = replay_client.get("/ferry-data").json()
        names = {v["VesselName"] for v in data}
        assert "Walla Walla" in names
        assert "Spokane" in names

    def test_no_delays(self, replay_client):
        data = replay_client.get("/ferry-data").json()
        for v in data:
            assert v["DelayMinutes"] is None, f"{v['VesselName']} has unexpected delay"

    def test_both_at_dock(self, replay_client):
        data = replay_client.get("/ferry-data").json()
        assert all(v["AtDock"] for v in data)

    def test_sailings_route_sections(self, replay_client):
        html = replay_client.get("/next-sailings").text
        assert "Seattle" in html
        assert "Bainbridge" in html


# ===================================================================
# Scenario: Multi-route
# ===================================================================


@pytest.mark.parametrize("replay_client", [scenario_multi_route()], indirect=True)
class TestMultiRoute:
    def test_all_three_vessels(self, replay_client):
        data = replay_client.get("/ferry-data").json()
        names = {v["VesselName"] for v in data}
        assert "Walla Walla" in names
        assert "Spokane" in names
        assert "Puyallup" in names

    def test_routes_isolated(self, replay_client):
        data = replay_client.get("/ferry-data").json()
        for v in data:
            routes = v["OpRouteAbbrev"]
            if v["VesselName"] == "Puyallup":
                assert "ed-king" in routes
                assert "sea-bi" not in routes
            else:
                assert "sea-bi" in routes
                assert "ed-king" not in routes

    def test_sailings_both_routes(self, replay_client):
        html = replay_client.get("/next-sailings").text
        assert "Seattle" in html
        assert "Edmonds" in html or "Kingston" in html

    def test_ferry_data_required_fields(self, replay_client):
        data = replay_client.get("/ferry-data").json()
        required = [
            "VesselID",
            "VesselName",
            "Latitude",
            "Longitude",
            "Heading",
            "Speed",
            "AtDock",
            "OpRouteAbbrev",
            "DelayMinutes",
            "PredictedDeparture",
        ]
        for v in data:
            for field in required:
                assert field in v, f"{v.get('VesselName', '?')} missing {field}"

    def test_positions_in_range(self, replay_client):
        data = replay_client.get("/ferry-data").json()
        for v in data:
            lat, lon = v["Latitude"], v["Longitude"]
            assert 47.0 <= lat <= 49.0, f"{v['VesselName']} lat {lat} out of range"
            assert -123.5 <= lon <= -122.0, f"{v['VesselName']} lon {lon} out of range"
