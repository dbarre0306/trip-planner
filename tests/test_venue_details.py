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
        '{"location": "1234 Canyon Rd, Tucson, AZ", "location_type": "STREET_ADDRESS", '
        '"hours_of_operation": null, "duration_minutes": null}'
    )

    result = extract_venue_details("The Moonstone", ["Located at 1234 Canyon Rd, Tucson, AZ"])

    assert result.location == "1234 Canyon Rd, Tucson, AZ"
    assert result.location_type == "STREET_ADDRESS"
    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "1234 Canyon Rd" in prompt
    assert "The Moonstone" in prompt


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_falls_back_to_distinct_place(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": "Sabino Canyon Recreation Area", "location_type": "PLACE", '
        '"hours_of_operation": null, "duration_minutes": null}'
    )

    result = extract_venue_details(
        "Blackett's Ridge", ["A challenging trail within Sabino Canyon Recreation Area"]
    )

    assert result.location == "Sabino Canyon Recreation Area"
    assert result.location_type == "PLACE"


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_returns_null_location_when_neither_found(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "location_type": null, "hours_of_operation": null, '
        '"duration_minutes": null}'
    )

    result = extract_venue_details("Mystery Spot", ["A quirky roadside attraction"])

    assert result.location is None
    assert result.location_type is None


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_never_returns_venue_name_as_location(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": "Blackett\'s Ridge", "location_type": "PLACE", '
        '"hours_of_operation": null, "duration_minutes": null}'
    )

    result = extract_venue_details("Blackett's Ridge", ["A trail in the desert"])

    assert result.location is None
    assert result.location_type is None


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_coerces_unexpected_location_type_to_none(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": "Sabino Canyon Recreation Area", "location_type": "SOMETHING_ELSE", '
        '"hours_of_operation": null, "duration_minutes": null}'
    )

    result = extract_venue_details(
        "Blackett's Ridge", ["A challenging trail within Sabino Canyon Recreation Area"]
    )

    assert result.location == "Sabino Canyon Recreation Area"
    assert result.location_type is None


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_calls_llm_when_no_notes(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": null, "duration_minutes": null}'
    )

    result = extract_venue_details("Mystery Spot", [])

    mock_chat_completion.assert_called_once()
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
def test_extract_venue_details_uses_general_knowledge_hours_when_notes_silent(
    mock_chat_completion,
):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": "Daily 9am-5pm", "duration_minutes": null}'
    )

    result = extract_venue_details("The Grand Canyon Visitor Center", ["A popular viewpoint"])

    assert result.hours_of_operation == "Daily 9am-5pm"
    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "not limited to the notes" in prompt.lower()


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_uses_general_knowledge_hours_when_no_notes(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": "Daily 6am-10pm", "duration_minutes": null}'
    )

    result = extract_venue_details("Central Park", [])

    assert result.hours_of_operation == "Daily 6am-10pm"
    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "(none provided)" in prompt


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
def test_extract_venue_details_marks_closed_when_notes_indicate_it(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": null, "duration_minutes": null, '
        '"closed": true}'
    )

    result = extract_venue_details("The Moonstone", ["This restaurant has permanently closed"])

    assert result.closed is True


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_defaults_closed_to_false_when_not_indicated(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": null, "duration_minutes": null, '
        '"closed": false}'
    )

    result = extract_venue_details("The Moonstone", ["A rooftop bar"])

    assert result.closed is False


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_defaults_closed_to_false_when_field_missing(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": null, "duration_minutes": null}'
    )

    result = extract_venue_details("The Moonstone", ["A rooftop bar"])

    assert result.closed is False


@patch("trip_planner.venue_details.chat_completion")
def test_venue_details_defaults_closed_to_false_when_no_notes(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": null, "duration_minutes": null, '
        '"closed": false}'
    )

    result = extract_venue_details("Mystery Spot", [])

    assert result.closed is False
    assert result == VenueDetails()


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_prompt_distinguishes_ruins_from_closed(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": null, "duration_minutes": null, '
        '"closed": false}'
    )

    result = extract_venue_details(
        "Bowen Stone House",
        ["This is a long-abandoned relic, the ruins of an old stone homestead."],
    )

    assert result.closed is False
    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "ruin" in prompt.lower()


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_prompt_distinguishes_temporary_from_permanent_closure(
    mock_chat_completion,
):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": null, "duration_minutes": null, '
        '"closed": false}'
    )

    result = extract_venue_details(
        "Some Trailhead",
        ["Temporarily closed for construction from Monday through Friday."],
    )

    assert result.closed is False
    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "reopening" in prompt.lower()


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_prompt_distinguishes_weekly_day_off_from_closed(
    mock_chat_completion,
):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": "Mon - Closed, Tue - Closed, '
        'Wed-Sat 12pm-8pm", "duration_minutes": null, "closed": false}'
    )

    result = extract_venue_details(
        "Batey Puerto Rican Gastronomy",
        ["Mon - Closed, Tue - Closed, Wed-Sat 12pm-8pm, Sunday 1pm-8pm"],
    )

    assert result.closed is False
    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "weekly hours listing" in prompt.lower()


@patch("trip_planner.venue_details.chat_completion")
def test_extract_venue_details_prompt_restricts_other_fields_to_notes(mock_chat_completion):
    mock_chat_completion.return_value = (
        '{"location": null, "hours_of_operation": null, "duration_minutes": null}'
    )

    extract_venue_details("The Moonstone", ["A rooftop bar"])

    prompt = mock_chat_completion.call_args[0][0][0]["content"].lower()
    assert "exactly as stated in the notes" not in prompt
    assert "if no hours are stated, use null" not in prompt
    assert "use only the notes below" in prompt


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
