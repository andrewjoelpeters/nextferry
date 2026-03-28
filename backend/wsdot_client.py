import logging
import os

import requests
from dotenv import load_dotenv

from .serializers import RawDirectionalSchedule, RawRouteSchedule, TerminalSpace, Vessel

logger = logging.getLogger(__name__)

load_dotenv()
APIAccessCode = os.getenv("WSDOT_API_KEY")

# ---------------------------------------------------------------------------
# Test mode: NEXTFERRY_TEST_MODE=<scenario_name> replaces live WSDOT calls
# with bundled fixture data so the app can run without an API key.
# Used by Playwright e2e tests (start real server with mock data).
# ---------------------------------------------------------------------------
_TEST_MODE = os.getenv("NEXTFERRY_TEST_MODE")
_test_scenario = None


def _get_test_scenario():
    global _test_scenario
    if _test_scenario is None and _TEST_MODE:
        import tests.fixtures.scenarios as scenarios

        builder = getattr(scenarios, f"scenario_{_TEST_MODE}", None)
        if builder is None:
            raise ValueError(
                f"Unknown test scenario: {_TEST_MODE}. "
                f"Available: {[n for n in dir(scenarios) if n.startswith('scenario_')]}"
            )
        _test_scenario = builder()
    return _test_scenario


def get_vessel_positions() -> list[Vessel]:
    scenario = _get_test_scenario()
    if scenario:
        logger.info(f"TEST MODE ({_TEST_MODE}): returning fixture vessel data")
        return [Vessel(**v) for v in scenario["vessels"]]

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
        raise Exception(f"Request failed: {str(e)}") from e


def get_schedule_today(route_id) -> list[RawDirectionalSchedule]:
    scenario = _get_test_scenario()
    if scenario:
        schedule_data = scenario["schedules"].get(route_id)
        if schedule_data:
            parsed = RawRouteSchedule(**schedule_data)
            return parsed.terminal_combos
        return []

    url = f"https://www.wsdot.wa.gov/ferries/api/schedule/rest/scheduletoday/{route_id}/false?apiaccesscode={APIAccessCode}"
    response = requests.get(url)

    if not response.ok:
        raise Exception(f"HTTP error! status: {response.status_code}")

    data = response.json()
    logger.debug(f"Got Schedule from WSDOT with length {len(data)}")
    schedule = RawRouteSchedule(**data)
    return schedule.terminal_combos


def get_sailing_space():
    scenario = _get_test_scenario()
    if scenario:
        return []

    url = f"https://www.wsdot.wa.gov/ferries/api/terminals/rest/terminalsailingspace?apiaccesscode={APIAccessCode}"
    response = requests.get(url)

    if not response.ok:
        raise Exception(f"HTTP error! status: {response.status_code}")

    data = response.json()
    return [TerminalSpace(**terminal) for terminal in data]
