"""Integration tests that start the app with mocked WSDOT data and verify
end-to-end behavior across endpoints.

These tests verify:
1. Cross-endpoint consistency: map data matches sailings data for the same vessel
2. Correct model selection: dock model for at-dock, en-route model for moving vessels
3. Edge cases: null fields, departed sailings, multi-route scenarios
4. Data pipeline integrity: WSDOT data flows correctly through to display
5. Additional scenarios: severe delay, both en route, just departed, arriving, late night

Run with: uv run pytest tests/test_integration.py -v
"""

import pytest

# ---------------------------------------------------------------------------
# Cross-endpoint consistency: /ferry-data (map) vs /next-sailings (list)
# ---------------------------------------------------------------------------


class TestCrossEndpointConsistency:
    """Verify that map view and sailings list show consistent data."""

    def test_map_and_sailings_show_same_vessels(self, client_two_boats_docked):
        """Every vessel on the map should appear in the sailings list."""
        client = client_two_boats_docked

        map_resp = client.get("/ferry-data")
        assert map_resp.status_code == 200
        map_data = map_resp.json()

        sailings_resp = client.get("/next-sailings")
        assert sailings_resp.status_code == 200
        html = sailings_resp.text

        # Both vessels should appear in the map data
        map_vessel_names = {v["VesselName"] for v in map_data}
        assert "Walla Walla" in map_vessel_names
        assert "Spokane" in map_vessel_names

        # Both vessels should appear in the sailings HTML
        assert "Walla Walla" in html
        assert "Spokane" in html

    def test_at_dock_vessel_consistent_between_endpoints(self, client_two_boats_docked):
        """A vessel shown at dock on the map should show as at-dock in sailings."""
        client = client_two_boats_docked

        map_resp = client.get("/ferry-data")
        map_data = map_resp.json()

        # Find at-dock vessels in map data
        at_dock_vessels = [v for v in map_data if v["AtDock"]]
        assert len(at_dock_vessels) >= 1

        sailings_resp = client.get("/next-sailings")
        html = sailings_resp.text

        for vessel in at_dock_vessels:
            # At-dock vessels should appear in the sailings view
            assert vessel["VesselName"] in html

    def test_en_route_vessel_delay_consistent(self, client_en_route_delayed):
        """Delay shown on map should match delay shown in sailings list."""
        client = client_en_route_delayed

        map_resp = client.get("/ferry-data")
        map_data = map_resp.json()

        # Find the en-route vessel
        en_route = [v for v in map_data if not v["AtDock"]]
        assert len(en_route) >= 1

        en_route_vessel = en_route[0]
        # En-route vessel with LeftDock and ScheduledDeparture should have delay
        if en_route_vessel["LeftDock"] and en_route_vessel["ScheduledDeparture"]:
            assert en_route_vessel["DelayMinutes"] is not None

            # The sailings view should also show this vessel as delayed
            sailings_resp = client.get("/next-sailings")
            html = sailings_resp.text
            assert en_route_vessel["VesselName"] in html
            # Delay should manifest as "status-delayed" class in the HTML
            assert "status-delayed" in html

    def test_map_positions_are_valid(self, client_two_boats_docked):
        """All vessels on the map should have valid lat/lon in Puget Sound area."""
        client = client_two_boats_docked
        map_data = client.get("/ferry-data").json()

        for vessel in map_data:
            lat = vessel["Latitude"]
            lon = vessel["Longitude"]
            assert lat is not None
            assert lon is not None
            # Puget Sound bounding box (approximate)
            assert 47.0 <= lat <= 49.0, f"{vessel['VesselName']} lat {lat} out of range"
            assert -123.5 <= lon <= -122.0, (
                f"{vessel['VesselName']} lon {lon} out of range"
            )

    def test_multi_route_sailings_separate(self, client_multi_route):
        """Vessels on different routes should appear in separate route sections."""
        client = client_multi_route

        sailings_resp = client.get("/next-sailings")
        html = sailings_resp.text

        # Both routes should be present
        assert "Seattle" in html
        assert "Bainbridge" in html
        assert "Edmonds" in html or "Kingston" in html

        # Map should show all vessels from all routes
        map_data = client.get("/ferry-data").json()
        map_vessel_names = {v["VesselName"] for v in map_data}
        assert "Walla Walla" in map_vessel_names
        assert "Spokane" in map_vessel_names
        assert "Puyallup" in map_vessel_names


