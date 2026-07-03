from datetime import datetime
from zoneinfo import ZoneInfo

from backend.sailing_id import SailingIdParts, make_sailing_id, parse_sailing_id
from backend.serializers import DirectionalSailing

PT = ZoneInfo("America/Los_Angeles")


class TestMakeSailingId:
    def test_basic(self):
        assert make_sailing_id("1435", 7, 3) == "1435-7-3"

    def test_zero_padded_time(self):
        assert make_sailing_id("0635", 3, 7) == "0635-3-7"

    def test_midnight(self):
        assert make_sailing_id("0000", 1, 2) == "0000-1-2"


class TestParseSailingId:
    def test_basic(self):
        parts = parse_sailing_id("1435-7-3")
        assert parts is not None
        assert parts.time == "1435"
        assert parts.dep_terminal == 7
        assert parts.arr_terminal == 3

    def test_hour_minute(self):
        parts = parse_sailing_id("0635-3-7")
        assert parts is not None
        assert parts.hour == 6
        assert parts.minute == 35

    def test_invalid_format(self):
        assert parse_sailing_id("bad") is None
        assert parse_sailing_id("1435-7") is None
        assert parse_sailing_id("1435-7-3-extra") is None

    def test_non_numeric_terminal(self):
        assert parse_sailing_id("1435-abc-3") is None

    def test_roundtrip(self):
        original = "1435-7-3"
        parts = parse_sailing_id(original)
        assert str(parts) == original


class TestSailingIdParts:
    def test_str(self):
        parts = SailingIdParts(time="0800", dep_terminal=1, arr_terminal=2)
        assert str(parts) == "0800-1-2"

    def test_frozen(self):
        parts = SailingIdParts(time="1435", dep_terminal=7, arr_terminal=3)
        try:
            parts.time = "0000"  # type: ignore[misc]
            raise AssertionError("Should be frozen")
        except AttributeError:
            pass


class TestDirectionalSailingSailingId:
    def test_sailing_id_property(self):
        sailing = DirectionalSailing(
            departing_terminal_id=7,
            arriving_terminal_id=3,
            departing_terminal_name="Seattle",
            arriving_terminal_name="Bainbridge Island",
            scheduled_departure=datetime(2024, 1, 1, 14, 35, tzinfo=PT),
            vessel_name="Walla Walla",
            vessel_position_num=1,
        )
        assert sailing.sailing_id == "1435-7-3"

    def test_sailing_id_none_when_no_departure(self):
        sailing = DirectionalSailing(
            departing_terminal_id=7,
            arriving_terminal_id=3,
            departing_terminal_name="Seattle",
            arriving_terminal_name="Bainbridge Island",
            scheduled_departure=None,
            vessel_name="Walla Walla",
            vessel_position_num=1,
        )
        assert sailing.sailing_id is None

    def test_sailing_id_early_morning(self):
        sailing = DirectionalSailing(
            departing_terminal_id=3,
            arriving_terminal_id=7,
            departing_terminal_name="Bainbridge Island",
            arriving_terminal_name="Seattle",
            scheduled_departure=datetime(2024, 6, 15, 6, 5, tzinfo=PT),
            vessel_name="Spokane",
            vessel_position_num=2,
        )
        assert sailing.sailing_id == "0605-3-7"

    def test_sailing_id_in_model_dump(self):
        """sailing_id should be included in serialized output via computed_field."""
        sailing = DirectionalSailing(
            departing_terminal_id=7,
            arriving_terminal_id=3,
            departing_terminal_name="Seattle",
            arriving_terminal_name="Bainbridge Island",
            scheduled_departure=datetime(2024, 1, 1, 14, 35, tzinfo=PT),
            vessel_name="Walla Walla",
            vessel_position_num=1,
        )
        data = sailing.model_dump()
        assert data["sailing_id"] == "1435-7-3"
