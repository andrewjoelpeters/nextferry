from typing import List, Dict, Optional
from .serializers import RawDirectionalSchedule, RouteSchedule, Vessel, DirectionalSailing, DirectionalSchedule
from .wsdot_client import get_schedule_today, get_vessel_positions
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
import logging


#TODO: IMPLEMENT SCHEDULE CACHING

ROUTES = [{
    "name": "Seattle - Bainbridge",
    "terminals": [3, 7],
    "route_id": 5,
    "route_name": "sea-bi"
}]

CACHED_DELAYS = {}

def update_cached_delay(vessel: Vessel, delay: datetime):
    for route in vessel.route_name:
        if route not in CACHED_DELAYS:
            CACHED_DELAYS[route] = {}
        CACHED_DELAYS[route][vessel.vessel_position_num] = delay
        
        
def get_cached_delay(vessel: Vessel) -> Optional[datetime]:
    route = vessel.route_name[0]
    if route in CACHED_DELAYS:
        return CACHED_DELAYS[route].get(vessel.vessel_position_num, None)
    

def get_vessels_with_delays():
    vessel_positions = get_vessel_positions()
    for v in vessel_positions:
        vessel_delay = v.left_dock - v.scheduled_departure if v.scheduled_departure and v.left_dock else None
        if vessel_delay:
            update_cached_delay(v, vessel_delay)
        else:
            vessel_delay = get_cached_delay(v)
        v.delay = vessel_delay
    return vessel_positions
            

def get_route_vessels(vessel_positions: List[Vessel], route_config):
    return [v for v in vessel_positions if route_config['route_name'] in v.route_name]
    
def get_route_schedule_by_boat(schedules: List[RawDirectionalSchedule]) -> Dict[int, List[DirectionalSailing]]:
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

def get_next_sailings_by_boat(schedule_by_boat: Dict[int, List[DirectionalSailing]], route_vessels: List[Vessel]) -> Dict[int, List[DirectionalSailing]]:
    route_vessels_by_position = {
        vessel.vessel_position_num: vessel for vessel in route_vessels
    }
    next_sailings_by_boat = {}
    for vessel_position_num, sailings in schedule_by_boat.items():
        # if this vessel_position_num isn't in route_vessels:
        # next sailings are all sailings with this vessel position num and a scheduled departure greater than right now
        current_vessel = route_vessels_by_position.get(vessel_position_num)
        if not current_vessel:
            next_sailings = [sailing for sailing in sailings if sailing.scheduled_departure > datetime.now(tz=ZoneInfo("America/Los_Angeles"))]
        elif current_vessel.at_dock:
            next_sailings = [sailing for sailing in sailings if sailing.scheduled_departure >= current_vessel.scheduled_departure]
        elif not current_vessel.at_dock:
            next_sailings = [sailing for sailing in sailings if sailing.scheduled_departure > current_vessel.scheduled_departure]
        
        next_sailings_by_boat[vessel_position_num] = next_sailings
    
    return next_sailings_by_boat


def get_directional_schedules(next_sailings_by_boat: Dict[int, List[DirectionalSailing]]) -> List[DirectionalSchedule]:
    direction_groups = defaultdict(list)

    # Flatten all sailings from all vessels and group by direction
    for vessel_sailings in next_sailings_by_boat.values():
        for sailing in vessel_sailings:
            # direction_key = (sailing.departing_terminal_id, sailing.arriving_terminal_id)
            direction_meta = (sailing.departing_terminal_id, sailing.departing_terminal_name, sailing.arriving_terminal_id, sailing.arriving_terminal_name)
            direction_groups[direction_meta].append(sailing)
            
    direction_schedules = []
    for direction_meta, sailings in direction_groups.items():
        departing_id, departing_name, arriving_id, arriving_name = direction_meta
        direction_schedules.append(DirectionalSchedule(
            departing_terminal_id=departing_id,
            departing_terminal_name=departing_name,
            arriving_terminal_id=arriving_id,
            arriving_terminal_name=arriving_name,
            times=sorted([sailing.to_route_sailing() for sailing in sailings], key=lambda x: x.scheduled_departure)
        ))
        
    return direction_schedules


def get_next_sailings_for_route(vessel_positions, route_config):
    route_schedule = get_schedule_today(route_config["route_id"])
    route_vessels = get_route_vessels(vessel_positions, route_config)
    schedule_by_boat = get_route_schedule_by_boat(route_schedule)
    next_sailings_by_boat = get_next_sailings_by_boat(schedule_by_boat, route_vessels)
    return get_directional_schedules(next_sailings_by_boat)
    

def get_next_sailings():
    vessel_positions = get_vessels_with_delays()
    all_next_sailings = []
    for route in ROUTES:
        next_sailings = get_next_sailings_for_route(vessel_positions, route)
        all_next_sailings.append(RouteSchedule(
            route_name=[route.get("route_name")],
            route_id=route.get("route_id"),
            schedules=next_sailings
        ))
    
    return all_next_sailings
