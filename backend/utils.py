import re
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from .replay import now as _now


def parse_ms_date(value: str | None) -> datetime | None:
    if value is None:
        return None
    match = re.match(r"/Date\((\d+)([-+]\d{4})?\)/", value)
    if match:
        timestamp = int(match.group(1)) / 1000  # milliseconds to seconds
        # Convert from UTC to Pacific Time
        return datetime.fromtimestamp(timestamp, tz=UTC).astimezone(
            ZoneInfo("America/Los_Angeles")
        )
    return value


def string_format_time(dt: datetime):
    return dt.strftime("%-I:%M %p")


def format_time_until(
    scheduled_time: datetime, departed: bool = False
) -> tuple[str, str]:
    if not scheduled_time:
        return "N/A", "status-unknown"

    now = _now()

    # Make sure scheduled_time is timezone-aware
    if scheduled_time.tzinfo is None:
        scheduled_time = scheduled_time.replace(tzinfo=ZoneInfo("America/Los_Angeles"))

    time_diff = scheduled_time - now
    minutes_until = int(time_diff.total_seconds() / 60)

    if departed:
        minutes_ago = abs(minutes_until)
        if minutes_ago <= 1:
            return "Just left", "status-departed"
        else:
            return f"{minutes_ago}m ago", "status-departed"
    elif -5 <= minutes_until <= 2:
        return "Now", "status-departing"
    elif minutes_until > 2:
        if minutes_until < 60:
            return f"{minutes_until}m", "status-on-time"
        else:
            hours = minutes_until // 60
            mins = minutes_until % 60
            return f"{hours}h {mins}m", "status-on-time"
    else:
        return "Departed", "status-departed"


def format_delay_text(delay_minutes: int) -> tuple[str, str]:
    """Format delay text and return appropriate status class"""
    if delay_minutes is None or delay_minutes == 0:
        return "", "status-on-time"
    elif delay_minutes > 0:
        return f" (+{delay_minutes}m)", "status-delayed"
    else:
        return f" ({delay_minutes}m)", "status-early"


def datetime_to_minutes(dt: timedelta) -> int:
    # get the floor of the total minutes,
    return int(dt.total_seconds() // 60)


def format_confidence_text(lower_bound: int | None, upper_bound: int | None) -> str:
    """Format the confidence interval as display text, e.g. '(+1 to +5m)'."""
    if lower_bound is None or upper_bound is None:
        return ""
    if lower_bound == 0 and upper_bound == 0:
        return ""

    def fmt(val):
        return f"+{val}" if val >= 0 else str(val)

    return f"({fmt(lower_bound)} to {fmt(upper_bound)}m)"


def is_peak_hour(hour: int) -> bool:
    """Return True if the hour falls in commuter peak windows."""
    return (6 <= hour <= 9) or (15 <= hour <= 19)
