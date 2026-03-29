import logging
from collections import defaultdict
from datetime import timedelta
from zoneinfo import ZoneInfo

from backend.config import ROUTES

from .database import get_previous_sailing_fullness, get_turnaround_minutes
from .replay import current_time
from .serializers import (
    DirectionalSailing,
    DirectionalSchedule,
    RawDirectionalSchedule,
    RouteSchedule,
    Vessel,
)
from .utils import datetime_to_minutes, minutes_since, minutes_until
from .wsdot_client import get_schedule_today, get_vessel_positions

try:
    from .ml_predictor import predictor as ml_predictor
except ImportError:
    ml_predictor = None

try:
    from .dock_predictor import dock_predictor
except ImportError:
    dock_predictor = None

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
    fallback_reason: str | None = None,
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
    }
    if prediction:
        entry["prediction"] = {
            "delay": prediction["predicted_delay"],
            "lower_bound": prediction["lower_bound"],
            "upper_bound": prediction["upper_bound"],
        }
    else:
        entry["fallback_delay"] = inputs.get("current_vessel_delay_minutes")
        if fallback_reason:
            entry["fallback_reason"] = fallback_reason

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
# Feature construction for ML models
# ---------------------------------------------------------------------------


def _build_en_route_features(
    sailing: DirectionalSailing,
    vessel_id: int | None,
    vessel_speed: float | None,
    delay_minutes: int,
) -> dict | None:
    """Build ML input features for en-route delay prediction.

    Returns None if the sailing's terminal doesn't match a known route.
    """
    route_abbrev = _route_abbrev_for_terminal(sailing.departing_terminal_id)
    if not route_abbrev:
        return None

    sched_iso = sailing.scheduled_departure.isoformat()
    prev_fullness = get_previous_sailing_fullness(
        sailing.departing_terminal_id, sched_iso
    )
    turnaround = (
        get_turnaround_minutes(vessel_id, sched_iso) if vessel_id is not None else None
    )

    return {
        "route_abbrev": route_abbrev,
        "departing_terminal_id": sailing.departing_terminal_id,
        "vessel_id": vessel_id or 0,
        "day_of_week": sailing.scheduled_departure.weekday(),
        "hour_of_day": sailing.scheduled_departure.hour,
        "minutes_until_scheduled_departure": round(
            minutes_until(sailing.scheduled_departure), 1
        ),
        "current_vessel_delay_minutes": delay_minutes,
        "vessel_speed": vessel_speed,
        "previous_sailing_fullness": prev_fullness,
        "turnaround_minutes": turnaround,
    }


def _build_dock_features(
    sailing: DirectionalSailing,
    vessel: Vessel,
    route_abbrev: str,
    mins_at_dock: float,
    delay_minutes: int,
) -> dict:
    """Build ML input features for at-dock delay prediction."""
    incoming_fullness = _get_incoming_fullness(sailing)
    return {
        "route_abbrev": route_abbrev,
        "departing_terminal_id": sailing.departing_terminal_id,
        "vessel_id": vessel.vessel_id,
        "day_of_week": sailing.scheduled_departure.weekday(),
        "hour_of_day": sailing.scheduled_departure.hour,
        "minutes_until_scheduled_departure": round(
            minutes_until(sailing.scheduled_departure), 1
        ),
        "minutes_at_dock": round(mins_at_dock, 1),
        "incoming_vehicle_fullness": (
            round(incoming_fullness, 2) if incoming_fullness is not None else None
        ),
        "current_vessel_delay_minutes": delay_minutes,
    }


def _get_incoming_fullness(sailing: DirectionalSailing) -> float | None:
    """Get fullness of the most recent inbound sailing to this terminal.

    For a vessel at dock at terminal X about to depart to terminal Y,
    the inbound trip arrived FROM Y TO X. get_previous_sailing_fullness
    looks up the most recent sailing arriving at departing_terminal_id,
    which is exactly the inbound trip's load.
    """
    try:
        sched_iso = sailing.scheduled_departure.isoformat()
        return get_previous_sailing_fullness(sailing.departing_terminal_id, sched_iso)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Delay prediction
# ---------------------------------------------------------------------------


