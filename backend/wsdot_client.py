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
        logging.info(f"Successfully got {len(data)} vessels from WSDOT API")
        return [Vessel(**ferry) for ferry in data if ferry.get("InService")]

    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")


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
