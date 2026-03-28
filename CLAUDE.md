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
- All datetimes use `zoneinfo.ZoneInfo("America/Los_Angeles")` — WSDOT API returns UTC
- SQLite with WAL mode; `data/` directory is gitignored (Railway uses persistent volume)

## Workflow

- Main branch is protected — all changes go through PRs
- CI runs `uv run pytest tests/ -v` on Python 3.13 via GitHub Actions
- Requires a `WSDOT_API_KEY` env var (from `.env` locally, Railway secret in prod)

## Pre-Merge Testing (AI Agent Checklist)

Before merging any change to main, an AI agent should independently verify the change by following this process. The goal is to catch regressions across the full data pipeline — not just the code you touched.

### 1. Run the automated test suite

```bash
# Unit + integration tests (no browser needed)
uv run pytest tests/ -v --tb=short -m "not e2e"

# E2e browser tests (requires playwright install chromium)
uv run pytest tests/e2e/ -v -m e2e

# Lint and type check
uv run ruff check . && uv run ruff format --check .
uv run mypy backend/
```

All tests must pass. If any fail, fix the root cause — do not skip or weaken assertions.

### 2. Verify cross-endpoint consistency

The app serves the same vessel data through two endpoints: `/ferry-data` (JSON for map) and `/next-sailings` (HTML for sailing list). After any change to `next_sailings.py`, `display_processing.py`, `main.py`, or `serializers.py`, verify:

- **Every vessel on the map appears in the sailings list** (and vice versa)
- **Delay values match**: if `/ferry-data` shows `DelayMinutes: 5` for a vessel, the sailings list should show that vessel as delayed
- **Vessel state is consistent**: an at-dock vessel on the map should show "At Dock" status in sailings, not "En route"

The `TestCrossEndpointConsistency` tests in `test_integration.py` cover this automatically. If you're adding a new data field, add a cross-endpoint test for it.

### 3. Verify correct model selection

The app uses two ML models with different features:
- **Dock model** (`dock_predictor`): for the FIRST sailing of at-dock vessels only — uses `minutes_at_dock`, `incoming_vehicle_fullness`
- **En-route model** (`ml_predictor`): for all other future sailings — uses `vessel_speed`, `minutes_until_scheduled_departure`

After changes to `next_sailings.py` or either predictor, verify:
- Dock model fires for at-dock vessels' current sailing
- Dock model does NOT fire when no vessels are at dock (use `scenario_both_en_route`)
- En-route model handles remaining future sailings
- Check `/debug/predictions` to see which model was used and what inputs it received

The `TestModelSelection` and `TestBothEnRoute` test classes cover this.

### 4. Test with bundled scenarios

The test fixtures (`tests/fixtures/scenarios.py`) provide WSDOT-format data for specific situations the app must handle. After any pipeline change, these should all work:

| Scenario | What it tests |
|---|---|
| `scenario_two_boats_at_dock` | Normal operations, both vessels docked |
| `scenario_one_en_route_one_docked` | Departed sailing shown, delay propagation |
| `scenario_both_en_route` | No dock model, direction matching critical |
| `scenario_severe_delay` | 25-min delay, severe delay styling |
| `scenario_null_fields` | Vessel with null ScheduledDeparture/LeftDock/Eta (the WSDOT gotcha) |
| `scenario_just_departed` | "Just left" display, 0-delay computation |
| `scenario_arriving` | Near-terminal ETA display |
| `scenario_late_night` | No future sailings, graceful empty state |
| `scenario_multi_route` | Two routes don't cross-contaminate |

To manually test a specific scenario with the real server:

```bash
NEXTFERRY_TEST_MODE=two_boats_at_dock uvicorn backend.main:app --reload
```

This starts the app with fixture data instead of live WSDOT API calls. Open `http://localhost:8000` and visually check the map, sailings list, and predictions tab.

### 5. If you changed templates or JS

Run the Playwright e2e tests (or manually verify with `NEXTFERRY_TEST_MODE`):
- Map markers render at correct positions and clicking opens info panel
- Direction toggle buttons switch the visible terminal
- Sailing details expand/collapse
- Tab switching (Sailings → Map → Predictions) loads content via HTMX
- Vessel name and status in map info panel match the sailings list

### 6. Adding new scenarios

When you encounter a new edge case or bug, add a scenario for it:

1. Add a vessel function to `tests/fixtures/scenarios.py` (follow existing patterns)
2. Add a `scenario_*()` bundle that composes vessels + schedules
3. Add a fixture in `tests/conftest.py`
4. Add integration tests that verify the expected behavior
5. The scenario name is automatically available for `NEXTFERRY_TEST_MODE`

### 7. Fix, don't suppress

If a test fails after your change:
- Read the assertion and understand what contract it's checking
- Fix your code to satisfy the contract, OR
- If the contract itself is wrong (the test is outdated), update the test AND explain why in the commit message
- Never delete a failing test without understanding why it existed

## Gotchas

- **WSDOT vessel data can have null fields even when the vessel is moving.** A vessel may report `AtDock: false` with non-zero speed but have `ScheduledDeparture`, `LeftDock`, and `Eta` all null. When matching vessel state to schedule sailings, always verify the direction (departing/arriving terminal) matches before annotating — don't assume the first future sailing corresponds to the vessel's current trip.
