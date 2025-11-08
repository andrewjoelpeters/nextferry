import json
import sqlite3
from pathlib import Path
from backend.database import get_db_path
from backend.data_collector import get_data_directory

def backfill_data():
    db_path = get_db_path()
    data_dir = get_data_directory()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for file_path in data_dir.glob("vessels_*.jsonl"):
        with open(file_path, "r") as f:
            for line in f:
                data = json.loads(line)
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
    backfill_data()
