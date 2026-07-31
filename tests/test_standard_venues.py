from unittest.mock import patch

from trip_planner.standard_venues import build_standard_venues
from trip_planner.venue_cost import VenueCost

_DESTINATION = "Tucson, AZ"


@patch("trip_planner.standard_venues.estimate_venue_cost")
def test_standard_venues_defines_breakfast_lunch_and_dinner_in_order(mock_estimate_venue_cost):
    mock_estimate_venue_cost.return_value = VenueCost(per_adult=15.0, per_child=8.0)

    venues = build_standard_venues(_DESTINATION)

    assert [venue.name for venue in venues] == ["Breakfast", "Lunch", "Dinner"]


@patch("trip_planner.standard_venues.estimate_venue_cost")
def test_breakfast_venue_matches_the_spec(mock_estimate_venue_cost):
    mock_estimate_venue_cost.return_value = VenueCost(per_adult=15.0, per_child=8.0)

    breakfast = build_standard_venues(_DESTINATION)[0]

    assert breakfast.name == "Breakfast"
    assert breakfast.interest_id is None
    assert breakfast.description == (
        "A generic placehold for breakfast at a restaurant or other establishment."
    )
    assert breakfast.location is None
    assert breakfast.location_type is None
    assert breakfast.geo_location is None
    assert breakfast.url is None
    assert breakfast.hours_of_operation is None
    assert breakfast.duration_minutes == 60
    assert breakfast.origin == "standard"
    assert breakfast.rating is None
    assert breakfast.tags == ["breakfast"]
    assert breakfast.notes == []
    assert breakfast.status == "accepted"
    assert breakfast.rejection_reason is None
    assert breakfast.estimated_cost_per_adult == 15.0
    assert breakfast.estimated_cost_per_child == 8.0


@patch("trip_planner.standard_venues.estimate_venue_cost")
def test_lunch_venue_matches_the_spec(mock_estimate_venue_cost):
    mock_estimate_venue_cost.return_value = VenueCost(per_adult=15.0, per_child=8.0)

    lunch = build_standard_venues(_DESTINATION)[1]

    assert lunch.name == "Lunch"
    assert lunch.interest_id is None
    assert lunch.description == (
        "A generic placehold for lunch at a restaurant or other establishment."
    )
    assert lunch.location is None
    assert lunch.location_type is None
    assert lunch.geo_location is None
    assert lunch.url is None
    assert lunch.hours_of_operation is None
    assert lunch.duration_minutes == 60
    assert lunch.origin == "standard"
    assert lunch.rating is None
    assert lunch.tags == ["lunch"]
    assert lunch.notes == []
    assert lunch.status == "accepted"
    assert lunch.rejection_reason is None
    assert lunch.estimated_cost_per_adult == 15.0
    assert lunch.estimated_cost_per_child == 8.0


@patch("trip_planner.standard_venues.estimate_venue_cost")
def test_dinner_venue_matches_the_spec(mock_estimate_venue_cost):
    mock_estimate_venue_cost.return_value = VenueCost(per_adult=15.0, per_child=8.0)

    dinner = build_standard_venues(_DESTINATION)[2]

    assert dinner.name == "Dinner"
    assert dinner.interest_id is None
    assert dinner.description == (
        "A generic placehold for dinner at a restaurant or other establishment."
    )
    assert dinner.location is None
    assert dinner.location_type is None
    assert dinner.geo_location is None
    assert dinner.url is None
    assert dinner.hours_of_operation is None
    assert dinner.duration_minutes == 120
    assert dinner.origin == "standard"
    assert dinner.rating is None
    assert dinner.tags == ["dinner"]
    assert dinner.notes == []
    assert dinner.status == "accepted"
    assert dinner.rejection_reason is None
    assert dinner.estimated_cost_per_adult == 15.0
    assert dinner.estimated_cost_per_child == 8.0


@patch("trip_planner.standard_venues.estimate_venue_cost")
def test_build_standard_venues_passes_the_destination_to_the_estimator(mock_estimate_venue_cost):
    mock_estimate_venue_cost.return_value = VenueCost(per_adult=15.0, per_child=8.0)

    build_standard_venues(_DESTINATION)

    for call in mock_estimate_venue_cost.call_args_list:
        assert call.args[2] == _DESTINATION


@patch("trip_planner.standard_venues.estimate_venue_cost")
def test_build_standard_venues_returns_none_costs_when_estimator_cannot_determine_them(
    mock_estimate_venue_cost,
):
    mock_estimate_venue_cost.return_value = VenueCost(per_adult=None, per_child=None)

    breakfast = build_standard_venues(_DESTINATION)[0]

    assert breakfast.estimated_cost_per_adult is None
    assert breakfast.estimated_cost_per_child is None


@patch("trip_planner.standard_venues.estimate_venue_cost")
def test_build_standard_venues_returns_distinct_instances_across_calls(mock_estimate_venue_cost):
    mock_estimate_venue_cost.return_value = VenueCost(per_adult=15.0, per_child=8.0)

    first_call = build_standard_venues(_DESTINATION)
    second_call = build_standard_venues(_DESTINATION)

    for first_venue, second_venue in zip(first_call, second_call):
        assert first_venue is not second_venue
        assert first_venue.tags is not second_venue.tags
