from unittest.mock import patch

from trip_planner.domain import InterestId, TravelInfo
from trip_planner.itinerary import assemble_itinerary
from trip_planner.models import GeoLocation, Venue
from trip_planner.venue_operating_hours import OperatingHours


def _venue(
    name: str,
    interest_id: InterestId | None = None,
    *,
    tags: list[str] | None = None,
    rating: float | None = None,
    duration_minutes: int = 60,
    geo_location: GeoLocation | None = None,
    origin: str = "web",
    status: str = "accepted",
    **kwargs,
) -> Venue:
    return Venue(
        name=name,
        interest_id=interest_id,
        tags=tags or [],
        rating=rating,
        duration_minutes=duration_minutes,
        geo_location=geo_location,
        origin=origin,
        status=status,
        **kwargs,
    )


def _to_minutes(start_time: str) -> int:
    hours, minutes = start_time.split(":")
    return int(hours) * 60 + int(minutes)


def test_meals_scheduled_within_windows_and_breakfast_first():
    breakfast = _venue("Cafe Sunrise", InterestId.COFFEE_SHOPS, tags=["breakfast"], rating=4.5)
    lunch = _venue("Bistro Noon", InterestId.RESTAURANTS, tags=["lunch"], rating=4.5)
    dinner = _venue("Dinner House", InterestId.RESTAURANTS, tags=["dinner"], rating=4.5)
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, [breakfast, lunch, dinner])

    venues = itinerary.days[0].venues
    assert venues[0].name == "Cafe Sunrise"
    assert 6 * 60 <= _to_minutes(venues[0].start_time) <= 9 * 60

    lunch_entry = next(v for v in venues if v.name == "Bistro Noon")
    assert 11 * 60 <= _to_minutes(lunch_entry.start_time) <= 13 * 60

    dinner_entry = next(v for v in venues if v.name == "Dinner House")
    assert 17 * 60 <= _to_minutes(dinner_entry.start_time) <= 20 * 60


def test_dinner_duration_is_extended_to_two_hours_when_venue_duration_is_shorter():
    dinner = _venue(
        "Quick Bites", InterestId.RESTAURANTS, tags=["dinner"], rating=4.5, duration_minutes=45
    )
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, [dinner])

    dinner_entry = itinerary.days[0].venues[0]
    assert dinner_entry.name == "Quick Bites"
    assert dinner_entry.duration_minutes == 120


def test_dinner_duration_is_not_shortened_when_venue_duration_is_longer():
    dinner = _venue(
        "Tasting Menu", InterestId.RESTAURANTS, tags=["dinner"], rating=4.5, duration_minutes=150
    )
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, [dinner])

    dinner_entry = itinerary.days[0].venues[0]
    assert dinner_entry.duration_minutes == 150


def test_breakfast_and_lunch_durations_are_not_extended_to_two_hours():
    breakfast = _venue(
        "Cafe Sunrise", InterestId.COFFEE_SHOPS, tags=["breakfast"], rating=4.5, duration_minutes=30
    )
    lunch = _venue(
        "Bistro Noon", InterestId.RESTAURANTS, tags=["lunch"], rating=4.5, duration_minutes=45
    )
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, [breakfast, lunch])

    venues = itinerary.days[0].venues
    assert next(v for v in venues if v.name == "Cafe Sunrise").duration_minutes == 30
    assert next(v for v in venues if v.name == "Bistro Noon").duration_minutes == 45


