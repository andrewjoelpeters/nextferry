"""Lightweight user metrics tracking via FastAPI middleware."""

import hashlib
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from user_agents import parse as parse_ua

from .database import insert_page_view

logger = logging.getLogger(__name__)

# Paths to skip tracking (static assets, polling endpoints, debug)
_SKIP_PREFIXES = ("/static/", "/debug/", "/sw.js")
_SKIP_PATHS = {"/ferry-data", "/next-sailings", "/favicon.ico"}

# Secret salt for hashing IPs — falls back to a default for local dev
_HASH_SALT = os.getenv("METRICS_HASH_SALT", "nextferry-local-dev")


def _hash_visitor(ip: str, user_agent: str) -> str:
    """Create a privacy-friendly visitor fingerprint from IP + User-Agent."""
    raw = f"{_HASH_SALT}:{ip}:{user_agent}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _should_track(path: str) -> bool:
    """Return True if this request path should be tracked."""
    if path in _SKIP_PATHS:
        return False
    return all(not path.startswith(prefix) for prefix in _SKIP_PREFIXES)


def track_request(path: str, client_ip: str, user_agent_str: str, referrer: str | None):
    """Parse user-agent and record a page view."""
    if not _should_track(path):
        return

    try:
        ua = parse_ua(user_agent_str)

        if ua.is_bot:
            return

        if ua.is_mobile:
            device_type = "Mobile"
        elif ua.is_tablet:
            device_type = "Tablet"
        elif ua.is_pc:
            device_type = "Desktop"
        else:
            device_type = "Other"

        browser = ua.browser.family if ua.browser.family else None
        os_name = ua.os.family if ua.os.family else None
        visitor_hash = _hash_visitor(client_ip, user_agent_str)

        now = datetime.now(tz=ZoneInfo("America/Los_Angeles")).isoformat()

        insert_page_view(
            timestamp=now,
            path=path,
            visitor_hash=visitor_hash,
            device_type=device_type,
            browser=browser,
            os=os_name,
            referrer=referrer,
        )
    except Exception as e:
        logger.warning(f"Failed to track page view: {e}")
