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
