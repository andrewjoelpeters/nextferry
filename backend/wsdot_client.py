import logging
import os

import requests
from dotenv import load_dotenv

from .serializers import RawDirectionalSchedule, RawRouteSchedule, TerminalSpace, Vessel

logger = logging.getLogger(__name__)

load_dotenv()
APIAccessCode = os.getenv("WSDOT_API_KEY")


WSDOT_BASE = "https://www.wsdot.wa.gov/ferries/api"


def _wsdot_headers() -> dict:
    return {"Authorization": APIAccessCode}


def get_vessel_positions() -> list[Vessel]:
    if not APIAccessCode:
        raise Exception("WSDOT_API_KEY environment variable is not set")

    url = f"{WSDOT_BASE}/vessels/rest/vessellocations"

    try:
        response = requests.get(url, headers=_wsdot_headers())

        if not response.ok:
            raise Exception(
                f"HTTP error! status: {response.status_code}, response: {response.text}, url: {url}"
            )

        data = response.json()
        logger.info(f"Successfully got {len(data)} vessels from WSDOT API")
        return [Vessel(**ferry) for ferry in data if ferry.get("InService")]

    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)}") from e


def get_schedule_today(route_id) -> list[RawDirectionalSchedule]:
    url = f"{WSDOT_BASE}/schedule/rest/scheduletoday/{route_id}/false"
    response = requests.get(url, headers=_wsdot_headers())

    if not response.ok:
        raise Exception(f"HTTP error! status: {response.status_code}")

    data = response.json()
    logger.debug(f"Got Schedule from WSDOT with length {len(data)}")
    schedule = RawRouteSchedule(**data)
    return schedule.terminal_combos


def get_sailing_space():
    url = f"{WSDOT_BASE}/terminals/rest/terminalsailingspace"
    response = requests.get(url, headers=_wsdot_headers())

    if not response.ok:
        raise Exception(f"HTTP error! status: {response.status_code}")

    data = response.json()
    return [TerminalSpace(**terminal) for terminal in data]
