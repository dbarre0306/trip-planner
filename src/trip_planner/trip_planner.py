from trip_planner.domain import TravelInfo
from trip_planner.models import VenueCandidate
from trip_planner.serper_places import search_places
from trip_planner.venue_processing import process_venues


def get_all_candidates(travel_info: TravelInfo) -> list[VenueCandidate]:
    candidates: list[VenueCandidate] = []
    for interest in travel_info.interests:
        candidates.extend(search_places(interest, travel_info.destination))
    return candidates


def create_itinerary(travel_info: TravelInfo):
    candidates = get_all_candidates(travel_info)
    for candidate in candidates:
        print(candidate.model_dump_json(indent=2))
    print("--------------")

    venues, errors = process_venues(candidates)
    for venue in venues:
        print(venue.model_dump_json(indent=2))
    for error in errors:
        print(f"Failed to process venue: {error}")