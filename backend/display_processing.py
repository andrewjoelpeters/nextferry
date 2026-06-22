import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

from .config import ROUTES
from .database import get_departed_sailing_space
from .fill_predictor import fill_predictor
from .replay import current_time
from .serializers import RouteSchedule
from .utils import format_delay_text, format_time_until

logger = logging.getLogger(__name__)


def _get_route_abbrev(departing_terminal_id: int) -> str:
    """Look up route abbreviation from departing terminal ID."""
    for route in ROUTES:
        if departing_terminal_id in route["terminals"]:
            return route["route_name"]
    return "unknown"


def _build_vessel_detail_lines(
    vessel_info: dict,
    departing_terminal_name: str,
    arriving_terminal_name: str,
    departed: bool,
) -> list[dict]:
    """Build pre-formatted detail lines for the outbound vessel's live status.

    Returns a list of dicts with keys:
      - ``text``: the display string
      - ``css_class``: optional extra CSS class(es) for the span (empty string = none)
    """
    lines: list[dict] = []
    if not vessel_info:
        return lines

    key = vessel_info.get("vessel_status_key")

    if key == "at_dock":
        docked_at = vessel_info.get("docked_at")
        docked_duration = vessel_info.get("docked_duration")
        predicted_departure = vessel_info.get("predicted_departure")
        overdue = vessel_info.get("overdue")
        minutes_overdue = vessel_info.get("minutes_overdue")

        if overdue:
            # Show dock time without expected departure, then two overdue lines
            if docked_at:
                dock_str = f"Docked at {docked_at}"
                if docked_duration:
                    dock_str += f" ({docked_duration})"
            else:
                dock_str = "Docked"
            lines.append({"text": dock_str, "css_class": ""})
            if predicted_departure:
                lines.append(
                    {
                        "text": f"Predicted departure: {predicted_departure}",
                        "css_class": "detail-overdue",
                    }
                )
            lines.append(
                {
                    "text": f"Expected to depart {minutes_overdue}m ago — status uncertain",
                    "css_class": "overdue-alert",
                }
            )
        else:
            if docked_at:
                dock_str = f"Docked at {docked_at}"
                if docked_duration:
                    dock_str += f" ({docked_duration})"
            else:
                dock_str = "Docked"
            if predicted_departure:
                dock_str += f", expected to depart {departing_terminal_name} at {predicted_departure}"
            lines.append({"text": dock_str, "css_class": ""})

    elif key == "en_route":
        left_dock = vessel_info.get("left_dock")
        departure_delay = vessel_info.get("departure_delay")

        if left_dock:
            # Departed sailings left from the departing terminal; upcoming sailings
            # have the vessel crossing from the arriving terminal toward us.
            other_terminal = (
                departing_terminal_name if departed else arriving_terminal_name
            )
            line = f"Left {other_terminal}: {left_dock}"
            if departure_delay:
                line += f" ({departure_delay})"
            lines.append({"text": line, "css_class": ""})

    return lines


