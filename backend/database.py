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


# --- Historical dashboard queries ---

SEASON_MONTHS = {
    "winter": (12, 1, 2),
    "spring": (3, 4, 5),
    "summer": (6, 7, 8),
    "fall": (9, 10, 11),
}

DAY_TYPE_MAP = {
    "weekdays": (1, 2, 3, 4, 5),  # SQLite strftime %w: Mon=1..Fri=5
    "weekends": (0, 6),  # Sun=0, Sat=6
}


def _build_where_clauses(
    route: str | None,
    season: str | None,
    day_type: str | None,
    date_col: str = "scheduled_departure",
    dow_col: str = "day_of_week",
) -> tuple[str, list]:
    """Build WHERE clause fragments and params for history filters."""
    clauses: list[str] = []
    params: list = []

    if route:
        clauses.append("route_abbrev = ?")
        params.append(route)

    if season and season in SEASON_MONTHS:
        months = SEASON_MONTHS[season]
        placeholders = ",".join("?" * len(months))
        clauses.append(
            f"CAST(strftime('%m', {date_col}) AS INTEGER) IN ({placeholders})"
        )
        params.extend(months)

    if day_type:
        if day_type in DAY_TYPE_MAP:
            days = DAY_TYPE_MAP[day_type]
            placeholders = ",".join("?" * len(days))
            clauses.append(f"{dow_col} IN ({placeholders})")
            params.extend(days)
        elif day_type.isdigit() and 0 <= int(day_type) <= 6:
            clauses.append(f"{dow_col} = ?")
            params.append(int(day_type))

    return (" AND " + " AND ".join(clauses) if clauses else ""), params


