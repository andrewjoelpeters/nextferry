import requests
from typing import List
from dotenv import load_dotenv
import os
from .serializers import Vessel, RawRouteSchedule, RawDirectionalSchedule
import logging

logger = logging.getLogger(__name__)

load_dotenv()
APIAccessCode = os.getenv("WSDOT_API_KEY")


def get_vessel_positions() -> List[Vessel]:
    if not APIAccessCode:
        raise Exception("WSDOT_API_KEY environment variable is not set")

    url = f"https://www.wsdot.wa.gov/ferries/api/vessels/rest/vessellocations?apiaccesscode={APIAccessCode}"

    try:
        response = requests.get(url)

        if not response.ok:
            # Include more details about the error
            raise Exception(
                f"HTTP error! status: {response.status_code}, response: {response.text}, url: {url}"
            )

        data = response.json()
        logger.info(f"Successfully got {len(data)} vessels from WSDOT API")
        return [Vessel(**ferry) for ferry in data if ferry.get("InService")]

    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")


def get_schedule_today(route_id) -> List[RawDirectionalSchedule]:
    url = f"https://www.wsdot.wa.gov/ferries/api/schedule/rest/scheduletoday/{route_id}/false?apiaccesscode={APIAccessCode}"
    response = requests.get(url)

    if not response.ok:
        raise Exception(f"HTTP error! status: {response.status_code}")

    data = response.json()
    logger.debug(f"Got Schedule from WSDOT with length {len(data)}")
    schedule = RawRouteSchedule(**data)
    return schedule.terminal_combos
