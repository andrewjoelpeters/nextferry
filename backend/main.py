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
    get_available_routes,
    get_busyness_heatmap,
    get_data_date_range,
    get_history_data,
    get_sailing_event_count,
    get_snapshot_count,
    get_time_travel_data,
    init_db,
)
from .display_processing import process_routes_for_display
from .dock_predictor import dock_predictor
from .fill_predictor import fill_predictor
from .ml_predictor import predictor as ml_predictor
from .next_sailings import (
    CACHED_DELAYS,
    get_last_predictions,
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
    dock_predictor.load()

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

    if not dock_predictor.is_trained:
        logger.info("No at-dock model found, attempting background train...")
        try:
            if dock_predictor.train():
                dock_predictor.save()
                logger.info(
                    f"Initial at-dock model trained on {dock_predictor.training_data_size} rows"
                )
            else:
                logger.info("At-dock model training skipped (insufficient data)")
        except Exception as e:
            logger.error(f"Initial at-dock model training failed: {e}")

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

            if dock_predictor.train():
                dock_predictor.save()
                logger.info(
                    f"At-dock model retrained on {dock_predictor.training_data_size} rows"
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


@app.get("/history-tab", response_class=HTMLResponse)
async def get_history_tab(request: Request):
    """Return the historical data dashboard tab content."""
    routes = get_available_routes()
    date_range = get_data_date_range()
    return templates.TemplateResponse(
        "history_tab_fragment.html",
        {"request": request, "routes": routes, "date_range": date_range},
    )


@app.get("/history-data")
async def get_history_data_endpoint(
    route: str | None = None,
    season: str | None = None,
    day_type: str | None = None,
):
    """Return filtered historical data as JSON for chart rendering."""
    history = get_history_data(route=route, season=season, day_type=day_type)
    heatmap = get_busyness_heatmap(route=route, season=season)

    # Model performance section (kept for ML engineer error analysis)
    evaluation = None
    raw_eval = ml_predictor.last_evaluation
    if raw_eval:
        evaluation = {
            "overall_mae": raw_eval.get("overall_mae"),
            "overall_mean_error": raw_eval.get("overall_bias"),
            "improvement_pct": raw_eval.get("overall_improvement_pct"),
        }
        by_horizon = raw_eval.get("by_horizon", {})
        if by_horizon:
            error_by_horizon = []
            for label, metrics in by_horizon.items():
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

    return {**history, "heatmap": heatmap, "model": model_info}


@app.get("/time-travel-data")
async def get_time_travel_endpoint(timestamp: str):
    """Return historical vessel state and prediction replay for a given moment.

    The timestamp should be ISO 8601 format, e.g. "2024-11-07T20:00:00".
    Returns vessel positions, actual sailing outcomes, capacity data,
    and what the current ML model would have predicted at that moment.
    """
    raw = get_time_travel_data(timestamp)

    # Re-run predictions for each vessel that had an upcoming sailing
    predictions = {}
    if ml_predictor.is_trained:
        for v in raw["vessels"]:
            sched = v.get("scheduled_departure")
            if not sched:
                continue

            try:
                sched_dt = datetime.fromisoformat(sched).replace(tzinfo=None)
                ts_dt = datetime.fromisoformat(timestamp).replace(tzinfo=None)
                mins_until = (sched_dt - ts_dt).total_seconds() / 60
            except (ValueError, TypeError):
                continue

            if mins_until < 0 or mins_until > 120:
                continue

            vid = v["vessel_id"]
            prev_delay = raw["vessel_delays"].get(vid, 0.0)
            turnaround = raw["vessel_turnarounds"].get(vid)

            pred = ml_predictor.predict(
                route_abbrev=v.get("route_abbrev", ""),
                departing_terminal_id=v.get("departing_terminal_id", 0),
                vessel_id=vid,
                day_of_week=sched_dt.weekday(),
                hour_of_day=sched_dt.hour,
                minutes_until_scheduled_departure=mins_until,
                current_vessel_delay_minutes=prev_delay,
                vessel_speed=v.get("speed"),
                turnaround_minutes=turnaround,
            )
            if pred:
                predictions[vid] = pred

    # Build sailing lookup by (vessel_id, scheduled_departure) for actual outcomes
    sailing_lookup = {}
    for s in raw["sailings"]:
        key = (s["vessel_id"], s["scheduled_departure"])
        sailing_lookup[key] = s

    # Build capacity lookup by (departing_terminal_id, departure_time)
    capacity_lookup = {}
    for c in raw["capacity"]:
        key = (c["departing_terminal_id"], c["departure_time"])
        capacity_lookup[key] = c

    # Assemble vessel cards
    vessel_cards = []
    for v in raw["vessels"]:
        vid = v["vessel_id"]
        sched = v.get("scheduled_departure")

        # Find actual outcome for this sailing
        actual = None
        if sched:
            actual = sailing_lookup.get((vid, sched))

        # Find capacity for this sailing
        cap = None
        if sched and v.get("departing_terminal_id"):
            cap = capacity_lookup.get((v["departing_terminal_id"], sched))

        card = {
            "vessel_id": vid,
            "vessel_name": v["vessel_name"],
            "route_abbrev": v.get("route_abbrev"),
            "departing_terminal_name": v.get("departing_terminal_name"),
            "arriving_terminal_name": v.get("arriving_terminal_name"),
            "latitude": v.get("latitude"),
            "longitude": v.get("longitude"),
            "speed": v.get("speed"),
            "heading": v.get("heading"),
            "at_dock": bool(v.get("at_dock")),
            "scheduled_departure": sched,
            "left_dock": v.get("left_dock"),
            "eta": v.get("eta"),
            "snapshot_time": v.get("collected_at"),
        }

        if actual:
            card["actual_delay_minutes"] = actual["delay_minutes"]
            card["actual_departure"] = actual["actual_departure"]

        pred = predictions.get(vid)
        if pred:
            card["predicted_delay"] = pred["predicted_delay"]
            card["predicted_lower"] = pred["lower_bound"]
            card["predicted_upper"] = pred["upper_bound"]

        if cap and cap["max_space_count"] > 0:
            fill_pct = round(
                (1 - cap["drive_up_space_count"] / cap["max_space_count"]) * 100, 1
            )
            card["capacity"] = {
                "drive_up_spaces": cap["drive_up_space_count"],
                "max_spaces": cap["max_space_count"],
                "fill_pct": fill_pct,
            }

        # Compute prediction error if we have both prediction and actual
        if "predicted_delay" in card and "actual_delay_minutes" in card:
            card["prediction_error"] = round(
                card["predicted_delay"] - card["actual_delay_minutes"], 2
            )
            card["within_bounds"] = (
                card["predicted_lower"] <= card["actual_delay_minutes"]
                <= card["predicted_upper"]
            )

        vessel_cards.append(card)

    date_range = get_data_date_range()

    return {
        "timestamp": timestamp,
        "vessels": vessel_cards,
        "all_sailings": raw["sailings"],
        "date_range": date_range,
        "model_trained": ml_predictor.is_trained,
    }


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
        "dock_model": {
            "is_trained": dock_predictor.is_trained,
            "last_trained": (
                dock_predictor.last_trained.isoformat()
                if dock_predictor.last_trained
                else None
            ),
            "training_data_size": dock_predictor.training_data_size,
            "evaluation_metrics": dock_predictor.last_evaluation,
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
