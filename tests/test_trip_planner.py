from unittest.mock import patch

from trip_planner.core.domain import InterestId, TravelInfo
from trip_planner.core.models import ItineraryDay, Venue, VenueCandidate
from trip_planner.trip_planner import (
    STAGE_BUILD_COMPLETE,
    STAGE_PROCESSING_COMPLETE,
    STAGE_SEARCH_COMPLETE,
    create_itinerary,
    get_all_candidates,
)


@patch("trip_planner.trip_planner.search_places")
def test_get_all_candidates_queries_once_per_interest(mock_search_places):
    mock_search_places.return_value = [VenueCandidate(name="Some Venue")]
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        travel_dates=["09/01/2026", "09/02/2026", "09/03/2026"],
        num_adults=2,
        num_children=0,
        interest_ids=[InterestId.HIKING, InterestId.RESTAURANTS],
    )

    get_all_candidates(travel_info)

    assert mock_search_places.call_count == 2
    mock_search_places.assert_any_call(InterestId.HIKING, "Tucson, AZ", family_friendly=False)
    mock_search_places.assert_any_call(InterestId.RESTAURANTS, "Tucson, AZ", family_friendly=False)


@patch("trip_planner.trip_planner.search_places")
def test_get_all_candidates_requests_family_friendly_when_children_present(mock_search_places):
    mock_search_places.return_value = [VenueCandidate(name="Some Venue")]
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        travel_dates=["09/01/2026", "09/02/2026", "09/03/2026"],
        num_adults=2,
        num_children=1,
        interest_ids=[InterestId.HIKING, InterestId.RESTAURANTS],
    )

    get_all_candidates(travel_info)

    mock_search_places.assert_any_call(InterestId.HIKING, "Tucson, AZ", family_friendly=True)
    mock_search_places.assert_any_call(InterestId.RESTAURANTS, "Tucson, AZ", family_friendly=True)


@patch("trip_planner.trip_planner.search_places")
def test_get_all_candidates_combines_results_across_interests(mock_search_places):
    hiking_candidate = VenueCandidate(name="Sabino Canyon", interest_id=InterestId.HIKING)
    restaurant_candidate = VenueCandidate(name="El Charro", interest_id=InterestId.RESTAURANTS)
    mock_search_places.side_effect = [[hiking_candidate], [restaurant_candidate]]
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        travel_dates=["09/01/2026", "09/02/2026", "09/03/2026"],
        num_adults=2,
        num_children=0,
        interest_ids=[InterestId.HIKING, InterestId.RESTAURANTS],
    )

    candidates = get_all_candidates(travel_info)

    assert candidates == [hiking_candidate, restaurant_candidate]


@patch("trip_planner.trip_planner.assemble_itinerary")
@patch("trip_planner.trip_planner.process_venues")
@patch("trip_planner.trip_planner.search_places")
def test_create_itinerary_processes_all_candidates_in_one_call(
    mock_search_places, mock_process_venues, mock_assemble_itinerary
):
    hiking_candidate = VenueCandidate(name="Sabino Canyon", interest_id=InterestId.HIKING)
    restaurant_candidate = VenueCandidate(name="El Charro", interest_id=InterestId.RESTAURANTS)
    mock_search_places.side_effect = [[hiking_candidate], [restaurant_candidate]]
    mock_process_venues.return_value = ([], [])
    mock_assemble_itinerary.return_value = []
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        travel_dates=["09/01/2026", "09/02/2026", "09/03/2026"],
        num_adults=2,
        num_children=0,
        interest_ids=[InterestId.HIKING, InterestId.RESTAURANTS],
    )

    create_itinerary(travel_info)

    mock_process_venues.assert_called_once_with(travel_info, [hiking_candidate, restaurant_candidate])


@patch("trip_planner.trip_planner.assemble_itinerary")
@patch("trip_planner.trip_planner.process_venues")
@patch("trip_planner.trip_planner.search_places")
def test_create_itinerary_returns_the_assembled_itinerary(
    mock_search_places, mock_process_venues, mock_assemble_itinerary
):
    mock_search_places.return_value = [VenueCandidate(name="Sabino Canyon", interest_id=InterestId.HIKING)]
    processed_venues = [Venue(name="Sabino Canyon", interest_id=InterestId.HIKING, location="Tucson, AZ")]
    mock_process_venues.return_value = (processed_venues, [])
    itinerary = [ItineraryDay(day_number=1, date="09/01/2026", venues=[])]
    mock_assemble_itinerary.return_value = itinerary
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        travel_dates=["09/01/2026", "09/02/2026", "09/03/2026"],
        num_adults=2,
        num_children=0,
        interest_ids=[InterestId.HIKING],
    )

    result = create_itinerary(travel_info)

    mock_assemble_itinerary.assert_called_once_with(travel_info, processed_venues)
    assert result == itinerary


@patch("trip_planner.trip_planner.assemble_itinerary")
@patch("trip_planner.trip_planner.process_venues")
@patch("trip_planner.trip_planner.search_places")
def test_create_itinerary_reports_processing_failures(
    mock_search_places, mock_process_venues, mock_assemble_itinerary, capsys
):
    mock_search_places.return_value = [VenueCandidate(name="Broken Venue", interest_id=InterestId.HIKING)]
    mock_process_venues.return_value = ([], [ValueError("boom")])
    mock_assemble_itinerary.return_value = []
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        travel_dates=["09/01/2026", "09/02/2026", "09/03/2026"],
        num_adults=2,
        num_children=0,
        interest_ids=[InterestId.HIKING],
    )

    create_itinerary(travel_info)

    captured = capsys.readouterr()
    assert "boom" in captured.out


@patch("trip_planner.trip_planner.assemble_itinerary")
@patch("trip_planner.trip_planner.process_venues")
@patch("trip_planner.trip_planner.search_places")
def test_create_itinerary_reports_stages_in_order(
    mock_search_places, mock_process_venues, mock_assemble_itinerary
):
    mock_search_places.return_value = [VenueCandidate(name="Sabino Canyon", interest_id=InterestId.HIKING)]
    mock_process_venues.return_value = ([], [])
    mock_assemble_itinerary.return_value = []
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        travel_dates=["09/01/2026", "09/02/2026", "09/03/2026"],
        num_adults=2,
        num_children=0,
        interest_ids=[InterestId.HIKING],
    )

    events: list[tuple[str, int | None]] = []
    create_itinerary(travel_info, on_stage=lambda event, count=None: events.append((event, count)))

    assert events == [
        (STAGE_SEARCH_COMPLETE, 1),
        (STAGE_PROCESSING_COMPLETE, None),
        (STAGE_BUILD_COMPLETE, None),
    ]
