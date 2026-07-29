from concurrent.futures import ThreadPoolExecutor

from trip_planner.domain import TravelInfo
from trip_planner.models import Venue, VenueCandidate
from trip_planner.serper_lookup import lookup_venue
from trip_planner.venue_description import generate_description
from trip_planner.venue_details import estimate_duration_minutes, extract_venue_details

_executor = ThreadPoolExecutor()


def process_venue(travel_info: TravelInfo, candidate: VenueCandidate) -> Venue:
    lookup_result = lookup_venue(candidate.name, travel_info.destination)
    description = generate_description(
        candidate.name, candidate.interest, travel_info.destination, lookup_result.notes
    )
    details = extract_venue_details(candidate.name, lookup_result.notes)
    duration_minutes = details.duration_minutes
    if duration_minutes is None:
        duration_minutes = estimate_duration_minutes(candidate.name, details.location)

    return Venue(
        name=candidate.name,
        interest=candidate.interest,
        description=description,
        location=details.location,
        geo_location=candidate.geo_location,
        rating=candidate.rating,
        tags=[candidate.tag] if candidate.tag else [],
        url=lookup_result.url,
        hours_of_operation=details.hours_of_operation,
        duration_minutes=duration_minutes,
        notes=lookup_result.notes,
    )


def process_venues(travel_info: TravelInfo, candidates: list[VenueCandidate]) -> tuple[list[Venue], list[Exception]]:
    futures = [_executor.submit(process_venue, travel_info, candidate) for candidate in candidates]

    venues: list[Venue] = []
    errors: list[Exception] = []
    for future in futures:
        try:
            venues.append(future.result())
        except Exception as exc:
            errors.append(exc)

    return venues, errors
