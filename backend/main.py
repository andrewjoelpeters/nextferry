import asyncio
import contextlib
import hashlib
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .data_collector import collect_data
from .database import (
    get_docked_since,
    get_metrics_data,
    get_sailing_event_count,
    get_snapshot_count,
    init_db,
)
from .display_processing import process_routes_for_display
from .fill_predictor import fill_predictor
from .metrics import track_request
from .next_sailings import (
    CACHED_DELAYS,
    get_last_predictions,
    get_next_sailings,
    get_vessels_with_delays,
)
from .replay import activate_replay, current_time, get_replay_time
from .sailing_space import get_sailing_space_lookup
from .utils import datetime_to_minutes

logger = logging.getLogger(__name__)
GITHUB_NEW_ISSUE_URL = "https://github.com/andrewjoelpeters/nextferry/issues/new"

# Global caches - shared by all users
_sailings_cache: dict[str, Any] | None = None


async def update_sailings_cache():
    """Background task to update sailings cache every 30 seconds"""
    global _sailings_cache

    while True:
        try:
            logger.info("Updating shared sailings cache")

            def _build_cache():
                routes_data = get_next_sailings()
                space_lookup = get_sailing_space_lookup()
                return process_routes_for_display(routes_data, space_lookup)

            processed_routes = await asyncio.to_thread(_build_cache)

            _sailings_cache = {
                "routes": processed_routes,
                "last_updated": current_time().strftime("%I:%M:%S %p").lstrip("0"),
                "cached_at": current_time(),
            }
            logger.info(f"Cache updated with {len(processed_routes)} routes")

        except Exception as e:
            logger.error(f"Error updating sailings cache: {e}")

        await asyncio.sleep(30)


async def retrain_fill_model_daily():
    """Background task to load/train fill risk model, then retrain daily at 2 AM Pacific."""
    logger.info("Attempting to load saved fill risk model...")
    fill_predictor.load()

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
            next_2am = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if now.hour >= 2:
                next_2am += timedelta(days=1)
            wait_seconds = (next_2am - now).total_seconds()

            logger.info(
                f"Next fill model retrain scheduled in {wait_seconds / 3600:.1f} hours"
            )
            await asyncio.sleep(wait_seconds)

            logger.info("Starting daily fill model retraining...")
            if fill_predictor.train():
                fill_predictor.save()
                logger.info(
                    f"Fill risk model retrained on {fill_predictor.training_data_size} sailings"
                )

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Fill model retraining failed: {e}")
            await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    logger.info("Initializing database")
    init_db()

    # Check for replay mode (serve captured WSDOT data instead of live API)
    scenario_path = os.getenv("NEXTFERRY_SCENARIO")
    is_replay = bool(scenario_path or get_replay_time())
    if scenario_path and not get_replay_time():
        activate_replay(scenario_path)

    tasks = []

    # Start background tasks on startup
    logger.info("Starting sailings cache background task")
    tasks.append(asyncio.create_task(update_sailings_cache()))

    if not is_replay:
        # In replay mode, skip data collection and model retraining
        logger.info("Starting data collector background tasks")
        tasks.append(asyncio.create_task(collect_data()))

        logger.info("Starting fill model retraining task")
        tasks.append(asyncio.create_task(retrain_fill_model_daily()))
    else:
        logger.info("Replay mode: skipping data collector and model retraining")

    yield

    # Clean shutdown
    logger.info("Shutting down background tasks")
    for task in tasks:
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