@patch("trip_planner.itinerary.parse_operating_hours")
def test_activity_after_dinner_respects_the_extended_dinner_duration(mock_parse_operating_hours):
    # Dinner's own duration (45min) would end too early to leave a 60-min gap before an
    # activity that only opens at 8pm; the enforced 2-hour dinner duration is what makes room.
    dinner = _venue(
        "Quick Bites", InterestId.RESTAURANTS, tags=["dinner"], rating=4.5, duration_minutes=45
    )
    after_dinner_activity = _venue(
        "Night Walk",
        InterestId.SCENIC_VIEWS,
        rating=4.0,
        duration_minutes=30,
        hours_of_operation="Opens at 8pm",
    )

    def side_effect(hours_of_operation):
        if hours_of_operation == "Opens at 8pm":
            return OperatingHours(open_minutes=20 * 60)
        return OperatingHours()

    mock_parse_operating_hours.side_effect = side_effect
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, [dinner, after_dinner_activity])

    venues = itinerary.days[0].venues
    dinner_entry = next(v for v in venues if v.name == "Quick Bites")
    activity_entry = next((v for v in venues if v.name == "Night Walk"), None)

    assert dinner_entry.duration_minutes == 120
    assert activity_entry is not None
    dinner_end = _to_minutes(dinner_entry.start_time) + dinner_entry.duration_minutes
    assert _to_minutes(activity_entry.start_time) - dinner_end >= 60


@patch("trip_planner.itinerary.generate_standard_meal_description")
def test_standard_breakfast_used_only_when_no_other_venue_available(mock_generate_description):
    mock_generate_description.return_value = "A whimsical placeholder breakfast."
    real_breakfast = _venue("Cafe Sunrise", InterestId.COFFEE_SHOPS, tags=["breakfast"], rating=4.0)
    standard_breakfast = _venue("Breakfast", None, tags=["breakfast"], origin="standard")
    travel_info = TravelInfo(
        destination="Tucson, AZ", travel_dates=["2026-09-01", "2026-09-02"], num_adults=2
    )

    itinerary = assemble_itinerary(travel_info, [real_breakfast, standard_breakfast])

    day1_breakfast = itinerary.days[0].venues[0]
    day2_breakfast = itinerary.days[1].venues[0]
    assert day1_breakfast.name == "Cafe Sunrise"
    assert day2_breakfast.name == "Breakfast"
    assert day2_breakfast.description == "A whimsical placeholder breakfast."
    mock_generate_description.assert_called_once_with("breakfast", "Tucson, AZ")


def test_no_overlap_and_minimum_gap_and_chronological_order():
    activities = [
        _venue(
            f"Activity {i}",
            InterestId.MUSEUMS if i % 2 == 0 else InterestId.HIKING,
            rating=3.0 + i * 0.1,
            duration_minutes=45,
            geo_location=GeoLocation(latitude=32.0, longitude=-110.0),
        )
        for i in range(8)
    ]
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, activities)

    venues = itinerary.days[0].venues
    assert len(venues) >= 2
    starts = [_to_minutes(v.start_time) for v in venues]
    assert starts == sorted(starts)
    for i in range(len(venues) - 1):
        end_of_current = starts[i] + venues[i].duration_minutes
        assert starts[i + 1] - end_of_current >= 60


def test_day_numbers_start_at_one_and_increase():
    travel_info = TravelInfo(
        destination="Tucson, AZ",
        travel_dates=["2026-09-01", "2026-09-02", "2026-09-03"],
        num_adults=2,
    )

    itinerary = assemble_itinerary(travel_info, [])

    assert [day.day_number for day in itinerary.days] == [1, 2, 3]
    assert [day.date for day in itinerary.days] == ["2026-09-01", "2026-09-02", "2026-09-03"]


def test_rejected_venues_are_excluded():
    rejected = _venue("Closed Place", InterestId.MUSEUMS, status="rejected", rejection_reason="closed")
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, [rejected])

    assert itinerary.days[0].venues == []


def test_venue_never_repeats_across_the_trip():
    only_lunch_spot = _venue("Only Lunch Spot", InterestId.RESTAURANTS, tags=["lunch"], rating=5.0)
    travel_info = TravelInfo(
        destination="Tucson, AZ", travel_dates=["2026-09-01", "2026-09-02"], num_adults=2
    )

    itinerary = assemble_itinerary(travel_info, [only_lunch_spot])

    day1_names = [v.name for v in itinerary.days[0].venues]
    day2_names = [v.name for v in itinerary.days[1].venues]
    assert day1_names.count("Only Lunch Spot") + day2_names.count("Only Lunch Spot") == 1


