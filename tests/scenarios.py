"""Synthetic WSDOT-format API data for replay-mode integration tests.

Each scenario_*() function returns a dict matching the capture_scenario.py
format (captured_at + vessels + schedules + sailing_space), ready to write
to a temp file and load via NEXTFERRY_SCENARIO replay mode.

All schedules are timed so tests are deterministic regardless of when
the test actually executes.
"""

from datetime import datetime, timedelta, timezone

PT = timezone(timedelta(hours=-7))

_SEA = {"id": 3, "name": "Seattle", "abbrev": "SEA"}
_BI = {"id": 7, "name": "Bainbridge Island", "abbrev": "BI"}
_ED = {"id": 8, "name": "Edmonds", "abbrev": "ED"}
_KING = {"id": 12, "name": "Kingston", "abbrev": "KING"}


def _ms_date(dt: datetime) -> str:
    return f"/Date({int(dt.timestamp() * 1000)}-0700)/"


def _make_sailing(
    dep_time: datetime,
    vessel_name: str,
    vessel_pos: int,
    vessel_id: int,
    route_ids: list[int],
) -> dict:
    return {
        "DepartingTime": _ms_date(dep_time),
        "ArrivingTime": _ms_date(dep_time + timedelta(minutes=35)),
        "VesselName": vessel_name,
        "VesselPositionNum": vessel_pos,
        "LoadingRule": 0,
        "VesselID": vessel_id,
        "AnnotationIndexes": [],
        "VesselHandicapAccessible": True,
        "Routes": route_ids,
    }


def _schedule_block(
    start: datetime,
    count: int,
    interval: int,
    vessel_name: str,
    vessel_pos: int,
    vessel_id: int,
    route_ids: list[int],
) -> list[dict]:
    return [
        _make_sailing(
            start + timedelta(minutes=i * interval),
            vessel_name,
            vessel_pos,
            vessel_id,
            route_ids,
        )
        for i in range(count)
    ]


def _sea_bi_schedule(now: datetime) -> dict:
    base = now.replace(hour=5, minute=0, second=0, microsecond=0)
    seattle = _schedule_block(base, 20, 70, "Walla Walla", 1, 70, [5])
    bainbridge = _schedule_block(
        base + timedelta(minutes=35), 20, 70, "Spokane", 2, 62, [5]
    )
    return {
        "ScheduleID": 101,
        "ScheduleName": "Summer 2026",
        "ScheduleSeason": 0,
        "SchedulePDFUrl": "",
        "ScheduleStart": None,
        "ScheduleEnd": None,
        "AllRoutes": [5],
        "TerminalCombos": [
            {
                "DepartingTerminalID": _SEA["id"],
                "DepartingTerminalName": _SEA["name"],
                "ArrivingTerminalID": _BI["id"],
                "ArrivingTerminalName": _BI["name"],
                "SailingNotes": "",
                "Times": seattle,
                "Annotations": [],
                "AnnotationsIVR": [],
            },
            {
                "DepartingTerminalID": _BI["id"],
                "DepartingTerminalName": _BI["name"],
                "ArrivingTerminalID": _SEA["id"],
                "ArrivingTerminalName": _SEA["name"],
                "SailingNotes": "",
                "Times": bainbridge,
                "Annotations": [],
                "AnnotationsIVR": [],
            },
        ],
    }


def _ed_king_schedule(now: datetime) -> dict:
    base = now.replace(hour=5, minute=30, second=0, microsecond=0)
    edmonds = _schedule_block(base, 16, 80, "Puyallup", 1, 45, [6])
    kingston = _schedule_block(
        base + timedelta(minutes=40), 16, 80, "Puyallup", 1, 45, [6]
    )
    return {
        "ScheduleID": 102,
        "ScheduleName": "Summer 2026",
        "ScheduleSeason": 0,
        "SchedulePDFUrl": "",
        "ScheduleStart": None,
        "ScheduleEnd": None,
        "AllRoutes": [6],
        "TerminalCombos": [
            {
                "DepartingTerminalID": _ED["id"],
                "DepartingTerminalName": _ED["name"],
                "ArrivingTerminalID": _KING["id"],
                "ArrivingTerminalName": _KING["name"],
                "SailingNotes": "",
                "Times": edmonds,
                "Annotations": [],
                "AnnotationsIVR": [],
            },
            {
                "DepartingTerminalID": _KING["id"],
                "DepartingTerminalName": _KING["name"],
                "ArrivingTerminalID": _ED["id"],
                "ArrivingTerminalName": _ED["name"],
                "SailingNotes": "",
                "Times": kingston,
                "Annotations": [],
                "AnnotationsIVR": [],
            },
        ],
    }


