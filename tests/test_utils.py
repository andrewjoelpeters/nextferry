from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from backend.utils import (format_confidence_text, format_delay_text,
                           format_time_until, is_peak_hour, parse_ms_date)

PT = ZoneInfo("America/Los_Angeles")


def _now():
    return datetime.now(PT)


class TestParseMsDate:
    def test_none_returns_none(self):
        assert parse_ms_date(None) is None

    def test_parses_wsdot_date_format(self):
        # /Date(1700000000000-0800)/ → 2023-11-14 in Pacific
        result = parse_ms_date("/Date(1700000000000-0800)/")
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    def test_parses_without_offset(self):
        result = parse_ms_date("/Date(1700000000000)/")
        assert isinstance(result, datetime)

    def test_non_matching_string_returned_as_is(self):
        assert parse_ms_date("not-a-date") == "not-a-date"


class TestFormatTimeUntil:
    def test_none_returns_na(self):
        assert format_time_until(None) == ("N/A", "status-unknown")

    def test_future_minutes(self):
        future = _now() + timedelta(minutes=25)
        text, status = format_time_until(future)
        # int() truncation means 25 minutes might show as 24m
        assert text in ("24m", "25m")
        assert status == "status-on-time"

    def test_future_hours(self):
        future = _now() + timedelta(hours=2, minutes=15)
        text, status = format_time_until(future)
        assert text in ("2h 14m", "2h 15m")
        assert status == "status-on-time"

    def test_departing_now(self):
        almost_now = _now() + timedelta(minutes=1)
        text, status = format_time_until(almost_now)
        assert text == "Now"
        assert status == "status-departing"

    def test_just_past(self):
        just_past = _now() - timedelta(minutes=3)
        text, status = format_time_until(just_past)
        assert text == "Now"
        assert status == "status-departing"

    def test_departed(self):
        long_past = _now() - timedelta(minutes=10)
        text, status = format_time_until(long_past)
        assert text == "Departed"
        assert status == "status-departed"

    def test_naive_datetime_gets_timezone(self):
        future = datetime.now() + timedelta(minutes=30)
        text, status = format_time_until(future)
        assert "m" in text
        assert status == "status-on-time"


class TestFormatDelayText:
    def test_no_delay(self):
        assert format_delay_text(0) == ("", "status-on-time")
        assert format_delay_text(None) == ("", "status-on-time")

    def test_positive_delay(self):
        text, status = format_delay_text(5)
        assert text == " (+5m)"
        assert status == "status-delayed"

    def test_negative_delay_early(self):
        text, status = format_delay_text(-3)
        assert text == " (-3m)"
        assert status == "status-early"


class TestFormatConfidenceText:
    def test_none_bounds(self):
        assert format_confidence_text(None, None) == ""
        assert format_confidence_text(None, 5) == ""
        assert format_confidence_text(5, None) == ""

    def test_zero_bounds(self):
        assert format_confidence_text(0, 0) == ""

    def test_positive_bounds(self):
        assert format_confidence_text(1, 5) == "(+1 to +5m)"

    def test_mixed_bounds(self):
        assert format_confidence_text(-2, 5) == "(-2 to +5m)"


class TestIsPeakHour:
    def test_morning_peak(self):
        assert is_peak_hour(7) is True
        assert is_peak_hour(9) is True

    def test_afternoon_peak(self):
        assert is_peak_hour(17) is True

    def test_off_peak(self):
        assert is_peak_hour(12) is False
        assert is_peak_hour(22) is False
