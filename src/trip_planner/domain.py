from enum import Enum

class CategoryId(Enum):
    FOOD = "food"
    CULTURE = "culture"
    OUTDOORS = "outdoors"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"

class Category:
    def __init__(self, id: CategoryId, label: str):
        self._id = id
        self._label = label

    @property
    def id(self) -> CategoryId:
        return self._id

    @property
    def label(self) -> str:
        return self._label

CATEGORIES = [
    Category(CategoryId.FOOD, "Food & Drinks"),
    Category(CategoryId.CULTURE, "Culture & History"),
    Category(CategoryId.OUTDOORS, "Outdoor Activities"),
    Category(CategoryId.ENTERTAINMENT, "Entertainment"),
    Category(CategoryId.OTHER, "Other"),
]

class Interest:
    def __init__(self, query: str, label: str, category_id: CategoryId):
        self._query = query
        self._label = label
        self._category_id = category_id

    @property
    def query(self) -> str:
        return self._query

    @property
    def label(self) -> str:
        return self._label

    @property
    def category_id(self) -> CategoryId:
        return self._category_id


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


class TravelInfo:
    def __init__(self, destination: str, start_date: str, num_days: int, num_adults: int, num_children: int = 0, interests: list[str] = []):
        self._destination = destination
        self._start_date = start_date
        self._num_days = num_days
        self._num_adults = num_adults
        self._num_children = num_children
        self._interests = interests

    @property
    def destination(self) -> str:
        return self._destination

    @property
    def start_date(self) -> str:
        return self._start_date

    @property
    def num_days(self) -> int:
        return self._num_days

    @property
    def num_adults(self) -> int:
        return self._num_adults

    @property
    def num_children(self) -> int:
        return self._num_children

    @property
    def interests(self) -> list[str]:
        return self._interests

