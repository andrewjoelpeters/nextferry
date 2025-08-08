from fastapi import FastAPI, Request, HTTPException, Query, Response
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from .wsdot_client import get_vessel_positions
from .data_collector import collect_data
from .next_sailings import get_next_sailings, CACHED_DELAYS
from .display_processing import process_routes_for_display
from datetime import datetime
from zoneinfo import ZoneInfo
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
import os
import zipfile
import tempfile
from pathlib import Path


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background task on startup
    logger.info("Starting sailings cache background task")
    sailings_cache_task = asyncio.create_task(update_sailings_cache())

    logger.info("Starting vessels data collector backround tasks")
    collector_task = asyncio.create_task(collect_data())

    yield

    # Clean shutdown
    logger.info("Shutting down background tasks")
    for task in [sailings_cache_task, collector_task]:
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


# --- DATA DOWNLOAD ENDPOINTS ---

# @app.get("/data/download/latest")
# async def download_latest_vessel_data():
#     """Download the most recent vessel data file"""
#     volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./data")
#     data_dir = Path(volume_path)

#     if not data_dir.exists():
#         raise HTTPException(status_code=404, detail="Data directory not found")

#     # Find latest file
#     json_files = list(data_dir.glob("vessels_*.json"))
#     if not json_files:
#         raise HTTPException(status_code=404, detail="No vessel data files found")

#     latest_file = max(json_files, key=lambda f: f.stat().st_mtime)

#     return FileResponse(
#         path=str(latest_file), filename=latest_file.name, media_type="application/json"
#     )


# @app.get("/data/download/all")
# async def download_all_vessel_data():
#     """Download all vessel data files as a ZIP archive"""
#     volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./data")
#     data_dir = Path(volume_path)

#     if not data_dir.exists():
#         raise HTTPException(status_code=404, detail="Data directory not found")

#     json_files = list(data_dir.glob("vessels_*.json"))
#     if not json_files:
#         raise HTTPException(status_code=404, detail="No vessel data files found")

#     # Create ZIP file in memory
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
#         with zipfile.ZipFile(temp_zip.name, "w", zipfile.ZIP_DEFLATED) as zipf:
#             for file_path in json_files:
#                 zipf.write(file_path, file_path.name)

#         # Return the ZIP file
#         def iterfile():
#             with open(temp_zip.name, "rb") as f:
#                 yield from f
#             os.unlink(temp_zip.name)  # Clean up temp file

#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         return StreamingResponse(
#             iterfile(),
#             media_type="application/zip",
#             headers={
#                 "Content-Disposition": f"attachment; filename=vessel_data_{timestamp}.zip"
#             },
#         )
