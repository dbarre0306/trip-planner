from unittest.mock import patch

from trip_planner.domain import TravelInfo
from trip_planner.models import VenueCandidate
from trip_planner.trip_planner import create_itinerary


@patch("trip_planner.trip_planner.search_places")
def test_create_itinerary_queries_once_per_interest(mock_search_places):
    mock_search_places.return_value = [VenueCandidate(name="Some Venue")]
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        start_date="09/01/2026",
        num_days=3,
        num_adults=2,
        interests=["hiking trails", "restaurants"],
    )

    create_itinerary(travel_info)

    assert mock_search_places.call_count == 2
    mock_search_places.assert_any_call("hiking trails", "Tucson, AZ")
    mock_search_places.assert_any_call("restaurants", "Tucson, AZ")


@patch("trip_planner.trip_planner.search_places")
def test_create_itinerary_prints_results(mock_search_places, capsys):
    venue = VenueCandidate(name="Sabino Canyon", rating=4.7, tag="Hiking area", location="Tucson, AZ", interest="hiking")
    mock_search_places.return_value = [venue]
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        start_date="09/01/2026",
        num_days=3,
        num_adults=2,
        interests=["hiking"],
    )

    create_itinerary(travel_info)

    captured = capsys.readouterr()
    assert "Sabino Canyon" in captured.out
