import logging
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.config import ROUTES

from .database import get_previous_sailing_fullness, get_turnaround_minutes
from .serializers import (
    DirectionalSailing,
    DirectionalSchedule,
    RawDirectionalSchedule,
    RouteSchedule,
    Vessel,
)
from .utils import datetime_to_minutes
from .wsdot_client import get_schedule_today, get_vessel_positions

try:
    from .ml_predictor import predictor as ml_predictor
except ImportError:
    ml_predictor = None

logger = logging.getLogger(__name__)


CACHED_DELAYS = {}


def update_cached_delay(vessel: Vessel, delay: timedelta):
    for route in vessel.route_name:
        if route not in CACHED_DELAYS:
            CACHED_DELAYS[route] = {}
        CACHED_DELAYS[route][vessel.vessel_position_num] = delay


def get_cached_delay(vessel: Vessel) -> timedelta | None:
    # some vessels don't have routes assigned
    if not vessel.route_name:
        return None

    route = vessel.route_name[0]
    if route in CACHED_DELAYS:
        return CACHED_DELAYS[route].get(vessel.vessel_position_num, None)


def get_vessels_with_delays():
    vessel_positions = get_vessel_positions()
    for v in vessel_positions:
        vessel_delay = (
            v.left_dock - v.scheduled_departure
            if v.scheduled_departure and v.left_dock
            else None
        )
        if vessel_delay:
            logging.debug(
                f"Updating cache to show {vessel_delay} delay for {v.vessel_name}"
            )
            update_cached_delay(v, vessel_delay)
        else:
            vessel_delay = get_cached_delay(v)
            logging.debug(f"Got cached delay of {vessel_delay} for {v.vessel_name}")
        v.delay = vessel_delay
    return vessel_positions


def get_route_vessels(vessel_positions: list[Vessel], route_config):
    return [v for v in vessel_positions if route_config["route_name"] in v.route_name]


def get_route_schedule_by_boat(
    schedules: list[RawDirectionalSchedule],
) -> dict[int, list[DirectionalSailing]]:
    schedule_by_boat = defaultdict(list)
    for directional_schedule in schedules:
        for sailing in directional_schedule.times:
            schedule_by_boat[sailing.vessel_position_num].append(
                DirectionalSailing(
                    departing_terminal_name=directional_schedule.departing_terminal_name,
                    arriving_terminal_name=directional_schedule.arriving_terminal_name,
                    departing_terminal_id=directional_schedule.departing_terminal_id,
                    arriving_terminal_id=directional_schedule.arriving_terminal_id,
                    scheduled_departure=sailing.scheduled_departure,
                    vessel_name=sailing.vessel_name,
                    vessel_position_num=sailing.vessel_position_num,
                )
            )
    for sailings in schedule_by_boat.values():
        sailings.sort(key=lambda x: x.scheduled_departure)

    return schedule_by_boat


def propigate_delays(
    delay: timedelta | None,
    sailings: list[DirectionalSailing],
    vessel_id: int | None = None,
    vessel_speed: float | None = None,
) -> list[DirectionalSailing]:
    """Apply delays to sailings, using ML predictions if available, else flat propagation."""
    if not delay and not (ml_predictor and ml_predictor.is_trained):
        return sailings

    delay_minutes = datetime_to_minutes(delay) if delay else 0
    now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))

    for sailing in sailings:
        if ml_predictor and ml_predictor.is_trained and sailing.scheduled_departure:
            # Compute minutes until departure
            time_diff = sailing.scheduled_departure - now
            minutes_until = max(0, time_diff.total_seconds() / 60)

            route_abbrev = None
            # Get route from config by terminal IDs
            for route in ROUTES:
                if sailing.departing_terminal_id in route["terminals"]:
                    route_abbrev = route["route_name"]
                    break

            if route_abbrev:
                sched_iso = sailing.scheduled_departure.isoformat()

                # Look up docking features for this sailing
                prev_fullness = get_previous_sailing_fullness(
                    sailing.departing_terminal_id, sched_iso
                )
                turnaround = None
                if vessel_id is not None:
                    turnaround = get_turnaround_minutes(vessel_id, sched_iso)

                prediction = ml_predictor.predict(
                    route_abbrev=route_abbrev,
                    departing_terminal_id=sailing.departing_terminal_id,
                    vessel_id=vessel_id or 0,
                    day_of_week=sailing.scheduled_departure.weekday(),
                    hour_of_day=sailing.scheduled_departure.hour,
                    minutes_until_scheduled_departure=minutes_until,
                    current_vessel_delay_minutes=delay_minutes,
                    vessel_speed=vessel_speed,
                    previous_sailing_fullness=prev_fullness,
                    turnaround_minutes=turnaround,
                )
                if prediction:
                    sailing.delay_in_minutes = round(prediction["predicted_delay"])
                    sailing.delay_lower_bound = round(prediction["lower_bound"])
                    sailing.delay_upper_bound = round(prediction["upper_bound"])
                    continue

        # Fallback: flat propagation
        if delay:
            sailing.delay_in_minutes = delay_minutes

    return sailings


