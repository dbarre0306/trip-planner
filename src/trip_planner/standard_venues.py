from trip_planner.models import Venue
from trip_planner.venue_cost import estimate_venue_cost

_BASE_STANDARD_VENUES: list[Venue] = [
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


def build_standard_venues(destination: str | None) -> list[Venue]:
    venues = []
    for base in _BASE_STANDARD_VENUES:
        cost = estimate_venue_cost(
            base.name, base.interest_id, destination, base.description, base.notes, base.tags
        )
        venues.append(
            base.model_copy(
                deep=True,
                update={
                    "estimated_cost_per_adult": cost.per_adult,
                    "estimated_cost_per_child": cost.per_child,
                },
            )
        )
    return venues
