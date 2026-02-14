import sqlite3
import os
from pathlib import Path
from typing import List, Any
from datetime import datetime

def get_data_directory() -> Path:
    """Get data directory from Railway volume or fallback to local"""
    volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    path = Path(volume_path) if volume_path else Path("./data")
    path.mkdir(exist_ok=True)
    return path

def get_db_path() -> Path:
    return get_data_directory() / "ferry_data.db"

def init_db():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vessel_data (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME,
            vessel_id INTEGER,
            vessel_name TEXT,
            mmsi INTEGER,
            departing_terminal_id INTEGER,
            departing_terminal_name TEXT,
            arriving_terminal_id INTEGER,
            arriving_terminal_name TEXT,
            latitude REAL,
            longitude REAL,
            speed REAL,
            heading REAL,
            in_service BOOLEAN,
            at_dock BOOLEAN,
            left_dock DATETIME,
            eta DATETIME,
            scheduled_departure DATETIME,
            actual_departure DATETIME,
            delay INTEGER
        )
        """
    )
    conn.commit()
    conn.close()

def save_vessel_data(vessels: List[Any]):
    """
    Saves a list of Vessel objects (or dicts) to the database.
    Supports both Pydantic models and dictionaries.
    """
    if not vessels:
        return

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    for vessel in vessels:
        # Handle both Pydantic models and dictionaries
        if hasattr(vessel, "model_dump"):
            data = vessel.model_dump(mode="json", by_alias=True)
        elif isinstance(vessel, dict):
            data = vessel
        else:
            continue

        cursor.execute(
            """
            INSERT INTO vessel_data (
                timestamp,
                vessel_id,
                vessel_name,
                mmsi,
                departing_terminal_id,
                departing_terminal_name,
                arriving_terminal_id,
                arriving_terminal_name,
                latitude,
                longitude,
                speed,
                heading,
                in_service,
                at_dock,
                left_dock,
                eta,
                scheduled_departure,
                actual_departure,
                delay
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("TimeStamp"),
                data.get("VesselID"),
                data.get("VesselName"),
                data.get("MMSI"),
                data.get("DepartingTerminalID"),
                data.get("DepartingTerminalName"),
                data.get("ArrivingTerminalID"),
                data.get("ArrivingTerminalName"),
                data.get("Latitude"),
                data.get("Longitude"),
                data.get("Speed"),
                data.get("Heading"),
                data.get("InService"),
                data.get("AtDock"),
                data.get("LeftDock"),
                data.get("Eta"),
                data.get("ScheduledDeparture"),
                data.get("ActualDeparture"),
                data.get("Delay"),
            ),
        )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
