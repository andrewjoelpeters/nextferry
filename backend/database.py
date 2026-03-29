"""SQLite database for accumulating historical ferry data."""

import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_db_path: Path | None = None


def get_db_path() -> Path:
    global _db_path
    if _db_path is None:
        volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
        data_dir = Path(volume_path) if volume_path else Path("./data")
        data_dir.mkdir(exist_ok=True)
        _db_path = data_dir / "ferry.db"
    return _db_path


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and enable WAL mode."""
    conn = get_connection()
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS vessel_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collected_at TEXT NOT NULL,
                vessel_id INTEGER NOT NULL,
                vessel_name TEXT NOT NULL,
                route_abbrev TEXT,
                departing_terminal_id INTEGER,
                departing_terminal_name TEXT,
                arriving_terminal_id INTEGER,
                arriving_terminal_name TEXT,
                latitude REAL,
                longitude REAL,
                speed REAL,
                heading INTEGER,
                in_service INTEGER NOT NULL,
                at_dock INTEGER NOT NULL,
                left_dock TEXT,
                eta TEXT,
                scheduled_departure TEXT,
                vessel_position_num INTEGER,
                UNIQUE(collected_at, vessel_id)
            );

            CREATE TABLE IF NOT EXISTS sailing_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vessel_id INTEGER NOT NULL,
                vessel_name TEXT NOT NULL,
                route_abbrev TEXT,
                departing_terminal_id INTEGER,
                arriving_terminal_id INTEGER,
                scheduled_departure TEXT NOT NULL,
                actual_departure TEXT NOT NULL,
                delay_minutes REAL NOT NULL,
                day_of_week INTEGER NOT NULL,
                hour_of_day INTEGER NOT NULL,
                UNIQUE(vessel_id, scheduled_departure)
            );

            CREATE TABLE IF NOT EXISTS sailing_space_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collected_at TEXT NOT NULL,
                departing_terminal_id INTEGER NOT NULL,
                departing_terminal_name TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                vessel_name TEXT NOT NULL,
                vessel_id INTEGER NOT NULL,
                arriving_terminal_id INTEGER NOT NULL,
                arriving_terminal_name TEXT NOT NULL,
                max_space_count INTEGER NOT NULL,
                drive_up_space_count INTEGER NOT NULL,
                reservable_space_count INTEGER,
                UNIQUE(collected_at, departing_terminal_id, arriving_terminal_id, departure_time)
            );

            CREATE INDEX IF NOT EXISTS idx_snapshots_vessel_time
                ON vessel_snapshots(vessel_id, collected_at);
            CREATE INDEX IF NOT EXISTS idx_sailing_events_scheduled
                ON sailing_events(scheduled_departure);
            CREATE INDEX IF NOT EXISTS idx_sailing_events_route
                ON sailing_events(route_abbrev);
            CREATE INDEX IF NOT EXISTS idx_sailing_space_time
                ON sailing_space_snapshots(collected_at);
            CREATE INDEX IF NOT EXISTS idx_sailing_space_arriving_departure
                ON sailing_space_snapshots(arriving_terminal_id, departure_time);
            CREATE INDEX IF NOT EXISTS idx_sailing_space_departing_departure
                ON sailing_space_snapshots(departing_terminal_id, departure_time, collected_at);

            CREATE TABLE IF NOT EXISTS page_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                path TEXT NOT NULL,
                visitor_hash TEXT NOT NULL,
                device_type TEXT,
                browser TEXT,
                os TEXT,
                referrer TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_page_views_timestamp
                ON page_views(timestamp);
            CREATE INDEX IF NOT EXISTS idx_page_views_visitor
                ON page_views(visitor_hash, timestamp);
            """
        )
        conn.commit()
        logger.info(f"Database initialized at {get_db_path()}")
    finally:
        conn.close()


