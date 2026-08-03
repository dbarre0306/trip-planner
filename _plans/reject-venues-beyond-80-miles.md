# Plan: Reject Venues Beyond 80 Miles

spec: _specs/reject-venues-beyond-80-miles.md

## Summary

Add a distance check to venue enrichment that rejects any venue 80 miles or more (great-circle distance, via the Haversine formula) from the trip's destination. The destination's coordinates are resolved once per itinerary via the existing Serper Places integration, then compared against each venue's already-known `geo_location` as part of the existing accept/reject logic in `venue_processing.py`.

## Assumptions

- If the destination's coordinates cannot be resolved (Serper error, no results, or missing coordinates on the result), the distance check is skipped and venues are not rejected for distance — consistent with how other enrichment failures in `process_venues` are collected as errors rather than aborting the whole run, and with the spec not calling for the itinerary to fail outright.
- If a venue candidate has no `geo_location` (Serper Places returned no coordinates for it), the distance check is skipped for that venue and it is not rejected for distance — there's nothing to compare, and this mirrors how `location`/`hours_of_operation` are already treated as optional elsewhere in the pipeline.
- The rejection reason string is `"too far from destination"`, matching the short, lowercase style of the existing `"closed"` and `"no website"` reasons.
- The 80-mile check applies only to venues produced by `process_venue` (i.e. `origin="web"`). The standard placeholder venues (Breakfast/Lunch/Dinner) have no `geo_location` and are appended after processing, so they're naturally unaffected — no special-casing needed.
- Destination coordinates are resolved by querying the existing Serper Places endpoint with the destination string itself and taking the first result's coordinates, reusing `serper_places.py`'s existing request/parsing helpers.
- The threshold is a hard cutoff: distance >= 80 miles rejects, distance < 80 miles is unaffected (already reflected in the spec's Acceptance Criteria wording).

## Files to Change

- `src/trip_planner/venue_distance.py` — new. Pure Haversine distance calculation (`haversine_miles(a: GeoLocation, b: GeoLocation) -> float`) and an `_MAX_DISTANCE_MILES = 80` constant plus a small helper to test a pair of coordinates against the threshold.
- `src/trip_planner/serper_places.py` — add `get_destination_geo_location(destination: str) -> GeoLocation | None`, reusing `_get_serper_places` and `_get_geo_location` to look up the destination itself and return the first result's coordinates (or `None` if unavailable).
- `src/trip_planner/venue_processing.py` — `process_venues` resolves the destination's `GeoLocation` once (guarded so a lookup failure doesn't abort the run) and passes it through to `process_venue`. `process_venue` passes the candidate's `geo_location` and the destination's `geo_location` into `_determine_status`. `_determine_status` gains the distance check, applied after the existing closed/no-url checks, only when both coordinates are present.
- `tests/test_venue_distance.py` — new. Unit tests for the Haversine calculation and threshold helper.
- `tests/test_serper_places.py` — add tests for `get_destination_geo_location` (happy path, no results, missing coordinates, API key missing/error propagation).
- `tests/test_venue_processing.py` — update existing `_determine_status`/`process_venue` tests to account for the new parameters, and add cases for: venue under threshold accepted, venue at/over threshold rejected with the correct reason, venue with no `geo_location` unaffected, destination coordinates unresolved unaffected. Update `process_venues` tests to stub the new destination-lookup call.

## Implementation Steps

1. Add `venue_distance.py` with the Haversine formula implementation and the 80-mile threshold check, taking two `GeoLocation` values.
2. Add `get_destination_geo_location` to `serper_places.py`, reusing the existing places-search request and coordinate-parsing helpers.
3. Update `venue_processing._determine_status` to accept the venue's and destination's `GeoLocation` (both optional) and return a `"rejected"` status with reason `"too far from destination"` when both are present and the distance is >= 80 miles, leaving existing closed/no-url behavior unchanged.
4. Update `process_venue` to accept a `destination_geo_location: GeoLocation | None` parameter and pass it, along with `candidate.geo_location`, into `_determine_status`.
5. Update `process_venues` to resolve the destination's `GeoLocation` once via `get_destination_geo_location` (catching and ignoring failures so the run continues without the distance check), and pass the result into every `process_venue` call submitted to the executor.
6. Add/update unit tests per the Files to Change section above.

## Testing

- `tests/test_venue_distance.py`: verify Haversine output against known coordinate pairs with known real-world distances, and verify the threshold helper's accept/reject boundary at exactly 80 miles.
- `tests/test_serper_places.py`: verify `get_destination_geo_location` builds the expected request, maps the first result's coordinates, and returns `None` when there are no places or coordinates are missing.
- `tests/test_venue_processing.py`: verify a venue just under 80 miles from the destination is accepted, a venue at or over 80 miles is rejected with reason `"too far from destination"`, a venue with no `geo_location` is unaffected, and an itinerary where the destination's coordinates can't be resolved leaves distance-based rejection out entirely (existing closed/no-url checks still apply).
- Run `uv run pytest` to confirm the full suite still passes.

## Risks / Open Questions

- None outstanding — the spec's open questions were resolved (destination coordinates via Serper; hard cutoff at 80 miles).
