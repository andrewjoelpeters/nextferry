# A script to create a historical dataset of WSDOT vessel positions for better delay prediction

import asyncio
import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

from .database import extract_sailing_events, insert_vessel_snapshots_batch
from .serializers import FlatSailingSpace, SailingSpace, Vessel
from .wsdot_client import get_sailing_space, get_vessel_positions

logger = logging.getLogger(__name__)

# Set to False to disable legacy JSONL writing
WRITE_JSONL = os.getenv("WRITE_JSONL", "true").lower() == "true"


def get_data_directory() -> Path:
    """Get data directory from Railway volume or fallback to local"""
    volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    return Path(volume_path) if volume_path else Path("./data")


def save_data_to_jsonl(
    prefix: str, data: List[Vessel | FlatSailingSpace], data_dir: Path
) -> None:
    """Save data to a daily jsonl file"""
    data_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(ZoneInfo("America/Los_Angeles"))
    filename = f"{prefix}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jsonl"
    filepath = data_dir / filename

    with open(filepath, "w") as f:
        for v in data:
            json.dump(v.model_dump(mode="json", by_alias=True), f)
            f.write("\n")

    logger.info(f"Saved {len(data)} {prefix} to {filename}")


def flatten_sailing_space(sailing_space: SailingSpace):
    return [
        FlatSailingSpace(
            departing_terminal_id=sailing_space.terminal_id,
            departing_terminal_name=sailing_space.terminal_name,
            departure_time=space.departure,
            vessel_name=space.vessel_name,
            vessel_id=space.vessel_id,
            arriving_terminal_id=arrival.terminal_id,
            arriving_terminal_name=arrival.terminal_name,
            max_space_count=arrival.max_space_count,
            drive_up_space_count=arrival.drive_up_space_count,
            reservable_space_count=arrival.reservable_space_count,
        )
        for space in sailing_space.departing_spaces
        for arrival in space.space_for_arrival_terminals
    ]


def next_two_departures_per_route(
    flat_dicts: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    grouped = defaultdict(list)

    # Group by (departing_terminal_id, arriving_terminal_id)
    for item in flat_dicts:
        key = (item.departing_terminal_id, item.arriving_terminal_id)
        grouped[key].append(item)

    # Sort each group by departure_time and take the first two
    result = []
    for key, departures in grouped.items():
        sorted_deps = sorted(departures, key=lambda x: x.departure_time)
        result.extend(sorted_deps[:2])

    return result


def store_vessels_to_db(vessels: List[Vessel]):
    """Insert vessel positions into SQLite for historical accumulation."""
    collected_at = datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
    batch = []
    for v in vessels:
        route_abbrev = v.route_name[0] if v.route_name else None
        batch.append(
            (
                collected_at,
                v.vessel_id,
                v.vessel_name,
                route_abbrev,
                v.departing_terminal_id,
                v.departing_terminal_name,
                v.arriving_terminal_id,
                v.arriving_terminal_name,
                v.latitude,
                v.longitude,
                v.speed,
                v.heading,
                int(v.in_service),
                int(v.at_dock),
                v.left_dock.isoformat() if v.left_dock else None,
                v.eta.isoformat() if v.eta else None,
                v.scheduled_departure.isoformat() if v.scheduled_departure else None,
                v.vessel_position_num,
            )
        )
    insert_vessel_snapshots_batch(batch)


async def collect_data():
    """Background task to collect WSDOT data every X minutes and write to volume"""
    data_dir = get_data_directory()
    logger.info(f"Starting vessel data collection to {data_dir}")

    while True:
        try:
            logger.info("Starting data collection cycle")

            logger.info("Fetching vessel positions")
            vessels = get_vessel_positions()

            # Store to SQLite for ML training
            store_vessels_to_db(vessels)
            extract_sailing_events()

            # Optionally keep JSONL writing
            if WRITE_JSONL:
                save_data_to_jsonl("vessels", vessels, data_dir)

            # get sailing space data
            logger.info("Fetching sailing space data")
            sailing_spaces = get_sailing_space()
            flattened = [
                flat
                for space in sailing_spaces
                for flat in flatten_sailing_space(space)
            ]
            filtered = next_two_departures_per_route(flattened)
            if WRITE_JSONL:
                save_data_to_jsonl("sailing_space", filtered, data_dir)

        except Exception as e:
            logger.error(f"Data collection failed: {e}")

        await asyncio.sleep(60 * 5)  # run every 5 minutes