def _build_inbound_detail_lines(
    sailing,
    departing_terminal_name: str,
    estimated_departure: str,
    departed: bool,
) -> list[dict]:
    """Build pre-formatted detail lines for the inbound vessel's live status.

    Uses ``sailing.inbound_prediction_trace`` (built by ``next_sailings.py``) so
    the (est.) / official-ETA distinction is handled by the trace, not here.

    Returns a list of dicts with keys:
      - ``text``: the display string
      - ``css_class``: optional extra CSS class(es) for the span (empty string = none)
    """
    lines: list[dict] = []
    if not sailing.inbound_vessel_name:
        return lines

    def fmt(dt):
        return dt.strftime("%I:%M %p").lstrip("0") if dt else None

    from_terminal = sailing.inbound_vessel_from_terminal or ""
    vessel_name = sailing.inbound_vessel_name

    if sailing.inbound_vessel_at_dock:
        # Line 1: vessel is docked at the other terminal with its predicted departure
        dep_str = None
        if sailing.inbound_vessel_scheduled_departure:
            delay_mins = sailing.inbound_vessel_delay_minutes or 0
            dep_str = fmt(
                sailing.inbound_vessel_scheduled_departure
                + timedelta(minutes=delay_mins)
            )
        line1 = f"Currently docked at {from_terminal}"
        if dep_str:
            line1 += f", expected departure {dep_str}"
        lines.append({"text": line1, "css_class": ""})

        # Line 2: bridge through to the departure the user cares about.
        # inbound_prediction_trace.explanation already encodes "(est.)" vs official
        # ETA via arrival_source, so no branching is needed here.
        if sailing.inbound_prediction_trace and not departed:
            lines.append(
                {
                    "text": sailing.inbound_prediction_trace.explanation,
                    "css_class": "",
                }
            )
        elif not departed:
            lines.append(
                {
                    "text": f"Expected departure from {departing_terminal_name} at {estimated_departure}",
                    "css_class": "",
                }
            )
    else:
        # En-route: single line with vessel name, departure, and ETA
        line = f"{vessel_name} left {from_terminal}"
        left_dock_str = fmt(sailing.inbound_vessel_left_dock)
        if left_dock_str:
            line += f" at {left_dock_str}"

        # Use predicted_arrival from the trace (EtaBoundedTrace) when available;
        # the trace also carries the authoritative terminal name.
        trace = sailing.inbound_prediction_trace
        if trace and hasattr(trace, "predicted_arrival"):
            eta_str = fmt(trace.predicted_arrival)
            arriving = trace.arriving_terminal_name
        else:
            eta_str = fmt(sailing.inbound_vessel_eta)
            arriving = departing_terminal_name
        if eta_str:
            line += f", arriving {arriving} ~{eta_str}"

        lines.append({"text": line, "css_class": ""})

    return lines


def _format_vessel_status(sailing) -> dict:
    """Build display info for the vessel's live status on the current sailing."""
    if sailing.vessel_at_dock is None:
        return {}

    def fmt_time(dt):
        return dt.strftime("%I:%M %p").lstrip("0") if dt else None

    if sailing.vessel_at_dock:
        # Vessel is at dock — boarding/unloading
        result = {"vessel_status": "At Dock", "vessel_status_key": "at_dock"}
        # Use WSDOT eta (precise arrival time) if available,
        # fall back to DB snapshot docked_since (within 30s accuracy)
        dock_time = sailing.vessel_eta or sailing.vessel_docked_since
        if dock_time:
            result["docked_at"] = fmt_time(dock_time)
            now = current_time()
            if dock_time.tzinfo is None:
                dock_time = dock_time.replace(tzinfo=ZoneInfo("America/Los_Angeles"))
            minutes_docked = int((now - dock_time).total_seconds() / 60)
            if minutes_docked >= 0:
                if minutes_docked < 60:
                    result["docked_duration"] = f"{minutes_docked}m"
                else:
                    hours = minutes_docked // 60
                    mins = minutes_docked % 60
                    result["docked_duration"] = f"{hours}h {mins}m"
        delay = (
            sailing.delay_in_minutes
            if sailing.delay_in_minutes
            else sailing.vessel_delay_minutes
        )
        if sailing.scheduled_departure:
            if delay:
                predicted = sailing.scheduled_departure + timedelta(minutes=delay)
                result["predicted_departure"] = fmt_time(predicted)
                # Check if vessel is overdue (10+ min past predicted departure)
                now = current_time()
                if predicted.tzinfo is None:
                    predicted = predicted.replace(
                        tzinfo=ZoneInfo("America/Los_Angeles")
                    )
                minutes_overdue = int((now - predicted).total_seconds() / 60)
                if minutes_overdue >= 10:
                    result["overdue"] = True
                    result["minutes_overdue"] = minutes_overdue
            else:
                # No delay info — show scheduled departure as expected time
                result["predicted_departure"] = fmt_time(sailing.scheduled_departure)
        return result
    else:
        # Vessel is en route — crossing toward this terminal
        status_text = "En route"
        if sailing.vessel_eta:
            status_text = f"En route · arrives ~{fmt_time(sailing.vessel_eta)}"
        result = {
            "vessel_status": status_text,
            "vessel_status_key": "en_route",
        }
        if sailing.vessel_left_dock:
            result["left_dock"] = fmt_time(sailing.vessel_left_dock)
        if sailing.vessel_delay_minutes is not None:
            dm = sailing.vessel_delay_minutes
            if dm > 0:
                result["departure_delay"] = f"+{dm}m late"
            elif dm < 0:
                result["departure_delay"] = f"{dm}m early"
            else:
                result["departure_delay"] = "on time"
        if sailing.vessel_eta:
            result["eta"] = fmt_time(sailing.vessel_eta)
        return result


