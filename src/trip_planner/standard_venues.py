from trip_planner.models import Venue

STANDARD_VENUES: list[Venue] = [
    Venue(
        name="Breakfast",
        interest_id=None,
        description="A generic placehold for breakfast at a restaurant or other establishment.",
        origin="standard",
        tags=["breakfast"],
        duration_minutes=60,
        status="accepted",
    ),
    Venue(
        name="Lunch",
        interest_id=None,
        description="A generic placehold for lunch at a restaurant or other establishment.",
        origin="standard",
        tags=["lunch"],
        duration_minutes=60,
        status="accepted",
    ),
    Venue(
        name="Dinner",
        interest_id=None,
        description="A generic placehold for dinner at a restaurant or other establishment.",
        origin="standard",
        tags=["dinner"],
        duration_minutes=120,
        status="accepted",
    ),
]
