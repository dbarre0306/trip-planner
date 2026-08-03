from concurrent.futures import ThreadPoolExecutor

from trip_planner.domain import TravelInfo
from trip_planner.models import GeoLocation, Venue, VenueCandidate
from trip_planner.serper_lookup import lookup_venue
from trip_planner.serper_places import get_destination_geo_location
from trip_planner.standard_venues import build_standard_venues
from trip_planner.venue_cost import estimate_venue_cost
from trip_planner.venue_deduplication import resolve_duplicate_venues
from trip_planner.venue_description import generate_description
from trip_planner.venue_details import VenueDetails, estimate_duration_minutes, extract_venue_details
from trip_planner.venue_distance import is_too_far
from trip_planner.venue_meal_tags import determine_meal_tags

_executor = ThreadPoolExecutor()


def _determine_status(
    details: VenueDetails,
    url: str | None,
    venue_geo_location: GeoLocation | None,
    destination_geo_location: GeoLocation | None,
) -> tuple[str, str | None]:
    if details.closed:
        return "rejected", "closed"
    if not url:
        return "rejected", "no website"
    if venue_geo_location and destination_geo_location and is_too_far(venue_geo_location, destination_geo_location):
        return "rejected", "too far from destination"
    return "accepted", None


def process_venue(
    travel_info: TravelInfo, candidate: VenueCandidate, destination_geo_location: GeoLocation | None = None
) -> Venue:
    lookup_result = lookup_venue(candidate.name, travel_info.destination)
    description = generate_description(
        candidate.name, candidate.interest_id, travel_info.destination, lookup_result.notes
    )
    details = extract_venue_details(candidate.name, travel_info.destination, lookup_result.notes)
    duration_minutes = details.duration_minutes
    if duration_minutes is None:
        duration_minutes = estimate_duration_minutes(candidate.name, details.location)
    status, rejection_reason = _determine_status(
        details, lookup_result.url, candidate.geo_location, destination_geo_location
    )
    meal_tags = determine_meal_tags(
        candidate.interest_id, candidate.name, lookup_result.notes, details.hours_of_operation
    )
    tags = ([candidate.tag] if candidate.tag else []) + meal_tags
    cost = estimate_venue_cost(
        candidate.name, candidate.interest_id, travel_info.destination, description, lookup_result.notes, tags
    )

    return Venue(
        name=candidate.name,
        interest_id=candidate.interest_id,
        description=description,
        location=details.location,
        location_type=details.location_type,
        geo_location=candidate.geo_location,
        rating=candidate.rating,
        tags=tags,
        url=lookup_result.url,
        hours_of_operation=details.hours_of_operation,
        duration_minutes=duration_minutes,
        notes=lookup_result.notes,
        status=status,
        rejection_reason=rejection_reason,
        estimated_cost_per_adult=cost.per_adult,
        estimated_cost_per_child=cost.per_child,
    )


def process_venues(travel_info: TravelInfo, candidates: list[VenueCandidate]) -> tuple[list[Venue], list[Exception]]:
    try:
        destination_geo_location = get_destination_geo_location(travel_info.destination)
    except Exception:
        destination_geo_location = None

    futures = [
        _executor.submit(process_venue, travel_info, candidate, destination_geo_location)
        for candidate in candidates
    ]

    venues: list[Venue] = []
    errors: list[Exception] = []
    for future in futures:
        try:
            venues.append(future.result())
        except Exception as exc:
            errors.append(exc)

    return resolve_duplicate_venues(venues) + build_standard_venues(travel_info.destination), errors
