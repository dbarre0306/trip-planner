import os

import requests

from trip_planner.core.domain import InterestId, find_interest_by_id
from trip_planner.core.models import GeoLocation, VenueCandidate

SERPER_PLACES_URL = "https://google.serper.dev/places"

def _get_serper_places(query: str) -> list[VenueCandidate]:
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        raise RuntimeError("SERPER_API_KEY environment variable is not set")
    response = requests.post(
        SERPER_PLACES_URL,
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
        json={"q": query},
    )
    response.raise_for_status()
    return response.json().get("places", [])


def _get_geo_location(place: dict) -> GeoLocation | None:
    latitude = place.get("latitude")
    longitude = place.get("longitude")
    if latitude is None or longitude is None:
        return None
    return GeoLocation(latitude=latitude, longitude=longitude)


def get_destination_geo_location(destination: str) -> GeoLocation | None:
    places = _get_serper_places(destination)
    if not places:
        return None
    return _get_geo_location(places[0])


def search_places(
    interest_id: InterestId, destination: str, *, family_friendly: bool = False
) -> list[VenueCandidate]:
    interest = find_interest_by_id(interest_id)
    search_text = interest.search_text if interest else ""
    if family_friendly:
        search_text = f"{search_text} family friendly"
    places = _get_serper_places(f"{search_text} '{destination}'")
    return [
        VenueCandidate(
            name=place.get("title"),
            interest_id=interest_id,
            geo_location=_get_geo_location(place),
            tag=place.get("category"),
            rating=place.get("rating"),
        )
        for place in places
    ]
