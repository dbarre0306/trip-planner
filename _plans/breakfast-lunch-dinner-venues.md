# Plan: Breakfast, Lunch, and Dinner Placeholder Venues

spec: _specs/breakfast-lunch-dinner-venues.md

## Summary

Add a new module that defines three fixed, generic `Venue` entries — Breakfast, Lunch, and Dinner — with `origin: "standard"`. These are static data, not derived from any candidate or web lookup. `process_venues` in `venue_processing.py` will append this fixed set of three standard venues (one of each, per trip) to the deduplicated list of web-sourced venues it already returns, so callers get both kinds of venues from the same function without any change to how web-sourced venues are searched, looked up, or deduplicated.

## Assumptions

- The three standard venues are a fixed, hardcoded list (not built from `VenueCandidate` or any lookup/description/details pipeline) — the spec's exact field values are static.
- "One per trip" means `process_venues` appends exactly one Breakfast, one Lunch, and one Dinner venue per call, regardless of how many candidates were passed in.
- The new module exposes a plain list (or a zero-argument function returning a list) of the three `Venue` objects; `venue_processing.py` imports and uses it directly.
- The standard venues are appended *after* `resolve_duplicate_venues(venues)` runs on the web-sourced venues, so they are never deduplicated against (or accidentally merged with) web-sourced venues — the spec's open-question answer says to merge "after processing for the duplicate venues."
- `duration_minutes` is explicitly set on all three standard venues: `60` for Breakfast and Lunch, `120` for Dinner.

## Files to Change

- `src/trip_planner/standard_venues.py` — new module. Defines the three `Venue` objects (Breakfast, Lunch, Dinner) with the exact field values from the spec (`origin="standard"`, `status="accepted"`, matching `name`/`description`/`tags`, everything else left at its default/`None`, except `duration_minutes` which is `60` for Breakfast and Lunch and `120` for Dinner), exposed as a single list constant.
- `src/trip_planner/venue_processing.py` — import the new standard venues list and, in `process_venues`, append it to the result of `resolve_duplicate_venues(venues)` before returning, so the final `(list[Venue], list[Exception])` tuple includes both the deduplicated web-sourced venues and the three standard venues.
- `tests/test_standard_venues.py` — new test file. Verifies each of the three standard venues has the exact field values specified in the spec.
- `tests/test_venue_processing.py` — extend existing tests to assert `process_venues` includes exactly one Breakfast, one Lunch, and one Dinner venue in its output alongside the web-sourced venues, and that existing web-sourced venue behavior (search/lookup/processing/deduplication) is unchanged.

## Implementation Steps

1. Create `src/trip_planner/standard_venues.py` defining the three `Venue` objects exactly as specified (Breakfast/Lunch/Dinner names, descriptions, `origin="standard"`, `status="accepted"`, `tags=["breakfast"|"lunch"|"dinner"]`, `duration_minutes` of `60` for Breakfast/Lunch and `120` for Dinner, all other fields at their default/`None`), collected into one exported list constant.
2. In `src/trip_planner/venue_processing.py`, import the new standard venues list from `standard_venues.py`.
3. Update `process_venues` to append the standard venues list to the deduplicated web-sourced venues (i.e. `return resolve_duplicate_venues(venues) + standard_venues_list, errors`), leaving `process_venue`, the executor/futures handling, and error collection untouched.
4. Add `tests/test_standard_venues.py` asserting each of the three venues' `name`, `description`, `origin`, `status`, `tags`, and the `None`/empty-list defaults for the remaining fields match the spec exactly.
5. Extend `tests/test_venue_processing.py` to cover `process_venues` returning the three standard venues in addition to whatever web-sourced venues result from the existing test candidates, and confirm the web-sourced portion of the output and any existing assertions are unaffected.
6. Run `uv run pytest` and fix any failures before considering the change complete.

## Testing

- New unit tests in `tests/test_standard_venues.py` construct/inspect the three standard venues and assert every field (`name`, `description`, `origin`, `status`, `tags`, `duration_minutes`, and the `None`/empty defaults for `interest_id`, `location`, `location_type`, `geo_location`, `url`, `hours_of_operation`, `rating`, `notes`, `rejection_reason`) matches the spec exactly — including that Breakfast's and Lunch's `duration_minutes` are `60` and Dinner's is `120`.
- Extended tests in `tests/test_venue_processing.py` call `process_venues` and assert the returned venue list contains exactly one Breakfast, one Lunch, and one Dinner venue (by name/tag) in addition to the processed web-sourced venues, and that the existing web-sourced venue assertions (search, lookup, processing, deduplication, error collection) still pass unchanged.
- Run the full suite with `uv run pytest` to confirm no regressions elsewhere.

## Risks / Open Questions

- If `process_venues` is called multiple times within a single trip-planning run (e.g. once per interest or search batch), appending the standard venues list on every call could produce duplicate Breakfast/Lunch/Dinner entries instead of "one per trip." Confirm how many times `process_venues` is invoked per trip before implementing, and if it's more than once, the standard venues may need to be added once at a higher level (e.g. where `process_venues` results are ultimately assembled into the trip's venue list) rather than inside `process_venues` itself.
