from unittest.mock import patch

from trip_planner.domain import InterestId
from trip_planner.venue_cost import VenueCost, estimate_venue_cost


@patch("trip_planner.venue_cost.chat_completion")
def test_estimate_venue_cost_parses_a_well_formed_response(mock_chat_completion):
    mock_chat_completion.return_value = '{"cost_per_adult": 25, "cost_per_child": 12.5}'

    result = estimate_venue_cost(
        "Sabino Canyon",
        InterestId.HIKING,
        "Tucson, AZ",
        "A scenic canyon perfect for a hike.",
        ["A scenic hiking spot", "Great views"],
        ["Hiking area"],
    )

    assert result == VenueCost(per_adult=25.0, per_child=12.5)


@patch("trip_planner.venue_cost.chat_completion")
def test_estimate_venue_cost_prompt_includes_all_expected_inputs(mock_chat_completion):
    mock_chat_completion.return_value = '{"cost_per_adult": 25, "cost_per_child": 12.5}'

    estimate_venue_cost(
        "Sabino Canyon",
        InterestId.HIKING,
        "Tucson, AZ",
        "A scenic canyon perfect for a hike.",
        ["A scenic hiking spot", "Great views"],
        ["Hiking area"],
    )

    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "Sabino Canyon" in prompt
    assert "hiking" in prompt
    assert "Tucson, AZ" in prompt
    assert "A scenic canyon perfect for a hike." in prompt
    assert "A scenic hiking spot" in prompt
    assert "Great views" in prompt
    assert "Hiking area" in prompt


@patch("trip_planner.venue_cost.chat_completion")
def test_estimate_venue_cost_handles_a_free_venue(mock_chat_completion):
    mock_chat_completion.return_value = '{"cost_per_adult": 0, "cost_per_child": 0}'

    result = estimate_venue_cost(
        "City Park", None, "Tucson, AZ", "A public park.", [], []
    )

    assert result == VenueCost(per_adult=0.0, per_child=0.0)


@patch("trip_planner.venue_cost.chat_completion")
def test_estimate_venue_cost_returns_none_when_llm_gives_explicit_nulls(mock_chat_completion):
    mock_chat_completion.return_value = '{"cost_per_adult": null, "cost_per_child": null}'

    result = estimate_venue_cost(
        "Mystery Spot", None, "Tucson, AZ", "A mysterious little spot.", [], []
    )

    assert result == VenueCost(per_adult=None, per_child=None)


@patch("trip_planner.venue_cost.chat_completion")
def test_estimate_venue_cost_returns_none_when_response_is_unparsable(mock_chat_completion):
    mock_chat_completion.return_value = "I'm not sure, sorry!"

    result = estimate_venue_cost(
        "Mystery Spot", None, "Tucson, AZ", "A mysterious little spot.", [], []
    )

    assert result == VenueCost(per_adult=None, per_child=None)


@patch("trip_planner.venue_cost.chat_completion")
def test_estimate_venue_cost_returns_none_for_a_single_missing_field(mock_chat_completion):
    mock_chat_completion.return_value = '{"cost_per_adult": 15}'

    result = estimate_venue_cost(
        "Mystery Spot", None, "Tucson, AZ", "A mysterious little spot.", [], []
    )

    assert result == VenueCost(per_adult=15.0, per_child=None)
