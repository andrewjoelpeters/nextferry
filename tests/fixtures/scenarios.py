"""Bundled test data representing different ferry scenarios.

Each scenario provides WSDOT-format vessel position data and schedule data
that can be injected via mocks to test the full pipeline without hitting
the real API.

WSDOT datetime format: /Date(milliseconds-offset)/
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")


def _wsdot_date(dt: datetime | None) -> str | None:
    """Convert a datetime to WSDOT /Date(...)/ format."""
    if dt is None:
        return None
    ms = int(dt.timestamp() * 1000)
    return f"/Date({ms}-0800)/"


def _now() -> datetime:
    return datetime.now(PT)


# ---------------------------------------------------------------------------
# Vessel position data (WSDOT vessellocations format)
# ---------------------------------------------------------------------------


def vessel_at_dock_seattle(
    departure_offset_minutes: int = 25,
    eta_offset_minutes: int = -15,
) -> dict:
    """Vessel docked at Seattle, scheduled to depart soon.

    - AtDock: True, Speed: 0
    - Has valid ScheduledDeparture, Eta (arrival time at dock)
    - No LeftDock (hasn't departed yet)
    """
    now = _now()
    return {
        "VesselID": 70,
        "VesselName": "Walla Walla",
        "DepartingTerminalID": 3,
        "DepartingTerminalName": "Seattle",
        "DepartingTerminalAbbrev": "SEA",
        "ArrivingTerminalID": 7,
        "ArrivingTerminalName": "Bainbridge Island",
        "ArrivingTerminalAbbrev": "BI",
        "Latitude": 47.6025,
        "Longitude": -122.3386,
        "Speed": 0.0,
        "Heading": 270,
        "InService": True,
        "AtDock": True,
        "LeftDock": None,
        "Eta": _wsdot_date(now + timedelta(minutes=eta_offset_minutes)),
        "ScheduledDeparture": _wsdot_date(
            (now + timedelta(minutes=departure_offset_minutes)).replace(
                second=0, microsecond=0
            )
        ),
        "TimeStamp": _wsdot_date(now),
        "OpRouteAbbrev": ["sea-bi"],
        "VesselPositionNum": 1,
        "SortSeq": 1,
        "ManagedBy": 0,
        "VesselWatchShutID": 0,
        "VesselWatchShutMsg": "",
        "VesselWatchShutFlag": "",
        "VesselWatchStatus": "",
        "VesselWatchMsg": "",
        "EtaBasis": "",
    }


def vessel_en_route_seattle_to_bainbridge(
    delay_minutes: int = 5,
    departed_minutes_ago: int = 10,
) -> dict:
    """Vessel en route from Seattle to Bainbridge, departed late.

    - AtDock: False, Speed: 15 knots
    - Has ScheduledDeparture and LeftDock (departed late = delay)
    - Has Eta (estimated arrival at Bainbridge)
    """
    now = _now()
    sched = (now - timedelta(minutes=departed_minutes_ago + delay_minutes)).replace(
        second=0, microsecond=0
    )
    left = sched + timedelta(minutes=delay_minutes)
    return {
        "VesselID": 70,
        "VesselName": "Walla Walla",
        "DepartingTerminalID": 3,
        "DepartingTerminalName": "Seattle",
        "DepartingTerminalAbbrev": "SEA",
        "ArrivingTerminalID": 7,
        "ArrivingTerminalName": "Bainbridge Island",
        "ArrivingTerminalAbbrev": "BI",
        "Latitude": 47.6200,
        "Longitude": -122.4100,
        "Speed": 15.0,
        "Heading": 280,
        "InService": True,
        "AtDock": False,
        "LeftDock": _wsdot_date(left),
        "Eta": _wsdot_date(now + timedelta(minutes=20)),
        "ScheduledDeparture": _wsdot_date(sched),
        "TimeStamp": _wsdot_date(now),
        "OpRouteAbbrev": ["sea-bi"],
        "VesselPositionNum": 1,
        "SortSeq": 1,
        "ManagedBy": 0,
        "VesselWatchShutID": 0,
        "VesselWatchShutMsg": "",
        "VesselWatchShutFlag": "",
        "VesselWatchStatus": "",
        "VesselWatchMsg": "",
        "EtaBasis": "",
    }


def vessel_at_dock_bainbridge(departure_offset_minutes: int = 20) -> dict:
    """Second vessel docked at Bainbridge (position 2 on sea-bi route).

    - AtDock: True, Speed: 0
    - Scheduled to depart Bainbridge to Seattle
    """
    now = _now()
    return {
        "VesselID": 62,
        "VesselName": "Spokane",
        "DepartingTerminalID": 7,
        "DepartingTerminalName": "Bainbridge Island",
        "DepartingTerminalAbbrev": "BI",
        "ArrivingTerminalID": 3,
        "ArrivingTerminalName": "Seattle",
        "ArrivingTerminalAbbrev": "SEA",
        "Latitude": 47.6228,
        "Longitude": -122.5095,
        "Speed": 0.0,
        "Heading": 90,
        "InService": True,
        "AtDock": True,
        "LeftDock": None,
        "Eta": _wsdot_date(now - timedelta(minutes=10)),
        "ScheduledDeparture": _wsdot_date(
            (now + timedelta(minutes=departure_offset_minutes)).replace(
                second=0, microsecond=0
            )
        ),
        "TimeStamp": _wsdot_date(now),
        "OpRouteAbbrev": ["sea-bi"],
        "VesselPositionNum": 2,
        "SortSeq": 2,
        "ManagedBy": 0,
        "VesselWatchShutID": 0,
        "VesselWatchShutMsg": "",
        "VesselWatchShutFlag": "",
        "VesselWatchStatus": "",
        "VesselWatchMsg": "",
        "EtaBasis": "",
    }


def vessel_null_fields() -> dict:
    """Vessel with null scheduling fields despite being en route.

    This is the gotcha from CLAUDE.md: AtDock=false, Speed > 0,
    but ScheduledDeparture, LeftDock, and Eta are all null.
    """
    now = _now()
    return {
        "VesselID": 70,
        "VesselName": "Walla Walla",
        "DepartingTerminalID": 3,
        "DepartingTerminalName": "Seattle",
        "DepartingTerminalAbbrev": "SEA",
        "ArrivingTerminalID": 7,
        "ArrivingTerminalName": "Bainbridge Island",
        "ArrivingTerminalAbbrev": "BI",
        "Latitude": 47.6200,
        "Longitude": -122.4100,
        "Speed": 12.0,
        "Heading": 280,
        "InService": True,
        "AtDock": False,
        "LeftDock": None,
        "Eta": None,
        "ScheduledDeparture": None,
        "TimeStamp": _wsdot_date(now),
        "OpRouteAbbrev": ["sea-bi"],
        "VesselPositionNum": 1,
        "SortSeq": 1,
        "ManagedBy": 0,
        "VesselWatchShutID": 0,
        "VesselWatchShutMsg": "",
        "VesselWatchShutFlag": "",
        "VesselWatchStatus": "",
        "VesselWatchMsg": "",
        "EtaBasis": "",
    }


def vessel_edmonds_kingston() -> dict:
    """Vessel on a different route (Edmonds-Kingston) at dock."""
    now = _now()
    return {
        "VesselID": 45,
        "VesselName": "Puyallup",
        "DepartingTerminalID": 8,
        "DepartingTerminalName": "Edmonds",
        "DepartingTerminalAbbrev": "ED",
        "ArrivingTerminalID": 12,
        "ArrivingTerminalName": "Kingston",
        "ArrivingTerminalAbbrev": "KING",
        "Latitude": 47.8104,
        "Longitude": -122.3834,
        "Speed": 0.0,
        "Heading": 0,
        "InService": True,
        "AtDock": True,
        "LeftDock": None,
        "Eta": _wsdot_date(now - timedelta(minutes=5)),
        "ScheduledDeparture": _wsdot_date(
            (now + timedelta(minutes=30)).replace(second=0, microsecond=0)
        ),
        "TimeStamp": _wsdot_date(now),
        "OpRouteAbbrev": ["ed-king"],
        "VesselPositionNum": 1,
        "SortSeq": 1,
        "ManagedBy": 0,
        "VesselWatchShutID": 0,
        "VesselWatchShutMsg": "",
        "VesselWatchShutFlag": "",
        "VesselWatchStatus": "",
        "VesselWatchMsg": "",
        "EtaBasis": "",
    }


# ---------------------------------------------------------------------------
# Schedule data (WSDOT scheduletoday format)
# ---------------------------------------------------------------------------


def schedule_sea_bi(vessel_1_name: str = "Walla Walla", vessel_2_name: str = "Spokane"):
    """Full day schedule for Seattle-Bainbridge route.

    Returns schedule data in the WSDOT TerminalCombos format
    with alternating departures from both terminals.
    """
    now = _now()
    base = now.replace(hour=5, minute=0, second=0, microsecond=0)

    seattle_departures = []
    bainbridge_departures = []

    # Generate departures every ~70 min from each terminal, alternating boats
    for i in range(14):
        dep_time = base + timedelta(minutes=i * 70)
        seattle_departures.append(
            {
                "DepartingTime": _wsdot_date(dep_time),
                "ArrivingTime": _wsdot_date(dep_time + timedelta(minutes=35)),
                "VesselName": vessel_1_name if i % 2 == 0 else vessel_2_name,
                "VesselPositionNum": 1 if i % 2 == 0 else 2,
                "LoadingRule": 0,
                "VesselID": 70 if i % 2 == 0 else 62,
                "AnnotationIndexes": [],
                "VesselHandicapAccessible": True,
                "Routes": [5],
            }
        )
        bi_dep_time = dep_time + timedelta(minutes=35)
        bainbridge_departures.append(
            {
                "DepartingTime": _wsdot_date(bi_dep_time),
                "ArrivingTime": _wsdot_date(bi_dep_time + timedelta(minutes=35)),
                "VesselName": vessel_1_name if i % 2 == 0 else vessel_2_name,
                "VesselPositionNum": 1 if i % 2 == 0 else 2,
                "LoadingRule": 0,
                "VesselID": 70 if i % 2 == 0 else 62,
                "AnnotationIndexes": [],
                "VesselHandicapAccessible": True,
                "Routes": [5],
            }
        )

    return {
        "ScheduleID": 123,
        "ScheduleName": "Spring 2026",
        "ScheduleSeason": 0,
        "SchedulePDFUrl": "",
        "ScheduleStart": None,
        "ScheduleEnd": None,
        "AllRoutes": [5],
        "TerminalCombos": [
            {
                "DepartingTerminalID": 3,
                "DepartingTerminalName": "Seattle",
                "ArrivingTerminalID": 7,
                "ArrivingTerminalName": "Bainbridge Island",
                "SailingNotes": "",
                "Times": seattle_departures,
                "Annotations": [],
                "AnnotationsIVR": [],
            },
            {
                "DepartingTerminalID": 7,
                "DepartingTerminalName": "Bainbridge Island",
                "ArrivingTerminalID": 3,
                "ArrivingTerminalName": "Seattle",
                "SailingNotes": "",
                "Times": bainbridge_departures,
                "Annotations": [],
                "AnnotationsIVR": [],
            },
        ],
    }


def schedule_ed_king():
    """Schedule for Edmonds-Kingston route."""
    now = _now()
    base = now.replace(hour=5, minute=30, second=0, microsecond=0)

    edmonds_departures = []
    kingston_departures = []

    for i in range(12):
        dep_time = base + timedelta(minutes=i * 80)
        edmonds_departures.append(
            {
                "DepartingTime": _wsdot_date(dep_time),
                "ArrivingTime": _wsdot_date(dep_time + timedelta(minutes=30)),
                "VesselName": "Puyallup",
                "VesselPositionNum": 1,
                "LoadingRule": 0,
                "VesselID": 45,
                "AnnotationIndexes": [],
                "VesselHandicapAccessible": True,
                "Routes": [6],
            }
        )
        king_dep_time = dep_time + timedelta(minutes=40)
        kingston_departures.append(
            {
                "DepartingTime": _wsdot_date(king_dep_time),
                "ArrivingTime": _wsdot_date(king_dep_time + timedelta(minutes=30)),
                "VesselName": "Puyallup",
                "VesselPositionNum": 1,
                "LoadingRule": 0,
                "VesselID": 45,
                "AnnotationIndexes": [],
                "VesselHandicapAccessible": True,
                "Routes": [6],
            }
        )

    return {
        "ScheduleID": 456,
        "ScheduleName": "Spring 2026",
        "ScheduleSeason": 0,
        "SchedulePDFUrl": "",
        "ScheduleStart": None,
        "ScheduleEnd": None,
        "AllRoutes": [6],
        "TerminalCombos": [
            {
                "DepartingTerminalID": 8,
                "DepartingTerminalName": "Edmonds",
                "ArrivingTerminalID": 12,
                "ArrivingTerminalName": "Kingston",
                "SailingNotes": "",
                "Times": edmonds_departures,
                "Annotations": [],
                "AnnotationsIVR": [],
            },
            {
                "DepartingTerminalID": 12,
                "DepartingTerminalName": "Kingston",
                "ArrivingTerminalID": 8,
                "ArrivingTerminalName": "Edmonds",
                "SailingNotes": "",
                "Times": kingston_departures,
                "Annotations": [],
                "AnnotationsIVR": [],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Pre-composed scenario bundles
# ---------------------------------------------------------------------------


def scenario_two_boats_at_dock():
    """Both boats docked at their respective terminals (normal ops)."""
    return {
        "vessels": [vessel_at_dock_seattle(), vessel_at_dock_bainbridge()],
        "schedules": {5: schedule_sea_bi()},
    }


def scenario_one_en_route_one_docked():
    """Boat 1 en route Seattle→Bainbridge (delayed), Boat 2 at Bainbridge dock."""
    return {
        "vessels": [
            vessel_en_route_seattle_to_bainbridge(delay_minutes=5),
            vessel_at_dock_bainbridge(),
        ],
        "schedules": {5: schedule_sea_bi()},
    }


def scenario_null_fields():
    """Vessel with null scheduling fields + normal vessel on same route."""
    return {
        "vessels": [vessel_null_fields(), vessel_at_dock_bainbridge()],
        "schedules": {5: schedule_sea_bi()},
    }


def scenario_multi_route():
    """Vessels on two different routes operating simultaneously."""
    return {
        "vessels": [
            vessel_at_dock_seattle(),
            vessel_at_dock_bainbridge(),
            vessel_edmonds_kingston(),
        ],
        "schedules": {5: schedule_sea_bi(), 6: schedule_ed_king()},
    }