def _vessel(
    vessel_id: int,
    name: str,
    pos: int,
    departing: dict,
    arriving: dict,
    lat: float,
    lon: float,
    speed: float,
    heading: int,
    at_dock: bool,
    left_dock: datetime | None,
    eta: datetime | None,
    scheduled_departure: datetime | None,
    route: str,
) -> dict:
    return {
        "VesselID": vessel_id,
        "VesselName": name,
        "DepartingTerminalID": departing["id"],
        "DepartingTerminalName": departing["name"],
        "DepartingTerminalAbbrev": departing["abbrev"],
        "ArrivingTerminalID": arriving["id"],
        "ArrivingTerminalName": arriving["name"],
        "ArrivingTerminalAbbrev": arriving["abbrev"],
        "Latitude": lat,
        "Longitude": lon,
        "Speed": speed,
        "Heading": heading,
        "InService": True,
        "AtDock": at_dock,
        "LeftDock": _ms_date(left_dock) if left_dock else None,
        "Eta": _ms_date(eta) if eta else None,
        "ScheduledDeparture": (
            _ms_date(scheduled_departure) if scheduled_departure else None
        ),
        "TimeStamp": _ms_date(_now()),
        "OpRouteAbbrev": [route],
        "VesselPositionNum": pos,
        "SortSeq": pos,
        "ManagedBy": 0,
        "VesselWatchShutID": 0,
        "VesselWatchShutMsg": "",
        "VesselWatchShutFlag": "",
        "VesselWatchStatus": "",
        "VesselWatchMsg": "",
        "EtaBasis": "",
    }


def _now() -> datetime:
    return datetime(2026, 7, 2, 14, 0, 0, tzinfo=PT)


def _scenario(
    vessels: list[dict],
    schedules: dict | None = None,
    now: datetime | None = None,
) -> dict:
    t = now or _now()
    return {
        "captured_at": t.isoformat(),
        "vessels": vessels,
        "schedules": schedules or {},
        "sailing_space": [],
    }


# ---------------------------------------------------------------------------
# Scenario: At-dock vessel overdue
# ---------------------------------------------------------------------------


def scenario_at_dock_overdue():
    """Vessel at Seattle dock, scheduled departure 50 min ago.

    No LeftDock → app computes overdue_delay = current_time - scheduled_departure.
    Expected: DelayMinutes=50 on ferry-data, "Loading" status in sailings.
    """
    now = _now()
    sched = now.replace(hour=13, minute=10)  # 13:10 — matches schedule
    eta = now - timedelta(minutes=55)
    return _scenario(
        vessels=[
            _vessel(
                70,
                "Walla Walla",
                1,
                _SEA,
                _BI,
                47.6025,
                -122.3386,
                0.0,
                270,
                True,
                None,
                eta,
                sched,
                "sea-bi",
            ),
            _vessel(
                62,
                "Spokane",
                2,
                _BI,
                _SEA,
                47.6228,
                -122.5095,
                0.0,
                90,
                True,
                None,
                now - timedelta(minutes=10),
                now.replace(hour=14, minute=55),
                "sea-bi",
            ),
        ],
        schedules={5: _sea_bi_schedule(now)},
    )


# ---------------------------------------------------------------------------
# Scenario: En route with computed delay
# ---------------------------------------------------------------------------


def scenario_en_route_delayed():
    """Vessel en route Seattle→Bainbridge with a 5-minute delay.

    LeftDock(13:15) - ScheduledDeparture(13:10) = 5 min delay.
    Flat-propagated to all future sailings.
    """
    now = _now()
    sched = now.replace(hour=13, minute=10)
    left = sched + timedelta(minutes=5)  # 13:15
    eta = now + timedelta(minutes=20)  # 14:20
    return _scenario(
        vessels=[
            _vessel(
                70,
                "Walla Walla",
                1,
                _SEA,
                _BI,
                47.62,
                -122.41,
                15.0,
                280,
                False,
                left,
                eta,
                sched,
                "sea-bi",
            ),
            _vessel(
                62,
                "Spokane",
                2,
                _BI,
                _SEA,
                47.6228,
                -122.5095,
                0.0,
                90,
                True,
                None,
                now - timedelta(minutes=15),
                now.replace(hour=14, minute=55),
                "sea-bi",
            ),
        ],
        schedules={5: _sea_bi_schedule(now)},
    )


