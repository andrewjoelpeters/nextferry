"""E2E tests for cross-tab data consistency.

Verifies that the same vessel data appears consistently across
the map view and the sailings list when viewed in a real browser.

Run with: uv run pytest tests/e2e/ -v
"""

import pytest

pytestmark = pytest.mark.e2e


class TestCrossTabConsistency:
    """Verify data consistency between map and sailings tabs."""

    def test_map_vessel_appears_in_sailings(self, page, live_server):
        """Vessels shown on the map should also appear in the sailings tab."""
        # First, get the raw ferry data from the API
        ferry_data = page.evaluate(
            """async (url) => {
                const resp = await fetch(url + '/ferry-data');
                return resp.json();
            }""",
            live_server,
        )

        vessel_names = {v["VesselName"] for v in ferry_data}

        # Now check the sailings tab
        page.wait_for_selector(".sailing-item", timeout=10000)
        html = page.content()

        for name in vessel_names:
            assert name in html, (
                f"Vessel '{name}' found in /ferry-data but not in sailings view"
            )

    def test_at_dock_vessel_status_matches(self, page, live_server):
        """At-dock status on map should match 'At Dock' in sailings tab."""
        # Get ferry data
        ferry_data = page.evaluate(
            """async (url) => {
                const resp = await fetch(url + '/ferry-data');
                return resp.json();
            }""",
            live_server,
        )

        at_dock_vessels = [v for v in ferry_data if v["AtDock"]]
        assert len(at_dock_vessels) >= 1

        # Check sailings tab shows "At Dock" status
        page.wait_for_selector(".sailing-item", timeout=10000)
        statuses = page.query_selector_all(".vessel-at_dock")
        at_dock_count = len(statuses)

        # Should have at least one "At Dock" vessel status in the sailings view
        assert at_dock_count >= 1, (
            f"Expected at least 1 'At Dock' status in sailings, found {at_dock_count}"
        )

    def test_ferry_data_api_matches_map_markers(self, page, live_server):
        """Number of markers on map should match vessels from /ferry-data."""
        # Get vessel count from API
        ferry_data = page.evaluate(
            """async (url) => {
                const resp = await fetch(url + '/ferry-data');
                return resp.json();
            }""",
            live_server,
        )
        # Only vessels with lat/lon get markers
        expected_markers = sum(
            1 for v in ferry_data if v["Latitude"] and v["Longitude"]
        )

        # Switch to map and count markers
        page.click('button:has-text("Map")')
        page.wait_for_selector(".ferry-marker", timeout=10000)
        markers = page.query_selector_all(".ferry-marker")

        assert len(markers) == expected_markers, (
            f"API has {expected_markers} vessels with positions, "
            f"but map shows {len(markers)} markers"
        )

    def test_map_marker_data_matches_info_panel(self, page, live_server):
        """Clicking a marker should show info matching the API data."""
        # Get vessel data
        ferry_data = page.evaluate(
            """async (url) => {
                const resp = await fetch(url + '/ferry-data');
                return resp.json();
            }""",
            live_server,
        )

        page.click('button:has-text("Map")')
        page.wait_for_selector(".ferry-marker", timeout=10000)

        # Click the first marker
        page.click(".ferry-marker")
        page.wait_for_selector("#ferry-info-panel:not(.hidden)", timeout=5000)

        # Get the displayed name
        displayed_name = page.text_content("#ferry-name")

        # Find matching vessel in API data
        matching = [v for v in ferry_data if v["VesselName"] == displayed_name]
        assert len(matching) == 1, f"Vessel '{displayed_name}' not found in API data"

        vessel = matching[0]
        details = page.text_content("#ferry-details")

        # Verify terminals match
        if vessel["DepartingTerminalName"]:
            assert vessel["DepartingTerminalName"] in details
        if vessel["ArrivingTerminalName"]:
            assert vessel["ArrivingTerminalName"] in details
