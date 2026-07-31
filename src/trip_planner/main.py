#!/usr/bin/env python
import warnings

from dotenv import load_dotenv

from trip_planner.domain import InterestId, TravelInfo, find_interest_by_id
from trip_planner.trip_planner import create_itinerary

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

load_dotenv()

def _to_queries(interests: list[InterestId]) -> list[str]:
    return [interest.query for id in interests if (interest := find_interest_by_id(id)) is not None]

def run():
    """
    Run the trip planner.
    """
    try:
        #interests = [InterestId.RESTAURANTS, InterestId.STREET_FOOD, InterestId.COFFEE_SHOPS]
        interests = [InterestId.RESTAURANTS]

        travel_info = TravelInfo(
            destination = "Tucson, AZ",
            start_date = "2026-09-01",
            num_days = 3,
            num_adults = 2,
            num_children = 0,
            interests=_to_queries(interests)
        )
        create_itinerary(travel_info)
    except Exception as e:
        raise Exception(f"An error occurred while running the trip planner: {e}")
