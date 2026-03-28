"""Capture a snapshot of WSDOT API responses for replay.

Saves the raw JSON from all three WSDOT endpoints (vessels, schedules,
sailing space) plus a timestamp into a single file under scenarios/.

Usage:
    uv run python -m scripts.capture_scenario
    uv run python -m scripts.capture_scenario --name rush-hour
"""

import argparse
import json
import os
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


def capture():
    if not API_KEY:
        raise SystemExit("WSDOT_API_KEY not set — add it to .env")

    now = datetime.now(tz=PT)
    print(f"Capturing WSDOT data at {now.isoformat()}")

    # Vessels
    resp = requests.get(
        f"{BASE}/vessels/rest/vessellocations?apiaccesscode={API_KEY}", timeout=TIMEOUT
    )
    resp.raise_for_status()
    vessels = resp.json()
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

    return scenario, now


def main():
    parser = argparse.ArgumentParser(description="Capture WSDOT API snapshot")
    parser.add_argument("--name", help="Scenario name (default: timestamp)")
    args = parser.parse_args()

    scenario, now = capture()

    filename = f"{args.name}.json" if args.name else now.strftime("%Y-%m-%dT%H_%M.json")

    out_dir = Path(__file__).parent.parent / "scenarios"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / filename

    with open(out_path, "w") as f:
        json.dump(scenario, f, indent=2)

    print(f"\nSaved: {out_path}")
    print(f"Replay: NEXTFERRY_SCENARIO={out_path} uvicorn backend.main:app --reload")


if __name__ == "__main__":
    main()
