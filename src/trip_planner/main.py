#!/usr/bin/env python
import warnings

from dotenv import load_dotenv

from trip_planner.domain import InterestId, TravelInfo
from trip_planner.trip_planner import create_itinerary

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

load_dotenv()

def run():
    """
    Run the trip planner.
    """
    try:
        #interests = [InterestId.RESTAURANTS, InterestId.STREET_FOOD, InterestId.COFFEE_SHOPS]
        interests = [InterestId.RESTAURANTS, InterestId.HIKING]

        travel_info = TravelInfo(
            destination = "Tucson, AZ",
            travel_dates = ["2026-09-01", "2026-09-02", "2026-09-03"],
            num_adults = 2,
            num_children = 0,
            interest_ids=interests
        )
        create_itinerary(travel_info)
    except Exception as e:
        raise Exception(f"An error occurred while running the trip planner: {e}")
