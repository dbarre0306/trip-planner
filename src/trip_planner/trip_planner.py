from trip_planner.domain import TravelInfo
from trip_planner.serper_places import search_places


def create_itinerary(travel_info: TravelInfo):
    for interest in travel_info.interests:
        venues = search_places(interest, travel_info.destination)
        for venue in venues:
            print(venue.model_dump_json(indent=2))