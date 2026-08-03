import math

from trip_planner.models import GeoLocation

_EARTH_RADIUS_MILES = 3958.8
_MAX_DISTANCE_MILES = 80


def haversine_miles(a: GeoLocation, b: GeoLocation) -> float:
    lat1, lon1 = math.radians(a.latitude), math.radians(a.longitude)
    lat2, lon2 = math.radians(b.latitude), math.radians(b.longitude)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    haversine = (
        math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return _EARTH_RADIUS_MILES * 2 * math.asin(math.sqrt(haversine))


def is_too_far(a: GeoLocation, b: GeoLocation) -> bool:
    return haversine_miles(a, b) >= _MAX_DISTANCE_MILES
