from unittest.mock import patch

from trip_planner.models import VenueCandidate
from trip_planner.serper_lookup import VenueLookupResult
from trip_planner.venue_processing import _executor, process_venue, process_venues


@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venue_maps_fields_and_defaults(mock_lookup_venue):
    mock_lookup_venue.return_value = VenueLookupResult(
        url="https://sabinocanyon.example", notes=["A scenic hiking spot"]
    )
    candidate = VenueCandidate(
        name="Sabino Canyon",
        interest="hiking",
        location="Tucson, AZ",
        tag="Hiking area",
        rating=4.7,
    )

    venue = process_venue(candidate)

    mock_lookup_venue.assert_called_once_with("Sabino Canyon", "Tucson, AZ")
    assert venue.name == "Sabino Canyon"
    assert venue.interest == "hiking"
    assert venue.location == "Tucson, AZ"
    assert venue.description == ""
    assert venue.url == "https://sabinocanyon.example"
    assert venue.hours_of_operation is None
    assert venue.duration_minutes is None
    assert venue.origin == "web"
    assert venue.rating == 4.7
    assert venue.tags == ["Hiking area"]
    assert venue.notes == ["A scenic hiking spot"]
    assert venue.status == "accepted"
    assert venue.rejection_reason is None


@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venue_leaves_tags_empty_when_candidate_has_no_tag(mock_lookup_venue):
    mock_lookup_venue.return_value = VenueLookupResult()
    candidate = VenueCandidate(name="Mystery Spot", interest="hiking")

    venue = process_venue(candidate)

    assert venue.rating is None
    assert venue.tags == []


@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venue_uses_no_url_or_notes_when_lookup_finds_nothing(mock_lookup_venue):
    mock_lookup_venue.return_value = VenueLookupResult()
    candidate = VenueCandidate(name="Mystery Spot", interest="hiking")

    venue = process_venue(candidate)

    assert venue.url is None
    assert venue.notes == []


@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venues_returns_venue_for_every_candidate(mock_lookup_venue):
    mock_lookup_venue.return_value = VenueLookupResult()
    candidates = [
        VenueCandidate(name="Sabino Canyon", interest="hiking"),
        VenueCandidate(name="Mystery Spot", interest="hiking"),
    ]

    venues, errors = process_venues(candidates)

    assert errors == []
    assert [venue.name for venue in venues] == ["Sabino Canyon", "Mystery Spot"]


@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venues_collects_errors_without_aborting_others(mock_lookup_venue):
    mock_lookup_venue.return_value = VenueLookupResult()
    candidates = [
        VenueCandidate(name="Good Venue", interest="hiking"),
        VenueCandidate(name="Bad Venue", interest="hiking"),
    ]

    def fake_process_venue(candidate):
        if candidate.name == "Bad Venue":
            raise ValueError("boom")
        return process_venue(candidate)

    with patch("trip_planner.venue_processing.process_venue", side_effect=fake_process_venue):
        venues, errors = process_venues(candidates)

    assert [venue.name for venue in venues] == ["Good Venue"]
    assert len(errors) == 1
    assert isinstance(errors[0], ValueError)


@patch("trip_planner.venue_processing.lookup_venue")
def test_process_venues_dispatches_through_shared_executor(mock_lookup_venue):
    mock_lookup_venue.return_value = VenueLookupResult()
    candidates = [
        VenueCandidate(name="Sabino Canyon", interest="hiking"),
        VenueCandidate(name="Mystery Spot", interest="hiking"),
    ]

    with patch.object(_executor, "submit", wraps=_executor.submit) as mock_submit:
        process_venues(candidates)

    assert mock_submit.call_count == 2