def get_history_data(
    route: str | None = None,
    season: str | None = None,
    day_type: str | None = None,
) -> dict:
    """Return filtered historical data for the history dashboard."""
    where_suffix, params = _build_where_clauses(route, season, day_type)
    conn = get_connection()
    try:
        # Delays by hour (filtered)
        delays_by_hour = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    hour_of_day,
                    COUNT(*) as count,
                    ROUND(AVG(delay_minutes), 2) as avg_delay,
                    ROUND(SUM(CASE WHEN delay_minutes <= 0 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as on_time_pct
                FROM sailing_events
                WHERE 1=1 {where_suffix}
                GROUP BY hour_of_day
                ORDER BY hour_of_day
                """,
                params,
            ).fetchall()
        ]

        # Delays by day of week (filtered)
        delays_by_dow = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    day_of_week,
                    COUNT(*) as count,
                    ROUND(AVG(delay_minutes), 2) as avg_delay,
                    ROUND(SUM(CASE WHEN delay_minutes <= 0 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as on_time_pct
                FROM sailing_events
                WHERE 1=1 {where_suffix}
                GROUP BY day_of_week
                ORDER BY day_of_week
                """,
                params,
            ).fetchall()
        ]

        # Delays by route (filtered)
        delays_by_route = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    route_abbrev,
                    COUNT(*) as count,
                    ROUND(AVG(delay_minutes), 2) as avg_delay,
                    ROUND(SUM(CASE WHEN delay_minutes <= 0 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as on_time_pct
                FROM sailing_events
                WHERE 1=1 {where_suffix}
                GROUP BY route_abbrev
                ORDER BY route_abbrev
                """,
                params,
            ).fetchall()
        ]

        # Delay distribution (filtered)
        delay_distribution = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    CAST(ROUND(delay_minutes) AS INTEGER) as delay_bin,
                    COUNT(*) as count
                FROM sailing_events
                WHERE delay_minutes BETWEEN -5 AND 20 {where_suffix}
                GROUP BY delay_bin
                ORDER BY delay_bin
                """,
                params,
            ).fetchall()
        ]

        # Daily on-time trend (filtered)
        daily_trend = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    DATE(scheduled_departure) as date,
                    COUNT(*) as count,
                    ROUND(AVG(delay_minutes), 2) as avg_delay,
                    ROUND(SUM(CASE WHEN delay_minutes <= 0 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as on_time_pct
                FROM sailing_events
                WHERE 1=1 {where_suffix}
                GROUP BY DATE(scheduled_departure)
                ORDER BY date
                """,
                params,
            ).fetchall()
        ]

        # Total count (filtered)
        event_count = conn.execute(
            f"SELECT COUNT(*) as cnt FROM sailing_events WHERE 1=1 {where_suffix}",
            params,
        ).fetchone()["cnt"]

        return {
            "delays_by_hour": delays_by_hour,
            "delays_by_dow": delays_by_dow,
            "delays_by_route": delays_by_route,
            "delay_distribution": delay_distribution,
            "daily_trend": daily_trend,
            "event_count": event_count,
        }
    finally:
        conn.close()


def get_busyness_heatmap(
    route: str | None = None,
    season: str | None = None,
) -> list[dict]:
    """Return average fill percentage by day-of-week × hour-of-day.

    Uses sailing_space_snapshots to compute how full ferries typically are.
    Returns list of {day_of_week, hour_of_day, avg_fill_pct, sailing_count}.
    """
    clauses: list[str] = []
    params: list = []

    if route:
        # Map route_abbrev to terminal pairs — need to join or filter by terminal
        # Since sailing_space_snapshots doesn't have route_abbrev, we filter
        # by known terminal IDs for each route
        from .config import ROUTES

        terminal_ids = []
        for r in ROUTES:
            if r["route_name"] == route:
                terminal_ids = r["terminals"]
                break
        if terminal_ids:
            placeholders = ",".join("?" * len(terminal_ids))
            clauses.append(f"departing_terminal_id IN ({placeholders})")
            params.extend(terminal_ids)

    if season and season in SEASON_MONTHS:
        months = SEASON_MONTHS[season]
        placeholders = ",".join("?" * len(months))
        clauses.append(
            f"CAST(strftime('%m', departure_time) AS INTEGER) IN ({placeholders})"
        )
        params.extend(months)

    where = " AND ".join(clauses) if clauses else "1=1"

    conn = get_connection()
    try:
        rows = conn.execute(
            f"""
            SELECT
                CAST(strftime('%w', departure_time) AS INTEGER) as day_of_week,
                CAST(strftime('%H', departure_time) AS INTEGER) as hour_of_day,
                ROUND(AVG(
                    CASE WHEN max_space_count > 0
                    THEN (1.0 - (1.0 * drive_up_space_count / max_space_count)) * 100
                    ELSE NULL END
                ), 1) as avg_fill_pct,
                COUNT(DISTINCT departure_time) as sailing_count
            FROM sailing_space_snapshots
            WHERE {where}
            GROUP BY day_of_week, hour_of_day
            ORDER BY day_of_week, hour_of_day
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_available_routes() -> list[dict]:
    """Return distinct routes that have sailing event data."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT route_abbrev, COUNT(*) as count
            FROM sailing_events
            WHERE route_abbrev IS NOT NULL
            GROUP BY route_abbrev
            ORDER BY route_abbrev
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# --- Time Travel queries ---


def get_data_date_range() -> dict:
    """Return the min/max dates we have vessel snapshot data for."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT
                MIN(DATE(collected_at)) as min_date,
                MAX(DATE(collected_at)) as max_date,
                COUNT(DISTINCT DATE(collected_at)) as days_with_data
            FROM vessel_snapshots
            """
        ).fetchone()
        if row and row["min_date"]:
            return {
                "min_date": row["min_date"],
                "max_date": row["max_date"],
                "days_with_data": row["days_with_data"],
            }
        return {"min_date": None, "max_date": None, "days_with_data": 0}
    finally:
        conn.close()


def get_time_travel_data(timestamp: str) -> dict:
    """Return vessel states, sailing outcomes, and capacity at a given moment.

    Args:
        timestamp: ISO 8601 datetime string (e.g. "2024-11-07T20:00:00")

    Returns dict with:
        - vessels: list of vessel states at that moment
        - sailings: upcoming sailings from that moment with actual outcomes
        - capacity: capacity snapshots near that time
    """
    conn = get_connection()
    try:
        # 1. Get each vessel's most recent snapshot at or before the timestamp
        vessels = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    vs.vessel_id, vs.vessel_name, vs.route_abbrev,
                    vs.departing_terminal_id, vs.departing_terminal_name,
                    vs.arriving_terminal_id, vs.arriving_terminal_name,
                    vs.latitude, vs.longitude, vs.speed, vs.heading,
                    vs.in_service, vs.at_dock, vs.left_dock, vs.eta,
                    vs.scheduled_departure, vs.collected_at
                FROM vessel_snapshots vs
                INNER JOIN (
                    SELECT vessel_id, MAX(collected_at) as max_collected
                    FROM vessel_snapshots
                    WHERE collected_at <= ?
                    GROUP BY vessel_id
                ) latest ON vs.vessel_id = latest.vessel_id
                    AND vs.collected_at = latest.max_collected
                WHERE vs.in_service = 1
                ORDER BY vs.vessel_name
                """,
                (timestamp,),
            ).fetchall()
        ]

        # 2. Find sailing events near this timestamp (window: 2 hours before to
        #    4 hours after) so we can show what happened with those sailings.
        sailings = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    vessel_id, vessel_name, route_abbrev,
                    departing_terminal_id, arriving_terminal_id,
                    scheduled_departure, actual_departure,
                    delay_minutes, day_of_week, hour_of_day
                FROM sailing_events
                WHERE scheduled_departure BETWEEN
                    datetime(?, '-2 hours') AND datetime(?, '+4 hours')
                ORDER BY scheduled_departure
                """,
                (timestamp, timestamp),
            ).fetchall()
        ]

        # 3. Get capacity snapshots near this timestamp (closest snapshot per sailing)
        capacity = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    departing_terminal_id, departing_terminal_name,
                    arriving_terminal_id, arriving_terminal_name,
                    departure_time, vessel_name, vessel_id,
                    max_space_count, drive_up_space_count,
                    collected_at
                FROM sailing_space_snapshots
                WHERE collected_at = (
                    SELECT MAX(s2.collected_at)
                    FROM sailing_space_snapshots s2
                    WHERE s2.departing_terminal_id = sailing_space_snapshots.departing_terminal_id
                      AND s2.departure_time = sailing_space_snapshots.departure_time
                      AND s2.collected_at <= ?
                )
                AND departure_time >= ?
                AND departure_time <= datetime(?, '+4 hours')
                ORDER BY departure_time
                """,
                (timestamp, timestamp, timestamp),
            ).fetchall()
        ]

        # 4. For prediction replay: get each vessel's previous sailing delay
        #    (the "current_vessel_delay_minutes" the model would have seen)
        vessel_delays = {}
        for v in vessels:
            if v["scheduled_departure"]:
                row = conn.execute(
                    """
                    SELECT
                        (julianday(left_dock) - julianday(scheduled_departure)) * 24 * 60
                            AS delay_minutes
                    FROM vessel_snapshots
                    WHERE vessel_id = ?
                      AND collected_at <= ?
                      AND left_dock IS NOT NULL
                      AND scheduled_departure IS NOT NULL
                      AND left_dock != '' AND scheduled_departure != ''
                      AND scheduled_departure != ?
                    ORDER BY collected_at DESC
                    LIMIT 1
                    """,
                    (v["vessel_id"], timestamp, v["scheduled_departure"]),
                ).fetchone()
                if row:
                    vessel_delays[v["vessel_id"]] = row["delay_minutes"]

        # 5. Get turnaround minutes for vessels at dock
        vessel_turnarounds = {}
        for v in vessels:
            if v["at_dock"] and v["scheduled_departure"]:
                row = conn.execute(
                    """
                    SELECT MIN(collected_at) as docked_at
                    FROM vessel_snapshots
                    WHERE vessel_id = ?
                      AND at_dock = 1
                      AND scheduled_departure = ?
                      AND collected_at <= ?
                    """,
                    (v["vessel_id"], v["scheduled_departure"], timestamp),
                ).fetchone()
                if row and row["docked_at"]:
                    try:
                        docked_dt = datetime.fromisoformat(row["docked_at"])
                        ts_dt = datetime.fromisoformat(timestamp)
                        docked_dt = docked_dt.replace(tzinfo=None)
                        ts_dt = ts_dt.replace(tzinfo=None)
                        mins = (ts_dt - docked_dt).total_seconds() / 60
                        vessel_turnarounds[v["vessel_id"]] = max(0, mins)
                    except (ValueError, TypeError):
                        pass

        return {
            "vessels": vessels,
            "sailings": sailings,
            "capacity": capacity,
            "vessel_delays": vessel_delays,
            "vessel_turnarounds": vessel_turnarounds,
        }
    finally:
        conn.close()
