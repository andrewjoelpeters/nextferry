"""Fetch live sailing space data and build a lookup for display."""

import logging
from typing import Dict, Optional, Tuple

from .wsdot_client import get_sailing_space

logger = logging.getLogger(__name__)


# Key: (departing_terminal_id, departure_time_iso) -> {drive_up_space_count, max_space_count}
SpaceLookup = Dict[Tuple[int, str], dict]


def get_sailing_space_lookup() -> SpaceLookup:
    """Fetch current sailing space from WSDOT and return a lookup dict.

    Keys are (departing_terminal_id, departure_time_iso_minute) so we can
    match capacity to scheduled sailings by terminal and time.
    """
    lookup: SpaceLookup = {}
    try:
        terminals = get_sailing_space()
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
    except Exception as e:
        logger.warning(f"Failed to fetch sailing space: {e}")

    return lookup