def get_next_sailings_by_boat(
    schedule_by_boat: dict[int, list[DirectionalSailing]], route_vessels: list[Vessel]
) -> dict[int, list[DirectionalSailing]]:
    route_vessels_by_position = {
        vessel.vessel_position_num: vessel for vessel in route_vessels
    }
    next_sailings_by_boat = {}
    for vessel_position_num, sailings in schedule_by_boat.items():
        # if this vessel_position_num isn't in route_vessels:
        # next sailings are all sailings with this vessel position num and a scheduled
        # departure greater than right now
        current_vessel = route_vessels_by_position.get(vessel_position_num)
        if not current_vessel or not current_vessel.scheduled_departure:
            next_sailings = [
                sailing
                for sailing in sailings
                if sailing.scheduled_departure
                > datetime.now(tz=ZoneInfo("America/Los_Angeles"))
            ]
        elif current_vessel.at_dock:
            next_sailings = [
                sailing
                for sailing in sailings
                if sailing.scheduled_departure >= current_vessel.scheduled_departure
            ]
        elif not current_vessel.at_dock:
            # Include the just-departed sailing so users can see it's en route
            departed_sailing = None
            for sailing in sailings:
                if sailing.scheduled_departure == current_vessel.scheduled_departure:
                    now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
                    minutes_since = (
                        now - sailing.scheduled_departure
                    ).total_seconds() / 60
                    # Show departed sailing for up to 30 minutes after departure
                    if minutes_since <= 30:
                        departed_sailing = sailing.model_copy()
                        departed_sailing.departed = True
                    break

            next_sailings = [
                sailing
                for sailing in sailings
                if sailing.scheduled_departure > current_vessel.scheduled_departure
            ]

            if departed_sailing:
                next_sailings.insert(0, departed_sailing)

        v_id = current_vessel.vessel_id if current_vessel else None
        v_speed = current_vessel.speed if current_vessel else None
        next_sailings = propigate_delays(
            current_vessel.delay, next_sailings, vessel_id=v_id, vessel_speed=v_speed
        )

        # Annotate the first sailing with live vessel state.
        # When the vessel is en route, verify the first sailing's direction matches
        # the vessel's current direction. E.g. if the vessel departed Seattle heading
        # to Bainbridge, only annotate a Seattle→Bainbridge sailing, not a future
        # sailing departing from a different terminal.
        if next_sailings and current_vessel:
            first = next_sailings[0]
            direction_matches = (
                current_vessel.at_dock
                or first.departing_terminal_id == current_vessel.departing_terminal_id
            )
            if direction_matches:
                first.vessel_at_dock = current_vessel.at_dock
                first.vessel_left_dock = current_vessel.left_dock
                first.vessel_eta = current_vessel.eta
                if current_vessel.delay:
                    first.vessel_delay_minutes = datetime_to_minutes(
                        current_vessel.delay
                    )

        next_sailings_by_boat[vessel_position_num] = next_sailings

    return next_sailings_by_boat


def get_directional_schedules(
    next_sailings_by_boat: dict[int, list[DirectionalSailing]],
) -> list[DirectionalSchedule]:
    direction_groups = defaultdict(list)

    # Flatten all sailings from all vessels and group by direction
    for vessel_sailings in next_sailings_by_boat.values():
        for sailing in vessel_sailings:
            # direction_key = (sailing.departing_terminal_id, sailing.arriving_terminal_id)
            direction_meta = (
                sailing.departing_terminal_id,
                sailing.departing_terminal_name,
                sailing.arriving_terminal_id,
                sailing.arriving_terminal_name,
            )
            direction_groups[direction_meta].append(sailing)

    direction_schedules = []
    for direction_meta, sailings in direction_groups.items():
        departing_id, departing_name, arriving_id, arriving_name = direction_meta
        direction_schedules.append(
            DirectionalSchedule(
                departing_terminal_id=departing_id,
                departing_terminal_name=departing_name,
                arriving_terminal_id=arriving_id,
                arriving_terminal_name=arriving_name,
                times=sorted(
                    [sailing.to_route_sailing() for sailing in sailings],
                    key=lambda x: x.scheduled_departure,
                ),
            )
        )

    direction_schedules.sort(key=lambda ds: ds.departing_terminal_name)
    return direction_schedules


def get_next_sailings_for_route(
    vessel_positions, route_config
) -> list[DirectionalSailing]:
    route_schedule = get_schedule_today(route_config["route_id"])
    route_vessels = get_route_vessels(vessel_positions, route_config)
    schedule_by_boat = get_route_schedule_by_boat(route_schedule)
    next_sailings_by_boat = get_next_sailings_by_boat(schedule_by_boat, route_vessels)
    directional_sailings = get_directional_schedules(next_sailings_by_boat)
    for direction in directional_sailings:
        logger.info(
            f"Got {len(direction.times)} upcoming sailings for {direction.departing_terminal_name} to {direction.arriving_terminal_name}"
        )
    return directional_sailings


def get_next_sailings() -> list[RouteSchedule]:
    vessel_positions = get_vessels_with_delays()
    all_next_sailings = []
    for route in ROUTES:
        next_sailings = get_next_sailings_for_route(vessel_positions, route)
        all_next_sailings.append(
            RouteSchedule(
                route_name=[route.get("name")],
                route_id=route.get("route_id"),
                schedules=next_sailings,
            )
        )

    return all_next_sailings
