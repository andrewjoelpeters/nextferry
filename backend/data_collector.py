# A script to create a historical dataset of WSDOT vessel positions for better delay prediction

import os
import json
import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Dict, List
from .wsdot_client import get_vessel_positions

logger = logging.getLogger(__name__)


def get_data_directory() -> Path:
    """Get data directory from Railway volume or fallback to local"""
    volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    return Path(volume_path) if volume_path else Path("./data")


def save_vessel_data(vessels: List[Dict], data_dir: Path) -> None:
    """Save vessel data with timestamp"""
    data_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(ZoneInfo("America/Los_Angeles"))
    filename = f"vessels_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    filepath = data_dir / filename

    with open(filepath, "w") as f:
        for v in vessels:
            json.dump(v.model_dump(mode='json', by_alias=True), f)
            f.write("\n")

    logger.info(f"Saved {len(vessels)} vessels to {filename}")


async def collect_vessel_data():
    """Background task to collect vessel data every 2 minutes"""
    data_dir = get_data_directory()
    logger.info(f"Starting vessel data collection to {data_dir}")

    while True:
        try:
            vessels = get_vessel_positions()
            save_vessel_data(vessels, data_dir)
        except Exception as e:
            logger.error(f"Data collection failed: {e}")

        await asyncio.sleep(60 * 5)  # run every 5 minutes
