import asyncio
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest

from trip_planner.app import (
    _fmt_date,
    _itinerary_to_html,
    _render_day,
    _to_12h,
    _travel_dates,
    _trip_summary_html,
    on_schedule_itinerary,
)
from trip_planner.models import Itinerary, ItineraryDay, ScheduledVenue


def _venue_entry(**overrides):
    defaults = dict(
        name="Sabino Canyon",
        interest_category="Outdoor Activities",
        duration_minutes=90,
        start_time="09:00",
        estimated_cost_usd=0.0,
        description="A scenic hike.",
        location="123 Canyon Rd",
        url="https://example.com",
        hours_of_operation="9am-5pm",
    )
    defaults.update(overrides)
    return ScheduledVenue(**defaults)


def _day(**overrides):
    venues = overrides.pop("venues", None)
    defaults = dict(day_number=1, date="2026-09-01")
    defaults.update(overrides)
    return ItineraryDay(venues=venues if venues is not None else [_venue_entry()], **defaults)


def _itinerary(days=None):
    return Itinerary(
        destination="Tucson, AZ",
        num_adults=2,
        num_children=0,
        days=days if days is not None else [_day()],
    )


async def _collect(agen):
    return [item async for item in agen]


# ── _fmt_date ────────────────────────────────────────────────

def test_fmt_date_formats_date_object():
    assert _fmt_date(date(2026, 9, 1)) == "2026-09-01"


def test_fmt_date_formats_timestamp():
    ts = datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp()
    assert _fmt_date(ts) == "2026-09-01"


def test_fmt_date_falls_back_to_str():
    assert _fmt_date("2026-09-01") == "2026-09-01"


# ── _travel_dates ────────────────────────────────────────────

def test_travel_dates_from_date_object():
    assert _travel_dates(date(2026, 9, 1), 3) == ["2026-09-01", "2026-09-02", "2026-09-03"]


def test_travel_dates_from_datetime_object():
    assert _travel_dates(datetime(2026, 9, 1), 2) == ["2026-09-01", "2026-09-02"]


def test_travel_dates_from_timestamp():
    ts = datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp()
    assert _travel_dates(ts, 1) == ["2026-09-01"]


def test_travel_dates_from_string():
    assert _travel_dates("2026-09-01", 2) == ["2026-09-01", "2026-09-02"]


# ── _to_12h ──────────────────────────────────────────────────

@pytest.mark.parametrize(
    "time_str,expected",
    [
        ("09:00", "9:00 AM"),
        ("00:00", "12:00 AM"),
        ("12:00", "12:00 PM"),
        ("13:05", "1:05 PM"),
        ("23:59", "11:59 PM"),
    ],
)
def test_to_12h_converts_24h_time(time_str, expected):
    assert _to_12h(time_str) == expected


def test_to_12h_returns_original_on_bad_input():
    assert _to_12h("not-a-time") == "not-a-time"


def test_to_12h_returns_original_when_none():
    assert _to_12h(None) is None


# ── _trip_summary_html ───────────────────────────────────────

def test_trip_summary_html_escapes_destination():
    html = _trip_summary_html("<script>alert(1)</script>", date(2026, 9, 1), 3, 2, 0, [])

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_trip_summary_html_shows_placeholder_when_no_interests_selected():
    html = _trip_summary_html("Tucson, AZ", date(2026, 9, 1), 3, 2, 0, [[], None])

    assert "General sightseeing" in html


def test_trip_summary_html_renders_selected_interests():
    html = _trip_summary_html("Tucson, AZ", date(2026, 9, 1), 3, 2, 0, [["Hiking"], ["Museums"]])

    assert "Hiking" in html
    assert "Museums" in html
    assert "General sightseeing" not in html


def test_trip_summary_html_button_disabled_by_default():
    html = _trip_summary_html("Tucson, AZ", date(2026, 9, 1), 3, 2, 0, [])

    assert "disabled" in html


