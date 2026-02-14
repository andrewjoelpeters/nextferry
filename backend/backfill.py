import json
import sqlite3
from pathlib import Path
from backend.database import get_db_path, get_data_directory, save_vessel_data

def backfill_data():
    data_dir = get_data_directory()

    all_vessel_data = []
    for file_path in data_dir.glob("vessels_*.jsonl"):
        with open(file_path, "r") as f:
            for line in f:
                data = json.loads(line)
                all_vessel_data.append(data)

    if all_vessel_data:
        print(f"Backfilling {len(all_vessel_data)} records...")
        save_vessel_data(all_vessel_data)
        print("Done.")
    else:
        print("No vessel data found to backfill.")

if __name__ == "__main__":
    backfill_data()
