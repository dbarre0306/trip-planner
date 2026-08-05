import pytest

from trip_planner.core.models import GeoLocation
from trip_planner.enrichment.venue_distance import haversine_miles, is_too_far

_NYC = GeoLocation(latitude=40.7128, longitude=-74.0060)
_LA = GeoLocation(latitude=34.0522, longitude=-118.2437)


def test_haversine_miles_matches_known_distance():
    distance = haversine_miles(_NYC, _LA)

    assert distance == pytest.approx(2445, abs=10)


def test_haversine_miles_is_zero_for_identical_points():
    assert haversine_miles(_NYC, _NYC) == pytest.approx(0.0, abs=1e-9)


def test_haversine_miles_is_symmetric():
    assert haversine_miles(_NYC, _LA) == pytest.approx(haversine_miles(_LA, _NYC))


def test_is_too_far_rejects_at_the_threshold():
    destination = GeoLocation(latitude=0.0, longitude=0.0)
    just_over_80_miles = GeoLocation(latitude=1.16, longitude=0.0)

    assert haversine_miles(destination, just_over_80_miles) >= 80
    assert is_too_far(destination, just_over_80_miles) is True


def test_is_too_far_accepts_just_under_the_threshold():
    destination = GeoLocation(latitude=0.0, longitude=0.0)
    just_under_80_miles = GeoLocation(latitude=1.0, longitude=0.0)

    assert haversine_miles(destination, just_under_80_miles) < 80
    assert is_too_far(destination, just_under_80_miles) is False