def insert_vessel_snapshot(
    collected_at: str,
    vessel_id: int,
    vessel_name: str,
    route_abbrev: str | None,
    departing_terminal_id: int | None,
    departing_terminal_name: str | None,
    arriving_terminal_id: int | None,
    arriving_terminal_name: str | None,
    latitude: float | None,
    longitude: float | None,
    speed: float | None,
    heading: int | None,
    in_service: bool,
    at_dock: bool,
    left_dock: str | None,
    eta: str | None,
    scheduled_departure: str | None,
    vessel_position_num: int | None,
):
    """Insert a vessel snapshot, ignoring duplicates."""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO vessel_snapshots (
                collected_at, vessel_id, vessel_name, route_abbrev,
                departing_terminal_id, departing_terminal_name,
                arriving_terminal_id, arriving_terminal_name,
                latitude, longitude, speed, heading,
                in_service, at_dock, left_dock, eta,
                scheduled_departure, vessel_position_num
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                collected_at,
                vessel_id,
                vessel_name,
                route_abbrev,
                departing_terminal_id,
                departing_terminal_name,
                arriving_terminal_id,
                arriving_terminal_name,
                latitude,
                longitude,
                speed,
                heading,
                int(in_service),
                int(at_dock),
                left_dock,
                eta,
                scheduled_departure,
                vessel_position_num,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def insert_vessel_snapshots_batch(snapshots: list):
    """Insert multiple vessel snapshots in one transaction."""
    conn = get_connection()
    try:
        conn.executemany(
            """
            INSERT OR IGNORE INTO vessel_snapshots (
                collected_at, vessel_id, vessel_name, route_abbrev,
                departing_terminal_id, departing_terminal_name,
                arriving_terminal_id, arriving_terminal_name,
                latitude, longitude, speed, heading,
                in_service, at_dock, left_dock, eta,
                scheduled_departure, vessel_position_num
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            snapshots,
        )
        conn.commit()
        logger.info(f"Inserted {conn.total_changes} vessel snapshots")
    finally:
        conn.close()


def insert_sailing_space_batch(rows: list):
    """Insert multiple sailing space snapshots in one transaction."""
    conn = get_connection()
    try:
        conn.executemany(
            """
            INSERT OR IGNORE INTO sailing_space_snapshots (
                collected_at, departing_terminal_id, departing_terminal_name,
                departure_time, vessel_name, vessel_id,
                arriving_terminal_id, arriving_terminal_name,
                max_space_count, drive_up_space_count, reservable_space_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        logger.info(f"Inserted {conn.total_changes} sailing space snapshots")
    finally:
        conn.close()


def extract_sailing_events():
    """Extract sailing events from vessel snapshots where left_dock is set.

    For each distinct (vessel_id, scheduled_departure) where left_dock is known,
    compute the delay and insert into sailing_events.
    """
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO sailing_events (
                vessel_id, vessel_name, route_abbrev,
                departing_terminal_id, arriving_terminal_id,
                scheduled_departure, actual_departure, delay_minutes,
                day_of_week, hour_of_day
            )
            SELECT
                vessel_id,
                vessel_name,
                route_abbrev,
                departing_terminal_id,
                arriving_terminal_id,
                scheduled_departure,
                left_dock AS actual_departure,
                (julianday(left_dock) - julianday(scheduled_departure)) * 24 * 60 AS delay_minutes,
                CAST(strftime('%w', scheduled_departure) AS INTEGER) AS day_of_week,
                CAST(strftime('%H', scheduled_departure) AS INTEGER) AS hour_of_day
            FROM vessel_snapshots
            WHERE left_dock IS NOT NULL
              AND scheduled_departure IS NOT NULL
              AND left_dock != ''
              AND scheduled_departure != ''
            GROUP BY vessel_id, scheduled_departure
            HAVING MAX(collected_at)
            """
        )
        inserted = conn.total_changes
        conn.commit()
        if inserted > 0:
            logger.info(f"Extracted {inserted} new sailing events")
    finally:
        conn.close()


def get_training_data() -> list[dict]:
    """Return all sailing events as dicts for ML training."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT
                id, vessel_id, vessel_name, route_abbrev,
                departing_terminal_id, arriving_terminal_id,
                scheduled_departure, actual_departure, delay_minutes,
                day_of_week, hour_of_day
            FROM sailing_events
            ORDER BY scheduled_departure
            """
        )
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_vessel_delay_at_time(
    vessel_id: int, query_time: str, scheduled_departure: str
) -> float | None:
    """Get the most recent observed delay for a vessel at a given time.

    Looks at the vessel's most recent snapshot before query_time where
    left_dock and scheduled_departure are set (i.e., it has departed
    on a *previous* sailing).
    """
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT
                (julianday(left_dock) - julianday(scheduled_departure)) * 24 * 60 AS delay_minutes
            FROM vessel_snapshots
            WHERE vessel_id = ?
              AND collected_at <= ?
              AND left_dock IS NOT NULL
              AND scheduled_departure IS NOT NULL
              AND left_dock != ''
              AND scheduled_departure != ''
              AND scheduled_departure != ?
            ORDER BY collected_at DESC
            LIMIT 1
            """,
            (vessel_id, query_time, scheduled_departure),
        ).fetchone()
        return row["delay_minutes"] if row else None
    finally:
        conn.close()


def get_previous_sailing_fullness(
    departing_terminal_id: int, scheduled_departure: str
) -> float | None:
    """Get the fullness (0.0-1.0) of the inbound sailing that brought the boat to this terminal.

    Looks at the most recent sailing_space_snapshot for a departure FROM the
    arriving terminal TO the departing terminal (i.e. the reverse direction)
    that occurred before this sailing's scheduled departure. Fullness is
    calculated as 1 - (drive_up_space_count / max_space_count).
    """
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT
                max_space_count,
                drive_up_space_count
            FROM sailing_space_snapshots
            WHERE arriving_terminal_id = ?
              AND departure_time <= ?
              AND max_space_count > 0
            ORDER BY departure_time DESC
            LIMIT 1
            """,
            (departing_terminal_id, scheduled_departure),
        ).fetchone()
        if row and row["max_space_count"] > 0:
            return 1.0 - (row["drive_up_space_count"] / row["max_space_count"])
        return None
    finally:
        conn.close()


def get_turnaround_minutes(vessel_id: int, scheduled_departure: str) -> float | None:
    """Get how many minutes before scheduled departure the vessel docked.

    Finds the earliest snapshot where the vessel is at_dock=1 at the departing
    terminal for this sailing, after its previous departure. Returns the
    difference between scheduled_departure and when the vessel first appeared
    at dock.
    """
    conn = get_connection()
    try:
        # Find when the vessel first appeared at dock before this scheduled departure
        # by looking for the most recent transition to at_dock after the previous sailing
        row = conn.execute(
            """
            SELECT
                MIN(collected_at) as docked_at
            FROM vessel_snapshots
            WHERE vessel_id = ?
              AND at_dock = 1
              AND scheduled_departure = ?
              AND collected_at <= ?
            """,
            (vessel_id, scheduled_departure, scheduled_departure),
        ).fetchone()
        if row and row["docked_at"]:
            docked_dt = datetime.fromisoformat(row["docked_at"])
            sched_dt = datetime.fromisoformat(scheduled_departure)
            # Strip tzinfo to avoid mixing naive/aware datetimes
            docked_dt = docked_dt.replace(tzinfo=None)
            sched_dt = sched_dt.replace(tzinfo=None)
            diff = (sched_dt - docked_dt).total_seconds() / 60
            return max(0, diff)
        return None
    finally:
        conn.close()


def get_docked_since(vessel_id: int, scheduled_departure: str) -> datetime | None:
    """Get when the vessel first appeared at dock for this sailing.

    Returns the earliest collected_at timestamp where at_dock=1 for this
    vessel and scheduled_departure, or None if no snapshots exist or DB
    is unavailable.
    """
    try:
        conn = get_connection()
    except Exception:
        return None
    try:
        row = conn.execute(
            """
            SELECT MIN(collected_at) as docked_at
            FROM vessel_snapshots
            WHERE vessel_id = ?
              AND at_dock = 1
              AND scheduled_departure = ?
            """,
            (vessel_id, scheduled_departure),
        ).fetchone()
        if row and row["docked_at"]:
            return datetime.fromisoformat(row["docked_at"])
        return None
    except sqlite3.OperationalError:
        return None
    finally:
        conn.close()


def get_departed_sailing_space(
    departing_terminal_id: int, departure_time: str
) -> dict | None:
    """Get the last known space snapshot for a departed sailing.

    Returns the most recent snapshot before the sailing departed,
    giving us the actual car count on board.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT
                max_space_count,
                drive_up_space_count
            FROM sailing_space_snapshots
            WHERE departing_terminal_id = ?
              AND departure_time = ?
              AND collected_at <= ?
              AND max_space_count > 0
            ORDER BY collected_at DESC
            LIMIT 1
            """,
            (departing_terminal_id, departure_time, departure_time),
        ).fetchone()
        if row:
            return {
                "max_space_count": row["max_space_count"],
                "drive_up_space_count": row["drive_up_space_count"],
            }
        return None
    finally:
        conn.close()


def get_sailing_event_count() -> int:
    """Return the total number of sailing events."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) as cnt FROM sailing_events").fetchone()
        return row["cnt"]
    finally:
        conn.close()


def get_snapshot_count() -> int:
    """Return the total number of vessel snapshots."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) as cnt FROM vessel_snapshots").fetchone()
        return row["cnt"]
    finally:
        conn.close()


def get_dashboard_data() -> dict:
    """Return aggregated data for the predictions dashboard."""
    conn = get_connection()
    try:
        # Delay stats by route
        delays_by_route = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    route_abbrev,
                    COUNT(*) as count,
                    ROUND(AVG(delay_minutes), 2) as avg_delay,
                    ROUND(MIN(delay_minutes), 2) as min_delay,
                    ROUND(MAX(delay_minutes), 2) as max_delay,
                    ROUND(AVG(CASE WHEN delay_minutes > 0 THEN delay_minutes END), 2) as avg_late_delay,
                    ROUND(SUM(CASE WHEN delay_minutes <= 0 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as on_time_pct
                FROM sailing_events
                GROUP BY route_abbrev
                ORDER BY route_abbrev
                """
            ).fetchall()
        ]

        # Delay stats by day of week
        delays_by_dow = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    day_of_week,
                    COUNT(*) as count,
                    ROUND(AVG(delay_minutes), 2) as avg_delay,
                    ROUND(AVG(CASE WHEN delay_minutes > 0 THEN delay_minutes END), 2) as avg_late_delay,
                    ROUND(SUM(CASE WHEN delay_minutes <= 0 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as on_time_pct
                FROM sailing_events
                GROUP BY day_of_week
                ORDER BY day_of_week
                """
            ).fetchall()
        ]

        # Delay stats by hour of day
        delays_by_hour = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    hour_of_day,
                    COUNT(*) as count,
                    ROUND(AVG(delay_minutes), 2) as avg_delay,
                    ROUND(AVG(CASE WHEN delay_minutes > 0 THEN delay_minutes END), 2) as avg_late_delay,
                    ROUND(SUM(CASE WHEN delay_minutes <= 0 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as on_time_pct
                FROM sailing_events
                GROUP BY hour_of_day
                ORDER BY hour_of_day
                """
            ).fetchall()
        ]

        # Delay distribution histogram (1-min bins from -5 to 20)
        delay_distribution = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    CAST(ROUND(delay_minutes) AS INTEGER) as delay_bin,
                    COUNT(*) as count
                FROM sailing_events
                WHERE delay_minutes BETWEEN -5 AND 20
                GROUP BY delay_bin
                ORDER BY delay_bin
                """
            ).fetchall()
        ]

        # Recent trend: daily average delay over time
        daily_trend = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    DATE(scheduled_departure) as date,
                    COUNT(*) as count,
                    ROUND(AVG(delay_minutes), 2) as avg_delay,
                    ROUND(SUM(CASE WHEN delay_minutes <= 0 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as on_time_pct
                FROM sailing_events
                GROUP BY DATE(scheduled_departure)
                ORDER BY date
                """
            ).fetchall()
        ]

        event_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM sailing_events"
        ).fetchone()["cnt"]

        return {
            "delays_by_route": delays_by_route,
            "delays_by_dow": delays_by_dow,
            "delays_by_hour": delays_by_hour,
            "delay_distribution": delay_distribution,
            "daily_trend": daily_trend,
            "event_count": event_count,
        }
    finally:
        conn.close()


