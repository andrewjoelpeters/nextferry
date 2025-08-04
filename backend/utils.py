from typing import Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import re


def parse_ms_date(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    match = re.match(r"/Date\((\d+)([-+]\d{4})?\)/", value)
    if match:
        timestamp = int(match.group(1)) / 1000  # milliseconds to seconds
        # Convert from UTC to Pacific Time
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone(ZoneInfo("America/Los_Angeles"))
    return value


def string_format_time(dt: datetime):
    return dt.strftime('%-I:%M %p')


def format_time_until(scheduled_time: datetime) -> tuple[str, str]:
    if not scheduled_time:
        return "N/A", "status-unknown"

    now = datetime.now(ZoneInfo("America/Los_Angeles"))

    # Make sure scheduled_time is timezone-aware
    if scheduled_time.tzinfo is None:
        scheduled_time = scheduled_time.replace(tzinfo=ZoneInfo("America/Los_Angeles"))

    time_diff = scheduled_time - now
    minutes_until = int(time_diff.total_seconds() / 60)

    if -5 <= minutes_until <= 2:
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
