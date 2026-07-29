from unittest.mock import patch

from trip_planner.venue_details import (
    DEFAULT_DURATION_MINUTES,
    VenueDetails,
    estimate_duration_minutes,
    extract_venue_details,
)


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_uses_street_address(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": "1234 Canyon Rd, Tucson, AZ", "hours_of_operation": null, '
        '"duration_minutes": null}'
    )

    result = extract_venue_details("The Moonstone", ["Located at 1234 Canyon Rd, Tucson, AZ"])

    assert result.location == "1234 Canyon Rd, Tucson, AZ"
    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "1234 Canyon Rd" in prompt
    assert "The Moonstone" in prompt


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_falls_back_to_distinct_place(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": "Sabino Canyon Recreation Area", "hours_of_operation": null, '
        '"duration_minutes": null}'
    )

    result = extract_venue_details(
        "Blackett's Ridge", ["A challenging trail within Sabino Canyon Recreation Area"]
    )

    assert result.location == "Sabino Canyon Recreation Area"


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_returns_null_location_when_neither_found(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": null, "duration_minutes": null}'
    )

    result = extract_venue_details("Mystery Spot", ["A quirky roadside attraction"])

    assert result.location is None


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_never_returns_venue_name_as_location(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": "Blackett\'s Ridge", "hours_of_operation": null, "duration_minutes": null}'
    )

    result = extract_venue_details("Blackett's Ridge", ["A trail in the desert"])

    assert result.location is None


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_skips_call_when_no_notes(mock_chat_completion):
    result = extract_venue_details("Mystery Spot", [])

    mock_chat_completion.assert_not_called()
    assert result == VenueDetails()


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_uses_explicit_hours(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": "Mon-Fri 9am-5pm", "duration_minutes": null}'
    )

    result = extract_venue_details("The Moonstone", ["Open Mon-Fri 9am-5pm"])

    assert result.hours_of_operation == "Mon-Fri 9am-5pm"


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_accepts_alternate_hours_format(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": "9-5 daily", "duration_minutes": null}'
    )

    result = extract_venue_details("The Moonstone", ["Hours: 9-5 daily"])

    assert result.hours_of_operation == "9-5 daily"


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_returns_null_hours_when_not_stated(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": null, "duration_minutes": null}'
    )

    result = extract_venue_details("The Moonstone", ["A rooftop bar"])

    assert result.hours_of_operation is None


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_converts_explicit_duration_to_minutes(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": null, "duration_minutes": 120}'
    )

    result = extract_venue_details("The Moonstone", ["Visits typically last about 2 hours"])

    assert result.duration_minutes == 120


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_returns_null_duration_when_not_stated(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": null, "duration_minutes": null}'
    )

    result = extract_venue_details("The Moonstone", ["A rooftop bar"])

    assert result.duration_minutes is None


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_tolerates_malformed_json(mock_chat_completion):
    mock_chat_completion.return_value = "not valid json"

    result = extract_venue_details("The Moonstone", ["A rooftop bar"])

    assert result == VenueDetails()


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_tolerates_markdown_fenced_json(mock_chat_completion):
    mock_chat_completion.return_value = (
        '```json\n{"location": null, "hours_of_operation": null, "duration_minutes": 45}\n```'
    )

    result = extract_venue_details("The Moonstone", ["A rooftop bar, about 45 minutes"])

    assert result.duration_minutes == 45


@patch("trip_planner.venue_details.chat_completion")
def test_estimate_duration_minutes_uses_model_estimate(mock_chat_completion):
    mock_chat_completion.return_value = "90"

    result = estimate_duration_minutes("The Moonstone", "Tucson, AZ")

    assert result == 90
    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "The Moonstone" in prompt
    assert "Tucson, AZ" in prompt
    assert "search" in prompt.lower()


@patch("trip_planner.venue_details.chat_completion")
def test_estimate_duration_minutes_parses_estimate_with_extra_words(mock_chat_completion):
    mock_chat_completion.return_value = "About 90 minutes for a typical visit."

    result = estimate_duration_minutes("The Moonstone", None)

    assert result == 90


@patch("trip_planner.venue_details.chat_completion")
def test_estimate_duration_minutes_falls_back_to_default_when_unparseable(mock_chat_completion):
    mock_chat_completion.return_value = "I'm not sure."

    result = estimate_duration_minutes("Obscure Spot", None)

    assert result == DEFAULT_DURATION_MINUTES
