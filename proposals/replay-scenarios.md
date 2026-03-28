# Proposal: Replay Scenario Collection

## Problem

Replay mode needs scenario files to be useful, but we don't have any committed yet. The capture script requires a live `WSDOT_API_KEY`, so a new contributor can't replay anything out of the box.

## Plan

### 1. Commit a few baseline scenarios

Capture 2-3 "golden" scenarios that cover the common cases:

- **Weekday rush hour** (e.g. 5:30 PM Friday) — heavy traffic, delays likely, high fill percentages
- **Quiet off-peak** (e.g. 10 AM Tuesday) — everything on time, low fill
- **Late ferry / disruption** (opportunistic) — capture when a real delay is happening

These get checked into `scenarios/` so anyone can replay immediately without an API key.

### 2. Gitignore ad-hoc captures

Add `scenarios/*.json` with explicit `!scenarios/` exceptions for the committed baselines, or just use a naming convention:

```
# .gitignore
scenarios/*.json
!scenarios/baseline-*.json
```

Baseline files are committed; anything else is local scratch.

### 3. Capture workflow

```bash
# Capture a named baseline (when conditions are right)
uv run python -m scripts.capture_scenario --name baseline-rush-hour

# Capture a quick throwaway for local testing
uv run python -m scripts.capture_scenario
```

### 4. Future: CI smoke test

Once we have committed scenarios, CI could run a lightweight smoke test:

```bash
NEXTFERRY_SCENARIO=scenarios/baseline-rush-hour.json uv run pytest tests/test_replay_smoke.py -v
```

This would start the app with a frozen scenario and assert that `/next-sailings` returns valid HTML, `/ferry-data` returns vessel JSON, etc. Not a priority yet, but committed scenarios make it possible.

## Open questions

- How large are scenario files? If they're >1MB we might want to use Git LFS or trim unused fields.
- Should we capture more routes when we expand beyond sea-bi and ed-king?
