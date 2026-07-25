from pydantic import BaseModel

class VenueCandidate(BaseModel):
    name: str
    interest: str | None = None
    address: str | None = None
    tag: str | None = None

class VenueCandidates(BaseModel):
    candidates: list[VenueCandidate]