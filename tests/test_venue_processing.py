from unittest.mock import patch

from trip_planner.domain import InterestId, TravelInfo
from trip_planner.models import GeoLocation, VenueCandidate
from trip_planner.serper_lookup import VenueLookupResult
from trip_planner.standard_venues import STANDARD_VENUES
from trip_planner.venue_details import VenueDetails
from trip_planner.venue_processing import _executor, process_venue, process_venues

_TRAVEL_INFO = TravelInfo(
    destination="Tucson, AZ",
    start_date="09/01/2026",
    num_days=3,
    num_adults=2,
)


@patch("trip_planner.venue_processing.determine_meal_tags")
@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.generate_description")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venue_maps_fields_and_defaults(
    mock_lookup_venue,
    mock_generate_description,
    mock_extract_venue_details,
    mock_estimate_duration_minutes,
    mock_determine_meal_tags,
):
    mock_lookup_venue.return_value = VenueLookupResult(
        url="https://sabinocanyon.example", notes=["A scenic hiking spot"]
    )
    mock_generate_description.return_value = "A scenic hiking spot in the desert."
    mock_extract_venue_details.return_value = VenueDetails(
        location="Sabino Canyon Recreation Area",
        location_type="PLACE",
        hours_of_operation="Daily 7am-6pm",
        duration_minutes=90,
    )
    mock_determine_meal_tags.return_value = []
    candidate = VenueCandidate(
        name="Sabino Canyon",
        interest_id=InterestId.HIKING,
        geo_location=GeoLocation(latitude=32.3199, longitude=-110.8226),
        tag="Hiking area",
        rating=4.7,
    )

    venue = process_venue(_TRAVEL_INFO, candidate)

    mock_lookup_venue.assert_called_once_with("Sabino Canyon", "Tucson, AZ")
    mock_generate_description.assert_called_once_with(
        "Sabino Canyon", InterestId.HIKING, "Tucson, AZ", ["A scenic hiking spot"]
    )
    mock_extract_venue_details.assert_called_once_with("Sabino Canyon", ["A scenic hiking spot"])
    mock_estimate_duration_minutes.assert_not_called()
    mock_determine_meal_tags.assert_called_once_with(
        InterestId.HIKING, "Sabino Canyon", ["A scenic hiking spot"], "Daily 7am-6pm"
    )
    assert venue.name == "Sabino Canyon"
    assert venue.interest_id == InterestId.HIKING
    assert venue.location == "Sabino Canyon Recreation Area"
    assert venue.location_type == "PLACE"
    assert venue.geo_location == GeoLocation(latitude=32.3199, longitude=-110.8226)
    assert venue.description == "A scenic hiking spot in the desert."
    assert venue.url == "https://sabinocanyon.example"
    assert venue.hours_of_operation == "Daily 7am-6pm"
    assert venue.duration_minutes == 90
    assert venue.origin == "web"
    assert venue.rating == 4.7
    assert venue.tags == ["Hiking area"]
    assert venue.notes == ["A scenic hiking spot"]
    assert venue.status == "accepted"
    assert venue.rejection_reason is None


@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.generate_description")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venue_falls_back_to_duration_estimate_when_not_in_notes(
    mock_lookup_venue,
    mock_generate_description,
    mock_extract_venue_details,
    mock_estimate_duration_minutes,
):
    mock_lookup_venue.return_value = VenueLookupResult(notes=["A scenic hiking spot"])
    mock_generate_description.return_value = "A scenic hiking spot in the desert."
    mock_extract_venue_details.return_value = VenueDetails(
        location="Sabino Canyon Recreation Area", hours_of_operation=None, duration_minutes=None
    )
    mock_estimate_duration_minutes.return_value = 120
    candidate = VenueCandidate(name="Sabino Canyon", interest_id=InterestId.HIKING)

    venue = process_venue(_TRAVEL_INFO, candidate)

    mock_estimate_duration_minutes.assert_called_once_with(
        "Sabino Canyon", "Sabino Canyon Recreation Area"
    )
    assert venue.duration_minutes == 120
    assert venue.hours_of_operation is None


