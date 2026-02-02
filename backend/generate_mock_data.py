import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

def generate_mock_vessel_data(num_records=1000):
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)

    vessels = [
        {"id": 1, "name": "Tacoma", "route": (3, "Seattle", 7, "Bainbridge")},
        {"id": 2, "name": "Wenatchee", "route": (7, "Bainbridge", 3, "Seattle")},
        {"id": 3, "name": "Puyallup", "route": (12, "Kingston", 8, "Edmonds")},
        {"id": 4, "name": "Spokane", "route": (8, "Edmonds", 12, "Kingston")},
    ]

    start_date = datetime.now(ZoneInfo("America/Los_Angeles")) - timedelta(days=7)

    records = []
    for i in range(num_records):
        vessel = random.choice(vessels)
        # Random time over the last 7 days
        scheduled_time = start_date + timedelta(
            days=random.randint(0, 6),
            hours=random.randint(6, 22),
            minutes=random.randint(0, 59)
        )

        # Simulate some delay patterns
        # More delay during rush hours (7-9 AM, 4-6 PM)
        hour = scheduled_time.hour
        base_delay = 0
        if 7 <= hour <= 9 or 16 <= hour <= 18:
            base_delay = random.randint(5, 15)

        # More delay on weekends? Maybe not for ferries, but let's add some variance
        if scheduled_time.weekday() >= 5:
            base_delay += random.randint(0, 10)

        actual_delay = base_delay + random.randint(-2, 5)
        left_dock = scheduled_time + timedelta(minutes=actual_delay)

        record = {
            "VesselID": vessel["id"],
            "VesselName": vessel["name"],
            "DepartingTerminalID": vessel["route"][0],
            "DepartingTerminalName": vessel["route"][1],
            "ArrivingTerminalID": vessel["route"][2],
            "ArrivingTerminalName": vessel["route"][3],
            "Latitude": 47.6,
            "Longitude": -122.4,
            "Speed": random.uniform(0, 15),
            "Heading": random.randint(0, 359),
            "InService": True,
            "AtDock": random.choice([True, False]),
            "LeftDock": left_dock.isoformat(),
            "Eta": (left_dock + timedelta(minutes=35)).isoformat(),
            "ScheduledDeparture": scheduled_time.isoformat(),
            "TimeStamp": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(),
        }
        records.append(record)

    # Save to a few files to mimic the collector behavior
    batch_size = 200
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        filename = f"vessels_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.jsonl"
        filepath = data_dir / filename
        with open(filepath, "w") as f:
            for r in batch:
                f.write(json.dumps(r) + "\n")

    print(f"Generated {len(records)} mock vessel records in {data_dir}")

if __name__ == "__main__":
    generate_mock_vessel_data()
