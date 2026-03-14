# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VesselWatch is a real-time Washington State Ferries tracker. It shows upcoming sailings with delay predictions and live vessel positions on a map. Deployed on Railway.

## Commands

```bash
# Install dependencies
uv pip install -e .

# Run dev server (from project root)
uvicorn backend.main:app --reload

# Production start (used by Railway)
uv run uvicorn backend.main:app --log-config=log_config.yaml --host 0.0.0.0 --port $PORT

# Format code
black .
isort .
```

## Environment

- Python 3.13, managed with `uv`
- Requires `WSDOT_API_KEY` in `.env` (get from WSDOT Developer Portal)

## Architecture

**Backend (FastAPI)** — `backend/`
- `main.py` — App entrypoint. Defines FastAPI app with lifespan that starts two background tasks: sailings cache (30s interval) and data collector (5min interval). All users share a single in-memory `_sailings_cache`.
- `wsdot_client.py` — HTTP client for three WSDOT API endpoints: vessel positions, today's schedule, and terminal sailing space. All responses use Pydantic models from `serializers.py`.
- `next_sailings.py` — Core business logic. Fetches vessels with delays, gets schedules per route, groups sailings by boat, propagates delays, and produces directional schedules. Uses a module-level `CACHED_DELAYS` dict to persist delay info across update cycles.
- `display_processing.py` — Transforms `RouteSchedule` models into template-ready dicts (next 3 sailings per direction with formatted times and delay text).
- `config.py` — Route definitions (currently Seattle-Bainbridge and Kingston-Edmonds). Each route has a display name, terminal IDs, route ID, and WSDOT route abbreviation.
- `serializers.py` — All Pydantic models. Two categories: raw WSDOT response models (using Field aliases to map PascalCase JSON) and internal models (`RouteSailing`, `DirectionalSailing`, `DirectionalSchedule`, `RouteSchedule`).
- `data_collector.py` — Background task that collects vessel positions and sailing space data to SQLite every 5 minutes.
- `database.py` — SQLite storage (WAL mode). Tables: `vessel_snapshots`, `sailing_events` (derived from snapshots), `sailing_space_snapshots`. DB location: `$RAILWAY_VOLUME_MOUNT_PATH/ferry.db` or `./data/ferry.db`.
- `ml_predictor.py` — HistGradientBoostingRegressor with quantile loss (q05/q50/q95) for delay prediction with 90% confidence intervals. Module-level `predictor` singleton. Loads models on startup: volume models (daily retrain) > bundled `models/` > background train > heuristic fallback.
- `evaluation.py` — RMSE by time horizon, prediction interval coverage, baseline comparison.
- `backfill.py` — One-time script to import historical JSONL files into SQLite.
- `utils.py` — Helpers: `parse_ms_date` (converts WSDOT's `/Date(ms)/` format), time formatting, delay text formatting.

**Frontend** — HTMX-driven, no build step
- `templates/` — Jinja2 templates. `index.html` is the shell; fragments (`next_sailings_fragment.html`, `map_fragment.html`, `sailings_tab_fragment.html`, `error_fragment.html`) are loaded via HTMX.
- `static/style.css` — Single stylesheet.

**Data flow**: WSDOT API → `wsdot_client` → `next_sailings` (business logic) → `display_processing` (formatting) → Jinja2 templates → HTMX fragments to browser.

## Key Patterns

- WSDOT API returns PascalCase JSON with dates in `/Date(milliseconds)/` format — all parsing happens in `serializers.py` via Pydantic field validators calling `parse_ms_date`.
- All times are in `America/Los_Angeles` timezone.
- Routes are configured as dicts in `config.py` — to add a new route, add an entry there.

## ML Model

The delay predictor uses three HistGradientBoostingRegressor models (median, 5th, 95th percentile) for point estimates with 90% confidence intervals. It retrains daily at 2 AM Pacific.

**Retrain locally:**
```bash
# 1. Download production database (via Railway SSH)
railway ssh
# Then inside SSH: cp /data/ferry.db /app/static/ferry.db
# Then locally:
curl -o data/ferry.db https://whens-the-ferry-production.up.railway.app/static/ferry.db
# Clean up: railway ssh, then rm /app/static/ferry.db

# 2. Train and save models
uv run python -m backend.ml_predictor

# 3. Update bundled models (shipped with deploys)
cp data/models/*.joblib models/
# Then commit models/
```

**Backfill SQLite from JSONL (one-time, on Railway or locally):**
```bash
uv run python -m backend.backfill [data_dir]
```

**Model load priority on startup:** volume models > bundled `models/` > background train > heuristic fallback. The app never blocks on model loading.