# ---------------------------------------------------------------------------
# Scenario: Just departed on time (0 delay)
# ---------------------------------------------------------------------------


def scenario_just_departed():
    """Vessel left at the scheduled time, delay=0.

    captured_at is shortly after the 13:10 departure so the sailing
    appears as "just departed" in the schedule.
    """
    now = datetime(2026, 7, 2, 13, 15, 0, tzinfo=PT)
    sched = now.replace(hour=13, minute=10)
    left = sched  # same time → 0 delay
    eta = now + timedelta(minutes=35)
    return _scenario(
        vessels=[
            _vessel(
                70,
                "Walla Walla",
                1,
                _SEA,
                _BI,
                47.605,
                -122.35,
                8.0,
                270,
                False,
                left,
                eta,
                sched,
                "sea-bi",
            ),
            _vessel(
                62,
                "Spokane",
                2,
                _BI,
                _SEA,
                47.6228,
                -122.5095,
                0.0,
                90,
                True,
                None,
                now - timedelta(minutes=20),
                now.replace(hour=14, minute=55),
                "sea-bi",
            ),
        ],
        schedules={5: _sea_bi_schedule(now)},
        now=now,
    )


# ---------------------------------------------------------------------------
# Scenario: En route with null timing fields
# ---------------------------------------------------------------------------


def scenario_null_fields():
    """Vessel en route but all timing fields null (WSDOT gotcha).

    AtDock=false, Speed>0, but LeftDock=Eta=ScheduledDeparture=None.
    Must NOT annotate future sailings as en route.
    """
    now = _now()
    return _scenario(
        vessels=[
            _vessel(
                70,
                "Walla Walla",
                1,
                _SEA,
                _BI,
                47.62,
                -122.41,
                15.0,
                280,
                False,
                None,
                None,
                None,
                "sea-bi",
            ),
            _vessel(
                62,
                "Spokane",
                2,
                _BI,
                _SEA,
                47.6228,
                -122.5095,
                0.0,
                90,
                True,
                None,
                now - timedelta(minutes=10),
                now.replace(hour=14, minute=55),
                "sea-bi",
            ),
        ],
        schedules={5: _sea_bi_schedule(now)},
    )


# ---------------------------------------------------------------------------
# Scenario: Normal ops (two boats at dock)
# ---------------------------------------------------------------------------


def scenario_normal_ops():
    """Two vessels at dock with future scheduled departures."""
    now = _now()
    return _scenario(
        vessels=[
            _vessel(
                70,
                "Walla Walla",
                1,
                _SEA,
                _BI,
                47.6025,
                -122.3386,
                0.0,
                270,
                True,
                None,
                now - timedelta(minutes=55),
                now.replace(hour=14, minute=20),
                "sea-bi",
            ),
            _vessel(
                62,
                "Spokane",
                2,
                _BI,
                _SEA,
                47.6228,
                -122.5095,
                0.0,
                90,
                True,
                None,
                now - timedelta(minutes=10),
                now.replace(hour=14, minute=55),
                "sea-bi",
            ),
        ],
        schedules={5: _sea_bi_schedule(now)},
    )


# ---------------------------------------------------------------------------
# Scenario: Multi-route (Sea-BI + Ed-King)
# ---------------------------------------------------------------------------


def scenario_multi_route():
    """Vessels operating on two routes simultaneously."""
    now = _now()
    return _scenario(
        vessels=[
            _vessel(
                70,
                "Walla Walla",
                1,
                _SEA,
                _BI,
                47.6025,
                -122.3386,
                0.0,
                270,
                True,
                None,
                now - timedelta(minutes=55),
                now.replace(hour=14, minute=20),
                "sea-bi",
            ),
            _vessel(
                62,
                "Spokane",
                2,
                _BI,
                _SEA,
                47.6228,
                -122.5095,
                0.0,
                90,
                True,
                None,
                now - timedelta(minutes=10),
                now.replace(hour=14, minute=55),
                "sea-bi",
            ),
            _vessel(
                45,
                "Puyallup",
                1,
                _ED,
                _KING,
                47.8104,
                -122.3834,
                0.0,
                0,
                True,
                None,
                now - timedelta(minutes=5),
                now.replace(hour=14, minute=30),
                "ed-king",
            ),
        ],
        schedules={
            5: _sea_bi_schedule(now),
            6: _ed_king_schedule(now),
        },
    )
