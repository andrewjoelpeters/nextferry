"""One-time script to backfill SQLite from existing JSONL vessel files.

Usage:
    python -m backend.backfill [data_dir]

If data_dir is not provided, uses RAILWAY_VOLUME_MOUNT_PATH or ./data.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from .database import (extract_sailing_events, get_connection, get_db_path,
                       init_db)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def parse_ms_date_str(value):
    """Parse WSDOT /Date(ms)/ format to ISO string, or return as-is if already ISO."""
    if value is None:
        return None
    if isinstance(value, str) and value.startswith("/Date("):
        import re

        match = re.match(r"/Date\((\d+)([-+]\d{4})?\)/", value)
        if match:
            from zoneinfo import ZoneInfo

            ts = int(match.group(1)) / 1000
            dt = datetime.fromtimestamp(ts, tz=ZoneInfo("UTC")).astimezone(
                ZoneInfo("America/Los_Angeles")
            )
            return dt.isoformat()
    return value


def backfill_from_jsonl(data_dir: Path):
    """Read all vessels_*.jsonl files and insert into SQLite."""
    jsonl_files = sorted(data_dir.glob("vessels_*.jsonl"))
    if not jsonl_files:
        logger.warning(f"No vessels JSONL files found in {data_dir}")
        return

    logger.info(f"Found {len(jsonl_files)} JSONL files to process")

    conn = get_connection()
    total_inserted = 0

    try:
        for filepath in jsonl_files:
            # Extract collection timestamp from filename: vessels_YYYYMMDD_HHMMSS.jsonl
            stem = filepath.stem  # e.g. vessels_20250301_143000
            parts = stem.split("_", 1)
            if len(parts) < 2:
                logger.warning(f"Skipping file with unexpected name: {filepath.name}")
                continue

            # Parse timestamp from filename
            try:
                ts_str = parts[1]  # e.g. 20250301_143000
                collected_dt = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                collected_at = collected_dt.isoformat()
            except ValueError:
                logger.warning(f"Cannot parse timestamp from {filepath.name}, skipping")
                continue

            batch = []
            with open(filepath) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        vessel = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    route_names = vessel.get("OpRouteAbbrev", [])
                    route_abbrev = route_names[0] if route_names else None

                    batch.append(
                        (
                            collected_at,
                            vessel.get("VesselID"),
                            vessel.get("VesselName", ""),
                            route_abbrev,
                            vessel.get("DepartingTerminalID"),
                            vessel.get("DepartingTerminalName"),
                            vessel.get("ArrivingTerminalID"),
                            vessel.get("ArrivingTerminalName"),
                            vessel.get("Latitude"),
                            vessel.get("Longitude"),
                            vessel.get("Speed"),
                            vessel.get("Heading"),
                            int(vessel.get("InService", False)),
                            int(vessel.get("AtDock", False)),
                            parse_ms_date_str(vessel.get("LeftDock")),
                            parse_ms_date_str(vessel.get("Eta")),
                            parse_ms_date_str(vessel.get("ScheduledDeparture")),
                            vessel.get("VesselPositionNum"),
                        )
                    )

            if batch:
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
                    batch,
                )
                total_inserted += len(batch)

            if len(jsonl_files) > 10 and jsonl_files.index(filepath) % 100 == 0:
                conn.commit()
                logger.info(
                    f"Progress: {jsonl_files.index(filepath)}/{len(jsonl_files)} files"
                )

        conn.commit()
        logger.info(f"Inserted {total_inserted} snapshot rows total")
    finally:
        conn.close()

    # Extract sailing events from the snapshots
    logger.info("Extracting sailing events from snapshots...")
    extract_sailing_events()

    # Report results
    from .database import get_sailing_event_count, get_snapshot_count

    logger.info(f"Database now has {get_snapshot_count()} snapshots")
    logger.info(f"Database now has {get_sailing_event_count()} sailing events")


def main():
    import os

    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])
    else:
        volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
        data_dir = Path(volume_path) if volume_path else Path("./data")

    if not data_dir.exists():
        logger.error(f"Data directory {data_dir} does not exist")
        sys.exit(1)

    logger.info(f"Initializing database at {get_db_path()}")
    init_db()

    logger.info(f"Backfilling from {data_dir}")
    backfill_from_jsonl(data_dir)


if __name__ == "__main__":
    main()
