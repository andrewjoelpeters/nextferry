"""Fetch live sailing space data and build a lookup for display."""

import logging

from .serializers import TerminalSpace
from .wsdot_client import get_sailing_space

logger = logging.getLogger(__name__)


# Key: (departing_terminal_id, departure_time_iso) -> {drive_up_space_count, max_space_count}
SpaceLookup = dict[tuple[int, str], dict]


def build_sailing_space_lookup(terminals: list[TerminalSpace]) -> SpaceLookup:
    """Build a lookup dict from sailing space data.

    Keys are (departing_terminal_id, departure_time_iso_minute) so we can
    match capacity to scheduled sailings by terminal and time.
    """
    lookup: SpaceLookup = {}
    for terminal in terminals:
        for sailing in terminal.departing_spaces:
            if not sailing.departure:
                continue
            # Use minute-level key for matching (ignore seconds)
            time_key = sailing.departure.strftime("%Y-%m-%d %H:%M")
            for arrival in sailing.space_for_arrival_terminals:
                lookup[(terminal.terminal_id, time_key)] = {
                    "drive_up_space_count": arrival.drive_up_space_count,
                    "max_space_count": arrival.max_space_count,
                }
    return lookup


def get_sailing_space_lookup() -> SpaceLookup:
    """Fetch current sailing space from WSDOT and return a lookup dict."""
    try:
        return build_sailing_space_lookup(get_sailing_space())
    except Exception as e:
        logger.warning(f"Failed to fetch sailing space: {e}")
        return {}
