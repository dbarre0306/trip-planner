from unittest.mock import MagicMock, patch

import pytest
import requests

from trip_planner.domain import InterestId
from trip_planner.models import GeoLocation
from trip_planner.serper_places import SERPER_PLACES_URL, search_places


def _mock_response(json_data, status_code=200):
    response = MagicMock()
    response.json.return_value = json_data
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(f"{status_code} error")
    else:
        response.raise_for_status.side_effect = None
    return response


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.serper_places.requests.post")
def test_search_places_builds_request(mock_post):
    mock_post.return_value = _mock_response({"places": []})

    search_places(InterestId.HIKING, "Tucson, AZ")

    mock_post.assert_called_once_with(
        SERPER_PLACES_URL,
        headers={"X-API-KEY": "test-key", "Content-Type": "application/json"},
        json={"q": "hiking 'Tucson, AZ'"},
    )


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.serper_places.requests.post")
def test_search_places_maps_full_fields(mock_post):
    mock_post.return_value = _mock_response(
        {
            "places": [
                {
                    "title": "Sabino Canyon",
                    "rating": 4.7,
                    "category": "Hiking area",
                    "address": "5700 N Sabino Canyon Rd, Tucson, AZ",
                    "latitude": 32.3199,
                    "longitude": -110.8226,
                }
            ]
        }
    )

    results = search_places(InterestId.HIKING, "Tucson, AZ")

    assert len(results) == 1
    venue = results[0]
    assert venue.name == "Sabino Canyon"
    assert venue.rating == 4.7
    assert venue.tag == "Hiking area"
    assert venue.location is None
    assert venue.geo_location == GeoLocation(latitude=32.3199, longitude=-110.8226)
    assert venue.interest_id == InterestId.HIKING


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.serper_places.requests.post")
def test_search_places_handles_missing_optional_fields(mock_post):
    mock_post.return_value = _mock_response({"places": [{"title": "Mystery Spot"}]})

    results = search_places(InterestId.HIKING, "Tucson, AZ")

    assert len(results) == 1
    venue = results[0]
    assert venue.name == "Mystery Spot"
    assert venue.rating is None
    assert venue.tag is None
    assert venue.location is None
    assert venue.geo_location is None
    assert venue.interest_id == InterestId.HIKING


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.serper_places.requests.post")
def test_search_places_treats_partial_coordinates_as_missing(mock_post):
    mock_post.return_value = _mock_response(
        {"places": [{"title": "Mystery Spot", "latitude": 32.3199}]}
    )

    results = search_places(InterestId.HIKING, "Tucson, AZ")

    assert len(results) == 1
    assert results[0].geo_location is None


@patch.dict("os.environ", {}, clear=True)
def test_search_places_raises_when_api_key_missing():
    with pytest.raises(RuntimeError):
        search_places(InterestId.HIKING, "Tucson, AZ")


@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
@patch("trip_planner.serper_places.requests.post")
def test_search_places_raises_on_error_response(mock_post):
    mock_post.return_value = _mock_response({}, status_code=500)

    with pytest.raises(requests.HTTPError):
        search_places(InterestId.HIKING, "Tucson, AZ")