@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.generate_description")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venue_leaves_tags_empty_when_candidate_has_no_tag(
    mock_lookup_venue,
    mock_generate_description,
    mock_extract_venue_details,
    mock_estimate_duration_minutes,
):
    mock_lookup_venue.return_value = VenueLookupResult()
    mock_generate_description.return_value = "A mysterious little spot."
    mock_extract_venue_details.return_value = VenueDetails(duration_minutes=30)
    candidate = VenueCandidate(name="Mystery Spot", interest_id=InterestId.HIKING)

    venue = process_venue(_TRAVEL_INFO, candidate)

    assert venue.rating is None
    assert venue.tags == []


@patch("trip_planner.venue_processing.determine_meal_tags")
@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.generate_description")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venue_appends_meal_tags_after_the_category_tag(
    mock_lookup_venue,
    mock_generate_description,
    mock_extract_venue_details,
    mock_estimate_duration_minutes,
    mock_determine_meal_tags,
):
    mock_lookup_venue.return_value = VenueLookupResult(notes=["Popular lunch spot"])
    mock_generate_description.return_value = "A cozy restaurant."
    mock_extract_venue_details.return_value = VenueDetails(
        duration_minutes=30, hours_of_operation="11am-9pm"
    )
    mock_determine_meal_tags.return_value = ["lunch", "dinner"]
    candidate = VenueCandidate(
        name="The Grand Steakhouse", interest_id=InterestId.RESTAURANTS, tag="Steakhouse"
    )

    venue = process_venue(_TRAVEL_INFO, candidate)

    mock_determine_meal_tags.assert_called_once_with(
        InterestId.RESTAURANTS, "The Grand Steakhouse", ["Popular lunch spot"], "11am-9pm"
    )
    assert venue.tags == ["Steakhouse", "lunch", "dinner"]


@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.generate_description")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venue_rejects_as_closed_when_details_say_so(
    mock_lookup_venue,
    mock_generate_description,
    mock_extract_venue_details,
    mock_estimate_duration_minutes,
):
    mock_lookup_venue.return_value = VenueLookupResult(
        url="https://sabinocanyon.example", notes=["This spot has permanently closed"]
    )
    mock_generate_description.return_value = "A scenic hiking spot."
    mock_extract_venue_details.return_value = VenueDetails(duration_minutes=30, closed=True)
    candidate = VenueCandidate(name="Sabino Canyon", interest_id=InterestId.HIKING)

    venue = process_venue(_TRAVEL_INFO, candidate)

    assert venue.status == "rejected"
    assert venue.rejection_reason == "closed"


@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.generate_description")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venue_rejects_as_closed_even_without_a_url(
    mock_lookup_venue,
    mock_generate_description,
    mock_extract_venue_details,
    mock_estimate_duration_minutes,
):
    mock_lookup_venue.return_value = VenueLookupResult(notes=["Permanently closed"])
    mock_generate_description.return_value = "A scenic hiking spot."
    mock_extract_venue_details.return_value = VenueDetails(duration_minutes=30, closed=True)
    candidate = VenueCandidate(name="Sabino Canyon", interest_id=InterestId.HIKING)

    venue = process_venue(_TRAVEL_INFO, candidate)

    assert venue.status == "rejected"
    assert venue.rejection_reason == "closed"


@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.generate_description")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venue_rejects_as_no_website_when_not_closed_and_no_url(
    mock_lookup_venue,
    mock_generate_description,
    mock_extract_venue_details,
    mock_estimate_duration_minutes,
):
    mock_lookup_venue.return_value = VenueLookupResult()
    mock_generate_description.return_value = "A mysterious little spot."
    mock_extract_venue_details.return_value = VenueDetails(duration_minutes=30, closed=False)
    candidate = VenueCandidate(name="Mystery Spot", interest_id=InterestId.HIKING)

    venue = process_venue(_TRAVEL_INFO, candidate)

    assert venue.status == "rejected"
    assert venue.rejection_reason == "no website"


