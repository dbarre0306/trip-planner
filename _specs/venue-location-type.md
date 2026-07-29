# Venue Location Type

branch: claude/feature/venue-location-type

## Summary

Venues currently carry a free-form `location` value that is either a street address, the name of a containing place (e.g. a park or parent institution), or absent entirely. This feature introduces a companion `location_type` classification that records which of those three kinds of value `location` holds — `"STREET_ADDRESS"`, `"PLACE"`, or `None` — so that downstream logic can later branch on the kind of location without re-parsing or re-inferring it. This spec covers only introducing and populating the classification; no feature consumes it yet.

## User Story

As a developer building future venue-location behavior (e.g. formatting, geocoding, or display logic that differs for a street address vs. a general place), I want each venue to carry an explicit `location_type` alongside its `location`, so that I don't have to re-derive whether a location string is a street address or a place name.

## Acceptance Criteria

- [ ] A venue's data model includes a `location_type` field that holds one of `"STREET_ADDRESS"`, `"PLACE"`, or `None`.
- [ ] When a venue's `location` is determined to be a street address, `location_type` is set to `"STREET_ADDRESS"`.
- [ ] When a venue's `location` is determined to be a place (a distinct place or area the venue sits within, not a street address), `location_type` is set to `"PLACE"`.
- [ ] When a venue's `location` is `None`, `location_type` is also `None`.
- [ ] `location_type` is always consistent with `location` — a `None` location never pairs with a non-`None` type, and a non-`None` location always pairs with exactly one of the two type values.

## Scope

### In Scope

- Adding the `location_type` classification alongside the existing `location` value wherever `location` is determined for a venue.
- Ensuring the classification is derived from the same source information used to determine `location` (i.e. no separate lookup or new data source is introduced).

### Out of Scope

- Any feature or behavior that consumes or branches on `location_type` — this spec only introduces and populates the field.
- Changing the existing rules for what qualifies as a street address vs. a place, or when `location` itself is `None`.
- Backfilling or migrating any previously stored venue data.

## UI / UX Notes

Not applicable — this is a data-model addition with no direct user-facing surface.

## Testing

- Cover the case where `location` resolves to a street address and confirm `location_type` is `"STREET_ADDRESS"`.
- Cover the case where `location` resolves to a place name and confirm `location_type` is `"PLACE"`.
- Cover the case where `location` is `None` and confirm `location_type` is also `None`.

## Open Questions

- Should `location_type` be represented as a plain string, or as a more constrained type (e.g. an enum/Literal)? use a literal (None is still acceptable)
