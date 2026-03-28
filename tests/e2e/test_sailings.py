"""E2E tests for the sailings view.

Verifies that the sailings tab loads, shows correct schedule data,
direction toggles work, and vessel details are expandable.

Run with: uv run pytest tests/e2e/ -v
"""

import pytest

pytestmark = pytest.mark.e2e


class TestSailingsView:
    """Verify the sailings tab loads and displays data correctly."""

    def test_sailings_tab_loads_by_default(self, page):
        """The sailings tab should be the default view on page load."""
        # Wait for sailings content to load via HTMX
        page.wait_for_selector(".route-section", timeout=10000)

    def test_route_sections_present(self, page):
        """Route sections should appear for configured routes."""
        page.wait_for_selector(".route-section", timeout=10000)

        route_sections = page.query_selector_all(".route-section")
        assert len(route_sections) >= 1

        # Seattle - Bainbridge route should be present
        sea_bi = page.query_selector(
            '.route-section[data-route="Seattle - Bainbridge"]'
        )
        assert sea_bi is not None

    def test_direction_toggle_buttons(self, page):
        """Each route should have direction toggle buttons."""
        page.wait_for_selector(".route-section", timeout=10000)

        buttons = page.query_selector_all(".direction-btn")
        assert len(buttons) >= 2, "Should have at least 2 direction buttons"

        # One should say "From Seattle", another "From Bainbridge Island"
        button_texts = [btn.text_content() for btn in buttons]
        assert any("Seattle" in t for t in button_texts)
        assert any("Bainbridge" in t for t in button_texts)

    def test_direction_toggle_switches_content(self, page):
        """Clicking a direction toggle should show that direction's sailings."""
        page.wait_for_selector(".route-section", timeout=10000)

        # Click "From Seattle" button
        page.click('.direction-btn:has-text("From Seattle")')

        # The Seattle terminal card should be visible
        seattle_card = page.query_selector('.terminal-card[data-departing="Seattle"]')
        assert seattle_card is not None
        assert not seattle_card.evaluate(
            "el => el.classList.contains('direction-hidden')"
        )

        # The Bainbridge card should be hidden
        bi_card = page.query_selector(
            '.terminal-card[data-departing="Bainbridge Island"]'
        )
        if bi_card:
            assert bi_card.evaluate("el => el.classList.contains('direction-hidden')")

    def test_sailing_items_present(self, page):
        """There should be sailing items showing upcoming departures."""
        page.wait_for_selector(".sailing-item", timeout=10000)

        items = page.query_selector_all(".sailing-item")
        assert len(items) >= 1, "Should show at least one sailing"

    def test_sailing_shows_vessel_name(self, page):
        """Sailing items should have vessel name data attribute."""
        page.wait_for_selector(".sailing-item", timeout=10000)

        item = page.query_selector(".sailing-item")
        vessel = item.get_attribute("data-vessel")
        assert vessel in ("Walla Walla", "Spokane"), f"Unexpected vessel: {vessel}"

    def test_sailing_details_expandable(self, page):
        """Clicking a sailing item should expand its details."""
        page.wait_for_selector(".sailing-item.has-details", timeout=10000)

        # Click the first expandable sailing
        item = page.query_selector(".sailing-item.has-details")
        item.click()

        # The details section should now be visible
        details = item.query_selector(".vessel-live-info")
        if details:
            assert details.is_visible()

    def test_time_until_displayed(self, page):
        """Each sailing should show a time-until indicator."""
        page.wait_for_selector(".sailing-item", timeout=10000)

        time_until = page.query_selector(".time-until-prominent")
        assert time_until is not None
        text = time_until.text_content()
        # Should be something like "25m", "1h 15m", "Departed", etc.
        assert len(text) > 0

    def test_vessel_status_shown_for_first_sailing(self, page):
        """The first sailing should show vessel status (At Dock / En route)."""
        page.wait_for_selector(".sailing-item", timeout=10000)

        # Look for vessel status badge
        status = page.query_selector(".vessel-status")
        if status:
            text = status.text_content()
            assert text in ("At Dock", "En route")


class TestSailingsAutoRefresh:
    """Verify HTMX auto-refresh behavior."""

    def test_last_updated_timestamp_shown(self, page):
        """The last-updated timestamp should appear after data loads."""
        page.wait_for_selector(".last-updated", timeout=10000)

        updated = page.text_content(".last-updated")
        assert "Last updated" in updated
