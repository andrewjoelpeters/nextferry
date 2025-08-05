from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from .wsdot_client import get_vessel_positions
from .next_sailings import get_next_sailings, CACHED_DELAYS
from .display_processing import process_routes_for_display
from datetime import datetime
from zoneinfo import ZoneInfo
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any


logger = logging.getLogger(__name__)

# Global cache - shared by all users
_sailings_cache: Optional[Dict[str, Any]] = None


async def update_sailings_cache():
    """Background task to update sailings cache every 30 seconds"""
    global _sailings_cache
    
    while True:
        try:
            logger.info("Updating shared sailings cache")
            routes_data = get_next_sailings()
            processed_routes = process_routes_for_display(routes_data)
            
            _sailings_cache = {
                "routes": processed_routes,
                "last_updated": datetime.now(tz=ZoneInfo("America/Los_Angeles")).strftime("%I:%M:%S %p").lstrip("0"),
                "cached_at": datetime.now(tz=ZoneInfo("America/Los_Angeles"))
            }
            logger.info(f"Cache updated with {len(processed_routes)} routes")
            
        except Exception as e:
            logger.error(f"Error updating sailings cache: {e}")
        
        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background task on startup
    logger.info("Starting sailings cache background task")
    task = asyncio.create_task(update_sailings_cache())
    yield
    # Clean shutdown
    logger.info("Shutting down sailings cache background task")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/next-sailings", response_class=HTMLResponse)
async def get_next_sailings_html(request: Request):
    """Return cached sailings data - same for all users"""
    logger.info("Serving shared sailings cache")
    
    # If cache isn't ready yet (app just started), do one sync fetch
    if _sailings_cache is None:
        logger.info("Cache not ready, doing initial fetch")
        try:
            routes_data = get_next_sailings()
            processed_routes = process_routes_for_display(routes_data)
            return templates.TemplateResponse(
                "next_sailings_fragment.html",
                {
                    "request": request,
                    "routes": processed_routes,
                    "last_updated": datetime.now().strftime("%I:%M:%S %p").lstrip("0"),
                },
            )
        except Exception as e:
            return templates.TemplateResponse(
                "error_fragment.html", {"request": request, "error": str(e)}
            )
    
    # Serve from shared cache
    return templates.TemplateResponse(
        "next_sailings_fragment.html",
        {
            "request": request,
            "routes": _sailings_cache["routes"],
            "last_updated": _sailings_cache["last_updated"],
        },
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


@app.get("/debug/cache-status")
async def debug_cache_status():
    """Debug endpoint to check cache status"""
    if _sailings_cache is None:
        return {"status": "Cache not initialized"}
    
    cache_age_seconds = (datetime.now() - _sailings_cache["cached_at"]).total_seconds()
    return {
        "status": "Cache active",
        "last_updated": _sailings_cache["last_updated"],
        "cache_age_seconds": cache_age_seconds,
        "routes_count": len(_sailings_cache["routes"])
    }
