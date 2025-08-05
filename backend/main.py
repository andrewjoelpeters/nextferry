from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from .wsdot_client import get_vessel_positions
from .next_sailings import get_next_sailings, CACHED_DELAYS
from .display_processing import process_routes_for_display
from datetime import datetime
import logging


logger = logging.getLogger(__name__)

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
    logger.info("Attempting to get next sailings")
    try:
        routes_data = get_next_sailings()
        logger.info(f"Got Next Sailings for {len(routes_data)} routes")
        processed_routes = process_routes_for_display(routes_data)
        logger.info(f"Processed Routes for display for {len(routes_data)} routes")

        return templates.TemplateResponse(
            "next_sailings_fragment.html",
            {
                "request": request,
                "routes": processed_routes,
                "last_updated": datetime.now().strftime("%I:%M:%S %p").lstrip("0"),
            },
        )

    except Exception as e:
        # Return error fragment
        return templates.TemplateResponse(
            "error_fragment.html", {"request": request, "error": str(e)}
        )


@app.get("/map-tab", response_class=HTMLResponse)
async def get_map_tab(request: Request):
    """Return the map tab content"""
    return templates.TemplateResponse("map_fragment.html", {"request": request})


@app.get("/ferry-data")
async def get_ferry_positions():
    """Return ferry position data as JSON for the map"""
    try:
        ferry_data = get_vessel_positions()
        return ferry_data
    except Exception as e:
        return {"error": str(e)}


@app.get("/sailings-tab", response_class=HTMLResponse)
async def get_sailings_tab(request: Request):
    """Return the sailings tab content"""
    return templates.TemplateResponse(
        "sailings_tab_fragment.html", {"request": request}
    )


@app.get("/debug/cached-delays")
async def debug_cached_delays():
    return CACHED_DELAYS
