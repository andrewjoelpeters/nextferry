import requests
from typing import List
from dotenv import load_dotenv
import os
from .serializers import Vessel, RawRouteSchedule, RawDirectionalSchedule
import logging


logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

load_dotenv()
APIAccessCode = os.getenv("WSDOT_API_KEY")


def get_vessel_positions() -> List[Vessel]:
    url = f"https://www.wsdot.wa.gov/ferries/api/vessels/rest/vessellocations?apiaccesscode={APIAccessCode}"
    response = requests.get(url)

    if not response.ok:
        raise Exception(f"HTTP error! status: {response.status_code}")

    data = response.json()
    logging.debug(f"GOT VESSEL POSITIONS: \n\n{data}")
    return [Vessel(**ferry) for ferry in data if ferry.get("InService")]


def get_schedule_today(route_id) -> List[RawDirectionalSchedule]:
    url = f"https://www.wsdot.wa.gov/ferries/api/schedule/rest/scheduletoday/{route_id}/false?apiaccesscode={APIAccessCode}"
    response = requests.get(url)

    if not response.ok:
        raise Exception(f"HTTP error! status: {response.status_code}")

    data = response.json()
    logging.debug(f"GOT SCHEDULE: \n\n{data}")
    schedule = RawRouteSchedule(**data)
    return schedule.terminal_combos


def get_routes(departing_terminal_id, arriving_terminal_id):
    url = f"https://www.wsdot.wa.gov/ferries/api/schedule/rest/routes/%7BTripDate%7D/%7BDepartingTerminalID%7D/%7BArrivingTerminalID%7D?apiaccesscode={APIAccessCode}"