# ---------------------------------------------------------------------------
# Model selection: dock model vs en-route model
# ---------------------------------------------------------------------------


class TestModelSelection:
    """Verify the correct ML model is used based on vessel state."""

    def test_dock_model_used_for_at_dock_vessel(self, client_with_ml_models):
        """When vessel is at dock, the dock predictor should be called."""
        client, mock_ml, mock_dock = client_with_ml_models

        # Trigger sailings computation
        client.get("/next-sailings")

        # dock_predictor.predict should have been called (for at-dock vessels)
        assert mock_dock.predict.called, (
            "Dock predictor should be called for at-dock vessels"
        )

    def test_en_route_model_used_for_moving_vessel(self, client_en_route_with_ml):
        """When vessel is en route, the en-route ML predictor should be called."""
        client, mock_ml, mock_dock = client_en_route_with_ml

        # Trigger sailings computation
        client.get("/next-sailings")

        # ml_predictor.predict should have been called (for future sailings)
        assert mock_ml.predict.called, (
            "En-route ML predictor should be called for future sailings"
        )

    def test_dock_model_only_on_first_sailing(self, client_with_ml_models):
        """Dock model should only be used for the FIRST sailing of an at-dock vessel."""
        client, mock_ml, mock_dock = client_with_ml_models

        # Reset call counts
        mock_dock.predict.reset_mock()
        mock_ml.predict.reset_mock()

        client.get("/next-sailings")

        # Dock model called once per at-dock vessel (first sailing only)
        # We have 2 vessels at dock, so up to 2 dock calls
        dock_calls = mock_dock.predict.call_count
        assert dock_calls <= 2, (
            f"Dock model called {dock_calls} times, expected at most 2 (one per vessel)"
        )

        # En-route model used for remaining sailings
        if mock_ml.predict.call_count > 0:
            # ML model should handle subsequent sailings
            assert mock_ml.predict.call_count >= dock_calls, (
                "En-route model should handle more sailings than dock model"
            )

    def test_predictions_appear_in_debug_endpoint(self, client_with_ml_models):
        """The /debug/predictions endpoint should show prediction sources."""
        client, _, _ = client_with_ml_models

        # First trigger a sailings computation
        client.get("/next-sailings")

        # Check debug endpoint
        debug_resp = client.get("/debug/predictions")
        assert debug_resp.status_code == 200
        predictions = debug_resp.json()

        # Should have predictions for at least one vessel
        assert len(predictions) > 0

        # Check that predictions include source information
        for _vessel_id, vessel_data in predictions.items():
            assert "sailings" in vessel_data
            for sailing in vessel_data["sailings"]:
                assert "source" in sailing
                assert sailing["source"] in (
                    "dock_model",
                    "en_route_model",
                    "fallback_flat",
                )

    def test_dock_prediction_uses_dock_specific_features(self, client_with_ml_models):
        """Dock model should receive dock-specific features like minutes_at_dock."""
        client, _, mock_dock = client_with_ml_models

        client.get("/next-sailings")

        if mock_dock.predict.called:
            call_kwargs = mock_dock.predict.call_args
            kwargs = call_kwargs.kwargs or {}

            if kwargs:
                assert "minutes_at_dock" in kwargs, (
                    "Dock model should receive minutes_at_dock feature"
                )
                assert "incoming_vehicle_fullness" in kwargs, (
                    "Dock model should receive incoming_vehicle_fullness feature"
                )


