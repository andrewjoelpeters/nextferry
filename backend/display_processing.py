from typing import List
from .serializers import RouteSchedule
from .utils import format_time_until, format_delay_text


def process_routes_for_display(routes_data: List[RouteSchedule]):
    processed_routes = []
    for route in routes_data:
        processed_schedules = []
        
        for schedule in route.schedules:
            processed_sailings = []
            
            # Only show next 3 sailings
            for sailing in schedule.times[:3]:
                time_until, base_status = format_time_until(sailing.scheduled_departure)
                delay_text, delay_status = format_delay_text(sailing.delay_in_minutes)
                
                # Delay status overrides base status if there's a delay
                final_status = delay_status if sailing.delay_in_minutes else base_status
                
                processed_sailings.append({
                    'time_until': time_until,
                    'scheduled_time': sailing.scheduled_departure.strftime('%I:%M %p').lstrip('0') if sailing.scheduled_departure else 'N/A',
                    'delay_text': delay_text,
                    'vessel_name': sailing.vessel_name,
                    'status_class': final_status,
                    'has_delay': sailing.delay_in_minutes is not None and sailing.delay_in_minutes != 0
                })
            
            processed_schedules.append({
                'departing_terminal_name': schedule.departing_terminal_name,
                'arriving_terminal_name': schedule.arriving_terminal_name,
                'sailings': processed_sailings
            })
        
        processed_routes.append({
            'route_name': ' - '.join(route.route_name),
            'schedules': processed_schedules
        })

    return processed_routes
