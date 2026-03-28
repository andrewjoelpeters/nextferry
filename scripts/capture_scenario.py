"""Capture a snapshot of WSDOT API responses for replay.

Saves the raw JSON from all three WSDOT endpoints (vessels, schedules,
sailing space) plus a timestamp into a single file under scenarios/.

By default, captures vessel positions every 30 seconds for 10 minutes
before taking the final snapshot.  This builds a ``vessel_history`` array
that replay mode fast-forwards through at startup to pre-warm the delay
cache — matching production behavior where delays are observed across
many polling cycles.

Usage:
    uv run python -m scripts.capture_scenario
    uv run python -m scripts.capture_scenario --name rush-hour
    uv run python -m scripts.capture_scenario --duration 300 --interval 15
    uv run python -m scripts.capture_scenario --no-history   # single snapshot (legacy)
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

from backend.config import ROUTES

load_dotenv()

PT = ZoneInfo("America/Los_Angeles")
API_KEY = os.getenv("WSDOT_API_KEY")
BASE = "https://www.wsdot.wa.gov/ferries/api"

ROUTE_IDS = [r["route_id"] for r in ROUTES]

TIMEOUT = 30


def _fetch_vessels() -> list[dict]:
    resp = requests.get(
        f"{BASE}/vessels/rest/vessellocations?apiaccesscode={API_KEY}", timeout=TIMEOUT
    )
    resp.raise_for_status()
    return resp.json()


def _capture_vessel_history(duration: int, interval: int) -> list[dict]:
    """Poll vessel positions repeatedly to build a history for delay cache warming."""
    history: list[dict] = []
    end_time = time.monotonic() + duration
    remaining = duration

    print(f"  Capturing vessel history ({duration}s, every {interval}s)...")
    while time.monotonic() < end_time:
        ts = datetime.now(tz=PT)
        vessels = _fetch_vessels()
        history.append({"captured_at": ts.isoformat(), "vessels": vessels})
        remaining = end_time - time.monotonic()
        print(
            f"    Snapshot {len(history)}: {len(vessels)} vessels "
            f"({max(0, int(remaining))}s remaining)"
        )
        if remaining <= 0:
            break
        time.sleep(min(interval, remaining))

    print(f"  Captured {len(history)} vessel snapshots")
    return history


def capture(duration: int = 600, interval: int = 30, history: bool = True):
    if not API_KEY:
        raise SystemExit("WSDOT_API_KEY not set — add it to .env")

    # Collect vessel history first (while waiting, delays may appear/disappear)
    vessel_history: list[dict] = []
    if history and duration > 0:
        vessel_history = _capture_vessel_history(duration, interval)

    now = datetime.now(tz=PT)
    print(f"Capturing final WSDOT snapshot at {now.isoformat()}")

    # Final vessel snapshot (the "live" state for the replay session)
    vessels = _fetch_vessels()
    print(f"  Vessels: {len(vessels)}")

    # Schedules (one per route)
    schedules = {}
    for route_id in ROUTE_IDS:
        resp = requests.get(
            f"{BASE}/schedule/rest/scheduletoday/{route_id}/false?apiaccesscode={API_KEY}",
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        schedules[str(route_id)] = resp.json()
        combos = schedules[str(route_id)].get("TerminalCombos", [])
        total_sailings = sum(len(c.get("Times", [])) for c in combos)
        print(f"  Schedule route {route_id}: {total_sailings} sailings")

    # Sailing space
    resp = requests.get(
        f"{BASE}/terminals/rest/terminalsailingspace?apiaccesscode={API_KEY}",
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    sailing_space = resp.json()
    print(f"  Sailing space: {len(sailing_space)} terminals")

    scenario = {
        "captured_at": now.isoformat(),
        "vessels": vessels,
        "schedules": schedules,
        "sailing_space": sailing_space,
    }

    if vessel_history:
        scenario["vessel_history"] = vessel_history

    return scenario, now


def main():
    parser = argparse.ArgumentParser(description="Capture WSDOT API snapshot")
    parser.add_argument("--name", help="Scenario name (default: timestamp)")
    parser.add_argument(
        "--duration",
        type=int,
        default=600,
        help="Seconds to poll vessel history before final snapshot (default: 600)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Seconds between vessel history polls (default: 30)",
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Skip vessel history capture (legacy single-snapshot mode)",
    )
    args = parser.parse_args()

    scenario, now = capture(
        duration=args.duration,
        interval=args.interval,
        history=not args.no_history,
    )

    filename = f"{args.name}.json" if args.name else now.strftime("%Y-%m-%dT%H_%M.json")

    out_dir = Path(__file__).parent.parent / "scenarios"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / filename

    with open(out_path, "w") as f:
        json.dump(scenario, f, indent=2)

    snapshots = len(scenario.get("vessel_history", []))
    print(f"\nSaved: {out_path} ({snapshots} history snapshots)")
    print(f"Replay: NEXTFERRY_SCENARIO={out_path} uvicorn backend.main:app --reload")


if __name__ == "__main__":
    main()
