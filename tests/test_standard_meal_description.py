from unittest.mock import patch

from trip_planner.standard_meal_description import generate_standard_meal_description


@patch("trip_planner.standard_meal_description.chat_completion")
def test_generate_standard_meal_description_returns_the_llm_response(mock_chat_completion):
    mock_chat_completion.return_value = "A whimsical morning feast awaits!"

    description = generate_standard_meal_description("breakfast", "Tucson, AZ")

    assert description == "A whimsical morning feast awaits!"


@patch("trip_planner.standard_meal_description.chat_completion")
def test_generate_standard_meal_description_includes_meal_and_destination_in_prompt(mock_chat_completion):
    mock_chat_completion.return_value = "A delightful dinner surprise."

    generate_standard_meal_description("dinner", "Tucson, AZ")

    prompt = mock_chat_completion.call_args[0][0][0]["content"]
    assert "dinner" in prompt
    assert "Tucson, AZ" in prompt


@patch("trip_planner.standard_meal_description.chat_completion")
def test_generate_standard_meal_description_handles_missing_destination(mock_chat_completion):
    mock_chat_completion.return_value = "A lovely lunch adventure."

    description = generate_standard_meal_description("lunch", None)

    assert description == "A lovely lunch adventure."


@patch("trip_planner.standard_meal_description.chat_completion")
def test_generate_standard_meal_description_strips_whitespace(mock_chat_completion):
    mock_chat_completion.return_value = "  A cozy breakfast nook.  \n"

    description = generate_standard_meal_description("breakfast", "Tucson, AZ")

    assert description == "A cozy breakfast nook."