def propigate_delays(
    delay: timedelta | None,
    sailings: list[DirectionalSailing],
    vessel_id: int | None = None,
    vessel_speed: float | None = None,
    vessel_name: str | None = None,
) -> list[DirectionalSailing]:
    """Apply delays to sailings, using ML predictions if available, else flat propagation."""
    if not delay and not (ml_predictor and ml_predictor.is_trained):
        return sailings

    delay_minutes = datetime_to_minutes(delay) if delay else 0

    for sailing in sailings:
        if ml_predictor and ml_predictor.is_trained and sailing.scheduled_departure:
            inputs = _build_en_route_features(
                sailing, vessel_id, vessel_speed, delay_minutes
            )
            if inputs:
                prediction = ml_predictor.predict(**inputs)
                if prediction:
                    sailing.delay_in_minutes = round(prediction["predicted_delay"])
                    sailing.delay_lower_bound = round(prediction["lower_bound"])
                    sailing.delay_upper_bound = round(prediction["upper_bound"])
                    _record_prediction(
                        vessel_id,
                        vessel_name,
                        sailing,
                        "en_route_model",
                        inputs,
                        prediction,
                    )
                    continue

        # Fallback: flat propagation
        if delay:
            sailing.delay_in_minutes = delay_minutes
            _record_prediction(
                vessel_id,
                vessel_name,
                sailing,
                "fallback_flat",
                {"current_vessel_delay_minutes": delay_minutes},
                None,
            )

    return sailings


def _apply_dock_prediction(sailing: DirectionalSailing, vessel: Vessel) -> None:
    """Predict departure delay for the current at-dock sailing.

    Two-model architecture:
    - propigate_delays() uses the en-route model for all future sailings
      (trained on vessel-in-motion features like speed and time horizons).
    - This function overrides the FIRST sailing only, using the at-dock model
      (trained on dock-specific features: time at dock, inbound vehicle load,
      and current loading state).

    Falls back to flat delay propagation (vessel's cached delay) if the dock
    model isn't available.
    """
    # Compute minutes_at_dock from vessel.eta (arrival/dock time)
    eta = vessel.eta
    if eta and eta.tzinfo is None:
        eta = eta.replace(tzinfo=ZoneInfo("America/Los_Angeles"))
    mins_at_dock = minutes_since(eta) if eta else 0.0

    delay_minutes = datetime_to_minutes(vessel.delay) if vessel.delay else 0
    route_abbrev = _route_abbrev_for_terminal(sailing.departing_terminal_id)

    if dock_predictor and dock_predictor.is_trained and route_abbrev:
        inputs = _build_dock_features(
            sailing, vessel, route_abbrev, mins_at_dock, delay_minutes
        )
        prediction = dock_predictor.predict(**inputs)
        if prediction:
            sailing.delay_in_minutes = round(prediction["predicted_delay"])
            sailing.delay_lower_bound = round(prediction["lower_bound"])
            sailing.delay_upper_bound = round(prediction["upper_bound"])
            _record_prediction(
                vessel.vessel_id,
                vessel.vessel_name,
                sailing,
                "dock_model",
                inputs,
                prediction,
            )
            return

    # Fallback: use the vessel's actual cached delay (flat propagation)
    _record_prediction(
        vessel_id=vessel.vessel_id,
        vessel_name=vessel.vessel_name,
        sailing=sailing,
        source="fallback_flat",
        inputs={
            "current_vessel_delay_minutes": delay_minutes if vessel.delay else None
        },
        prediction=None,
        fallback_reason=(
            "model not trained"
            if not (dock_predictor and dock_predictor.is_trained)
            else "no route match"
            if not route_abbrev
            else "prediction returned None"
        ),
    )
    if vessel.delay:
        sailing.delay_in_minutes = delay_minutes
        sailing.delay_lower_bound = None
        sailing.delay_upper_bound = None


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

        # When the vessel is at dock, hold back the first sailing from the
        # en-route model — it will be handled by the dock predictor below.
        first_held_back = None
        if (
            vessel
            and vessel.at_dock
            and next_sailings
            and next_sailings[0].scheduled_departure
        ):
            first_held_back = next_sailings[0]
            remaining = next_sailings[1:]
        else:
            remaining = next_sailings

        remaining = propigate_delays(
            vessel.delay if vessel else None,
            remaining,
            vessel_id=vessel.vessel_id if vessel else None,
            vessel_speed=vessel.speed if vessel else None,
            vessel_name=vessel.vessel_name if vessel else None,
        )

        next_sailings = (
            [first_held_back] + remaining if first_held_back is not None else remaining
        )

        # Annotate first sailing with live vessel state + dock prediction
        if next_sailings and vessel:
            _annotate_with_vessel_state(next_sailings[0], vessel)
            if vessel.at_dock and next_sailings[0].scheduled_departure:
                _apply_dock_prediction(next_sailings[0], vessel)

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
