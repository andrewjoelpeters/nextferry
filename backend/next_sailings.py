import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from backend.config import ROUTES

from .serializers import (DirectionalSailing, DirectionalSchedule,
                          RawDirectionalSchedule, RouteSchedule, Vessel)
from .utils import datetime_to_minutes
from .wsdot_client import get_schedule_today, get_vessel_positions
from .ml_model import predict_delay, PredictionFeatures

logger = logging.getLogger(__name__)


CACHED_DELAYS = {}


def update_cached_delay(vessel: Vessel, delay: datetime):
    for route in vessel.route_name:
        if route not in CACHED_DELAYS:
            CACHED_DELAYS[route] = {}
        CACHED_DELAYS[route][vessel.vessel_position_num] = delay


def get_cached_delay(vessel: Vessel) -> Optional[datetime]:
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


def get_route_vessels(vessel_positions: List[Vessel], route_config):
    return [v for v in vessel_positions if route_config["route_name"] in v.route_name]


def get_route_schedule_by_boat(
    schedules: List[RawDirectionalSchedule],
) -> Dict[int, List[DirectionalSailing]]:
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


def predict_future_delays(
    vessel: Optional[Vessel], sailings: List[DirectionalSailing]
) -> List[DirectionalSailing]:
    if not vessel or not sailings:
        # Fallback to rule-based or zero if no vessel info
        return sailings

    try:
        features = [
            PredictionFeatures(
                speed=vessel.speed or 0.0,
                heading=float(vessel.heading) if vessel.heading is not None else 0.0,
                at_dock=vessel.at_dock,
                scheduled_departure=sailing.scheduled_departure,
                departing_terminal_id=sailing.departing_terminal_id,
                arriving_terminal_id=sailing.arriving_terminal_id
            )
            for sailing in sailings if sailing.scheduled_departure
        ]

        if not features:
            return sailings

        predictions = predict_delay(features)

        # Map predictions back to sailings
        feat_idx = 0
        for sailing in sailings:
            if sailing.scheduled_departure:
                sailing.delay_in_minutes = int(max(0, predictions[feat_idx]))
                feat_idx += 1

        return sailings
    except Exception as e:
        logger.error(f"Error predicting delays with ML model: {e}")
        # Fallback to old behavior if ML fails
        if vessel.delay:
            for sailing in sailings:
                sailing.delay_in_minutes = datetime_to_minutes(vessel.delay)
        return sailings


def get_next_sailings_by_boat(
    schedule_by_boat: Dict[int, List[DirectionalSailing]], route_vessels: List[Vessel]
) -> Dict[int, List[DirectionalSailing]]:
    route_vessels_by_position = {
        vessel.vessel_position_num: vessel for vessel in route_vessels
    }
    next_sailings_by_boat = {}
    for vessel_position_num, sailings in schedule_by_boat.items():
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
            next_sailings = [
                sailing
                for sailing in sailings
                if sailing.scheduled_departure > current_vessel.scheduled_departure
            ]

        next_sailings = predict_future_delays(current_vessel, next_sailings)
        next_sailings_by_boat[vessel_position_num] = next_sailings

    return next_sailings_by_boat


def get_directional_schedules(
    next_sailings_by_boat: Dict[int, List[DirectionalSailing]],
) -> List[DirectionalSchedule]:
    direction_groups = defaultdict(list)

    # Flatten all sailings from all vessels and group by direction
    for vessel_sailings in next_sailings_by_boat.values():
        for sailing in vessel_sailings:
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

    return direction_schedules


def get_next_sailings_for_route(
    vessel_positions, route_config
) -> List[DirectionalSailing]:
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


def get_next_sailings() -> List[RouteSchedule]:
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
