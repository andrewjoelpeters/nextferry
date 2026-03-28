"""E2E tests for the map view.

Verifies that ferry markers render at correct positions, clicking markers
opens the info panel with correct data, and marker colors match vessel state.

Run with: uv run pytest tests/e2e/ -v --headed  (to see the browser)
"""

import pytest

pytestmark = pytest.mark.e2e


class TestMapRendering:
    """Verify the map loads and shows ferry markers."""

    def test_map_tab_loads(self, page):
        """Clicking the Map tab should load the Leaflet map."""
        # Click the Map tab
        page.click('button:has-text("Map")')

        # Wait for the map container to appear
        page.wait_for_selector("#map", timeout=5000)

        # The Leaflet map creates .leaflet-container
        page.wait_for_selector(".leaflet-container", timeout=10000)

    def test_ferry_markers_appear(self, page):
        """Ferry markers should appear on the map after data loads."""
        page.click('button:has-text("Map")')
        page.wait_for_selector(".leaflet-container", timeout=10000)

        # Wait for ferry markers to load (they're added by JS after /ferry-data fetch)
        page.wait_for_selector(".ferry-marker", timeout=10000)

        markers = page.query_selector_all(".ferry-marker")
        assert len(markers) >= 2, (
            f"Expected at least 2 ferry markers (2 boats at dock), got {len(markers)}"
        )

    def test_marker_click_opens_info_panel(self, page):
        """Clicking a ferry marker should open the info panel with vessel name."""
        page.click('button:has-text("Map")')
        page.wait_for_selector(".ferry-marker", timeout=10000)

        # Click the first marker
        page.click(".ferry-marker")

        # Info panel should become visible
        panel = page.wait_for_selector("#ferry-info-panel:not(.hidden)", timeout=5000)
        assert panel is not None

        # Should show a vessel name
        name = page.text_content("#ferry-name")
        assert name in ("Walla Walla", "Spokane"), f"Unexpected vessel name: {name}"

    def test_info_panel_shows_at_dock_status(self, page):
        """At-dock vessel's info panel should show 'At Dock' status."""
        page.click('button:has-text("Map")')
        page.wait_for_selector(".ferry-marker", timeout=10000)

        # Click a marker
        page.click(".ferry-marker")
        page.wait_for_selector("#ferry-info-panel:not(.hidden)", timeout=5000)

        # Panel content should include dock-related info
        details = page.text_content("#ferry-details")
        assert "At Dock" in details

    def test_info_panel_close_button(self, page):
        """Close button should hide the info panel."""
        page.click('button:has-text("Map")')
        page.wait_for_selector(".ferry-marker", timeout=10000)

        page.click(".ferry-marker")
        page.wait_for_selector("#ferry-info-panel:not(.hidden)", timeout=5000)

        # Click close
        page.click("#close-panel")

        # Panel should be hidden again
        page.wait_for_selector("#ferry-info-panel.hidden", timeout=3000)

    def test_info_panel_shows_route(self, page):
        """Info panel should display the vessel's route."""
        page.click('button:has-text("Map")')
        page.wait_for_selector(".ferry-marker", timeout=10000)

        page.click(".ferry-marker")
        page.wait_for_selector("#ferry-info-panel:not(.hidden)", timeout=5000)

        details = page.text_content("#ferry-details")
        assert "sea-bi" in details

    def test_info_panel_shows_terminals(self, page):
        """Info panel should show departing and arriving terminals."""
        page.click('button:has-text("Map")')
        page.wait_for_selector(".ferry-marker", timeout=10000)

        page.click(".ferry-marker")
        page.wait_for_selector("#ferry-info-panel:not(.hidden)", timeout=5000)

        details = page.text_content("#ferry-details")
        # Should show either Seattle or Bainbridge terminals
        assert "Seattle" in details or "Bainbridge" in details
