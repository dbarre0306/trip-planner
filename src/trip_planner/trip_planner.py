from typing import Callable

from trip_planner.domain import TravelInfo
from trip_planner.itinerary import assemble_itinerary
from trip_planner.models import Itinerary, VenueCandidate
from trip_planner.serper_places import search_places
from trip_planner.venue_processing import process_venues

OnStage = Callable[[str, int | None], None]

STAGE_SEARCH_COMPLETE = "search_complete"
STAGE_PROCESSING_COMPLETE = "processing_complete"
STAGE_BUILD_COMPLETE = "build_complete"


def get_all_candidates(travel_info: TravelInfo) -> list[VenueCandidate]:
    candidates: list[VenueCandidate] = []
    for interest_id in travel_info.interest_ids:
        candidates.extend(search_places(interest_id, travel_info.destination))
    return candidates


def create_itinerary(travel_info: TravelInfo, *, on_stage: OnStage | None = None) -> Itinerary:
    candidates = get_all_candidates(travel_info)
    if on_stage:
        on_stage(STAGE_SEARCH_COMPLETE, len(candidates))

    venues, errors = process_venues(travel_info, candidates)
    for error in errors:
        print(f"Failed to process venue: {error}")
    if on_stage:
        on_stage(STAGE_PROCESSING_COMPLETE, None)

    itinerary = assemble_itinerary(travel_info, venues)
    if on_stage:
        on_stage(STAGE_BUILD_COMPLETE, None)

    return itinerary