def test_trip_summary_html_button_enabled_when_requested():
    html = _trip_summary_html("Tucson, AZ", date(2026, 9, 1), 3, 2, 0, [], button_enabled=True)

    assert "disabled" not in html


def test_trip_summary_html_includes_modify_trip_button():
    html = _trip_summary_html("Tucson, AZ", date(2026, 9, 1), 3, 2, 0, [])

    assert "Modify Trip" in html
    assert 'class="trip-modify-btn"' in html


def test_trip_summary_html_modify_button_disabled_by_default():
    html = _trip_summary_html("Tucson, AZ", date(2026, 9, 1), 3, 2, 0, [])

    modify_btn = html.split('class="trip-modify-btn"', 1)[1]
    assert modify_btn.startswith(" disabled")


def test_trip_summary_html_modify_button_enabled_when_requested():
    html = _trip_summary_html("Tucson, AZ", date(2026, 9, 1), 3, 2, 0, [], button_enabled=True)

    modify_btn = html.split('class="trip-modify-btn"', 1)[1]
    assert not modify_btn.startswith(" disabled")


def test_trip_summary_html_modify_trip_precedes_plan_a_new_trip():
    html = _trip_summary_html("Tucson, AZ", date(2026, 9, 1), 3, 2, 0, [], button_enabled=True)

    assert html.index("Modify Trip") < html.index("Plan a New Trip")


def test_trip_summary_html_pluralizes_days_and_party():
    html = _trip_summary_html("Tucson, AZ", date(2026, 9, 1), 1, 1, 1, [])

    assert "1 day" in html and "1 days" not in html
    assert "1 adult" in html and "1 adults" not in html
    assert "1 child" in html and "1 children" not in html


# ── _render_day / _itinerary_to_html ─────────────────────────

def test_render_day_includes_activity_details():
    day = _day(venues=[_venue_entry(name="El Charro", description="Great tacos.")])

    html = _render_day(day, _itinerary())

    assert "El Charro" in html
    assert "Great tacos." in html
    assert "itin-badge-outdoors" in html


def test_render_day_falls_back_to_other_badge_for_unknown_category():
    day = _day(venues=[_venue_entry(interest_category="Mystery")])

    html = _render_day(day, _itinerary())

    assert "itin-badge-other" in html
    assert "Mystery" in html


@pytest.mark.parametrize(
    "duration_minutes,expected",
    [(90, "1h 30m"), (60, "1h"), (45, "45m"), (0, "0m")],
)
def test_render_day_formats_duration(duration_minutes, expected):
    day = _day(venues=[_venue_entry(duration_minutes=duration_minutes)])

    html = _render_day(day, _itinerary())

    assert expected in html


def test_render_day_omits_meta_when_activity_has_no_extras():
    day = _day(venues=[_venue_entry(location=None, url=None, hours_of_operation=None)])

    html = _render_day(day, _itinerary())

    assert "itin-card-meta" not in html


def test_render_day_escapes_activity_fields():
    day = _day(venues=[_venue_entry(name="<b>Bold</b>", description="<i>Italic</i>")])

    html = _render_day(day, _itinerary())

    assert "<b>Bold</b>" not in html
    assert "&lt;b&gt;Bold&lt;/b&gt;" in html


def test_itinerary_to_html_includes_total_cost():
    day = _day(venues=[_venue_entry(estimated_cost_usd=123.45)])

    html = _itinerary_to_html(_itinerary(days=[day]))

    assert "$123.45" in html


def test_itinerary_to_html_splits_days_across_two_columns():
    days = [_day(day_number=i, date=f"2026-09-0{i}") for i in range(1, 4)]

    html = _itinerary_to_html(_itinerary(days=days))

    assert html.count("itin-day-header") == 3


# ── on_schedule_itinerary ─────────────────────────────────────

def _run(coro_factory, *args):
    return asyncio.run(_collect(coro_factory(*args)))


