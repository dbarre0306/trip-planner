from trip_planner.domain import TravelInfo
from trip_planner.itinerary import assemble_itinerary
from trip_planner.models import Itinerary, VenueCandidate
from trip_planner.serper_places import search_places
from trip_planner.venue_processing import process_venues


def get_all_candidates(travel_info: TravelInfo) -> list[VenueCandidate]:
    candidates: list[VenueCandidate] = []
    for interest_id in travel_info.interest_ids:
        candidates.extend(search_places(interest_id, travel_info.destination))
    return candidates


def create_itinerary(travel_info: TravelInfo) -> Itinerary:
    candidates = get_all_candidates(travel_info)

    venues, errors = process_venues(travel_info, candidates)
    for error in errors:
        print(f"Failed to process venue: {error}")

    return assemble_itinerary(travel_info, venues)