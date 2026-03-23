# Background task to collect WSDOT vessel and sailing space data into SQLite

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from .database import (
    extract_sailing_events,
    insert_sailing_space_batch,
    insert_vessel_snapshots_batch,
)
from .serializers import FlatSailingSpace, SailingSpace, Vessel
from .wsdot_client import get_sailing_space, get_vessel_positions

logger = logging.getLogger(__name__)


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
    flat_items: list[FlatSailingSpace],
) -> list[FlatSailingSpace]:
    grouped = defaultdict(list)

    for item in flat_items:
        key = (item.departing_terminal_id, item.arriving_terminal_id)
        grouped[key].append(item)

    result = []
    for _key, departures in grouped.items():
        sorted_deps = sorted(departures, key=lambda x: x.departure_time)
        result.extend(sorted_deps[:2])

    return result


def store_vessels_to_db(vessels: list[Vessel]):
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


def store_sailing_space_to_db(flat_items: list[FlatSailingSpace]):
    """Insert sailing space data into SQLite."""
    collected_at = datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
    batch = []
    for item in flat_items:
        batch.append(
            (
                collected_at,
                item.departing_terminal_id,
                item.departing_terminal_name,
                item.departure_time.isoformat() if item.departure_time else None,
                item.vessel_name,
                item.vessel_id,
                item.arriving_terminal_id,
                item.arriving_terminal_name,
                item.max_space_count,
                item.drive_up_space_count,
                item.reservable_space_count,
            )
        )
    insert_sailing_space_batch(batch)


async def collect_data():
    """Background task to collect WSDOT vessel data every 5 minutes into SQLite."""
    logger.info("Starting data collection to SQLite")

    while True:
        try:
            logger.info("Starting data collection cycle")

            logger.info("Fetching vessel positions")
            vessels = get_vessel_positions()
            store_vessels_to_db(vessels)
            extract_sailing_events()

            logger.info("Fetching sailing space data")
            sailing_spaces = get_sailing_space()
            flattened = [
                flat
                for space in sailing_spaces
                for flat in flatten_sailing_space(space)
            ]
            filtered = next_two_departures_per_route(flattened)
            store_sailing_space_to_db(filtered)

        except Exception as e:
            logger.error(f"Data collection failed: {e}")

        await asyncio.sleep(60 * 5)  # run every 5 minutes
