from unittest.mock import patch

from trip_planner.domain import InterestId
from trip_planner.venue_meal_tags import determine_meal_tags


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_uses_single_meal_period_stated_in_notes(mock_chat_completion):
    mock_chat_completion.return_value = '{"meal_tags": ["dinner"]}'

    result = determine_meal_tags(
        InterestId.RESTAURANTS, "The Grand Steakhouse", ["Dinner only, reservations recommended"], None
    )

    assert result == ["dinner"]


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_uses_multiple_meal_periods_stated_in_notes(mock_chat_completion):
    mock_chat_completion.return_value = '{"meal_tags": ["breakfast", "lunch"]}'

    result = determine_meal_tags(
        InterestId.RESTAURANTS, "Joe's Diner", ["Serves breakfast and lunch daily"], None
    )

    assert result == ["breakfast", "lunch"]


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_uses_hours_spanning_a_single_meal_period(mock_chat_completion):
    mock_chat_completion.return_value = '{"meal_tags": ["breakfast"]}'

    result = determine_meal_tags(InterestId.RESTAURANTS, "Sunrise Cafe", [], "6am-11am")

    assert result == ["breakfast"]
    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "6am-11am" in prompt


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_uses_hours_spanning_multiple_meal_periods(mock_chat_completion):
    mock_chat_completion.return_value = '{"meal_tags": ["lunch", "dinner"]}'

    result = determine_meal_tags(InterestId.RESTAURANTS, "The Grand Steakhouse", [], "11am-11pm")

    assert result == ["lunch", "dinner"]


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_notes_and_hours_agree(mock_chat_completion):
    mock_chat_completion.return_value = '{"meal_tags": ["dinner"]}'

    result = determine_meal_tags(
        InterestId.RESTAURANTS, "The Grand Steakhouse", ["Popular dinner spot"], "4pm-11pm"
    )

    assert result == ["dinner"]


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_notes_and_hours_disagreement_unions_both_signals(mock_chat_completion):
    mock_chat_completion.return_value = '{"meal_tags": ["breakfast", "lunch", "dinner"]}'

    result = determine_meal_tags(
        InterestId.RESTAURANTS, "The Grand Steakhouse", ["Popular breakfast spot"], "11am-11pm"
    )

    assert result == ["breakfast", "lunch", "dinner"]


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_best_guess_when_notes_and_hours_are_uninformative(mock_chat_completion):
    mock_chat_completion.return_value = '{"meal_tags": ["dinner"]}'

    result = determine_meal_tags(
        InterestId.RESTAURANTS, "The Grand Steakhouse", ["A fine dining spot"], None
    )

    assert result == ["dinner"]


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_best_guess_when_no_notes_and_no_hours_at_all(mock_chat_completion):
    mock_chat_completion.return_value = '{"meal_tags": ["dinner"]}'

    result = determine_meal_tags(InterestId.RESTAURANTS, "The Grand Steakhouse", [], None)

    assert result == ["dinner"]
    mock_chat_completion.assert_called_once()


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_coffee_shop_is_always_breakfast_only_without_calling_the_model(mock_chat_completion):
    result = determine_meal_tags(
        InterestId.COFFEE_SHOPS,
        "Downtown Coffee Co",
        ["Open until 3pm, great lunch sandwiches"],
        "6am-3pm",
    )

    assert result == ["breakfast"]
    mock_chat_completion.assert_not_called()


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_street_food_and_markets_never_returns_breakfast(mock_chat_completion):
    mock_chat_completion.return_value = '{"meal_tags": ["breakfast", "lunch"]}'

    result = determine_meal_tags(
        InterestId.STREET_FOOD, "Night Market", ["Open early for breakfast bites"], "6am-2pm"
    )

    assert result == ["lunch"]
    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "never be tagged" in prompt.lower()


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_ineligible_interest_returns_empty_without_calling_the_model(mock_chat_completion):
    result = determine_meal_tags(InterestId.HIKING, "Sabino Canyon", ["A scenic hiking spot"], None)

    assert result == []
    mock_chat_completion.assert_not_called()


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_none_interest_returns_empty_without_calling_the_model(mock_chat_completion):
    result = determine_meal_tags(None, "Mystery Spot", [], None)

    assert result == []
    mock_chat_completion.assert_not_called()


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_falls_back_to_lunch_and_dinner_when_response_is_malformed(mock_chat_completion):
    mock_chat_completion.return_value = "not valid json"

    result = determine_meal_tags(InterestId.RESTAURANTS, "The Grand Steakhouse", [], None)

    assert result == ["lunch", "dinner"]


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_falls_back_to_lunch_and_dinner_when_response_has_no_valid_tags(mock_chat_completion):
    mock_chat_completion.return_value = '{"meal_tags": []}'

    result = determine_meal_tags(InterestId.RESTAURANTS, "The Grand Steakhouse", [], None)

    assert result == ["lunch", "dinner"]


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_street_food_falls_back_to_lunch_and_dinner_when_only_breakfast_returned(
    mock_chat_completion,
):
    mock_chat_completion.return_value = '{"meal_tags": ["breakfast"]}'

    result = determine_meal_tags(InterestId.STREET_FOOD, "Night Market", [], None)

    assert result == ["lunch", "dinner"]


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_tolerates_markdown_fenced_json(mock_chat_completion):
    mock_chat_completion.return_value = '```json\n{"meal_tags": ["lunch"]}\n```'

    result = determine_meal_tags(InterestId.RESTAURANTS, "The Grand Steakhouse", [], None)

    assert result == ["lunch"]


@patch("trip_planner.venue_meal_tags.chat_completion")
def test_ignores_unknown_tag_values_and_dedupes(mock_chat_completion):
    mock_chat_completion.return_value = '{"meal_tags": ["Lunch", "lunch", "brunch"]}'

    result = determine_meal_tags(InterestId.RESTAURANTS, "The Grand Steakhouse", [], None)

    assert result == ["lunch"]
