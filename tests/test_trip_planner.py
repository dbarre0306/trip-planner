from unittest.mock import patch

from trip_planner.domain import TravelInfo
from trip_planner.models import Venue, VenueCandidate
from trip_planner.trip_planner import create_itinerary, get_all_candidates


@patch("trip_planner.trip_planner.search_places")
def test_get_all_candidates_queries_once_per_interest(mock_search_places):
    mock_search_places.return_value = [VenueCandidate(name="Some Venue")]
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        start_date="09/01/2026",
        num_days=3,
        num_adults=2,
        num_children=0,
        interests=["hiking trails", "restaurants"],
    )

    get_all_candidates(travel_info)

    assert mock_search_places.call_count == 2
    mock_search_places.assert_any_call("hiking trails", "Tucson, AZ")
    mock_search_places.assert_any_call("restaurants", "Tucson, AZ")


@patch("trip_planner.trip_planner.search_places")
def test_get_all_candidates_combines_results_across_interests(mock_search_places):
    hiking_candidate = VenueCandidate(name="Sabino Canyon", interest="hiking trails")
    restaurant_candidate = VenueCandidate(name="El Charro", interest="restaurants")
    mock_search_places.side_effect = [[hiking_candidate], [restaurant_candidate]]
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        start_date="09/01/2026",
        num_days=3,
        num_adults=2,
        num_children=0,
        interests=["hiking trails", "restaurants"],
    )

    candidates = get_all_candidates(travel_info)

    assert candidates == [hiking_candidate, restaurant_candidate]


@patch("trip_planner.trip_planner.process_venues")
@patch("trip_planner.trip_planner.search_places")
def test_create_itinerary_processes_all_candidates_in_one_call(mock_search_places, mock_process_venues):
    hiking_candidate = VenueCandidate(name="Sabino Canyon", interest="hiking trails")
    restaurant_candidate = VenueCandidate(name="El Charro", interest="restaurants")
    mock_search_places.side_effect = [[hiking_candidate], [restaurant_candidate]]
    mock_process_venues.return_value = ([], [])
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        start_date="09/01/2026",
        num_days=3,
        num_adults=2,
        num_children=0,
        interests=["hiking trails", "restaurants"],
    )

    create_itinerary(travel_info)

    mock_process_venues.assert_called_once_with([hiking_candidate, restaurant_candidate])


@patch("trip_planner.trip_planner.process_venues")
@patch("trip_planner.trip_planner.search_places")
def test_create_itinerary_prints_processed_venues(mock_search_places, mock_process_venues, capsys):
    mock_search_places.return_value = [VenueCandidate(name="Sabino Canyon", interest="hiking")]
    mock_process_venues.return_value = (
        [Venue(name="Sabino Canyon", interest="hiking", location="Tucson, AZ")],
        [],
    )
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        start_date="09/01/2026",
        num_days=3,
        num_adults=2,
        num_children=0,
        interests=["hiking"],
    )

    create_itinerary(travel_info)

    captured = capsys.readouterr()
    assert "Sabino Canyon" in captured.out


@patch("trip_planner.trip_planner.process_venues")
@patch("trip_planner.trip_planner.search_places")
def test_create_itinerary_reports_processing_failures(mock_search_places, mock_process_venues, capsys):
    mock_search_places.return_value = [VenueCandidate(name="Broken Venue", interest="hiking")]
    mock_process_venues.return_value = ([], [ValueError("boom")])
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        start_date="09/01/2026",
        num_days=3,
        num_adults=2,
        num_children=0,
        interests=["hiking"],
    )

    create_itinerary(travel_info)

    captured = capsys.readouterr()
    assert "boom" in captured.out
