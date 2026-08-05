from typing import Literal

from pydantic import BaseModel, Field, computed_field

from trip_planner.core.domain import InterestId

class GeoLocation(BaseModel):
    latitude: float
    longitude: float

class VenueCandidate(BaseModel):
    name: str
    interest_id: InterestId | None = None
    location: str | None = None
    geo_location: GeoLocation | None = None
    tag: str | None = None
    rating: float | None = None

class VenueCandidates(BaseModel):
    candidates: list[VenueCandidate]

class Venue(BaseModel):
    name: str
    interest_id: InterestId | None
    description: str = Field(default="", max_length=300)
    location: str | None = None
    location_type: Literal["STREET_ADDRESS", "PLACE"] | None = None
    geo_location: GeoLocation | None = None
    url: str | None = None
    hours_of_operation: str | None = None
    duration_minutes: int | None = None
    origin: Literal["web", "standard"] = "web"
    rating: float | None = None
    tags: list[str] = []
    notes: list[str] = []
    status: Literal["accepted", "rejected"] = "accepted"
    rejection_reason: str | None = None
    estimated_cost_per_adult: float | None = None
    estimated_cost_per_child: float | None = None

class ScheduledVenue(BaseModel):
    name: str
    interest_category: str
    description: str
    rating: float | None = None
    location: str | None = None
    location_type: Literal["STREET_ADDRESS", "PLACE"] | None = None
    geo_location: GeoLocation | None = None
    hours_of_operation: str | None = None
    url: str | None = None
    start_time: str
    duration_minutes: int
    estimated_cost_usd: float

class ItineraryDay(BaseModel):
    day_number: int
    date: str
    venues: list[ScheduledVenue]

    @computed_field  # type: ignore[misc]
    @property
    def estimated_cost_usd(self) -> float:
        return round(sum(venue.estimated_cost_usd for venue in self.venues), 2)

class Itinerary(BaseModel):
    destination: str
    num_adults: int
    num_children: int
    days: list[ItineraryDay]

    @computed_field  # type: ignore[misc]
    @property
    def estimated_cost_usd(self) -> float:
        return round(sum(day.estimated_cost_usd for day in self.days), 2)

