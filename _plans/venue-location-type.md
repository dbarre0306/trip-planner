# Plan: Venue Location Type

spec: _specs/venue-location-type.md

## Summary

Add a `location_type` classification (`Literal["STREET_ADDRESS", "PLACE"] | None`) that travels alongside a venue's existing `location` string. The only place `location` is actually determined today is the LLM-based extraction in `venue_details.py`, which already distinguishes a street address from a containing place when it produces `location`. Rather than re-deriving that distinction separately (which would risk diverging from the existing rules), the extraction prompt is extended to also return the classification in the same response, and the result is threaded through `VenueDetails` → `venue_processing.py` → `Venue` exactly like `location` is today.

## Assumptions

- "A venue's data model" in the spec's acceptance criteria refers to the `Venue` model (`src/trip_planner/models.py`), which is the model that actually carries a populated `location` today. `VenueCandidate.location` is never set anywhere in the current codebase (`serper_places.py` never populates it), so it is out of scope for this plan — there is no "location determined" event for `VenueCandidate` to attach a type to.
- The LLM extraction step in `venue_details.py` is the single source of truth for both `location` and `location_type`; no independent classification logic (e.g. regex-based address detection) is introduced, per the spec's "no separate lookup or new data source" constraint.
- Per the spec's resolved open question, `location_type` is typed as `Literal["STREET_ADDRESS", "PLACE"] | None`, not a plain string.

## Files to Change

- `src/trip_planner/models.py` — add `location_type: Literal["STREET_ADDRESS", "PLACE"] | None = None` to the `Venue` model, next to its existing `location` field.
- `src/trip_planner/venue_details.py` — the core of this change:
  - Add `location_type: Literal["STREET_ADDRESS", "PLACE"] | None = None` to the `VenueDetails` dataclass.
  - Extend `_EXTRACTION_INSTRUCTIONS` to request a fourth JSON key, `location_type`, describing it as the classification of whatever value was produced for `location`: `"STREET_ADDRESS"` when `location` is a street address, `"PLACE"` when `location` is a containing place/area, and `null` when `location` itself is `null`. Update the "Respond with ONLY a JSON object with exactly these..." line to list all four keys.
  - Add a small parsing helper (alongside `_as_optional_str` / `_as_optional_int`) that coerces the raw `location_type` value to one of the two accepted literal strings, or `None` for anything else (missing key, wrong casing, unexpected value, etc.).
  - Update the resolution logic so the existing invariant holds even if the model response is inconsistent: whenever the resolved `location` ends up `None` (either the raw value was `null`, or `_resolve_location` nulled it out because it echoed the venue name back), `location_type` must also be forced to `None`.
  - Update `extract_venue_details` to parse `location_type` from the response and apply the coercion/consistency logic above before constructing `VenueDetails`.
- `src/trip_planner/venue_processing.py` — pass `location_type=details.location_type` into the `Venue(...)` construction in `process_venue`, alongside the existing `location=details.location`.
- `tests/test_venue_details.py` — extend/add cases (see Testing below).
- `tests/test_venue_processing.py` — extend the field-mapping test to cover `location_type` passthrough.

## Implementation Steps

1. Add the `location_type` field to the `Venue` model in `models.py`.
2. Add the `location_type` field to the `VenueDetails` dataclass in `venue_details.py`.
3. Update `_EXTRACTION_INSTRUCTIONS` to ask the model for `location_type` alongside `location`, `hours_of_operation`, and `duration_minutes`, describing the same street-address-vs-place distinction already used for `location`.
4. Add a coercion helper that maps the raw parsed value to `"STREET_ADDRESS"`, `"PLACE"`, or `None`.
5. Update `extract_venue_details` to read `location_type` from the parsed JSON, coerce it, and force it to `None` whenever the resolved `location` is `None` (reusing/extending the existing `_resolve_location` check).
6. Wire `details.location_type` into the `Venue(...)` call in `venue_processing.py`.
7. Update `tests/test_venue_details.py` and `tests/test_venue_processing.py` per the Testing section.
8. Run `uv run pytest` and fix any failures.

## Testing

In `tests/test_venue_details.py`:
- Street-address case: mock response includes `"location_type": "STREET_ADDRESS"` alongside the existing street-address `location`; assert `result.location_type == "STREET_ADDRESS"`.
- Distinct-place case: mock response includes `"location_type": "PLACE"` alongside the existing place-name `location`; assert `result.location_type == "PLACE"`.
- Null-location case: mock response has `"location": null, "location_type": null`; assert `result.location_type is None`.
- Venue-name-echoed-back case (existing "never returns venue name as location" test): even if the mocked response includes a non-null `location_type`, assert it is forced to `None` once `location` resolves to `None`, preserving the consistency invariant.
- No-notes case: assert the default `VenueDetails()` has `location_type is None` (already true via the dataclass default).
- Malformed-JSON case: assert `location_type is None` (already covered by the existing `VenueDetails()` equality check).
- Unexpected value case: mock response with `"location_type": "SOMETHING_ELSE"` (or missing entirely) alongside a non-null `location`; assert it coerces to `None` rather than raising.

In `tests/test_venue_processing.py`:
- Extend `test_process_venue_maps_fields_and_defaults` (or add a new test) so the mocked `VenueDetails` includes a `location_type`, and assert `venue.location_type` matches it after `process_venue` runs.

Run the full suite with `uv run pytest` to confirm no regressions elsewhere.

## Risks / Open Questions

- The consistency invariant ("a non-`None` location always pairs with exactly one of the two type values") can only be *guaranteed* in the direction of nulling `location_type` when `location` is `None`. If the model returns a non-null `location` but an invalid/missing `location_type`, the coercion helper falls back to `None`, which technically leaves a non-null `location` paired with a `None` type — a narrow gap between the spec's stated invariant and what can be enforced without adding new classification logic (which is out of scope). This is expected to be rare in practice given the prompt now explicitly asks for the paired value, but is worth flagging during implementation.
