# Venue Description Generation

branch: claude/feature/venue-description-generation

## Summary

Each `Venue` currently carries a `notes` field populated with raw search-result snippets from the Serper lookup, and an unused `description` field that defaults to an empty string. This feature adds a dedicated module that calls the OpenAI API to turn a venue's `notes` — along with its name, interest, and destination — into a short, human-readable description, and wires that description into the `Venue` instance so downstream itinerary output can display it. When notes are available, the description is generated from notes alone; when there are no notes, the description is generated from the venue's name, interest, and destination instead.

## User Story

As a trip planner user, I want each recommended venue to include a concise, readable description, so that I can quickly understand what the venue is and why it might be worth visiting without having to read raw search snippets.

## Acceptance Criteria

- [ ] A new module exists whose sole responsibility is invoking the LLM to generate a venue description.
- [ ] The description-generation logic is not embedded in `venue_processing.py`, `serper_lookup.py`, or `openai_client.py` — it lives in its own module that uses `openai_client.py`'s existing helper(s) to talk to the OpenAI API.
- [ ] The module accepts the venue's name, interest, destination, and notes (list of strings) as input, and produces a single description string suitable for storing in `Venue.description`.
- [ ] When notes are present (non-empty), the generated description is based primarily on the notes, with name, interest, and destination included as light supporting context (e.g., to disambiguate the venue or ground the description in its destination) rather than as the main source.
- [ ] When notes are empty, the generated description is based on the venue's name, interest, and destination instead, producing a "cool and meaningful" description without notes to draw from.
- [ ] In both paths, the description is written to sound interesting and appealing to a tourist.
- [ ] The generated description never includes a URL, website reference, physical location/address, or hours of operation — even if such details appear in the notes.
- [ ] The generated description respects the existing `Venue.description` constraint (max length 300 characters).
- [ ] `venue_processing.py` (or the appropriate call site) is updated so that each processed `Venue` has its `description` field populated using the new module, passing along the venue's name, interest, destination, and notes gathered during lookup.
- [ ] Description generation happens synchronously within `process_venue`, as part of the existing per-venue processing step.
- [ ] If the LLM call fails or errors, venue processing for that venue does not crash the overall batch; the existing error-collection behavior in `process_venues` continues to work.

## Scope

### In Scope

- A new, standalone module for generating a venue description via the OpenAI API from a venue's name, interest, destination, and notes.
- Logic to prefer notes as the primary source (with name/interest/destination as light supporting context) when notes are present, and fall back to name/interest/destination-based generation when notes are absent.
- A prompt that produces descriptions with an engaging, tourist-facing tone in both paths, and that excludes URLs, websites, addresses/locations, and hours of operation.
- Integrating that module into the existing venue-processing flow, synchronously, so `Venue.description` is populated.
- Basic handling of LLM-call failures so the rest of venue processing is unaffected.

### Out of Scope

- Changing the `Venue` model's fields or validation rules.
- Changing how notes are collected (`serper_lookup.py`).
- Batching, caching, or rate-limiting LLM calls across multiple venues.
- Any UI/output-layer changes to how descriptions are displayed.
- Prompt engineering guidelines beyond producing a reasonable, on-topic description.

## UI / UX Notes

Not applicable — this is a backend/data-layer feature. No UI changes are involved. The only user-facing effect is that itinerary output for a venue will include a generated description instead of an empty string.

## Testing

- Unit tests for the new description-generation module, covering: notes present produces a notes-driven description, empty notes falls back to name/interest/destination-based generation, an LLM/API error is surfaced or handled without raising an unhandled exception, and the output contains no URL, website, location/address, or hours-of-operation content.
- Unit tests (or updates to existing tests) for `venue_processing.py` confirming that `Venue.description` is populated from the generated description during normal processing, for both the notes and no-notes paths.
- Verify the generated description does not exceed the `Venue.description` max length constraint in both paths.

## Open Questions

None at this time.
