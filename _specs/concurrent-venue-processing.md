# Concurrent Venue Processing

branch: claude/feature/concurrent-venue-processing

## Summary

Introduce a new venue processing step that runs for every `VenueCandidate` discovered during itinerary creation. The processing logic will live in its own module and, for this iteration, will be a no-op placeholder — its purpose here is only to establish the seam where future venue enrichment/validation logic will be added. The key behavioral change in this spec is _how_ venues are processed: instead of processing venues one at a time in a sequential loop, venues are processed concurrently using a thread pool, so that once real work is added to the processing step, it does not block on each venue in turn.

## User Story

As a developer extending the trip planner, I want venue processing to happen concurrently across all discovered venues, so that adding real per-venue work (e.g. calls to external APIs) later doesn't make itinerary creation slower than it needs to be.

## Acceptance Criteria

- [ ] A new, separate module exists whose sole responsibility is processing a single venue.
- [ ] The venue processing function currently does nothing (no-op) but is called for every venue produced by the venue search step.
- [ ] Venues for a given interest are processed concurrently via a thread pool rather than sequentially.
- [ ] The itinerary creation flow (`create_itinerary`) is updated to invoke concurrent venue processing instead of (or in addition to) the current sequential print loop.
- [ ] The change does not alter the behavior or output of venue search (`search_places`) itself.
- [ ] If a single venue's processing raises an error, it does not silently disappear — the failure is surfaced in a way that lets the caller know something went wrong.

## Scope

### In Scope

- A new module dedicated to venue processing, containing a no-op processing function/entry point.
- Updating the itinerary creation flow to submit each venue to a thread pool for processing.
- Ensuring all submitted venues are processed (waited on) before itinerary creation for a given interest completes.

### Out of Scope

- Any real venue processing logic (enrichment, filtering, scoring, external API calls, etc.) — the processing step is a placeholder only.
- Changing how venues are searched/discovered (`serper_places.py`).
- Persisting or returning processed venue results to a caller beyond what already happens today.
- Tuning thread pool size, retries, backoff, or rate limiting for future real processing work.

## UI / UX Notes

Not applicable — this is a backend/internal processing change with no user-facing interface.

## Testing

- Unit test that the new venue processing module's function can be called with a venue and completes without error (no-op behavior).
- Unit/integration test verifying that `create_itinerary` submits every discovered venue for processing when given a set of interests/venues.
- Test verifying that venues are processed concurrently (e.g. via a thread pool) rather than strictly sequentially, and that all results/completions are accounted for before moving on.
- Test covering the case where venue processing raises an exception, confirming the error is surfaced rather than silently swallowed.

## Open Questions

- Should the thread pool be created once per `create_itinerary` call, once per interest, or shared/reused across the whole crew run? shared/reused across the whole crew app
- What should happen to the overall itinerary creation flow if processing fails for one or more venues — abort entirely, skip the failed venue, or collect and report all failures at the end? collect and report all failures at the end
- Does the no-op processing function need a defined signature/return type now (e.g. returning the venue unchanged) to make future real implementation a drop-in replacement? Yes, it will need to return a Venue:

```
class Venue(BaseModel):
    name: str
    interest: str | None
    description: str = Field(default="", max_length=300)
    location: str | None = None
    url: str | None = None
    hours_of_operation: str | None = None
    duration_minutes: int | None = None
    origin: Literal["web", "standard"] = "web"
    tags: list[str] = []
    notes: list[str] = []
    status: Literal["accepted", "rejected"] = "accepted"
    rejection_reason: str | None = None
```
