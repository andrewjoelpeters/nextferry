"""Canonical sailing ID: a stable identifier for a recurring schedule slot.

Format: {HHMM}-{departing_terminal_id}-{arriving_terminal_id}
Example: 1435-7-3 = the 2:35 PM sailing from Seattle (terminal 7) to Bainbridge (terminal 3).

The ID is date-agnostic — it identifies the schedule slot, not a specific instance.
A specific instance is (sailing_id, date).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SailingIdParts:
    """Parsed components of a canonical sailing ID."""

    time: str  # "HHMM"
    dep_terminal: int
    arr_terminal: int

    @property
    def hour(self) -> int:
        return int(self.time[:2])

    @property
    def minute(self) -> int:
        return int(self.time[2:])

    def __str__(self) -> str:
        return f"{self.time}-{self.dep_terminal}-{self.arr_terminal}"


def make_sailing_id(hhmm: str, dep_terminal_id: int, arr_terminal_id: int) -> str:
    """Construct a sailing ID from components.

    Args:
        hhmm: Zero-padded time string like "0635" or "1435".
        dep_terminal_id: Departing terminal ID.
        arr_terminal_id: Arriving terminal ID.
    """
    return f"{hhmm}-{dep_terminal_id}-{arr_terminal_id}"


def parse_sailing_id(sailing_id: str) -> SailingIdParts | None:
    """Parse a sailing ID string like '1435-7-3' into its components.

    Returns None if the string is not a valid sailing ID.
    """
    parts = sailing_id.split("-")
    if len(parts) != 3:
        return None
    try:
        return SailingIdParts(
            time=parts[0],
            dep_terminal=int(parts[1]),
            arr_terminal=int(parts[2]),
        )
    except ValueError:
        return None
