import json
from unittest.mock import patch

from trip_planner.venue_operating_hours import OperatingHours, parse_operating_hours


def test_parse_operating_hours_returns_all_day_when_hours_are_missing():
    result = parse_operating_hours(None)

    assert result == OperatingHours()
    assert result.is_available(weekday=0, start_minutes=0, end_minutes=24 * 60)


@patch("trip_planner.venue_operating_hours.chat_completion")
def test_parse_operating_hours_does_not_call_llm_when_hours_are_missing(mock_chat_completion):
    parse_operating_hours(None)
    parse_operating_hours("")

    mock_chat_completion.assert_not_called()


@patch("trip_planner.venue_operating_hours.chat_completion")
def test_parse_operating_hours_extracts_open_and_close_time(mock_chat_completion):
    mock_chat_completion.return_value = json.dumps(
        {"open_time": "13:00", "close_time": "20:00", "closed_weekdays": []}
    )

    result = parse_operating_hours("Daily 1pm-8pm")

    assert result.open_minutes == 13 * 60
    assert result.close_minutes == 20 * 60
    assert result.closed_weekdays == frozenset()


@patch("trip_planner.venue_operating_hours.chat_completion")
def test_parse_operating_hours_extracts_closed_weekdays(mock_chat_completion):
    mock_chat_completion.return_value = json.dumps(
        {"open_time": "09:00", "close_time": "17:00", "closed_weekdays": ["Monday"]}
    )

    result = parse_operating_hours("Tue-Sun 9am-5pm, closed Mondays")

    assert result.closed_weekdays == frozenset({0})


@patch("trip_planner.venue_operating_hours.chat_completion")
def test_parse_operating_hours_prompt_includes_the_hours_text(mock_chat_completion):
    mock_chat_completion.return_value = json.dumps(
        {"open_time": None, "close_time": None, "closed_weekdays": []}
    )

    parse_operating_hours("Open 24 hours")

    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "Open 24 hours" in prompt


@patch("trip_planner.venue_operating_hours.chat_completion")
def test_parse_operating_hours_defaults_when_response_is_unparsable(mock_chat_completion):
    mock_chat_completion.return_value = "not json"

    result = parse_operating_hours("Some hours")

    assert result == OperatingHours()


def test_is_available_rejects_time_before_opening():
    hours = OperatingHours(open_minutes=13 * 60, close_minutes=20 * 60)

    assert hours.is_available(weekday=0, start_minutes=10 * 60, end_minutes=11 * 60) is False


def test_is_available_rejects_time_after_closing():
    hours = OperatingHours(open_minutes=9 * 60, close_minutes=17 * 60)

    assert hours.is_available(weekday=0, start_minutes=16 * 60, end_minutes=18 * 60) is False


def test_is_available_accepts_time_within_hours():
    hours = OperatingHours(open_minutes=9 * 60, close_minutes=17 * 60)

    assert hours.is_available(weekday=0, start_minutes=10 * 60, end_minutes=11 * 60) is True


def test_is_available_rejects_closed_weekday():
    hours = OperatingHours(closed_weekdays=frozenset({0}))

    assert hours.is_available(weekday=0, start_minutes=10 * 60, end_minutes=11 * 60) is False
    assert hours.is_available(weekday=1, start_minutes=10 * 60, end_minutes=11 * 60) is True


def test_is_available_ignores_weekday_restriction_when_weekday_unknown():
    hours = OperatingHours(closed_weekdays=frozenset({0}))

    assert hours.is_available(weekday=None, start_minutes=10 * 60, end_minutes=11 * 60) is True