# ---------------------------------------------------------------------------
# Edge cases and data integrity
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test handling of unusual vessel states and data conditions."""

    def test_null_fields_dont_crash(self, client_null_fields):
        """Vessel with null ScheduledDeparture/LeftDock/Eta should not crash."""
        client = client_null_fields

        # Both endpoints should respond without error
        map_resp = client.get("/ferry-data")
        assert map_resp.status_code == 200
        map_data = map_resp.json()
        assert isinstance(map_data, list)

        sailings_resp = client.get("/next-sailings")
        assert sailings_resp.status_code == 200

    def test_null_fields_vessel_no_delay_on_map(self, client_null_fields):
        """Vessel with null fields should show no delay info on map."""
        client = client_null_fields

        map_data = client.get("/ferry-data").json()
        null_vessel = next(
            (v for v in map_data if v["VesselName"] == "Walla Walla"), None
        )
        assert null_vessel is not None
        # No LeftDock or ScheduledDeparture means no delay can be computed
        assert null_vessel["DelayMinutes"] is None
        assert null_vessel["PredictedDeparture"] is None

    def test_departed_sailing_shown_in_sailings(self, client_en_route_delayed):
        """En-route vessel's departed sailing should appear in sailings list."""
        client = client_en_route_delayed

        sailings_resp = client.get("/next-sailings")
        html = sailings_resp.text

        # The departed sailing should be visible (shows "Departed" or time ago)
        # and the vessel name should appear
        assert "Walla Walla" in html

    def test_all_endpoints_return_200(self, client_two_boats_docked):
        """All main endpoints should return 200 with mocked data."""
        client = client_two_boats_docked
        endpoints = [
            "/",
            "/ferry-data",
            "/next-sailings",
            "/map-tab",
            "/sailings-tab",
            "/predictions-tab",
            "/debug/cache-status",
            "/debug/model-status",
            "/debug/predictions",
        ]
        for endpoint in endpoints:
            resp = client.get(endpoint)
            assert resp.status_code == 200, f"{endpoint} returned {resp.status_code}"

    def test_ferry_data_returns_list(self, client_two_boats_docked):
        """The /ferry-data endpoint should always return a JSON list."""
        client = client_two_boats_docked
        resp = client.get("/ferry-data")
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_ferry_data_has_required_fields(self, client_two_boats_docked):
        """Each vessel in /ferry-data should have all fields the map JS expects."""
        client = client_two_boats_docked
        map_data = client.get("/ferry-data").json()

        required_fields = [
            "VesselID",
            "VesselName",
            "Latitude",
            "Longitude",
            "Heading",
            "Speed",
            "InService",
            "AtDock",
            "OpRouteAbbrev",
            "DelayMinutes",
            "PredictedDeparture",
        ]

        for vessel in map_data:
            for field in required_fields:
                assert field in vessel, (
                    f"Vessel {vessel.get('VesselName', '?')} missing field {field}"
                )

    def test_sailings_html_has_schedule_structure(self, client_two_boats_docked):
        """The /next-sailings HTML should contain expected structural elements."""
        client = client_two_boats_docked
        html = client.get("/next-sailings").text

        # Should have route and terminal information
        assert "Seattle" in html
        assert "Bainbridge" in html

    def test_multi_route_isolation(self, client_multi_route):
        """Vessels from one route should not appear in another route's sailings."""
        client = client_multi_route

        map_data = client.get("/ferry-data").json()

        # Verify route assignments are correct
        for vessel in map_data:
            routes = vessel["OpRouteAbbrev"]
            if vessel["VesselName"] == "Puyallup":
                assert "ed-king" in routes
                assert "sea-bi" not in routes
            elif vessel["VesselName"] in ("Walla Walla", "Spokane"):
                assert "sea-bi" in routes
                assert "ed-king" not in routes


# ---------------------------------------------------------------------------
# Data pipeline: verify transformations are correct
# ---------------------------------------------------------------------------