def test_on_schedule_itinerary_yields_validation_errors():
    results = _run(
        on_schedule_itinerary, "", date(2026, 9, 1), 3, 2, 0, ["Hiking", "Museums"]
    )

    assert len(results) == 1
    form_panel, results_panel, _summary, field_errors = results[0][:4]
    assert form_panel.get("visible") is True
    assert results_panel.get("visible") is False
    assert "Destination is required" in field_errors
    assert results[0][5].get("elem_classes") == ["field-error"]


def test_on_schedule_itinerary_flags_interests_group_on_too_few_interests():
    results = _run(
        on_schedule_itinerary, "Tucson, AZ", date(2026, 9, 1), 3, 2, 0, ["Hiking"]
    )

    field_errors = results[0][3]
    assert "Select from 2 to 4 interests" in field_errors
    assert results[0][4].get("elem_classes") == ["interests-outer", "field-error"]


@patch("trip_planner.app.is_valid_destination", return_value=False)
def test_on_schedule_itinerary_reports_unknown_destination(mock_is_valid):
    results = _run(
        on_schedule_itinerary, "Nowhereville", date(2026, 9, 1), 3, 2, 0, ["Hiking", "Museums"]
    )

    mock_is_valid.assert_called_once_with("Nowhereville")
    assert len(results) == 1
    form_panel, results_panel = results[-1][0], results[-1][1]
    assert form_panel.get("visible") is True
    assert results_panel.get("visible") is False
    field_errors = results[-1][3]
    assert "Unknown destination" in field_errors
    destination_update = results[-1][5]
    assert destination_update.get("elem_classes") == ["field-error"]


@patch("trip_planner.app.create_itinerary")
@patch("trip_planner.app.is_valid_destination", return_value=True)
def test_on_schedule_itinerary_renders_successful_itinerary(mock_is_valid, mock_create_itinerary):
    fake_itinerary = _itinerary(days=[_day(venues=[_venue_entry(name="Sabino Canyon")])])
    mock_create_itinerary.return_value = fake_itinerary

    results = _run(
        on_schedule_itinerary, "Tucson, AZ", date(2026, 9, 1), 3, 2, 0, ["Hiking", "Museums"]
    )

    results_html = results[-1][11]
    assert "Sabino Canyon" in results_html.get("value", "")


@patch("trip_planner.app.create_itinerary")
@patch("trip_planner.app.is_valid_destination", return_value=True)
def test_on_schedule_itinerary_handles_selected_interests_without_crashing(mock_is_valid, mock_create_itinerary):
    # Regression check: selecting a real interest used to raise AttributeError
    # in _format_interest because Interest had no `examples` field.
    mock_create_itinerary.return_value = _itinerary()

    results = _run(
        on_schedule_itinerary, "Tucson, AZ", date(2026, 9, 1), 3, 2, 0, ["Hiking"], ["Museums"]
    )

    status_md = results[-1][10]
    assert status_md.get("value", "") == ""


@patch("trip_planner.app.create_itinerary")
@patch("trip_planner.app.is_valid_destination", return_value=True)
def test_on_schedule_itinerary_reports_default_message_when_no_itinerary(mock_is_valid, mock_create_itinerary):
    mock_create_itinerary.return_value = _itinerary(days=[_day(venues=[])])

    results = _run(
        on_schedule_itinerary, "Tucson, AZ", date(2026, 9, 1), 3, 2, 0, ["Hiking", "Museums"]
    )

    status_md = results[-1][10]
    assert "No itinerary could be generated" in status_md.get("value", "")


@patch("trip_planner.app.create_itinerary", side_effect=RuntimeError("boom"))
@patch("trip_planner.app.is_valid_destination", return_value=True)
def test_on_schedule_itinerary_reports_exception(mock_is_valid, mock_create_itinerary):
    results = _run(
        on_schedule_itinerary, "Tucson, AZ", date(2026, 9, 1), 3, 2, 0, ["Hiking", "Museums"]
    )

    status_md = results[-1][10]
    assert "An error occurred" in status_md.get("value", "")
    assert "boom" in status_md.get("value", "")