def _serialize_report_value(value: Any) -> Any:
    """Recursively convert datetimes to ISO strings for JSON-safe report data."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _serialize_report_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_report_value(v) for v in value]
    return value


def _find_prediction_report_context(
    vessel_name: str | None,
    scheduled_departure: str,
    departing_terminal: str,
    arriving_terminal: str,
) -> dict[str, Any] | None:
    """Return matching prediction-debug context for a reported sailing.

    Searches the latest cached prediction records for an exact sailing match and,
    if that fails, falls back to returning the broader vessel-level context.
    Returns None when no relevant prediction context is available.
    """
    last_predictions = list(get_last_predictions().values())
    candidate_predictions = (
        [p for p in last_predictions if p.get("vessel_name") == vessel_name]
        if vessel_name
        else last_predictions
    )

    for vessel_prediction in candidate_predictions:
        for sailing in vessel_prediction.get("sailings", []):
            if (
                sailing.get("scheduled_departure") == scheduled_departure
                and sailing.get("departing") == departing_terminal
                and sailing.get("arriving") == arriving_terminal
            ):
                return {
                    "vessel_id": vessel_prediction.get("vessel_id"),
                    "vessel_name": vessel_prediction.get("vessel_name"),
                    "matched_sailing": sailing,
                    "all_vessel_sailings": vessel_prediction.get("sailings", []),
                }

    if candidate_predictions:
        vessel_prediction = candidate_predictions[0]
        return {
            "vessel_id": vessel_prediction.get("vessel_id"),
            "vessel_name": vessel_prediction.get("vessel_name"),
            "matched_sailing": None,
            "all_vessel_sailings": vessel_prediction.get("sailings", []),
        }

    return None


def _build_prediction_report_url(
    route_name: str,
    departing_terminal: str,
    arriving_terminal: str,
    scheduled_departure: str,
    displayed_time: str,
    time_until: str,
    last_updated: str,
    vessel_name: str | None = None,
    delay_text: str | None = None,
    referrer: str | None = None,
) -> str:
    """Build the GitHub issue URL for a prediction-error report.

    The issue includes what the user saw in the UI along with the app's latest
    cached prediction-debug context so the report is actionable to developers.
    """
    replay_time = get_replay_time()
    try:
        scheduled_departure_label = datetime.fromisoformat(
            scheduled_departure
        ).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        logger.debug(
            "Using raw scheduled departure in prediction report title: %s",
            scheduled_departure,
        )
        # Keep the raw value in the issue title if the browser sends an
        # unexpected format so the report still goes through.
        scheduled_departure_label = scheduled_departure

    report_context = {
        "reported_at": current_time().isoformat(),
        "referrer": referrer,
        "replay_time": _serialize_report_value(replay_time),
        "sailings_cache": (
            {
                "last_updated": _sailings_cache.get("last_updated"),
                "cached_at": _sailings_cache.get("cached_at"),
                "routes": _sailings_cache.get("routes"),
            }
            if _sailings_cache
            else None
        ),
        "reported_sailing": {
            "route_name": route_name,
            "departing_terminal": departing_terminal,
            "arriving_terminal": arriving_terminal,
            "scheduled_departure": scheduled_departure,
            "displayed_time": displayed_time,
            "time_until": time_until,
            "delay_text": delay_text,
            "vessel_name": vessel_name,
            "last_updated_on_page": last_updated,
        },
        "prediction_debug": _find_prediction_report_context(
            vessel_name=vessel_name,
            scheduled_departure=scheduled_departure,
            departing_terminal=departing_terminal,
            arriving_terminal=arriving_terminal,
        ),
    }

    issue_title = (
        f"Prediction error: {route_name} {departing_terminal} → "
        f"{arriving_terminal} {scheduled_departure_label}"
    )
    issue_body = "\n".join(
        [
            "## What looked wrong?",
            "",
            "<!-- Please briefly describe what you expected to see instead. -->",
            "",
            "## Captured app context",
            "```json",
            json.dumps(
                _serialize_report_value(report_context),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            ),
            "```",
        ]
    )
    return f"{GITHUB_NEW_ISSUE_URL}?{urlencode({'title': issue_title, 'body': issue_body})}"


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
                    "last_updated": current_time().strftime("%I:%M:%S %p").lstrip("0"),
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
            # Add docked_since from DB snapshots when WSDOT Eta is null
            if v.at_dock and v.eta is None and v.scheduled_departure:
                docked_since = get_docked_since(
                    v.vessel_id, v.scheduled_departure.isoformat()
                )
                data["DockedSince"] = docked_since.isoformat() if docked_since else None
            else:
                data["DockedSince"] = None
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
    """Return the sailings tab content."""
    return templates.TemplateResponse(
        "sailings_tab_fragment.html", {"request": request}
    )


@app.post("/report-prediction-error", name="report_prediction_error")
async def report_prediction_error(
    request: Request,
    route_name: str = Form(...),
    departing_terminal: str = Form(...),
    arriving_terminal: str = Form(...),
    scheduled_departure: str = Form(...),
    displayed_time: str = Form(...),
    time_until: str = Form(...),
    last_updated: str = Form(...),
    vessel_name: str | None = Form(None),
    delay_text: str | None = Form(None),
):
    """Prefill a GitHub issue with the current prediction context."""
    return templates.TemplateResponse(
        "report_prediction_error.html",
        {
            "request": request,
            "issue_url": _build_prediction_report_url(
                route_name=route_name,
                departing_terminal=departing_terminal,
                arriving_terminal=arriving_terminal,
                scheduled_departure=scheduled_departure,
                displayed_time=displayed_time,
                time_until=time_until,
                last_updated=last_updated,
                vessel_name=vessel_name,
                delay_text=delay_text,
                referrer=request.headers.get("referer"),
            ),
        },
    )


@app.get("/metrics-data")
async def get_metrics_data_endpoint(days: int = 30):
    """Return user metrics as JSON."""
    return get_metrics_data(days=days)


@app.get("/debug/cache-status")
async def debug_cache_status():
    """Debug endpoint to check cache status"""
    if _sailings_cache is None:
        return {"status": "Cache not initialized"}

    cache_age_seconds = (current_time() - _sailings_cache["cached_at"]).total_seconds()
    return {
        "status": "Cache active",
        "last_updated": _sailings_cache["last_updated"],
        "cache_age_seconds": cache_age_seconds,
        "routes_count": len(_sailings_cache["routes"]),
        "cached_delays": CACHED_DELAYS,
    }


@app.get("/debug/model-status")
async def debug_model_status():
    """Debug endpoint showing model status."""
    return {
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


@app.get("/debug/predictions")
async def debug_predictions():
    """Show the most recent predictions for all vessels on active routes.

    Each vessel entry contains every sailing prediction from the last cache
    cycle (~30s), including:
    - source: which model made the prediction (dock_model, en_route_model,
      fallback_flat)
    - inputs: the full feature dict passed to the model
    - prediction: the model output (delay, lower_bound, upper_bound)
    """
    return get_last_predictions()
