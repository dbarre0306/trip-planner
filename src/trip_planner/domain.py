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

@dataclass(frozen=True)
class Interest:
    query: str
    label: str
    category_id: CategoryId

INTERESTS = [
    # Food
    Interest("restaurants", "Restaurants", CategoryId.FOOD),
    Interest("street food and markets", "Street food & markets", CategoryId.FOOD),
    Interest("coffee shops", "Coffee shops", CategoryId.FOOD),

    # Culture
    Interest("museums", "Museums", CategoryId.CULTURE),
    Interest("history", "History", CategoryId.CULTURE),

    # Entertainment
    Interest("live music", "Live music & nightlife", CategoryId.ENTERTAINMENT),
    Interest("shows", "Shows & performances", CategoryId.ENTERTAINMENT),
    Interest("amusement parks", "Amusement parks", CategoryId.ENTERTAINMENT),

    # Outdoors
    Interest("hiking", "Hiking", CategoryId.OUTDOORS),
    Interest("beaches", "Beaches", CategoryId.OUTDOORS),
    Interest("scenic views", "Scenic views", CategoryId.OUTDOORS),

    # Other
    Interest("shopping", "Shopping", CategoryId.OTHER),
    Interest("wellness", "Wellness & relaxation", CategoryId.OTHER),
]


@dataclass(frozen=True)
class TravelInfo:
    destination: str
    start_date: str
    num_days: int
    num_adults: int
    num_children: int = 0
    interests: list[str] = field(default_factory=list)
