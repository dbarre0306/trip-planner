# Plan: Venue Geo Location

spec: _specs/venue-geo-location.md

## Summary

Replace the street-address retrieval currently performed in `search_places()` (`src/trip_planner/serper_places.py`) with a latitude/longitude retrieval from the same Serper Places API response. Introduce a new structured `GeoLocation` value (latitude + longitude) on both `VenueCandidate` and `Venue` (`src/trip_planner/models.py`), populate it from the places search step, and carry it through `process_venue()` (`src/trip_planner/venue_processing.py`) to the final `Venue`. The final `Venue.location` field stays in the model (per the spec's open question — kept for future use) but is now always set to `None` instead of being copied from the candidate.

## Assumptions

- The Serper Places API response includes `latitude` and `longitude` fields on each place object (alongside the `address` field it already returns). If a place is missing either value, `geo_location` is set to `None` for that candidate rather than a partially-filled object.
- `GeoLocation` is a small nested model with two fields, `latitude: float | None` and `longitude: float | None`, added to `src/trip_planner/models.py` — matching the "structured object with lat/lng fields" choice made when the spec was drafted.
- `VenueCandidate.location` and `Venue.location` remain in the models unchanged (per the spec's resolved open question: kept because `location` will be used again in the future). Only `search_places()`'s population of it, and `process_venue()`'s pass-through of it, change.
- `process_venue()` currently passes `candidate.location` (the address) into `lookup_venue(...)` and `generate_description(...)` as a "destination" argument — this is a pre-existing quirk unrelated to the trip's actual destination. Since `search_places()` will no longer populate `candidate.location`, those calls will now always receive `None` in that position. This is an accepted side effect of the spec (the venue lookup step itself is explicitly out of scope / unaffected in its own logic) and is not being separately fixed here.

## Files to Change

- `src/trip_planner/models.py` — add a `GeoLocation` model (`latitude: float | None`, `longitude: float | None`); add `geo_location: GeoLocation | None = None` to `VenueCandidate` and to `Venue`.
- `src/trip_planner/serper_places.py` — in `search_places()`, stop mapping `place.get("address")` into `location`; instead build a `GeoLocation` from `place.get("latitude")` / `place.get("longitude")` (or `None` if either is missing) and map it into the new `geo_location` field. Leave `location` unset (defaults to `None`).
- `src/trip_planner/venue_processing.py` — in `process_venue()`, stop passing `location=candidate.location` into the `Venue(...)` constructor; instead pass `geo_location=candidate.geo_location` and omit `location` (or pass `location=None` explicitly) so the final venue's `location` is always `None`.
- `tests/test_serper_places.py` — update `test_search_places_maps_full_fields` to supply `latitude`/`longitude` in the mocked response and assert `venue.geo_location` reflects them and `venue.location is None`; update `test_search_places_handles_missing_optional_fields` to assert `venue.geo_location is None` when lat/long are absent; add a new test for the partial case (only one of latitude/longitude present) confirming `geo_location` is `None` rather than partially populated.
- `tests/test_venue_processing.py` — update `test_process_venue_maps_fields_and_defaults` (and any other test asserting `venue.location`) to assert `venue.location is None` and add assertions that `venue.geo_location` equals the candidate's `geo_location` when set.

## Implementation Steps

1. Add the `GeoLocation` model to `src/trip_planner/models.py` and add the `geo_location` field to both `VenueCandidate` and `Venue`.
2. Update `search_places()` in `src/trip_planner/serper_places.py` to build `geo_location` from the place result's latitude/longitude instead of mapping `address` into `location`.
3. Update `process_venue()` in `src/trip_planner/venue_processing.py` to carry `candidate.geo_location` onto the returned `Venue` and to leave/force `location` as `None`.
4. Update `tests/test_serper_places.py` to cover: full lat/long present, lat/long absent, and partial lat/long present.
5. Update `tests/test_venue_processing.py` to assert `venue.location is None` and that `geo_location` passes through from candidate to venue.
6. Run the full test suite and confirm no other tests (e.g. `tests/test_trip_planner.py`) depend on `Venue.location` being populated from a candidate.

## Testing

- `uv run pytest tests/test_serper_places.py` — verify `geo_location` is correctly derived from latitude/longitude in the places response, degrades to `None` when either coordinate is missing, and that `location` is no longer populated by this step.
- `uv run pytest tests/test_venue_processing.py` — verify `geo_location` flows from candidate to final venue, and that `venue.location` is always `None` regardless of what the candidate carries.
- `uv run pytest` (full suite) — confirm no regressions elsewhere, including `tests/test_trip_planner.py`, which constructs a `Venue` directly with `location` set (unaffected, since that test builds a `Venue` manually rather than through the pipeline).

## Risks / Open Questions

- Real shape/field names for latitude/longitude in the Serper Places API response are assumed (`latitude` / `longitude`); if the live API uses different key names or a nested coordinates object, `search_places()`'s extraction logic will need to match the actual response shape.
- `process_venue()`'s existing use of `candidate.location` as a pseudo-"destination" argument to `lookup_venue()` and `generate_description()` will now always receive `None`. This is accepted per the spec's scope but is a behavior change worth flagging during review.
