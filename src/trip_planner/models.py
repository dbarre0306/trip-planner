from typing import Literal

from pydantic import BaseModel, Field

class GeoLocation(BaseModel):
    latitude: float
    longitude: float

class VenueCandidate(BaseModel):
    name: str
    interest: str | None = None
    location: str | None = None
    geo_location: GeoLocation | None = None
    tag: str | None = None
    rating: float | None = None

class VenueCandidates(BaseModel):
    candidates: list[VenueCandidate]

class Venue(BaseModel):
    name: str
    interest: str | None
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