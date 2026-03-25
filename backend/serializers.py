from datetime import datetime, timedelta

from pydantic import BaseModel, Field, field_validator

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


class RouteSailing(BaseModel):
    scheduled_departure: datetime | None
    delay_in_minutes: int | None = None
    delay_lower_bound: int | None = None
    delay_upper_bound: int | None = None
    vessel_name: str
    vessel_position_num: int
    departed: bool = False
    # Live vessel state for the current/next sailing
    vessel_at_dock: bool | None = None
    vessel_left_dock: datetime | None = None
    vessel_eta: datetime | None = None
    vessel_delay_minutes: int | None = None
    # Inbound vessel info (vessel is crossing toward this departure terminal)
    inbound_vessel_name: str | None = None
    inbound_vessel_left_dock: datetime | None = None
    inbound_vessel_eta: datetime | None = None
    inbound_vessel_from_terminal: str | None = None


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
                    "delay_lower_bound",
                    "delay_upper_bound",
                    "vessel_name",
                    "vessel_position_num",
                    "departed",
                    "vessel_at_dock",
                    "vessel_left_dock",
                    "vessel_eta",
                    "vessel_delay_minutes",
                    "inbound_vessel_name",
                    "inbound_vessel_left_dock",
                    "inbound_vessel_eta",
                    "inbound_vessel_from_terminal",
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