def test_higher_rated_meal_venue_is_preferred():
    low_rated = _venue("So-so Diner", InterestId.RESTAURANTS, tags=["lunch"], rating=3.0)
    high_rated = _venue("Great Diner", InterestId.RESTAURANTS, tags=["lunch"], rating=4.8)
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, [low_rated, high_rated])

    lunch_entry = next(v for v in itinerary.days[0].venues if "Diner" in v.name)
    assert lunch_entry.name == "Great Diner"


def test_prefers_variety_over_repeating_interest_within_a_day():
    museum_a = _venue("Museum A", InterestId.MUSEUMS, rating=5.0)
    museum_b = _venue("Museum B", InterestId.MUSEUMS, rating=4.9)
    trailhead = _venue("Trailhead", InterestId.HIKING, rating=3.0)
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, [museum_a, museum_b, trailhead])

    names_in_order = [v.name for v in itinerary.days[0].venues]
    assert names_in_order.index("Museum A") < names_in_order.index("Trailhead")
    assert names_in_order.index("Trailhead") < names_in_order.index("Museum B")


def test_activities_are_geographically_clustered_by_day():
    north = [
        _venue(
            f"North {i}",
            InterestId.MUSEUMS,
            rating=4.0,
            duration_minutes=30,
            geo_location=GeoLocation(latitude=40.0 + i * 0.01, longitude=-110.0),
        )
        for i in range(3)
    ]
    south = [
        _venue(
            f"South {i}",
            InterestId.HIKING,
            rating=4.0,
            duration_minutes=30,
            geo_location=GeoLocation(latitude=10.0 + i * 0.01, longitude=-110.0),
        )
        for i in range(3)
    ]
    travel_info = TravelInfo(
        destination="Tucson, AZ", travel_dates=["2026-09-01", "2026-09-02"], num_adults=2
    )

    itinerary = assemble_itinerary(travel_info, north + south)

    day1_names = {v.name for v in itinerary.days[0].venues}
    day2_names = {v.name for v in itinerary.days[1].venues}
    north_names = {"North 0", "North 1", "North 2"}
    south_names = {"South 0", "South 1", "South 2"}
    assert (day1_names, day2_names) in ((north_names, south_names), (south_names, north_names))


def test_estimated_cost_usd_reflects_party_size():
    venue = _venue(
        "Lunch Spot",
        InterestId.RESTAURANTS,
        tags=["lunch"],
        rating=4.0,
        estimated_cost_per_adult=20.0,
        estimated_cost_per_child=10.0,
    )
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2, num_children=3)

    itinerary = assemble_itinerary(travel_info, [venue])

    lunch_entry = itinerary.days[0].venues[0]
    assert lunch_entry.estimated_cost_usd == 2 * 20.0 + 3 * 10.0


def test_scheduled_venue_omits_unknown_location_fields():
    venue = _venue("Mystery Museum", InterestId.MUSEUMS, rating=4.0)
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=1)

    itinerary = assemble_itinerary(travel_info, [venue])

    entry = itinerary.days[0].venues[0]
    assert entry.location is None
    assert entry.location_type is None
    assert entry.geo_location is None
    dumped = entry.model_dump(exclude_none=True)
    assert "location" not in dumped
    assert "location_type" not in dumped
    assert "geo_location" not in dumped


def test_day_left_without_meal_when_nothing_available():
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, [])

    assert itinerary.days[0].venues == []


def test_interest_category_reflects_domain_category_label():
    venue = _venue("City Museum", InterestId.MUSEUMS, rating=4.0)
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=1)

    itinerary = assemble_itinerary(travel_info, [venue])

    assert itinerary.days[0].venues[0].interest_category == "Culture & History"


@patch("trip_planner.itinerary.generate_standard_meal_description")
def test_standard_meal_copy_uses_food_and_drinks_category(mock_generate_description):
    mock_generate_description.return_value = "Fun placeholder."
    standard_breakfast = _venue("Breakfast", None, tags=["breakfast"], origin="standard")
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=1)

    itinerary = assemble_itinerary(travel_info, [standard_breakfast])

    assert itinerary.days[0].venues[0].interest_category == "Food & Drinks"


