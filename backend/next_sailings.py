import logging
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.config import ROUTES

from .database import get_docked_since
from .replay import current_time
from .serializers import (
    DirectionalSailing,
    DirectionalSchedule,
    RawDirectionalSchedule,
    RouteSchedule,
    Vessel,
)
from .utils import datetime_to_minutes, minutes_since
from .wsdot_client import get_schedule_today, get_vessel_positions

logger = logging.getLogger(__name__)


CACHED_DELAYS = {}

# Stores the most recent prediction for every sailing across all vessels.
# Keyed by vessel_id → list of sailing predictions (first = current/next).
# Overwritten each cache cycle (~30s).
_last_predictions: dict[int, list[dict]] = {}


def get_last_predictions() -> dict[int, list[dict]]:
    return _last_predictions


def _record_prediction(
    vessel_id: int | None,
    vessel_name: str | None,
    sailing: DirectionalSailing,
    source: str,
    inputs: dict,
    prediction: dict | None,
) -> None:
    """Record a prediction for the debug endpoint."""
    if vessel_id is None:
        return
    entry = {
        "scheduled_departure": sailing.scheduled_departure.isoformat(),
        "departing": sailing.departing_terminal_name,
        "arriving": sailing.arriving_terminal_name,
        "source": source,
        "inputs": inputs,
        "delay": sailing.delay_in_minutes,
    }

    if vessel_id not in _last_predictions:
        _last_predictions[vessel_id] = {
            "vessel_id": vessel_id,
            "vessel_name": vessel_name,
            "sailings": [],
        }
    _last_predictions[vessel_id]["sailings"].append(entry)


# ---------------------------------------------------------------------------
# Delay caching
# ---------------------------------------------------------------------------


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

        # If vessel is at dock and past scheduled departure, compute real-time delay
        if v.at_dock and v.scheduled_departure and not v.left_dock:
            now = current_time()
            if v.scheduled_departure.tzinfo is None:
                sched = v.scheduled_departure.replace(
                    tzinfo=ZoneInfo("America/Los_Angeles")
                )
            else:
                sched = v.scheduled_departure
            minutes_past = (now - sched).total_seconds() / 60
            if minutes_past > 0:
                overdue_delay = timedelta(minutes=minutes_past)
                if vessel_delay is None or overdue_delay > vessel_delay:
                    vessel_delay = overdue_delay

        v.delay = vessel_delay
    return vessel_positions


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _route_abbrev_for_terminal(terminal_id: int) -> str | None:
    """Look up route abbreviation by departing terminal ID."""
    for route in ROUTES:
        if terminal_id in route["terminals"]:
            return route["route_name"]
    return None


# ---------------------------------------------------------------------------
# Schedule grouping
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Delay prediction
# ---------------------------------------------------------------------------

# Turnaround time bounds (minutes) from experiments 27-34
_TURNAROUND_FLOOR = {"sea-bi": 9.3, "ed-king": 14.8}  # p10: fastest 10%
_TURNAROUND_CEILING = {"sea-bi": 22.0, "ed-king": 26.0}  # p75
_CEILING_THRESHOLD = 4  # boats recover from ≤4 min delays


def predict_eta_bounded_delay(
    current_delay_minutes: float,
    eta: datetime,
    scheduled_departure: datetime,
    route_abbrev: str,
) -> float | None:
    """Predict next-sailing delay using ETA + turnaround bounds.

    Floor: earliest departure = ETA + fastest turnaround (p10).
    Ceiling (delay > 4 min): cap at ETA + slow turnaround (p75).
    Returns None for unknown routes (caller falls back to flat).
    """
    p10 = _TURNAROUND_FLOOR.get(route_abbrev)
    p75 = _TURNAROUND_CEILING.get(route_abbrev)
    if p10 is None or p75 is None:
        return None

    eta_floor = max(
        0.0,
        (eta + timedelta(minutes=p10) - scheduled_departure).total_seconds() / 60,
    )
    if current_delay_minutes > _CEILING_THRESHOLD:
        eta_ceiling = max(
            0.0,
            (eta + timedelta(minutes=p75) - scheduled_departure).total_seconds() / 60,
        )
        return round(max(eta_floor, min(current_delay_minutes, eta_ceiling)))
    return round(max(current_delay_minutes, eta_floor))


def propigate_delays(
    delay: timedelta | None,
    sailings: list[DirectionalSailing],
    vessel_id: int | None = None,
    vessel_name: str | None = None,
) -> list[DirectionalSailing]:
    """Apply flat delay propagation to all sailings."""
    if not delay:
        return sailings

    delay_minutes = datetime_to_minutes(delay)

    for sailing in sailings:
        sailing.delay_in_minutes = delay_minutes
        _record_prediction(
            vessel_id,
            vessel_name,
            sailing,
            "flat_propagation",
            {"current_vessel_delay_minutes": delay_minutes},
            None,
        )

    return sailings


# ---------------------------------------------------------------------------
# Sailing selection & vessel state annotation
# ---------------------------------------------------------------------------


def _filter_next_sailings(
    sailings: list[DirectionalSailing],
    vessel: Vessel | None,
) -> list[DirectionalSailing]:
    """Select upcoming sailings based on vessel state.

    - No vessel data or no scheduled departure: all future sailings.
    - At dock: current sailing (by scheduled departure) and later.
    - En route: just-departed sailing (if within 30 min) plus future sailings.
    """
    now = current_time()

    if not vessel or not vessel.scheduled_departure:
        return [s for s in sailings if s.scheduled_departure > now]

    if vessel.at_dock:
        return [
            s for s in sailings if s.scheduled_departure >= vessel.scheduled_departure
        ]

    # En route: include the just-departed sailing so users can see it's in transit
    future = [s for s in sailings if s.scheduled_departure > vessel.scheduled_departure]
    for s in sailings:
        if s.scheduled_departure == vessel.scheduled_departure:
            if minutes_since(s.scheduled_departure) <= 30:
                departed = s.model_copy()
                departed.departed = True
                future.insert(0, departed)
            break

    return future


