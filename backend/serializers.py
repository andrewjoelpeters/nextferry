from datetime import datetime, timedelta
from typing import Annotated, Literal

from pydantic import BaseModel, Field, computed_field, field_validator

from .utils import parse_ms_date


# --- Vessels Endpoint ----
class Vessel(BaseModel):
    vessel_id: int = Field(alias="VesselID")
    vessel_name: str = Field(alias="VesselName")
    # Mmsi: Optional[int]

    departing_terminal_id: int | None = Field(alias="DepartingTerminalID")
    departing_terminal_name: str | None = Field(alias="DepartingTerminalName")
    departing_terminal_abbrev: str | None = Field(alias="DepartingTerminalAbbrev")

    arriving_terminal_id: int | None = Field(alias="ArrivingTerminalID")
    arriving_terminal_name: str | None = Field(alias="ArrivingTerminalName")
    arriving_terminal_abbrev: str | None = Field(alias="ArrivingTerminalAbbrev")

    latitude: float | None = Field(alias="Latitude")
    longitude: float | None = Field(alias="Longitude")
    speed: float | None = Field(alias="Speed")
    heading: int | None = Field(alias="Heading")

    in_service: bool = Field(alias="InService")
    at_dock: bool = Field(alias="AtDock")

    left_dock: datetime | None = Field(alias="LeftDock")
    eta: datetime | None = Field(alias="Eta")
    scheduled_departure: datetime | None = Field(alias="ScheduledDeparture")
    timestamp: datetime | None = Field(alias="TimeStamp")

    # delay as timedelta, added in next_sailings.py (not provided by WSDOT)
    delay: timedelta | None = None

    # EtaBasis: Optional[str]
    route_name: list[str] = Field(alias="OpRouteAbbrev")

    vessel_position_num: int | None = Field(alias="VesselPositionNum")

    # SortSeq: Optional[int]
    # ManagedBy: Optional[int]

    # VesselWatchShutID: Optional[int]
    # VesselWatchShutMsg: Optional[str]
    # VesselWatchShutFlag: Optional[str]
    # VesselWatchStatus: Optional[str]
    # VesselWatchMsg: Optional[str]

    @field_validator(
        "left_dock", "eta", "scheduled_departure", "timestamp", mode="before"
    )
    @classmethod
    def parse_schedule_dates(cls, value):
        return parse_ms_date(value)


# --- ScheduleToday Endpoint ----