def process_routes_for_display(
    routes_data: list[RouteSchedule],
    space_lookup: dict[tuple[int, str], dict] | None = None,
):
    processed_routes = []
    for route in routes_data:
        processed_schedules = []

        for schedule in route.schedules:
            processed_sailings = []

            # Show departed sailings + next 3 upcoming
            departed = [s for s in schedule.times if s.departed]
            upcoming = [s for s in schedule.times if not s.departed][:3]
            visible_sailings = departed + upcoming

            for sailing in visible_sailings:
                # Calculate estimated departure
                estimated_departure = None
                if sailing.scheduled_departure:
                    estimated_departure = sailing.scheduled_departure
                    if sailing.delay_in_minutes:
                        estimated_departure += timedelta(
                            minutes=sailing.delay_in_minutes
                        )

                # Use estimated departure for time_until
                time_until, base_status = format_time_until(
                    estimated_departure, departed=sailing.departed
                )

                # When vessel is at dock but scheduled/estimated time has passed,
                # don't show "Departed" — the vessel hasn't left yet
                if (
                    sailing.vessel_at_dock
                    and not sailing.departed
                    and base_status == "status-departed"
                ):
                    time_until = "Loading"
                    base_status = "status-delayed"

                # Delay info
                delay_text, delay_status = format_delay_text(sailing.delay_in_minutes)

                # Final status prioritizes delay status if there is a delay
                final_status = delay_status if sailing.delay_in_minutes else base_status

                # Look up drive-up capacity
                capacity = None
                if sailing.departed and sailing.scheduled_departure:
                    # For departed sailings, get actual space from DB snapshots
                    departure_iso = sailing.scheduled_departure.isoformat()
                    space_info = get_departed_sailing_space(
                        schedule.departing_terminal_id, departure_iso
                    )
                    if space_info and space_info["max_space_count"] > 0:
                        cars_on_board = max(
                            0,
                            min(
                                space_info["max_space_count"],
                                space_info["max_space_count"]
                                - space_info["drive_up_space_count"],
                            ),
                        )
                        pct = max(
                            0,
                            min(
                                100,
                                int(
                                    cars_on_board / space_info["max_space_count"] * 100
                                ),
                            ),
                        )
                        capacity = {
                            "spaces": space_info["drive_up_space_count"],
                            "total": space_info["max_space_count"],
                            "cars_on_board": cars_on_board,
                            "percent": pct,
                        }
                elif space_lookup and sailing.scheduled_departure:
                    time_key = sailing.scheduled_departure.strftime("%Y-%m-%d %H:%M")
                    space_info = space_lookup.get(
                        (schedule.departing_terminal_id, time_key)
                    )
                    if space_info and space_info["max_space_count"] > 0:
                        fill_pct = max(
                            0,
                            min(
                                100,
                                int(
                                    (
                                        space_info["max_space_count"]
                                        - space_info["drive_up_space_count"]
                                    )
                                    / space_info["max_space_count"]
                                    * 100
                                ),
                            ),
                        )
                        capacity = {
                            "spaces": space_info["drive_up_space_count"],
                            "total": space_info["max_space_count"],
                            "percent": fill_pct,
                        }

                # Fill risk prediction (skip for departed sailings — show actual data instead)
                fill_risk = None
                if (
                    not sailing.departed
                    and fill_predictor.is_trained
                    and sailing.scheduled_departure
                ):
                    try:
                        fill_risk = fill_predictor.predict(
                            route_abbrev=_get_route_abbrev(
                                schedule.departing_terminal_id
                            ),
                            departing_terminal_id=schedule.departing_terminal_id,
                            day_of_week=sailing.scheduled_departure.weekday(),
                            hour_of_day=sailing.scheduled_departure.hour,
                        )
                    except Exception as e:
                        logger.debug(f"Fill risk prediction failed: {e}")

                # Build display_time: arrow notation for delays
                scheduled_time_str = (
                    sailing.scheduled_departure.strftime("%I:%M %p").lstrip("0")
                    if sailing.scheduled_departure
                    else "N/A"
                )
                estimated_time_str = (
                    estimated_departure.strftime("%I:%M %p").lstrip("0")
                    if estimated_departure
                    else "N/A"
                )
                has_delay = (
                    sailing.delay_in_minutes is not None
                    and sailing.delay_in_minutes != 0
                )
                delay_minutes = sailing.delay_in_minutes or 0
                if has_delay:
                    display_time = f"{scheduled_time_str} → {estimated_time_str}"
                    # HTML version with styled spans for scheduled (faded) vs estimated (bold)
                    display_time_html = (
                        f'<span class="scheduled-part">{scheduled_time_str}</span>'
                        f' <span class="arrow-part">→</span> '
                        f'<span class="estimated-part">{estimated_time_str}</span>'
                    )
                else:
                    display_time = scheduled_time_str
                    display_time_html = scheduled_time_str

                vessel_info = _format_vessel_status(sailing)
                vessel_detail_lines = _build_vessel_detail_lines(
                    vessel_info,
                    schedule.departing_terminal_name,
                    schedule.arriving_terminal_name,
                    sailing.departed,
                )
                inbound_detail_lines = _build_inbound_detail_lines(
                    sailing,
                    schedule.departing_terminal_name,
                    estimated_time_str,
                    sailing.departed,
                )

                sailing_data = {
                    "time_until": time_until,
                    "scheduled_time": scheduled_time_str,
                    "estimated_departure": estimated_time_str,
                    "display_time": display_time,
                    "display_time_html": display_time_html,
                    "delay_minutes": delay_minutes,
                    "delay_text": delay_text,
                    "vessel_name": sailing.vessel_name,
                    "status_class": final_status,
                    "departed": sailing.departed,
                    "has_delay": has_delay,
                    "vessel_info": vessel_info,
                    "vessel_detail_lines": vessel_detail_lines,
                    "inbound_detail_lines": inbound_detail_lines,
                    "capacity": capacity,
                    "departing_terminal_name": schedule.departing_terminal_name,
                    "scheduled_departure_iso": (
                        sailing.scheduled_departure.isoformat()
                        if sailing.scheduled_departure
                        else ""
                    ),
                    "fill_risk": fill_risk,
                }

                processed_sailings.append(sailing_data)

            processed_schedules.append(
                {
                    "departing_terminal_name": schedule.departing_terminal_name,
                    "arriving_terminal_name": schedule.arriving_terminal_name,
                    "direction_header": f"{schedule.departing_terminal_name} → {schedule.arriving_terminal_name}",
                    "sailings": processed_sailings,
                }
            )

        # Sort schedules so western terminals (left button) come first,
        # eastern terminals (right button) come second.
        EAST_TERMINALS = {"Seattle", "Edmonds"}
        processed_schedules.sort(
            key=lambda s: s["departing_terminal_name"] in EAST_TERMINALS
        )

        processed_routes.append(
            {
                "route_name": " - ".join(route.route_name),
                "schedules": processed_schedules,
            }
        )

    return processed_routes
