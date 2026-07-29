# Venue Geo Location

branch: claude/feature/venue-geo-location

## Summary

Venue candidates are currently enriched with a street address pulled from the places search results and carried through to the final venue record as a `location` string. This feature replaces that address retrieval with a geographic coordinate (latitude/longitude) lookup instead. The address field is dropped entirely — `location` on the final venue will always be null — and a new structured `geo_location` field (holding latitude and longitude) is populated in its place, flowing through the venue pipeline the same way `location` does today.

## User Story

As a trip planner user, I want venues to carry precise geographic coordinates instead of a free-text address, so that downstream features (e.g. mapping, distance/routing calculations) can rely on structured, unambiguous location data.

## Acceptance Criteria

- [ ] The places search step no longer reads or stores a street address for a venue candidate.
- [ ] The places search step retrieves latitude and longitude for each venue candidate from the places search results.
- [ ] A new `geo_location` field, structured with distinct latitude and longitude values, is available on both the venue candidate and the final venue record.
- [ ] `geo_location` is populated end-to-end: from the places search result, onto the venue candidate, and through to the final venue record.
- [ ] The `location` field on the final venue record is always null.
- [ ] If latitude/longitude data is unavailable for a given place result, `geo_location` is null (or its lat/long components are null) rather than causing an error.

## Scope

### In Scope

- Updating the places search step to stop retrieving/storing a street address.
- Updating the places search step to retrieve latitude/longitude from the places search results.
- Adding a structured `geo_location` representation (latitude + longitude) to the venue candidate model.
- Adding the same structured `geo_location` representation to the final venue model.
- Carrying `geo_location` through the existing venue processing pipeline (candidate -> final venue), the same way `location` currently flows through.
- Ensuring the final venue's `location` field is always null.

### Out of Scope

- Any changes to the venue lookup step that fetches a venue's URL and descriptive notes (this step does not currently retrieve an address and is unaffected).
- Any changes to venue description generation.
- Removing the `location` field itself from the venue candidate or venue models (it remains present but unused/null on the final venue).
- Adding any new consumers of `geo_location` (e.g. maps, distance calculations) — this feature only introduces and populates the field.
- Reverse geocoding or converting coordinates back into a human-readable address.

## UI / UX Notes

Not applicable — this is a backend data model and retrieval change with no user-facing UI.

## Testing

- Unit tests covering the places search step should verify that a venue candidate's `geo_location` is populated from latitude/longitude values in the search results, and that no address/location value is set.
- Unit tests should cover the case where latitude/longitude is missing from a place result, confirming `geo_location` degrades gracefully (null) rather than raising.
- Tests covering the venue processing pipeline should verify that `geo_location` set on a venue candidate is carried through to the final venue record, and that the final venue's `location` is always null.
- Existing tests that assert on the previous address-based `location` behavior should be updated to reflect the new `geo_location` behavior.

## Open Questions

- Should the existing `location` field be deprecated/removed from the models in a future pass now that it will always be null on the final venue, or is keeping it as an unused field intentional for now? it will be used in the future so keep it
