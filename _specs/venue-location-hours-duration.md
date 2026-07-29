# Venue Location, Hours, and Duration Extraction

branch: claude/feature/venue-location-hours-duration

## Summary

Currently, a `Venue`'s `location`, `hours_of_operation`, and `duration_minutes` fields are never populated during venue processing — `location` is explicitly set to `None` and the other two are left at their defaults. This feature adds logic to derive these three fields from the venue's notes (the text gathered during venue lookup) so that itineraries can display where a venue actually is, when it's open, and how long a visit typically takes.

## User Story

As a trip planner user, I want each venue in my itinerary to show its location, hours of operation, and an estimated visit duration, so that I can better plan my day around when and where to go.

## Acceptance Criteria

- [ ] For each venue, the notes gathered during venue lookup are inspected to determine a `location`:
  - If the notes contain a street address for the venue, that address is used as the `location`.
  - If no street address is found, but the notes reference a distinct place or area the venue is situated within (e.g., a park, recreation area, or district that is not simply the venue's own name), that place name is used as the `location`.
  - If neither a street address nor a distinct containing place can be found in the notes, `location` is left as `null`.
- [ ] The `hours_of_operation` field is populated only when hours are explicitly stated in the notes; otherwise it is left as `null`. No hours are invented.
- [ ] The `duration_minutes` field is always populated — it is never `null` — determined in this order of preference:
  1. If a duration or typical visit length is stated in the notes, use that value (converted to minutes).
  2. If not stated in the notes, use outside knowledge already available to the model to produce a duration for this type of venue (no web search is performed for this).
  3. If the model has no specific knowledge of this venue or venue type, it must still produce its best estimate (e.g., based on the venue's category or similar venues) rather than returning `null`.
- [ ] The extracted `location` is distinct from the venue's own name — the venue name itself is never used as the `location` value.
- [ ] Existing venue fields (name, description, geo_location, url, rating, tags, notes, etc.) continue to populate as they do today; this feature only affects `location`, `hours_of_operation`, and `duration_minutes`.

## Scope

### In Scope

- Deriving `location` from venue notes, preferring a street address and falling back to a distinct containing place name.
- Deriving `hours_of_operation` from venue notes when explicitly present.
- Deriving `duration_minutes` from venue notes when explicitly present, or via a best-effort estimate drawn from the model's own knowledge when not; `duration_minutes` is always set to a value, never `null`.
- Applying this extraction as part of the existing per-venue processing flow, alongside description generation.

### Out of Scope

- Changing how notes themselves are gathered or looked up (e.g., Serper search/lookup behavior).
- Validating or geocoding the extracted `location` string against `geo_location`.
- Real-time or seasonal hours (e.g., holiday hours, day-by-day breakdowns) beyond what is stated in the notes.
- Any UI changes to display these new fields to end users.
- Performing web searches to inform the duration estimate; only the model's existing knowledge is used.

## UI / UX Notes

No user-facing UI changes are included in this feature; it populates existing `Venue` model fields (`location`, `hours_of_operation`, `duration_minutes`) that are not currently surfaced in any interface.

## Testing

- Unit tests covering location extraction: notes containing a clear street address, notes containing only a distinct place name (not the venue name), and notes containing neither (expect `null`).
- Unit tests covering hours-of-operation extraction: notes with explicit hours, and notes without any hours mentioned (expect `null`).
- Unit tests covering duration extraction: notes with an explicit duration/visit length, notes without one where the model's own knowledge should produce an estimate, and notes without one and no specific model knowledge, where the model must still produce a best-guess estimate — confirming `duration_minutes` is never `null` in any case.
- A regression check that the venue name is never returned as the `location` value.
- A regression check that other `Venue` fields are unaffected by this change.

## Open Questions

- What counts as a "distinct place" versus part of the venue's own name in ambiguous cases (e.g., a museum wing named after its parent institution)? use the parent institution
- What format should `hours_of_operation` use when notes state hours in inconsistent formats (e.g., "9-5 daily" vs. "Mon-Fri 9am-5pm")? Use whatever is found in the notes. Using the example, both are acceptable.
