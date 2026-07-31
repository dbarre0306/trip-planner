from trip_planner.standard_venues import STANDARD_VENUES


def test_standard_venues_defines_breakfast_lunch_and_dinner_in_order():
    assert [venue.name for venue in STANDARD_VENUES] == ["Breakfast", "Lunch", "Dinner"]


def test_breakfast_venue_matches_the_spec():
    breakfast = STANDARD_VENUES[0]

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


def test_lunch_venue_matches_the_spec():
    lunch = STANDARD_VENUES[1]

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


def test_dinner_venue_matches_the_spec():
    dinner = STANDARD_VENUES[2]

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
