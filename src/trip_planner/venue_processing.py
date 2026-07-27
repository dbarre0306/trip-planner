from concurrent.futures import ThreadPoolExecutor

from trip_planner.models import Venue, VenueCandidate
from trip_planner.serper_lookup import lookup_venue

_executor = ThreadPoolExecutor()


def process_venue(candidate: VenueCandidate) -> Venue:
    lookup_result = lookup_venue(candidate.name, candidate.location)
    return Venue(
        name=candidate.name,
        interest=candidate.interest,
        location=candidate.location,
        rating=candidate.rating,
        tags=[candidate.tag] if candidate.tag else [],
        url=lookup_result.url,
        notes=lookup_result.notes,
    )


def process_venues(candidates: list[VenueCandidate]) -> tuple[list[Venue], list[Exception]]:
    futures = [_executor.submit(process_venue, candidate) for candidate in candidates]

    venues: list[Venue] = []
    errors: list[Exception] = []
    for future in futures:
        try:
            venues.append(future.result())
        except Exception as exc:
            errors.append(exc)

    return venues, errors
