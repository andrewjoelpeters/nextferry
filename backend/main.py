from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from .next_sailings import get_next_sailings
from .serializers import RouteSchedule
from .utils import format_time_until, format_delay_text
from typing import List
from datetime import datetime


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/next-sailings", response_class=HTMLResponse)
async def get_next_sailings_html(request: Request):
    """Return HTML fragment for next sailings - this is what HTMX will call"""
    try:
        routes_data = get_next_sailings()
        
        # Process the data for display
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
        
        return templates.TemplateResponse(
            "next_sailings_fragment.html", 
            {
                "request": request, 
                "routes": processed_routes,
                "last_updated": datetime.now().strftime('%I:%M:%S %p').lstrip('0')
            }
        )
    
    except Exception as e:
        # Return error fragment
        return templates.TemplateResponse(
            "error_fragment.html", 
            {"request": request, "error": str(e)}
        )