def insert_page_view(
    timestamp: str,
    path: str,
    visitor_hash: str,
    device_type: str | None,
    browser: str | None,
    os: str | None,
    referrer: str | None,
):
    """Insert a page view record."""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO page_views (
                timestamp, path, visitor_hash, device_type, browser, os, referrer
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (timestamp, path, visitor_hash, device_type, browser, os, referrer),
        )
        conn.commit()
    finally:
        conn.close()


def get_metrics_data(days: int = 30) -> dict:
    """Return aggregated user metrics for the last N days."""
    conn = get_connection()
    try:
        cutoff = f"DATE('now', '-{days} days')"

        # Total page views and unique visitors
        totals = conn.execute(
            f"""
            SELECT
                COUNT(*) as total_views,
                COUNT(DISTINCT visitor_hash) as unique_visitors
            FROM page_views
            WHERE timestamp >= {cutoff}
            """
        ).fetchone()

        # Views by path
        views_by_path = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT path, COUNT(*) as views, COUNT(DISTINCT visitor_hash) as visitors
                FROM page_views
                WHERE timestamp >= {cutoff}
                GROUP BY path
                ORDER BY views DESC
                """
            ).fetchall()
        ]

        # Device breakdown
        device_breakdown = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    COALESCE(device_type, 'Unknown') as device_type,
                    COUNT(*) as views,
                    COUNT(DISTINCT visitor_hash) as visitors
                FROM page_views
                WHERE timestamp >= {cutoff}
                GROUP BY device_type
                ORDER BY views DESC
                """
            ).fetchall()
        ]

        # Browser breakdown
        browser_breakdown = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    COALESCE(browser, 'Unknown') as browser,
                    COUNT(*) as views,
                    COUNT(DISTINCT visitor_hash) as visitors
                FROM page_views
                WHERE timestamp >= {cutoff}
                GROUP BY browser
                ORDER BY views DESC
                """
            ).fetchall()
        ]

        # OS breakdown
        os_breakdown = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    COALESCE(os, 'Unknown') as os,
                    COUNT(*) as views,
                    COUNT(DISTINCT visitor_hash) as visitors
                FROM page_views
                WHERE timestamp >= {cutoff}
                GROUP BY os
                ORDER BY views DESC
                """
            ).fetchall()
        ]

        # Daily traffic
        daily_traffic = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    DATE(timestamp) as date,
                    COUNT(*) as views,
                    COUNT(DISTINCT visitor_hash) as visitors
                FROM page_views
                WHERE timestamp >= {cutoff}
                GROUP BY DATE(timestamp)
                ORDER BY date
                """
            ).fetchall()
        ]

        # Hourly traffic pattern
        hourly_traffic = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                    COUNT(*) as views,
                    COUNT(DISTINCT visitor_hash) as visitors
                FROM page_views
                WHERE timestamp >= {cutoff}
                GROUP BY hour
                ORDER BY hour
                """
            ).fetchall()
        ]

        return {
            "period_days": days,
            "total_views": totals["total_views"],
            "unique_visitors": totals["unique_visitors"],
            "views_by_path": views_by_path,
            "device_breakdown": device_breakdown,
            "browser_breakdown": browser_breakdown,
            "os_breakdown": os_breakdown,
            "daily_traffic": daily_traffic,
            "hourly_traffic": hourly_traffic,
        }
    finally:
        conn.close()
