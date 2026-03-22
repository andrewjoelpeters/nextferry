from datetime import timedelta
from typing import List

from .serializers import RouteSchedule
from .utils import format_confidence_text, format_delay_text, format_time_until


def _format_vessel_status(sailing) -> dict:
    """Build display info for the vessel's live status on the current sailing."""
    if sailing.vessel_at_dock is None:
        return {}

    fmt_time = lambda dt: dt.strftime("%I:%M %p").lstrip("0") if dt else None

    if sailing.vessel_at_dock:
        # Vessel is at dock — show docked time and predicted departure
        result = {"vessel_status": "At Dock"}
        if sailing.vessel_eta:
            result["docked_at"] = fmt_time(sailing.vessel_eta)
        if sailing.scheduled_departure and sailing.vessel_delay_minutes:
            predicted = sailing.scheduled_departure + timedelta(
                minutes=sailing.vessel_delay_minutes
            )
            result["predicted_departure"] = fmt_time(predicted)
        return result
    else:
        # Vessel is in transit — show departure time and delay
        result = {"vessel_status": "In Transit"}
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


def process_routes_for_display(routes_data: List[RouteSchedule]):
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

                # Delay info
                delay_text, delay_status = format_delay_text(sailing.delay_in_minutes)

                # Final status prioritizes delay status if there is a delay
                final_status = delay_status if sailing.delay_in_minutes else base_status

                # Confidence interval text
                confidence_text = format_confidence_text(
                    sailing.delay_lower_bound, sailing.delay_upper_bound
                )

                sailing_data = {
                    "time_until": time_until,
                    "scheduled_time": (
                        sailing.scheduled_departure.strftime("%I:%M %p").lstrip("0")
                        if sailing.scheduled_departure
                        else "N/A"
                    ),
                    "estimated_departure": (
                        estimated_departure.strftime("%I:%M %p").lstrip("0")
                        if estimated_departure
                        else "N/A"
                    ),
                    "delay_text": delay_text,
                    "confidence_text": confidence_text,
                    "vessel_name": sailing.vessel_name,
                    "status_class": final_status,
                    "departed": sailing.departed,
                    "has_delay": sailing.delay_in_minutes is not None
                    and sailing.delay_in_minutes != 0,
                    "vessel_info": _format_vessel_status(sailing),
                    "departing_terminal_name": schedule.departing_terminal_name,
                    "scheduled_departure_iso": (
                        sailing.scheduled_departure.isoformat()
                        if sailing.scheduled_departure
                        else ""
                    ),
                }

                processed_sailings.append(sailing_data)

            processed_schedules.append(
                {
                    "departing_terminal_name": schedule.departing_terminal_name,
                    "arriving_terminal_name": schedule.arriving_terminal_name,
                    "sailings": processed_sailings,
                }
            )

        processed_routes.append(
            {
                "route_name": " - ".join(route.route_name),
                "schedules": processed_schedules,
            }
        )

    return processed_routes