def _annotate_with_vessel_state(
    sailing: DirectionalSailing,
    vessel: Vessel,
) -> None:
    """Attach live vessel state to the first sailing.

    Only annotates if the vessel's direction matches this sailing's direction.
    At-dock vessels always match; en-route vessels must be heading toward this
    sailing's departing terminal (guards against the WSDOT null-field edge case
    where a vessel reports no direction data).
    """
    direction_matches = (
        vessel.at_dock or sailing.departing_terminal_id == vessel.departing_terminal_id
    )
    if not direction_matches:
        return

    sailing.vessel_at_dock = vessel.at_dock
    sailing.vessel_left_dock = vessel.left_dock
    sailing.vessel_eta = vessel.eta
    if vessel.at_dock and vessel.eta is None and vessel.scheduled_departure:
        docked_since = get_docked_since(
            vessel.vessel_id, vessel.scheduled_departure.isoformat()
        )
        if docked_since:
            sailing.vessel_docked_since = docked_since
    if vessel.delay:
        sailing.vessel_delay_minutes = datetime_to_minutes(vessel.delay)


# ---------------------------------------------------------------------------
# Core orchestration
# ---------------------------------------------------------------------------


def get_next_sailings_by_boat(
    schedule_by_boat: dict[int, list[DirectionalSailing]], route_vessels: list[Vessel]
) -> dict[int, list[DirectionalSailing]]:
    vessels_by_position = {v.vessel_position_num: v for v in route_vessels}
    result = {}

    for position_num, sailings in schedule_by_boat.items():
        vessel = vessels_by_position.get(position_num)
        next_sailings = _filter_next_sailings(sailings, vessel)

        # Step 1: flat-propagate current delay to all sailings
        next_sailings = propigate_delays(
            vessel.delay if vessel else None,
            next_sailings,
            vessel_id=vessel.vessel_id if vessel else None,
            vessel_name=vessel.vessel_name if vessel else None,
        )

        # Annotate first sailing with live vessel state
        if next_sailings and vessel:
            _annotate_with_vessel_state(next_sailings[0], vessel)

        # Step 2: ETA-bounded override for first opposite-terminal sailing
        # Only fires when vessel is en-route with an ETA
        if vessel and not vessel.at_dock and vessel.eta and vessel.delay:
            delay_minutes = datetime_to_minutes(vessel.delay)
            for i, s in enumerate(next_sailings):
                if (
                    not s.departed
                    and s.departing_terminal_id != vessel.departing_terminal_id
                    and s.scheduled_departure
                ):
                    route_abbrev = _route_abbrev_for_terminal(s.departing_terminal_id)
                    if route_abbrev:
                        bounded = predict_eta_bounded_delay(
                            delay_minutes,
                            vessel.eta,
                            s.scheduled_departure,
                            route_abbrev,
                        )
                        if bounded is not None:
                            s.delay_in_minutes = bounded
                            _record_prediction(
                                vessel.vessel_id,
                                vessel.vessel_name,
                                s,
                                "eta_bounded",
                                {
                                    "current_vessel_delay_minutes": delay_minutes,
                                    "vessel_eta": vessel.eta.isoformat(),
                                    "scheduled_departure": s.scheduled_departure.isoformat(),
                                    "route_abbrev": route_abbrev,
                                },
                                None,
                            )
                            # Re-propagate the improved prediction to later sailings
                            for later in next_sailings[i + 1 :]:
                                later.delay_in_minutes = bounded
                                _record_prediction(
                                    vessel.vessel_id,
                                    vessel.vessel_name,
                                    later,
                                    "flat_propagation",
                                    {"current_vessel_delay_minutes": bounded},
                                    None,
                                )
                    break

        # Annotate the first opposite-direction sailing with info about the
        # immediately preceding sailing (the vessel heading toward that terminal).
        # Works for both at-dock (waiting to depart) and en-route (crossing).
        if vessel:
            # Find the vessel's own first sailing to get its predicted delay
            vessel_first_delay = None
            if next_sailings and next_sailings[0].delay_in_minutes is not None:
                first = next_sailings[0]
                if first.departing_terminal_id == vessel.departing_terminal_id:
                    vessel_first_delay = first.delay_in_minutes

            for s in next_sailings:
                if (
                    not s.departed
                    and s.departing_terminal_id != vessel.departing_terminal_id
                ):
                    s.inbound_vessel_name = vessel.vessel_name
                    s.inbound_vessel_at_dock = vessel.at_dock
                    s.inbound_vessel_from_terminal = vessel.departing_terminal_name
                    if vessel.at_dock:
                        s.inbound_vessel_scheduled_departure = (
                            vessel.scheduled_departure
                        )
                        s.inbound_vessel_delay_minutes = vessel_first_delay
                    else:
                        s.inbound_vessel_left_dock = vessel.left_dock
                        s.inbound_vessel_eta = vessel.eta
                    break

        result[position_num] = next_sailings

    return result


def get_directional_schedules(
    next_sailings_by_boat: dict[int, list[DirectionalSailing]],
) -> list[DirectionalSchedule]:
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
    _last_predictions.clear()
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
