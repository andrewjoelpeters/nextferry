import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .data_collector import collect_data
from .database import get_sailing_event_count, get_snapshot_count, init_db
from .display_processing import process_routes_for_display
from .ml_predictor import predictor as ml_predictor
from .next_sailings import CACHED_DELAYS, get_next_sailings
from .wsdot_client import get_vessel_positions

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
                "last_updated": datetime.now(tz=ZoneInfo("America/Los_Angeles"))
                .strftime("%I:%M:%S %p")
                .lstrip("0"),
                "cached_at": datetime.now(tz=ZoneInfo("America/Los_Angeles")),
            }
            logger.info(f"Cache updated with {len(processed_routes)} routes")

        except Exception as e:
            logger.error(f"Error updating sailings cache: {e}")

        await asyncio.sleep(30)


async def retrain_model_daily():
    """Background task to retrain the ML model daily at 2 AM Pacific."""
    # On startup, try to load saved model
    logger.info("Attempting to load saved ML model...")
    ml_predictor.load()

    while True:
        try:
            now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
            # Calculate seconds until next 2 AM
            next_2am = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if now.hour >= 2:
                next_2am += timedelta(days=1)
            wait_seconds = (next_2am - now).total_seconds()

            logger.info(
                f"Next model retrain scheduled in {wait_seconds / 3600:.1f} hours"
            )
            await asyncio.sleep(wait_seconds)

            logger.info("Starting daily model retraining...")
            success = ml_predictor.train()
            if success:
                ml_predictor.save()
                logger.info(
                    f"Model retrained on {ml_predictor.training_data_size} rows"
                )
            else:
                logger.info("Model retraining skipped (insufficient data)")

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Model retraining failed: {e}")
            await asyncio.sleep(3600)  # retry in 1 hour on error


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    logger.info("Initializing database")
    init_db()

    # Start background task on startup
    logger.info("Starting sailings cache background task")
    sailings_cache_task = asyncio.create_task(update_sailings_cache())

    logger.info("Starting data collector backround tasks")
    collector_task = asyncio.create_task(collect_data())

    logger.info("Starting ML model retraining task")
    retrain_task = asyncio.create_task(retrain_model_daily())

    yield

    # Clean shutdown
    logger.info("Shutting down background tasks")
    for task in [sailings_cache_task, collector_task, retrain_task]:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/sw.js")
async def service_worker():
    """Serve service worker from root scope for full app control"""
    return FileResponse("static/sw.js", media_type="application/javascript")


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
        "routes_count": len(_sailings_cache["routes"]),
        "cached_delays": CACHED_DELAYS,
    }


@app.get("/debug/model-status")
async def debug_model_status():
    """Debug endpoint showing ML model status and evaluation metrics."""
    return {
        "is_trained": ml_predictor.is_trained,
        "last_trained": (
            ml_predictor.last_trained.isoformat() if ml_predictor.last_trained else None
        ),
        "training_data_size": ml_predictor.training_data_size,
        "evaluation_metrics": ml_predictor.last_evaluation,
        "database": {
            "snapshot_count": get_snapshot_count(),
            "sailing_event_count": get_sailing_event_count(),
        },
    }
