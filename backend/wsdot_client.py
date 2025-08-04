import requests
from typing import List
from dotenv import load_dotenv
import os
from .serializers import Vessel, RawRouteSchedule, RawDirectionalSchedule


load_dotenv()
APIAccessCode = os.getenv("WSDOT_API_KEY")


def get_vessel_positions() -> List[Vessel]:
    url = f'https://www.wsdot.wa.gov/ferries/api/vessels/rest/vessellocations?apiaccesscode={APIAccessCode}'
    response = requests.get(url)

    if not response.ok:
        raise Exception(f'HTTP error! status: {response.status_code}')

    data = response.json()
    return [Vessel(**ferry) for ferry in data if ferry.get('InService')]


def get_schedule_today(route_id) -> List[RawDirectionalSchedule]:
    url = f'https://www.wsdot.wa.gov/ferries/api/schedule/rest/scheduletoday/{route_id}/false?apiaccesscode={APIAccessCode}'
    response = requests.get(url)
    
    if not response.ok:
        raise Exception(f'HTTP error! status: {response.status_code}')

    schedule = RawRouteSchedule(**response.json())
    return schedule.terminal_combos