class RawDeparture(BaseModel):
    scheduled_departure: datetime | None = Field(alias="DepartingTime")
    # arriving_time: Optional[datetime] = Field(alias="ArrivingTime")
    vessel_name: str = Field(alias="VesselName")
    vessel_position_num: int = Field(alias="VesselPositionNum")
    # Routes: List[int]
    # LoadingRule: int
    # VesselID: int
    # AnnotationIndexes: List[int]
    # VesselHandicapAccessible: bool

    @field_validator("scheduled_departure", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        return parse_ms_date(value)


class RawDirectionalSchedule(BaseModel):
    departing_terminal_id: int = Field(alias="DepartingTerminalID")
    departing_terminal_name: str = Field(alias="DepartingTerminalName")
    arriving_terminal_id: int = Field(alias="ArrivingTerminalID")
    arriving_terminal_name: str = Field(alias="ArrivingTerminalName")
    sailing_notes: str = Field(alias="SailingNotes")
    times: list[RawDeparture] = Field(alias="Times")
    # Annotations: List[str]
    # AnnotationsIVR: List[str]


class RawRouteSchedule(BaseModel):
    # ScheduleID: int
    # ScheduleName: str
    # ScheduleSeason: int  # 0=Spring, 1=Summer, etc.
    # SchedulePDFUrl: str
    # ScheduleStart: Optional[datetime]
    # ScheduleEnd: Optional[datetime]
    # AllRoutes: List[int]
    terminal_combos: list[RawDirectionalSchedule] = Field(..., alias="TerminalCombos")


# -- Sailing Space Endpoint --


class ArrivalTerminal(BaseModel):
    terminal_id: int = Field(alias="TerminalID")
    terminal_name: str = Field(alias="TerminalName")
    # vessel_id: int = Field(alias="VesselID")
    # vessel_name: str = Field(alias="VesselName")
    # display_reservable_space: bool = Field(alias="DisplayReservableSpace")
    reservable_space_count: int | None = Field(alias="ReservableSpaceCount")
    # reservable_space_hex_color: Optional[str] = Field(alias="ReservableSpaceHexColor")
    # display_drive_up_space: bool = Field(alias="DisplayDriveUpSpace")
    drive_up_space_count: int = Field(alias="DriveUpSpaceCount")
    # drive_up_space_hex_color: str = Field(alias="DriveUpSpaceHexColor")
    max_space_count: int = Field(alias="MaxSpaceCount")
    # arrival_terminal_ids: List[int] = Field(alias="ArrivalTerminalIDs")


class SailingSpace(BaseModel):
    departure: datetime | None = Field(alias="Departure")
    is_cancelled: bool = Field(alias="IsCancelled")
    vessel_id: int = Field(alias="VesselID")
    vessel_name: str = Field(alias="VesselName")
    max_space_count: int = Field(alias="MaxSpaceCount")
    space_for_arrival_terminals: list[ArrivalTerminal] = Field(
        alias="SpaceForArrivalTerminals"
    )

    @field_validator("departure", mode="before")
    @classmethod
    def parse_departure_date(cls, value):
        return parse_ms_date(value)


class TerminalSpace(BaseModel):
    terminal_id: int = Field(alias="TerminalID")
    # terminal_subject_id: int = Field(alias="TerminalSubjectID")
    # region_id: int = Field(alias="RegionID")
    terminal_name: str = Field(alias="TerminalName")
    # terminal_abbrev: str = Field(alias="TerminalAbbrev")
    # sort_seq: int = Field(alias="SortSeq")
    departing_spaces: list[SailingSpace] = Field(alias="DepartingSpaces")
    # is_no_fare_collected: Optional[bool] = Field(alias="IsNoFareCollected")
    # no_fare_collected_msg: Optional[str] = Field(alias="NoFareCollectedMsg")


# --- My Serializers -----


def _fmt(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip("0")


class EtaBoundedTrace(BaseModel):
    """Trace for delays predicted via ETA + turnaround bounds."""

    source: Literal["eta_bounded"] = "eta_bounded"
    current_delay_minutes: float
    """The observed delay at the time this prediction was made."""
    predicted_arrival: datetime
    """ETA at the destination terminal."""
    arrival_source: Literal["wsdot_eta", "estimated_crossing"]
    """Whether the arrival time is an official WSDOT ETA or our own crossing estimate."""
    arriving_terminal_name: str
    """Name of the terminal where the vessel arrives before the predicted departure."""
    turnaround_minutes: float
    """Turnaround constant used, in minutes."""
    turnaround_source: str
    """Which turnaround bound was applied: 'p10_floor' or 'p75_ceiling'."""
    predicted_departure: datetime
    """Computed estimated departure time: predicted_arrival + turnaround."""
    delay_minutes: int
    """Final predicted delay in whole minutes."""

    @computed_field
    @property
    def explanation(self) -> str:
        """Human-readable description of this prediction step."""
        est_label = " (est.)" if self.arrival_source == "estimated_crossing" else ""
        delay_label = f" (+{self.delay_minutes} min)" if self.delay_minutes > 0 else ""
        return (
            f"Expected to arrive {self.arriving_terminal_name} "
            f"~{_fmt(self.predicted_arrival)}{est_label}; "
            f"expected departure {_fmt(self.predicted_departure)}{delay_label}"
        )


class FlatPropagationTrace(BaseModel):
    """Trace for delays propagated unchanged from the vessel's current delay."""

    source: Literal["flat_propagation"] = "flat_propagation"
    reason: Literal["at_dock_delay", "en_route_delay"]
    """Whether the vessel is delayed at dock or departed late."""
    current_delay_minutes: float
    """The delay carried forward from the vessel."""
    predicted_departure: datetime | None = None
    """Scheduled departure shifted by delay (None if no scheduled departure)."""
    delay_minutes: int
    """Final predicted delay in whole minutes."""

    @computed_field
    @property
    def explanation(self) -> str:
        """Human-readable description of this prediction step."""
        if self.reason == "at_dock_delay":
            verb = (
                "Vessel delayed at dock" if self.delay_minutes > 0 else "Vessel at dock"
            )
        else:
            verb = (
                "Vessel departed late" if self.delay_minutes > 0 else "Vessel departed"
            )
        if self.predicted_departure:
            delay_label = (
                f" (+{self.delay_minutes} min)" if self.delay_minutes > 0 else ""
            )
            return f"{verb}; expected departure {_fmt(self.predicted_departure)}{delay_label}"
        return verb


class RePropagatedTrace(BaseModel):
    """Trace for later sailings that inherit an ETA-bounded prediction."""

    source: Literal["re_propagated"] = "re_propagated"
    current_delay_minutes: float
    """The ETA-bounded delay inherited from the preceding sailing."""
    predicted_departure: datetime | None = None
    """Scheduled departure shifted by delay (None if no scheduled departure)."""
    delay_minutes: int
    """Final predicted delay in whole minutes."""

    @computed_field
    @property
    def explanation(self) -> str:
        """Human-readable description of this prediction step."""
        delay_label = (
            f"{self.delay_minutes} min delay" if self.delay_minutes > 0 else "On time"
        )
        if self.predicted_departure:
            return f"{delay_label}; expected departure {_fmt(self.predicted_departure)}"
        return f"{delay_label} (propagated)"


PredictionTrace = Annotated[
    EtaBoundedTrace | FlatPropagationTrace | RePropagatedTrace,
    Field(discriminator="source"),
]
"""Union of all prediction trace types, discriminated by 'source'."""


class RouteSailing(BaseModel):
    scheduled_departure: datetime | None
    delay_in_minutes: int | None = None
    vessel_name: str
    vessel_position_num: int
    departed: bool = False
    # Structured prediction metadata explaining how delay_in_minutes was derived
    prediction_trace: PredictionTrace | None = None
    # Live vessel state for the current/next sailing
    vessel_at_dock: bool | None = None
    vessel_left_dock: datetime | None = None
    vessel_eta: datetime | None = None
    vessel_delay_minutes: int | None = None
    vessel_docked_since: datetime | None = (
        None  # from DB snapshots, fallback when eta is null
    )
    # Inbound vessel info (preceding sailing heading toward this departure terminal)
    inbound_vessel_name: str | None = None
    inbound_vessel_at_dock: bool | None = None
    inbound_vessel_left_dock: datetime | None = None
    inbound_vessel_eta: datetime | None = None
    inbound_vessel_from_terminal: str | None = None
    inbound_vessel_scheduled_departure: datetime | None = None
    inbound_vessel_delay_minutes: int | None = None
    # Structured prediction for the inbound vessel's arrival at this terminal
    inbound_prediction_trace: PredictionTrace | None = None


class DirectionalSailing(RouteSailing):
    departing_terminal_id: int
    arriving_terminal_id: int
    departing_terminal_name: str
    arriving_terminal_name: str

    def to_route_sailing(self) -> RouteSailing:
        return RouteSailing(
            **self.model_dump(
                include={
                    "scheduled_departure",
                    "delay_in_minutes",
                    "vessel_name",
                    "vessel_position_num",
                    "departed",
                    "prediction_trace",
                    "vessel_at_dock",
                    "vessel_left_dock",
                    "vessel_eta",
                    "vessel_delay_minutes",
                    "vessel_docked_since",
                    "inbound_vessel_name",
                    "inbound_vessel_at_dock",
                    "inbound_vessel_left_dock",
                    "inbound_vessel_eta",
                    "inbound_vessel_from_terminal",
                    "inbound_vessel_scheduled_departure",
                    "inbound_vessel_delay_minutes",
                    "inbound_prediction_trace",
                }
            )
        )


class DirectionalSchedule(BaseModel):
    departing_terminal_id: int
    departing_terminal_name: str
    arriving_terminal_id: int
    arriving_terminal_name: str
    times: list[RouteSailing]


class RouteSchedule(BaseModel):
    route_name: list[str]
    route_id: int
    schedules: list[DirectionalSchedule]


class FlatSailingSpace(BaseModel):
    departing_terminal_id: int = Field(alias="DepartingTerminalID")
    departing_terminal_name: str = Field(alias="DepartingTerminalName")
    departure_time: datetime = Field(alias="DepartureTime")
    vessel_name: str = Field(alias="VesselName")
    vessel_id: int = Field(alias="VesselID")
    arriving_terminal_id: int = Field(alias="ArrivingTerminalID")
    arriving_terminal_name: str = Field(alias="ArrivingTerminalName")
    max_space_count: int = Field(None, alias="MaxSpaceCount")
    drive_up_space_count: int = Field(None, alias="DriveUpSpaceCount")
    reservable_space_count: int | None = Field(None, alias="ReservableSpaceCount")

    class Config:
        populate_by_name = True
