import json
from unittest.mock import patch

from trip_planner.enrichment.venue_url_selection import rank_urls

RESULTS = [
    {"link": "https://official.example", "snippet": "The venue's own site"},
    {"link": "https://instagram.com/venue", "snippet": "Photos of the venue"},
    {"link": "https://yelp.com/biz/venue", "snippet": "Reviews of the venue"},
]


def _mock_response(payload: str):
    return payload


@patch("trip_planner.enrichment.venue_url_selection.chat_completion")
def test_rank_urls_includes_name_destination_and_all_candidates_in_prompt(mock_chat):
    mock_chat.return_value = json.dumps({"urls": []})

    rank_urls("Some Venue", "Tucson, AZ", RESULTS)

    prompt = mock_chat.call_args[0][0][0]["content"]
    assert "Some Venue" in prompt
    assert "Tucson, AZ" in prompt
    for result in RESULTS:
        assert result["link"] in prompt
        assert result["snippet"] in prompt


@patch("trip_planner.enrichment.venue_url_selection.chat_completion")
def test_rank_urls_returns_well_formed_ranking_in_order(mock_chat):
    ordered = [
        "https://yelp.com/biz/venue",
        "https://official.example",
        "https://instagram.com/venue",
    ]
    mock_chat.return_value = json.dumps({"urls": ordered})

    result = rank_urls("Some Venue", "Tucson, AZ", RESULTS)

    assert result == ordered


@patch("trip_planner.enrichment.venue_url_selection.chat_completion")
def test_rank_urls_drops_hallucinated_url_not_in_candidates(mock_chat):
    mock_chat.return_value = json.dumps(
        {"urls": ["https://official.example", "https://made-up.example", "https://yelp.com/biz/venue"]}
    )

    result = rank_urls("Some Venue", "Tucson, AZ", RESULTS)

    assert result == ["https://official.example", "https://yelp.com/biz/venue"]


@patch("trip_planner.enrichment.venue_url_selection.chat_completion")
def test_rank_urls_returns_partial_list_when_llm_omits_a_candidate(mock_chat):
    mock_chat.return_value = json.dumps({"urls": ["https://official.example"]})

    result = rank_urls("Some Venue", "Tucson, AZ", RESULTS)

    assert result == ["https://official.example"]


@patch("trip_planner.enrichment.venue_url_selection.chat_completion")
def test_rank_urls_collapses_duplicates_to_first_occurrence(mock_chat):
    mock_chat.return_value = json.dumps(
        {"urls": ["https://official.example", "https://official.example", "https://yelp.com/biz/venue"]}
    )

    result = rank_urls("Some Venue", "Tucson, AZ", RESULTS)

    assert result == ["https://official.example", "https://yelp.com/biz/venue"]


@patch("trip_planner.enrichment.venue_url_selection.chat_completion")
def test_rank_urls_returns_empty_list_for_non_json_response(mock_chat):
    mock_chat.return_value = "not json at all"

    result = rank_urls("Some Venue", "Tucson, AZ", RESULTS)

    assert result == []


@patch("trip_planner.enrichment.venue_url_selection.chat_completion")
def test_rank_urls_returns_empty_list_when_urls_key_missing(mock_chat):
    mock_chat.return_value = json.dumps({"something_else": []})

    result = rank_urls("Some Venue", "Tucson, AZ", RESULTS)

    assert result == []


@patch("trip_planner.enrichment.venue_url_selection.chat_completion")
def test_rank_urls_returns_empty_list_when_urls_is_not_a_list(mock_chat):
    mock_chat.return_value = json.dumps({"urls": "https://official.example"})

    result = rank_urls("Some Venue", "Tucson, AZ", RESULTS)

    assert result == []


@patch("trip_planner.enrichment.venue_url_selection.chat_completion")
def test_rank_urls_parses_fenced_json_code_block(mock_chat):
    ordered = ["https://official.example", "https://instagram.com/venue", "https://yelp.com/biz/venue"]
    mock_chat.return_value = "```json\n" + json.dumps({"urls": ordered}) + "\n```"

    result = rank_urls("Some Venue", "Tucson, AZ", RESULTS)

    assert result == ordered


@patch("trip_planner.enrichment.venue_url_selection.chat_completion")
def test_rank_urls_returns_empty_list_when_no_candidates(mock_chat):
    result = rank_urls("Some Venue", "Tucson, AZ", [])

    assert result == []
    mock_chat.assert_not_called()