def test_no_travel_dates_returns_empty_days_list():
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=[], num_adults=1)

    itinerary = assemble_itinerary(travel_info, [])

    assert itinerary.days == []
    assert itinerary.destination == "Tucson, AZ"


def test_itinerary_total_cost_sums_all_scheduled_venues():
    lunch = _venue(
        "Lunch Spot",
        InterestId.RESTAURANTS,
        tags=["lunch"],
        rating=4.0,
        estimated_cost_per_adult=20.0,
        estimated_cost_per_child=0.0,
    )
    dinner = _venue(
        "Dinner Spot",
        InterestId.RESTAURANTS,
        tags=["dinner"],
        rating=4.0,
        estimated_cost_per_adult=30.0,
        estimated_cost_per_child=0.0,
    )
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, [lunch, dinner])

    assert itinerary.destination == "Tucson, AZ"
    assert itinerary.num_adults == 2
    assert itinerary.num_children == 0
    assert itinerary.estimated_cost_usd == 2 * 20.0 + 2 * 30.0


@patch("trip_planner.itinerary.parse_operating_hours")
def test_venue_not_scheduled_before_its_opening_time(mock_parse_operating_hours):
    late_opener = _venue(
        "Afternoon Bistro",
        InterestId.RESTAURANTS,
        tags=["lunch"],
        rating=5.0,
        hours_of_operation="Opens at 1pm",
    )
    early_opener = _venue(
        "Noon Cafe",
        InterestId.RESTAURANTS,
        tags=["lunch"],
        rating=3.0,
        hours_of_operation="Opens at 11am",
    )

    def side_effect(hours_of_operation):
        if hours_of_operation == "Opens at 1pm":
            return OperatingHours(open_minutes=13 * 60)
        return OperatingHours(open_minutes=11 * 60)

    mock_parse_operating_hours.side_effect = side_effect
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, [late_opener, early_opener])

    lunch_entry = itinerary.days[0].venues[0]
    assert lunch_entry.name == "Noon Cafe"


@patch("trip_planner.itinerary.parse_operating_hours")
def test_venue_not_scheduled_on_a_day_it_is_closed(mock_parse_operating_hours):
    monday_closed = _venue(
        "Weekday Grill",
        InterestId.RESTAURANTS,
        tags=["lunch"],
        rating=5.0,
        hours_of_operation="Closed Mondays",
    )
    always_open = _venue(
        "Diner",
        InterestId.RESTAURANTS,
        tags=["lunch"],
        rating=3.0,
        hours_of_operation="Daily",
    )

    def side_effect(hours_of_operation):
        if hours_of_operation == "Closed Mondays":
            return OperatingHours(closed_weekdays=frozenset({0}))
        return OperatingHours()

    mock_parse_operating_hours.side_effect = side_effect
    # 2026-09-07 is a Monday.
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-07"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, [monday_closed, always_open])

    lunch_entry = itinerary.days[0].venues[0]
    assert lunch_entry.name == "Diner"


def test_venue_without_hours_information_can_be_scheduled_any_time():
    venue = _venue("Mystery Diner", InterestId.RESTAURANTS, tags=["lunch"], rating=4.0)
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, [venue])

    assert itinerary.days[0].venues[0].name == "Mystery Diner"


@patch("trip_planner.itinerary.parse_operating_hours")
def test_activity_never_scheduled_before_its_opening_time(mock_parse_operating_hours):
    evening_only = _venue(
        "Night Market",
        InterestId.SHOPPING,
        rating=4.5,
        duration_minutes=60,
        hours_of_operation="Opens at 7pm",
    )
    mock_parse_operating_hours.return_value = OperatingHours(open_minutes=19 * 60)
    travel_info = TravelInfo(destination="Tucson, AZ", travel_dates=["2026-09-01"], num_adults=2)

    itinerary = assemble_itinerary(travel_info, [evening_only])

    assert itinerary.days[0].venues == []