@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.generate_description")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venue_uses_no_url_or_notes_when_lookup_finds_nothing(
    mock_lookup_venue,
    mock_generate_description,
    mock_extract_venue_details,
    mock_estimate_duration_minutes,
):
    mock_lookup_venue.return_value = VenueLookupResult()
    mock_generate_description.return_value = "A mysterious little spot."
    mock_extract_venue_details.return_value = VenueDetails(duration_minutes=30)
    candidate = VenueCandidate(name="Mystery Spot", interest_id=InterestId.HIKING)

    venue = process_venue(_TRAVEL_INFO, candidate)

    assert venue.url is None
    assert venue.notes == []


@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.generate_description")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venue_falls_back_to_name_interest_destination_when_no_notes(
    mock_lookup_venue,
    mock_generate_description,
    mock_extract_venue_details,
    mock_estimate_duration_minutes,
):
    mock_lookup_venue.return_value = VenueLookupResult()
    mock_generate_description.return_value = "A mysterious little spot."
    mock_extract_venue_details.return_value = VenueDetails(duration_minutes=30)
    candidate = VenueCandidate(name="Mystery Spot", interest_id=InterestId.HIKING)

    venue = process_venue(_TRAVEL_INFO, candidate)

    mock_generate_description.assert_called_once_with(
        "Mystery Spot", InterestId.HIKING, "Tucson, AZ", []
    )
    assert venue.description == "A mysterious little spot."


@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.generate_description")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venues_returns_venue_for_every_candidate(
    mock_lookup_venue,
    mock_generate_description,
    mock_extract_venue_details,
    mock_estimate_duration_minutes,
):
    mock_lookup_venue.return_value = VenueLookupResult()
    mock_generate_description.return_value = "A great place to visit."
    mock_extract_venue_details.return_value = VenueDetails(duration_minutes=30)
    candidates = [
        VenueCandidate(name="Sabino Canyon", interest_id=InterestId.HIKING),
        VenueCandidate(name="Mystery Spot", interest_id=InterestId.HIKING),
    ]

    venues, errors = process_venues(_TRAVEL_INFO, candidates)

    assert errors == []
    assert [venue.name for venue in venues] == [
        "Sabino Canyon",
        "Mystery Spot",
        "Breakfast",
        "Lunch",
        "Dinner",
    ]


@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.generate_description")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venues_appends_the_standard_meal_venues(
    mock_lookup_venue,
    mock_generate_description,
    mock_extract_venue_details,
    mock_estimate_duration_minutes,
):
    mock_lookup_venue.return_value = VenueLookupResult()
    mock_generate_description.return_value = "A great place to visit."
    mock_extract_venue_details.return_value = VenueDetails(duration_minutes=30)
    candidates = [VenueCandidate(name="Sabino Canyon", interest_id=InterestId.HIKING)]

    venues, errors = process_venues(_TRAVEL_INFO, candidates)

    assert errors == []
    standard_venues = [venue for venue in venues if venue.origin == "standard"]
    assert standard_venues == STANDARD_VENUES
    assert [venue.tags for venue in standard_venues] == [["breakfast"], ["lunch"], ["dinner"]]


