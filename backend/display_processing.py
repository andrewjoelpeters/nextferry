from datetime import timedelta
from typing import List

from .serializers import RouteSchedule
from .utils import format_confidence_text, format_delay_text, format_time_until


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

                processed_sailings.append(
                    {
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
                    }
                )

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
