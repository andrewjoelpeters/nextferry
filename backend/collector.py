"""Static live-data collector.

Fetches WSDOT data once per cycle, builds the live JSON/HTML artifacts, and
publishes them to Cloudflare R2. It can also persist raw history to SQLite for
offline model training.

Usage:
    uv run python -m backend.collector --once --output-dir live --no-upload
    R2_ACCOUNT_ID=... R2_ACCESS_KEY_ID=... R2_SECRET_ACCESS_KEY=... \
        R2_BUCKET=... uv run python -m backend.collector
"""

import argparse
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config
from fastapi.templating import Jinja2Templates

from .data_collector import (
    flatten_sailing_space,
    next_two_departures_per_route,
    store_sailing_space_to_db,
    store_vessels_to_db,
)
from .database import extract_sailing_events, init_db
from .display_processing import process_routes_for_display
from .fill_predictor import fill_predictor
from .live_data import build_ferry_data
from .next_sailings import get_next_sailings, get_vessels_with_delays
from .replay import activate_replay, current_time
from .sailing_space import build_sailing_space_lookup
from .wsdot_client import get_sailing_space

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
_templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

LIVE_OBJECTS = ("ferry-data.json", "next-sailings.html", "meta.json")
CONTENT_TYPES = {
    "ferry-data.json": "application/json",
    "next-sailings.html": "text/html; charset=utf-8",
    "meta.json": "application/json",
}
CACHE_CONTROL = "public, max-age=30, stale-while-revalidate=30"
HISTORY_EVERY_CYCLES = 5


def collect_once(*, persist_history: bool = True) -> dict[str, Any]:
    """Fetch WSDOT data and build the live artifacts.

    Raises if vessel or sailing data cannot be fetched so the caller can keep
    serving the previous R2 objects instead of publishing a broken snapshot.
    """
    vessels = get_vessels_with_delays()

    try:
        terminals = get_sailing_space()
    except Exception as e:
        logger.warning(f"Failed to fetch sailing space: {e}")
        terminals = []

    space_lookup = build_sailing_space_lookup(terminals)
    routes_data = get_next_sailings(vessel_positions=vessels)
    processed_routes = process_routes_for_display(routes_data, space_lookup)

    generated_at = current_time()
    last_updated = generated_at.strftime("%I:%M:%S %p").lstrip("0")

    html = _templates.get_template("next_sailings_fragment.html").render(
        routes=processed_routes,
        last_updated=last_updated,
        report_url="/report-prediction-error",
    )
    ferry_data = build_ferry_data(vessels)

    if persist_history:
        try:
            store_vessels_to_db(vessels)
            extract_sailing_events()
            if terminals:
                flattened = [
                    flat for space in terminals for flat in flatten_sailing_space(space)
                ]
                store_sailing_space_to_db(next_two_departures_per_route(flattened))
        except Exception:
            logger.exception(
                "Failed to persist history; live artifacts are still valid"
            )

    return {
        "ferry-data.json": ferry_data,
        "next-sailings.html": html,
        "meta.json": {
            "generated_at": generated_at.isoformat(),
            "last_updated": last_updated,
            "route_count": len(processed_routes),
            "vessel_count": len(ferry_data),
        },
    }


def _artifact_body(content: Any) -> bytes:
    if isinstance(content, str):
        return content.encode("utf-8")
    return json.dumps(content, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )


def write_local(artifacts: dict[str, Any], output_dir: Path) -> None:
    """Write artifacts to a local directory for inspection/testing."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in LIVE_OBJECTS:
        (output_dir / name).write_bytes(_artifact_body(artifacts[name]))


def _build_r2_client():
    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key = os.getenv("R2_ACCESS_KEY_ID")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
    missing = [
        name
        for name, value in (
            ("R2_ACCOUNT_ID", account_id),
            ("R2_ACCESS_KEY_ID", access_key),
            ("R2_SECRET_ACCESS_KEY", secret_key),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing R2 environment variables: {', '.join(missing)}")

    endpoint = os.getenv("R2_ENDPOINT") or (
        f"https://{account_id}.r2.cloudflarestorage.com"
    )
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=Config(
            signature_version="s3v4",
            connect_timeout=10,
            read_timeout=30,
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    )


class R2Publisher:
    """Publish live artifacts to an R2 bucket."""

    def __init__(
        self,
        *,
        bucket: str,
        prefix: str = "live",
        client: Any | None = None,
    ):
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.client = client or _build_r2_client()

    @classmethod
    def from_env(cls) -> "R2Publisher":
        bucket = os.getenv("R2_BUCKET")
        if not bucket:
            raise RuntimeError("Missing R2 environment variable: R2_BUCKET")
        return cls(bucket=bucket, prefix=os.getenv("R2_PREFIX", "live"))

    def publish(self, artifacts: dict[str, Any]) -> None:
        for name in LIVE_OBJECTS:
            key = f"{self.prefix}/{name}" if self.prefix else name
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=_artifact_body(artifacts[name]),
                ContentType=CONTENT_TYPES[name],
                CacheControl=CACHE_CONTROL,
            )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish Next Ferry live artifacts")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one collection cycle and exit",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Seconds between collection cycles (default: 60)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("live"),
        help="Directory for local artifact copies (default: live)",
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Write local artifacts without publishing to R2",
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Skip SQLite history persistence",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    scenario_path = os.getenv("NEXTFERRY_SCENARIO")
    if scenario_path:
        activate_replay(scenario_path)

    init_db()
    logger.info("Loading fill risk model")
    fill_predictor.load()

    publisher = None if args.no_upload else R2Publisher.from_env()
    if publisher:
        logger.info(f"Publishing to R2 bucket {publisher.bucket}/{publisher.prefix}")
    else:
        logger.info(f"R2 upload disabled; writing to {args.output_dir}")

    cycle = 0
    while True:
        try:
            persist_history = not args.no_history and cycle % HISTORY_EVERY_CYCLES == 0
            artifacts = collect_once(persist_history=persist_history)
            write_local(artifacts, args.output_dir)
            if publisher:
                publisher.publish(artifacts)
            logger.info(
                "Published %s vessels across %s routes",
                artifacts["meta.json"]["vessel_count"],
                artifacts["meta.json"]["route_count"],
            )
        except Exception:
            logger.exception("Collection cycle failed; keeping previous artifacts")

        if args.once:
            break
        cycle += 1
        time.sleep(max(1, args.interval))


if __name__ == "__main__":
    main()