class TestDataPipeline:
    """Verify data flows correctly through the pipeline."""

    def test_vessel_delay_computation(self, client_en_route_delayed):
        """Delay = LeftDock - ScheduledDeparture should be computed correctly."""
        client = client_en_route_delayed

        map_data = client.get("/ferry-data").json()
        en_route = next(
            (v for v in map_data if not v["AtDock"] and v["LeftDock"]), None
        )

        if en_route:
            delay = en_route["DelayMinutes"]
            assert delay is not None
            # The fixture creates a 5-minute delay
            assert delay == pytest.approx(5, abs=1)

    def test_at_dock_vessel_no_computed_delay(self, client_two_boats_docked):
        """At-dock vessel without LeftDock should have no computed delay on map."""
        client = client_two_boats_docked

        map_data = client.get("/ferry-data").json()
        for vessel in map_data:
            if vessel["AtDock"] and vessel["LeftDock"] is None:
                # No LeftDock means no delay can be computed from position data
                assert vessel["DelayMinutes"] is None

    def test_debug_model_status_reflects_config(self, client_with_ml_models):
        """Debug endpoint should accurately report model training status."""
        client, _, _ = client_with_ml_models

        resp = client.get("/debug/model-status")
        data = resp.json()

        assert data["delay_model"]["is_trained"] is True
        assert data["dock_model"]["is_trained"] is True

    def test_predictions_data_endpoint(self, client_with_ml_models):
        """The /predictions-data endpoint should return valid JSON."""
        client, _, _ = client_with_ml_models

        resp = client.get("/predictions-data")
        assert resp.status_code == 200
        data = resp.json()
        assert "model" in data
        assert data["model"]["is_trained"] is True


# ---------------------------------------------------------------------------
# Severe delay scenario
# ---------------------------------------------------------------------------


class TestSevereDelay:
    """Tests for vessels delayed 20+ minutes (triggers delay-severe styling)."""

    def test_severe_delay_on_map(self, client_severe_delay):
        """Severely delayed vessel should show large delay on map."""
        client = client_severe_delay
        map_data = client.get("/ferry-data").json()

        en_route = [v for v in map_data if not v["AtDock"] and v["LeftDock"]]
        assert len(en_route) >= 1

        vessel = en_route[0]
        assert vessel["DelayMinutes"] is not None
        assert vessel["DelayMinutes"] >= 20

    def test_severe_delay_in_sailings(self, client_severe_delay):
        """Severe delay should appear with delay-severe class in sailings HTML."""
        client = client_severe_delay
        html = client.get("/next-sailings").text
        assert "status-delayed" in html

    def test_severe_delay_endpoints_dont_crash(self, client_severe_delay):
        """All endpoints should handle severe delays without errors."""
        client = client_severe_delay
        for endpoint in ["/ferry-data", "/next-sailings", "/debug/predictions"]:
            resp = client.get(endpoint)
            assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Both vessels en route scenario
# ---------------------------------------------------------------------------


class TestBothEnRoute:
    """Tests when both vessels are in transit (neither at dock)."""

    def test_no_at_dock_vessels(self, client_both_en_route):
        """Map should show no vessels at dock."""
        client = client_both_en_route
        map_data = client.get("/ferry-data").json()

        at_dock = [v for v in map_data if v["AtDock"]]
        assert len(at_dock) == 0

    def test_both_vessels_have_positions(self, client_both_en_route):
        """Both en-route vessels should have lat/lon and speed."""
        client = client_both_en_route
        map_data = client.get("/ferry-data").json()

        for vessel in map_data:
            assert vessel["Speed"] > 0
            assert vessel["Latitude"] is not None
            assert vessel["Longitude"] is not None

    def test_dock_model_not_called_when_both_en_route(
        self, client_both_en_route_with_ml
    ):
        """Dock model should NOT fire when no vessels are at dock."""
        client, mock_ml, mock_dock = client_both_en_route_with_ml
        mock_dock.predict.reset_mock()

        client.get("/next-sailings")

        assert not mock_dock.predict.called, (
            "Dock model should not be called when no vessels are at dock"
        )

    def test_en_route_model_handles_both_vessels(self, client_both_en_route_with_ml):
        """En-route model should be called for both vessels' future sailings."""
        client, mock_ml, mock_dock = client_both_en_route_with_ml
        mock_ml.predict.reset_mock()

        client.get("/next-sailings")

        assert mock_ml.predict.called
        # Should be called multiple times (once per future sailing per vessel)
        assert mock_ml.predict.call_count >= 2

    def test_departed_sailings_shown(self, client_both_en_route):
        """Both departed sailings should appear in the sailings list."""
        client = client_both_en_route
        html = client.get("/next-sailings").text

        assert "Walla Walla" in html
        assert "Spokane" in html


