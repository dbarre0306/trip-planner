import os

import requests

from trip_planner.models import VenueCandidate

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


def search_places(interest: str, destination: str) -> list[VenueCandidate]:
    places = _get_serper_places(f"{interest} {destination}")
    return [
        VenueCandidate(
            name=place.get("title"),
            interest=interest,
            location=place.get("address"),
            tag=place.get("category"),
            rating=place.get("rating"),
        )
        for place in places
    ]
