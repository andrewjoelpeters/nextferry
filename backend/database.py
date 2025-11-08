import sqlite3
from pathlib import Path

def get_db_path() -> Path:
    return Path("./ferry_data.db")

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

if __name__ == "__main__":
    init_db()
