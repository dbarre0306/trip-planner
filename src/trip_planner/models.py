from pydantic import BaseModel

class VenueCandidate(BaseModel):
    name: str
    interest: str | None = None
    location: str | None = None
    tag: str | None = None
    rating: float | None = None

class VenueCandidates(BaseModel):
    candidates: list[VenueCandidate]