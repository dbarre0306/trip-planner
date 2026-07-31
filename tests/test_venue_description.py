from unittest.mock import patch

import pytest

from trip_planner.domain import InterestId
from trip_planner.venue_description import generate_description


@patch("trip_planner.venue_description.chat_completion")
def test_generate_description_uses_notes_as_primary_source(mock_chat_completion):
    mock_chat_completion.return_value = "A scenic canyon perfect for a hike."

    result = generate_description(
        "Sabino Canyon", InterestId.HIKING, "Tucson, AZ", ["A scenic hiking spot", "Great views"]
    )

    assert result == "A scenic canyon perfect for a hike."
    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "A scenic hiking spot" in prompt
    assert "Great views" in prompt
    assert "Sabino Canyon" in prompt
    assert "hiking" in prompt
    assert "Tucson, AZ" in prompt


@patch("trip_planner.venue_description.chat_completion")
def test_generate_description_falls_back_to_name_interest_destination_when_no_notes(
    mock_chat_completion,
):
    mock_chat_completion.return_value = "A mysterious spot worth exploring."

    result = generate_description("Mystery Spot", InterestId.HIKING, "Tucson, AZ", [])

    assert result == "A mysterious spot worth exploring."
    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "Mystery Spot" in prompt
    assert "hiking" in prompt
    assert "Tucson, AZ" in prompt
    assert "Notes:" not in prompt


@patch("trip_planner.venue_description.chat_completion")
def test_generate_description_prompt_excludes_url_location_and_hours(mock_chat_completion):
    mock_chat_completion.return_value = "A great place to visit."

    generate_description("Sabino Canyon", InterestId.HIKING, "Tucson, AZ", ["A scenic hiking spot"])

    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "URL" in prompt
    assert "address" in prompt.lower()
    assert "hours of operation" in prompt.lower()


@patch("trip_planner.venue_description.chat_completion")
def test_generate_description_truncates_to_max_length(mock_chat_completion):
    mock_chat_completion.return_value = "x" * 400

    result = generate_description("Sabino Canyon", InterestId.HIKING, "Tucson, AZ", ["A scenic hiking spot"])

    assert len(result) == 300


@patch("trip_planner.venue_description.chat_completion")
def test_generate_description_truncation_ends_on_a_complete_sentence(mock_chat_completion):
    sentence = "Elevate your dining experience at The Moonstone, a rooftop bar with stunning views. "
    mock_chat_completion.return_value = sentence * 5

    result = generate_description("The Moonstone", InterestId.RESTAURANTS, "Tucson, AZ", ["A rooftop bar"])

    assert len(result) <= 300
    assert result.endswith(".")
    assert not result.endswith("impre")


@patch("trip_planner.venue_description.chat_completion")
def test_generate_description_propagates_errors(mock_chat_completion):
    mock_chat_completion.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError):
        generate_description("Sabino Canyon", InterestId.HIKING, "Tucson, AZ", ["A scenic hiking spot"])
