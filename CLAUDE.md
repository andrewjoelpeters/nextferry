# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Next Ferry — a real-time Washington State Ferries tracking and delay prediction web app. Python 3.13, FastAPI backend, HTMX frontend, scikit-learn ML models. Deployed on Railway.

## Commands

```bash
# Install dependencies
uv sync

# Run dev server (auto-reload)
uvicorn backend.main:app --reload

# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_ml_predictor.py -v

# Run a single test
uv run pytest tests/test_ml_predictor.py::test_function_name -v

# Lint and format
uv run ruff check .        # lint
uv run ruff check --fix .  # lint with auto-fix
uv run ruff format .       # format

# Type check
uv run mypy backend/
```

## Architecture

**Backend (`backend/`):** FastAPI app with three background tasks managed via async lifespan:
1. Sailings cache updater (every 30s from WSDOT API)
2. Data collector (vessel snapshots + sailing space → SQLite)
3. ML model retrainer (daily at 2 AM Pacific)

**Data flow:** WSDOT API → Pydantic serializers → SQLite (`data/ferry.db`) → `next_sailings.py` computes delays → ML predictor adds confidence intervals → `display_processing.py` formats for templates → Jinja2 HTMX fragments

**Frontend (`templates/` + `static/`):** Server-rendered HTML fragments loaded on-demand via HTMX `hx-get`. No client-side framework. Leaflet for maps, Chart.js for charts (both via CDN). PWA with service worker for ferry arrival notifications.

**ML models (`backend/ml_predictor.py`, `backend/fill_predictor.py`):**
- Delay predictor: Three HistGradientBoostingRegressors (quantiles q15/q50/q85) trained on `sailing_events` table
- Fill predictor: Classifier + regressor for capacity forecasting from `sailing_space_snapshots`
- Feature definitions live in `backend/model_training/backtest_model.py` (single source of truth)
- Models saved as joblib files in `models/`; feature compatibility validated at load time

**Key patterns:**
- Module-level singletons for `predictor` and `fill_predictor` with `.train()/.save()/.load()` lifecycle
- Global `_sailings_cache` dict in `main.py` shared across requests, updated by background task
- All datetimes use `zoneinfo.ZoneInfo("America/Los_Angeles")` — WSDOT API returns UTC. Use `replay.current_time()` instead of `datetime.now()` so replay mode works.
- SQLite with WAL mode; `data/` directory is gitignored (Railway uses persistent volume)

## Workflow

- Main branch is protected — all changes go through PRs
- CI runs `uv run pytest tests/ -v` on Python 3.13 via GitHub Actions
- Requires a `WSDOT_API_KEY` env var (from `.env` locally, Railway secret in prod)

## Replay Mode

The app can replay captured WSDOT API snapshots, serving the app exactly as it would have appeared at the capture time. Useful for verifying changes against real data without hitting the live API.

```bash
# Capture a snapshot from the live API
uv run python -m scripts.capture_scenario
uv run python -m scripts.capture_scenario --name rush-hour

# Start the app with a captured scenario
NEXTFERRY_SCENARIO=scenarios/rush-hour.json uvicorn backend.main:app --reload
```

Scenarios are JSON files in `scenarios/` containing raw WSDOT API responses + a timestamp. In replay mode, the data collector and ML retrainer are disabled.

## Gotchas

- **WSDOT vessel data can have null fields even when the vessel is moving.** A vessel may report `AtDock: false` with non-zero speed but have `ScheduledDeparture`, `LeftDock`, and `Eta` all null. When matching vessel state to schedule sailings, always verify the direction (departing/arriving terminal) matches before annotating — don't assume the first future sailing corresponds to the vessel's current trip.
