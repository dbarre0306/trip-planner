from unittest.mock import patch

from trip_planner.models import VenueCandidate
from trip_planner.venue_processing import _executor, process_venue, process_venues


def test_process_venue_maps_fields_and_defaults():
    candidate = VenueCandidate(
        name="Sabino Canyon",
        interest="hiking",
        location="Tucson, AZ",
        tag="Hiking area",
        rating=4.7,
    )

    venue = process_venue(candidate)

    assert venue.name == "Sabino Canyon"
    assert venue.interest == "hiking"
    assert venue.location == "Tucson, AZ"
    assert venue.description == ""
    assert venue.url is None
    assert venue.hours_of_operation is None
    assert venue.duration_minutes is None
    assert venue.origin == "web"
    assert venue.rating == 4.7
    assert venue.tags == ["Hiking area"]
    assert venue.notes == []
    assert venue.status == "accepted"
    assert venue.rejection_reason is None


def test_process_venue_leaves_tags_empty_when_candidate_has_no_tag():
    candidate = VenueCandidate(name="Mystery Spot", interest="hiking")

    venue = process_venue(candidate)

    assert venue.rating is None
    assert venue.tags == []


def test_process_venues_returns_venue_for_every_candidate():
    candidates = [
        VenueCandidate(name="Sabino Canyon", interest="hiking"),
        VenueCandidate(name="Mystery Spot", interest="hiking"),
    ]

    venues, errors = process_venues(candidates)

    assert errors == []
    assert [venue.name for venue in venues] == ["Sabino Canyon", "Mystery Spot"]


def test_process_venues_collects_errors_without_aborting_others():
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


def test_process_venues_dispatches_through_shared_executor():
    candidates = [
        VenueCandidate(name="Sabino Canyon", interest="hiking"),
        VenueCandidate(name="Mystery Spot", interest="hiking"),
    ]

    with patch.object(_executor, "submit", wraps=_executor.submit) as mock_submit:
        process_venues(candidates)

    assert mock_submit.call_count == 2
