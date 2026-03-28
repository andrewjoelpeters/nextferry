import logging
import os

import requests
from dotenv import load_dotenv

from .replay import get_replay_time, get_scenario_data
from .serializers import RawDirectionalSchedule, RawRouteSchedule, TerminalSpace, Vessel

logger = logging.getLogger(__name__)

load_dotenv()
APIAccessCode = os.getenv("WSDOT_API_KEY")


def get_vessel_positions() -> list[Vessel]:
    if get_replay_time():
        data = get_scenario_data()["vessels"]
    else:
        if not APIAccessCode:
            raise Exception("WSDOT_API_KEY environment variable is not set")

        url = f"https://www.wsdot.wa.gov/ferries/api/vessels/rest/vessellocations?apiaccesscode={APIAccessCode}"

        try:
            response = requests.get(url)

            if not response.ok:
                raise Exception(
                    f"HTTP error! status: {response.status_code}, response: {response.text}, url: {url}"
                )

            data = response.json()
            logger.info(f"Successfully got {len(data)} vessels from WSDOT API")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}") from e

    return [Vessel(**ferry) for ferry in data if ferry.get("InService")]


def get_schedule_today(route_id) -> list[RawDirectionalSchedule]:
    if get_replay_time():
        data = get_scenario_data()["schedules"].get(str(route_id))
    else:
        url = f"https://www.wsdot.wa.gov/ferries/api/schedule/rest/scheduletoday/{route_id}/false?apiaccesscode={APIAccessCode}"
        response = requests.get(url)

        if not response.ok:
            raise Exception(f"HTTP error! status: {response.status_code}")

        data = response.json()
        logger.debug(f"Got Schedule from WSDOT with length {len(data)}")

    if not data:
        return []
    schedule = RawRouteSchedule(**data)
    return schedule.terminal_combos


def get_sailing_space():
    if get_replay_time():
        data = get_scenario_data().get("sailing_space", [])
    else:
        url = f"https://www.wsdot.wa.gov/ferries/api/terminals/rest/terminalsailingspace?apiaccesscode={APIAccessCode}"
        response = requests.get(url)

        if not response.ok:
            raise Exception(f"HTTP error! status: {response.status_code}")

        data = response.json()

    return [TerminalSpace(**terminal) for terminal in data]
