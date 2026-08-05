from unittest.mock import MagicMock, patch

import pytest
import requests

from trip_planner.enrichment.serper_lookup import SERPER_SEARCH_URL, lookup_venue


def _mock_search_response(json_data, status_code=200):
    response = MagicMock()
    response.json.return_value = json_data
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(f"{status_code} error")
    else:
        response.raise_for_status.side_effect = None
    return response


def _mock_head_response(status_code):
    response = MagicMock()
    response.status_code = status_code
    return response


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.enrichment.serper_lookup.requests.post")
def test_lookup_venue_builds_request(mock_post):
    mock_post.return_value = _mock_search_response({"organic": []})

    lookup_venue("Sabino Canyon", "Tucson, AZ")

    mock_post.assert_called_once_with(
        SERPER_SEARCH_URL,
        headers={"X-API-KEY": "test-key", "Content-Type": "application/json"},
        json={"q": "Sabino Canyon 'Tucson, AZ'"},
        timeout=5,
    )


@patch.dict("os.environ", {}, clear=True)
def test_lookup_venue_raises_when_api_key_missing():
    with pytest.raises(RuntimeError):
        lookup_venue("Sabino Canyon", "Tucson, AZ")


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.enrichment.serper_lookup.requests.post")
def test_lookup_venue_raises_on_error_response(mock_post):
    mock_post.return_value = _mock_search_response({}, status_code=500)

    with pytest.raises(requests.HTTPError):
        lookup_venue("Sabino Canyon", "Tucson, AZ")


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.enrichment.serper_lookup.rank_urls")
@patch("trip_planner.enrichment.serper_lookup.requests.head")
@patch("trip_planner.enrichment.serper_lookup.requests.post")
def test_lookup_venue_picks_first_reachable_result_when_ranking_matches_order(
    mock_post, mock_head, mock_rank_urls
):
    mock_post.return_value = _mock_search_response(
        {
            "organic": [
                {"link": "https://one.example", "snippet": "First snippet"},
                {"link": "https://two.example", "snippet": "Second snippet"},
            ]
        }
    )
    mock_rank_urls.return_value = ["https://one.example", "https://two.example"]
    mock_head.return_value = _mock_head_response(200)

    result = lookup_venue("Sabino Canyon", "Tucson, AZ")

    assert result.url == "https://one.example"
    assert result.notes == ["First snippet", "Second snippet"]
    mock_head.assert_called_once_with("https://one.example", timeout=5, allow_redirects=True)


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.enrichment.serper_lookup.rank_urls")
@patch("trip_planner.enrichment.serper_lookup.requests.head")
@patch("trip_planner.enrichment.serper_lookup.requests.post")
def test_lookup_venue_skips_unreachable_result_for_later_reachable_one(mock_post, mock_head, mock_rank_urls):
    mock_post.return_value = _mock_search_response(
        {
            "organic": [
                {"link": "https://broken.example", "snippet": "First snippet"},
                {"link": "https://ok.example", "snippet": "Second snippet"},
            ]
        }
    )
    mock_rank_urls.return_value = ["https://broken.example", "https://ok.example"]
    mock_head.side_effect = [_mock_head_response(404), _mock_head_response(200)]

    result = lookup_venue("Sabino Canyon", "Tucson, AZ")

    assert result.url == "https://ok.example"
    assert result.notes == ["First snippet", "Second snippet"]
    assert mock_head.call_count == 2


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.enrichment.serper_lookup.rank_urls")
@patch("trip_planner.enrichment.serper_lookup.requests.head")
@patch("trip_planner.enrichment.serper_lookup.requests.post")
def test_lookup_venue_uses_llm_ranking_over_serper_order(mock_post, mock_head, mock_rank_urls):
    mock_post.return_value = _mock_search_response(
        {
            "organic": [
                {"link": "https://instagram.com/venue", "snippet": "Photos"},
                {"link": "https://official.example", "snippet": "Official site"},
            ]
        }
    )
    mock_rank_urls.return_value = ["https://official.example", "https://instagram.com/venue"]
    mock_head.return_value = _mock_head_response(200)

    result = lookup_venue("Sabino Canyon", "Tucson, AZ")

    assert result.url == "https://official.example"
    mock_head.assert_called_once_with("https://official.example", timeout=5, allow_redirects=True)


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.enrichment.serper_lookup.rank_urls")
@patch("trip_planner.enrichment.serper_lookup.requests.head")
@patch("trip_planner.enrichment.serper_lookup.requests.post")
def test_lookup_venue_falls_through_to_lower_ranked_reachable_candidate(mock_post, mock_head, mock_rank_urls):
    mock_post.return_value = _mock_search_response(
        {
            "organic": [
                {"link": "https://official.example", "snippet": "Official site"},
                {"link": "https://instagram.com/venue", "snippet": "Photos"},
            ]
        }
    )
    mock_rank_urls.return_value = ["https://official.example", "https://instagram.com/venue"]
    mock_head.side_effect = [_mock_head_response(500), _mock_head_response(200)]

    result = lookup_venue("Sabino Canyon", "Tucson, AZ")

    assert result.url == "https://instagram.com/venue"
    assert mock_head.call_count == 2


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.enrichment.serper_lookup.rank_urls")
@patch("trip_planner.enrichment.serper_lookup.requests.head")
@patch("trip_planner.enrichment.serper_lookup.requests.post")
def test_lookup_venue_backfills_candidates_omitted_from_ranking(mock_post, mock_head, mock_rank_urls):
    mock_post.return_value = _mock_search_response(
        {
            "organic": [
                {"link": "https://one.example", "snippet": "First snippet"},
                {"link": "https://two.example", "snippet": "Second snippet"},
            ]
        }
    )
    # The LLM only ranked one of the two candidates.
    mock_rank_urls.return_value = ["https://one.example"]
    mock_head.side_effect = [_mock_head_response(404), _mock_head_response(200)]

    result = lookup_venue("Sabino Canyon", "Tucson, AZ")

    assert result.url == "https://two.example"
    assert mock_head.call_count == 2


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.enrichment.serper_lookup.rank_urls")
@patch("trip_planner.enrichment.serper_lookup.requests.head")
@patch("trip_planner.enrichment.serper_lookup.requests.post")
def test_lookup_venue_falls_back_to_serper_order_when_ranking_raises(mock_post, mock_head, mock_rank_urls):
    mock_post.return_value = _mock_search_response(
        {
            "organic": [
                {"link": "https://one.example", "snippet": "First snippet"},
                {"link": "https://two.example", "snippet": "Second snippet"},
            ]
        }
    )
    mock_rank_urls.side_effect = RuntimeError("boom")
    mock_head.return_value = _mock_head_response(200)

    result = lookup_venue("Sabino Canyon", "Tucson, AZ")

    assert result.url == "https://one.example"
    mock_head.assert_called_once_with("https://one.example", timeout=5, allow_redirects=True)


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.enrichment.serper_lookup.rank_urls")
@patch("trip_planner.enrichment.serper_lookup.requests.head")
@patch("trip_planner.enrichment.serper_lookup.requests.post")
def test_lookup_venue_returns_no_url_when_nothing_reachable(mock_post, mock_head, mock_rank_urls):
    mock_post.return_value = _mock_search_response(
        {
            "organic": [
                {"link": "https://broken-one.example", "snippet": "First snippet"},
                {"link": "https://broken-two.example", "snippet": "Second snippet"},
            ]
        }
    )
    mock_rank_urls.return_value = ["https://broken-one.example", "https://broken-two.example"]
    mock_head.return_value = _mock_head_response(500)

    result = lookup_venue("Sabino Canyon", "Tucson, AZ")

    assert result.url is None
    assert result.notes == ["First snippet", "Second snippet"]


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.enrichment.serper_lookup.rank_urls")
@patch("trip_planner.enrichment.serper_lookup.requests.head")
@patch("trip_planner.enrichment.serper_lookup.requests.post")
def test_lookup_venue_treats_head_request_exceptions_as_unreachable(mock_post, mock_head, mock_rank_urls):
    mock_post.return_value = _mock_search_response(
        {"organic": [{"link": "https://timeout.example", "snippet": "Snippet"}]}
    )
    mock_rank_urls.return_value = ["https://timeout.example"]
    mock_head.side_effect = requests.ConnectionError("boom")

    result = lookup_venue("Sabino Canyon", "Tucson, AZ")

    assert result.url is None
    assert result.notes == ["Snippet"]


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.enrichment.serper_lookup.rank_urls")
@patch("trip_planner.enrichment.serper_lookup.requests.head")
@patch("trip_planner.enrichment.serper_lookup.requests.post")
def test_lookup_venue_handles_zero_results(mock_post, mock_head, mock_rank_urls):
    mock_post.return_value = _mock_search_response({"organic": []})

    result = lookup_venue("Sabino Canyon", "Tucson, AZ")

    assert result.url is None
    assert result.notes == []
    mock_head.assert_not_called()
    mock_rank_urls.assert_not_called()


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.enrichment.serper_lookup.rank_urls")
@patch("trip_planner.enrichment.serper_lookup.requests.head")
@patch("trip_planner.enrichment.serper_lookup.requests.post")
def test_lookup_venue_skips_results_missing_link_when_checking_reachability(mock_post, mock_head, mock_rank_urls):
    mock_post.return_value = _mock_search_response(
        {
            "organic": [
                {"snippet": "No link here"},
                {"link": "https://ok.example", "snippet": "Has a link"},
            ]
        }
    )
    mock_rank_urls.return_value = ["https://ok.example"]
    mock_head.return_value = _mock_head_response(200)

    result = lookup_venue("Sabino Canyon", "Tucson, AZ")

    assert result.url == "https://ok.example"
    assert result.notes == ["No link here", "Has a link"]
    mock_head.assert_called_once_with("https://ok.example", timeout=5, allow_redirects=True)
