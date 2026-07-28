#!/usr/bin/env python
import warnings

from dotenv import load_dotenv

from trip_planner.domain import TravelInfo
from trip_planner.trip_planner import create_itinerary

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

load_dotenv()


def run():
    """
    Run the trip planner.
    """
    try:
        travel_info = TravelInfo(
            destination = "Tucson, AZ",
            start_date = "09/01/2026",
            num_days = 3,
            num_adults = 2,
            num_children = 0,
            interests = ["restaurants"]
            #interests = ["hiking trails", "restaurants"]
        )
        create_itinerary(travel_info)
    except Exception as e:
        raise Exception(f"An error occurred while running the trip planner: {e}")
