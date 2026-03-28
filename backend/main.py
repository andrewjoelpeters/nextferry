import asyncio
import contextlib
import hashlib
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .data_collector import collect_data
from .database import (
    get_dashboard_data,
    get_metrics_data,
    get_sailing_event_count,
    get_snapshot_count,
    init_db,
)
from .display_processing import process_routes_for_display
from .fill_predictor import fill_predictor
from .metrics import track_request
from .ml_predictor import predictor as ml_predictor
from .next_sailings import (
    CACHED_DELAYS,
    get_next_sailings,
    get_vessels_with_delays,
)
from .sailing_space import get_sailing_space_lookup
from .utils import datetime_to_minutes

logger = logging.getLogger(__name__)

# Global cache - shared by all users
_sailings_cache: dict[str, Any] | None = None


async def update_sailings_cache():
    """Background task to update sailings cache every 30 seconds"""
    global _sailings_cache

    while True:
        try:
            logger.info("Updating shared sailings cache")
            routes_data = get_next_sailings()
            space_lookup = get_sailing_space_lookup()
            processed_routes = process_routes_for_display(routes_data, space_lookup)

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
    """Background task to load/train ML models, then retrain daily at 2 AM Pacific."""
    # On startup, try to load saved models from volume
    logger.info("Attempting to load saved ML models...")
    ml_predictor.load()
    fill_predictor.load()

    # If no models found, try an immediate background train
    if not ml_predictor.is_trained:
        logger.info("No delay model found, attempting background train...")
        try:
            if ml_predictor.train():
                ml_predictor.save()
                logger.info(
                    f"Initial delay model trained on {ml_predictor.training_data_size} rows"
                )
            else:
                logger.info("Delay model training skipped (insufficient data)")
        except Exception as e:
            logger.error(f"Initial delay model training failed: {e}")

    if not fill_predictor.is_trained:
        logger.info("No fill risk model found, attempting background train...")
        try:
            if fill_predictor.train():
                fill_predictor.save()
                logger.info(
                    f"Initial fill risk model trained on {fill_predictor.training_data_size} sailings"
                )
            else:
                logger.info("Fill risk training skipped (insufficient data)")
        except Exception as e:
            logger.error(f"Initial fill risk training failed: {e}")

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
            if ml_predictor.train():
                ml_predictor.save()
                logger.info(
                    f"Delay model retrained on {ml_predictor.training_data_size} rows"
                )

            if fill_predictor.train():
                fill_predictor.save()
                logger.info(
                    f"Fill risk model retrained on {fill_predictor.training_data_size} sailings"
                )

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
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track page views for user metrics."""
    response = await call_next(request)
    if response.status_code == 200:
        track_request(
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
            user_agent_str=request.headers.get("user-agent", ""),
            referrer=request.headers.get("referer"),
        )
    return response


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def _compute_asset_version() -> str:
    """Hash local static assets to produce a short cache-busting token."""
    h = hashlib.md5()
    for name in sorted(["style.css", "alerts.js"]):
        p = Path("static") / name
        if p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()[:8]


ASSET_VERSION = _compute_asset_version()
templates.env.globals["asset_version"] = ASSET_VERSION


@app.get("/sw.js")
async def service_worker():
    """Serve service worker from root scope for full app control"""
    return FileResponse(
        "static/sw.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )


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
    """Return enriched ferry position data as JSON for the map"""
    try:
        ferry_data = get_vessels_with_delays()
        result = []
        for v in ferry_data:
            data = v.model_dump(by_alias=True)
            # Add computed delay fields (not in WSDOT response)
            if v.delay:
                delay_minutes = datetime_to_minutes(v.delay)
                data["DelayMinutes"] = delay_minutes
                if v.scheduled_departure:
                    predicted = v.scheduled_departure + timedelta(minutes=delay_minutes)
                    data["PredictedDeparture"] = predicted.isoformat()
                else:
                    data["PredictedDeparture"] = None
            else:
                data["DelayMinutes"] = None
                data["PredictedDeparture"] = None
            result.append(data)
        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/sailings-tab", response_class=HTMLResponse)
async def get_sailings_tab(request: Request):
    """Return the sailings tab content"""
    return templates.TemplateResponse(
        "sailings_tab_fragment.html", {"request": request}
    )


@app.get("/predictions-tab", response_class=HTMLResponse)
async def get_predictions_tab(request: Request):
    """Return the predictions dashboard tab content."""
    return templates.TemplateResponse(
        "predictions_tab_fragment.html", {"request": request}
    )


@app.get("/predictions-data")
async def get_predictions_data():
    """Return dashboard data as JSON for chart rendering."""
    dashboard = get_dashboard_data()

    # Transform evaluation metrics into the format the frontend expects
    evaluation = None
    raw_eval = ml_predictor.last_evaluation
    if raw_eval:
        evaluation = {
            "overall_mae": raw_eval.get("overall_mae"),
            "overall_mean_error": raw_eval.get("overall_bias"),
            "improvement_pct": raw_eval.get("overall_improvement_pct"),
        }
        # Convert by_horizon dict into error_by_horizon array
        by_horizon = raw_eval.get("by_horizon", {})
        if by_horizon:
            error_by_horizon = []
            for label, metrics in by_horizon.items():
                # Parse midpoint from label like "2–4m" → 3
                parts = label.rstrip("m").split("–")
                lo, hi = float(parts[0]), float(parts[1])
                error_by_horizon.append(
                    {
                        "minutes_out": int((lo + hi) / 2),
                        "mae": metrics.get("mae"),
                        "mean_error": metrics.get("bias"),
                        "error_p88": metrics.get("error_p90"),
                        "error_p12": (
                            round(-abs(metrics.get("error_p90", 0)), 2)
                            if metrics.get("error_p90") is not None
                            else None
                        ),
                    }
                )
            error_by_horizon.sort(key=lambda d: d["minutes_out"])
            evaluation["error_by_horizon"] = error_by_horizon

    model_info = {
        "is_trained": ml_predictor.is_trained,
        "last_trained": (
            ml_predictor.last_trained.isoformat() if ml_predictor.last_trained else None
        ),
        "training_data_size": ml_predictor.training_data_size,
        "evaluation": evaluation,
    }

    return {**dashboard, "model": model_info}


@app.get("/metrics-data")
async def get_metrics_data_endpoint(days: int = 30):
    """Return user metrics as JSON."""
    return get_metrics_data(days=days)


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
        "delay_model": {
            "is_trained": ml_predictor.is_trained,
            "last_trained": (
                ml_predictor.last_trained.isoformat()
                if ml_predictor.last_trained
                else None
            ),
            "training_data_size": ml_predictor.training_data_size,
            "evaluation_metrics": ml_predictor.last_evaluation,
        },
        "fill_risk_model": {
            "is_trained": fill_predictor.is_trained,
            "last_trained": (
                fill_predictor.last_trained.isoformat()
                if fill_predictor.last_trained
                else None
            ),
            "training_data_size": fill_predictor.training_data_size,
            "fill_rate": fill_predictor.fill_rate,
        },
        "database": {
            "snapshot_count": get_snapshot_count(),
            "sailing_event_count": get_sailing_event_count(),
        },
    }
