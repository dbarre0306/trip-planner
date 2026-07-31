from dataclasses import dataclass, field
from enum import Enum

class CategoryId(Enum):
    FOOD = "food"
    CULTURE = "culture"
    OUTDOORS = "outdoors"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"

@dataclass(frozen=True)
class Category:
    id: CategoryId
    label: str

CATEGORIES = [
    Category(CategoryId.FOOD, "Food & Drinks"),
    Category(CategoryId.CULTURE, "Culture & History"),
    Category(CategoryId.OUTDOORS, "Outdoor Activities"),
    Category(CategoryId.ENTERTAINMENT, "Entertainment"),
    Category(CategoryId.OTHER, "Other"),
]

def find_category_by_id(id: CategoryId) -> Category | None:
    return next((category for category in INTERESTS if category.id == id), None)

class InterestId(Enum):
    RESTAURANTS = "restaurants"
    STREET_FOOD = "street-food"
    COFFEE_SHOPS = "coffee-shops"
    MUSEUMS = "museums"
    HISTORY = "history"
    LIVE_MUSIC = "live-music"
    SHOWS = "shows"
    AMUSEMENT_PARKS = "amusement-parks"
    HIKING = "hiking"
    BEACHES = "beaches"
    SCENIC_VIEWS = "scenic-views"
    SHOPPING = "shopping"
    WELLNESS = "wellness"

@dataclass(frozen=True)
class Interest:
    id: InterestId
    search_text: str
    label: str
    category_id: CategoryId
    examples: tuple[str, ...] = ()

INTERESTS = [
    # Food
    Interest(InterestId.RESTAURANTS, "restaurants", "Restaurants", CategoryId.FOOD),
    Interest(InterestId.STREET_FOOD, "street food and markets", "Street food & markets", CategoryId.FOOD),
    Interest(InterestId.COFFEE_SHOPS, "coffee shops", "Coffee shops", CategoryId.FOOD),

    # Culture
    Interest(InterestId.MUSEUMS, "museums", "Museums", CategoryId.CULTURE),
    Interest(InterestId.HISTORY, "history", "History", CategoryId.CULTURE),

    # Entertainment
    Interest(InterestId.LIVE_MUSIC, "live music", "Live music & nightlife", CategoryId.ENTERTAINMENT),
    Interest(InterestId.SHOWS, "shows and performances", "Shows & performances", CategoryId.ENTERTAINMENT),
    Interest(InterestId.AMUSEMENT_PARKS, "amusement parks", "Amusement parks", CategoryId.ENTERTAINMENT),

    # Outdoors
    Interest(InterestId.HIKING, "hiking trails", "Hiking", CategoryId.OUTDOORS),
    Interest(InterestId.BEACHES, "beaches", "Beaches", CategoryId.OUTDOORS),
    Interest(InterestId.SCENIC_VIEWS, "scenic views", "Scenic views", CategoryId.OUTDOORS),

    # Other
    Interest(InterestId.SHOPPING, "shopping", "Shopping", CategoryId.OTHER),
    Interest(InterestId.WELLNESS, "wellness", "Wellness & relaxation", CategoryId.OTHER),
]

def find_interest_by_id(id: InterestId) -> Interest | None:
    return next((interest for interest in INTERESTS if interest.id == id), None)

def choices_for(category_id: CategoryId) -> list[str]:
    return [i.label for i in INTERESTS if i.category_id == category_id]

@dataclass(frozen=True)
class TravelInfo:
    destination: str
    travel_dates: list[str]
    num_adults: int
    num_children: int = 0
    interest_ids: list[InterestId] = field(default_factory=list)