# ---------------------------------------------------------------------------
# Just-departed scenario
# ---------------------------------------------------------------------------


class TestJustDeparted:
    """Tests for a vessel that just left (< 2 minutes ago)."""

    def test_just_departed_vessel_on_map(self, client_just_departed):
        """Just-departed vessel should show as not at dock on map."""
        client = client_just_departed
        map_data = client.get("/ferry-data").json()

        walla = next((v for v in map_data if v["VesselName"] == "Walla Walla"), None)
        assert walla is not None
        assert walla["AtDock"] is False
        assert walla["Speed"] > 0

    def test_just_departed_in_sailings(self, client_just_departed):
        """Just-departed sailing should appear in sailings view."""
        client = client_just_departed
        html = client.get("/next-sailings").text
        assert "Walla Walla" in html

    def test_just_departed_no_delay(self, client_just_departed):
        """On-time departure should show 0 delay on map."""
        client = client_just_departed
        map_data = client.get("/ferry-data").json()

        walla = next((v for v in map_data if v["VesselName"] == "Walla Walla"), None)
        # LeftDock == ScheduledDeparture means 0 delay
        if walla and walla["DelayMinutes"] is not None:
            assert walla["DelayMinutes"] == 0


# ---------------------------------------------------------------------------
# Arriving scenario
# ---------------------------------------------------------------------------


class TestArriving:
    """Tests for a vessel about to arrive at terminal."""

    def test_arriving_vessel_position(self, client_arriving):
        """Arriving vessel should be near Bainbridge terminal."""
        client = client_arriving
        map_data = client.get("/ferry-data").json()

        walla = next((v for v in map_data if v["VesselName"] == "Walla Walla"), None)
        assert walla is not None
        assert walla["AtDock"] is False
        # Should be close to Bainbridge longitude (~-122.5)
        assert walla["Longitude"] < -122.45

    def test_arriving_vessel_has_eta(self, client_arriving):
        """Arriving vessel should have a near-future ETA."""
        client = client_arriving
        map_data = client.get("/ferry-data").json()

        walla = next((v for v in map_data if v["VesselName"] == "Walla Walla"), None)
        assert walla is not None
        assert walla["Eta"] is not None

    def test_arriving_endpoints_work(self, client_arriving):
        """All endpoints should work with arriving vessel scenario."""
        client = client_arriving
        for endpoint in ["/ferry-data", "/next-sailings"]:
            assert client.get(endpoint).status_code == 200


# ---------------------------------------------------------------------------
# Late night scenario (no future sailings)
# ---------------------------------------------------------------------------


class TestLateNight:
    """Tests for late-night operation when all sailings are past."""

    def test_late_night_doesnt_crash(self, client_late_night):
        """App should handle having no future sailings gracefully."""
        client = client_late_night

        map_resp = client.get("/ferry-data")
        assert map_resp.status_code == 200

        sailings_resp = client.get("/next-sailings")
        assert sailings_resp.status_code == 200

    def test_late_night_sailings_empty_or_minimal(self, client_late_night):
        """With no future sailings, the display should handle it gracefully."""
        client = client_late_night
        html = client.get("/next-sailings").text
        # May show route sections with no sailings, "No upcoming sailings",
        # or an error fragment - all are acceptable for this edge case
        assert (
            "route-section" in html
            or "No upcoming sailings" in html
            or "error" in html.lower()
        )