@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.generate_description")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venues_collects_errors_without_aborting_others(
    mock_lookup_venue,
    mock_generate_description,
    mock_extract_venue_details,
    mock_estimate_duration_minutes,
):
    mock_lookup_venue.return_value = VenueLookupResult()
    mock_generate_description.return_value = "A great place to visit."
    mock_extract_venue_details.return_value = VenueDetails(duration_minutes=30)
    candidates = [
        VenueCandidate(name="Good Venue", interest_id=InterestId.HIKING),
        VenueCandidate(name="Bad Venue", interest_id=InterestId.HIKING),
    ]

    def fake_process_venue(travel_info, candidate):
        if candidate.name == "Bad Venue":
            raise ValueError("boom")
        return process_venue(travel_info, candidate)

    with patch("trip_planner.venue_processing.process_venue", side_effect=fake_process_venue):
        venues, errors = process_venues(_TRAVEL_INFO, candidates)

    assert [venue.name for venue in venues] == ["Good Venue", "Breakfast", "Lunch", "Dinner"]
    assert len(errors) == 1
    assert isinstance(errors[0], ValueError)


@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venues_collects_errors_from_description_generation_failures(
    mock_lookup_venue, mock_extract_venue_details, mock_estimate_duration_minutes
):
    mock_lookup_venue.return_value = VenueLookupResult()
    mock_extract_venue_details.return_value = VenueDetails(duration_minutes=30)
    candidates = [
        VenueCandidate(name="Good Venue", interest_id=InterestId.HIKING),
        VenueCandidate(name="Bad Venue", interest_id=InterestId.HIKING),
    ]

    def fake_generate_description(name, interest_id, destination, notes):
        if name == "Bad Venue":
            raise RuntimeError("llm boom")
        return "A great place to visit."

    with patch(
        "trip_planner.venue_processing.generate_description", side_effect=fake_generate_description
    ):
        venues, errors = process_venues(_TRAVEL_INFO, candidates)

    assert [venue.name for venue in venues] == ["Good Venue", "Breakfast", "Lunch", "Dinner"]
    assert len(errors) == 1
    assert isinstance(errors[0], RuntimeError)


@patch("trip_planner.venue_processing.resolve_duplicate_venues")
@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.generate_description")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venues_runs_duplicate_resolution_over_the_full_list(
    mock_lookup_venue,
    mock_generate_description,
    mock_extract_venue_details,
    mock_estimate_duration_minutes,
    mock_resolve_duplicate_venues,
):
    mock_lookup_venue.return_value = VenueLookupResult(url="https://example.com")
    mock_generate_description.return_value = "A great place to visit."
    mock_extract_venue_details.return_value = VenueDetails(duration_minutes=30)
    deduplicated = [object()]
    mock_resolve_duplicate_venues.return_value = deduplicated
    candidates = [
        VenueCandidate(name="Sabino Canyon", interest_id=InterestId.HIKING),
        VenueCandidate(name="Mystery Spot", interest_id=InterestId.HIKING),
    ]

    venues, errors = process_venues(_TRAVEL_INFO, candidates)

    assert errors == []
    mock_resolve_duplicate_venues.assert_called_once()
    (called_venues,) = mock_resolve_duplicate_venues.call_args[0]
    assert [venue.name for venue in called_venues] == ["Sabino Canyon", "Mystery Spot"]
    assert venues == deduplicated + STANDARD_VENUES


@patch("trip_planner.venue_processing.estimate_duration_minutes")
@patch("trip_planner.venue_processing.extract_venue_details")
@patch("trip_planner.venue_processing.generate_description")
@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venues_dispatches_through_shared_executor(
    mock_lookup_venue,
    mock_generate_description,
    mock_extract_venue_details,
    mock_estimate_duration_minutes,
):
    mock_lookup_venue.return_value = VenueLookupResult()
    mock_generate_description.return_value = "A great place to visit."
    mock_extract_venue_details.return_value = VenueDetails(duration_minutes=30)
    candidates = [
        VenueCandidate(name="Sabino Canyon", interest_id=InterestId.HIKING),
        VenueCandidate(name="Mystery Spot", interest_id=InterestId.HIKING),
    ]

    with patch.object(_executor, "submit", wraps=_executor.submit) as mock_submit:
        process_venues(_TRAVEL_INFO, candidates)

    assert mock_submit.call_count == 2
