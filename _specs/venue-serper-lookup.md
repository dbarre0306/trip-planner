# Venue Serper Lookup

branch: claude/feature/venue-serper-lookup

## Summary

Turning a `VenueCandidate` into a fully-formed `Venue` is a multi-step pipeline. This spec covers only the first step of that pipeline: a new module that performs a Serper web search for a given venue name and destination, and returns the venue's website URL along with a list of descriptive notes drawn from the search result snippets. This gives downstream venue-processing steps a reachable, verified URL and raw source material (notes) to work with, without yet handling the rest of the venue enrichment process.

## User Story

As the venue-processing pipeline, I want to look up a venue candidate's name and destination via Serper, so that I can attach a verified, reachable website URL and a set of descriptive notes to the venue before further enrichment happens.

## Acceptance Criteria

- [ ] Given a venue name and a destination, the module performs a Serper search using both as input.
- [ ] The module examines search results in order and selects the URL of the first result whose website is actually reachable.
- [ ] If none of the returned results are reachable, the module returns no URL (rather than a broken one).
- [ ] The module collects the snippet text from every search result into a list of notes, regardless of which result's URL was selected as reachable.
- [ ] The returned URL and notes are structured so they can be assigned directly to a `Venue`'s `url` and `notes` fields.
- [ ] A venue search that returns no results at all is handled without raising an unhandled error.

## Scope

### In Scope

- A new module responsible for querying Serper with a venue name and location.
- Logic to determine reachability of candidate result URLs and select the first reachable one.
- Collection of all result snippets into a notes list.
- Returning the URL and notes in a form consumable by the existing `Venue` model's `url` and `notes` fields.

### Out of Scope

- Any other step of the venue candidate-to-venue processing pipeline (e.g. description generation, hours of operation, duration, tagging).
- Changes to the existing `VenueCandidate` or `Venue` data models beyond using their existing `url`/`notes` fields.
- Changes to the existing Serper Places search module used for initial candidate discovery.
- Retrying or caching failed reachability checks.
- Rate limiting or throttling of Serper API calls.

## UI / UX Notes

Not applicable — this is a backend data-processing module with no user-facing interface.

## Testing

- Unit tests covering: a normal case with multiple results where the first result is reachable; a case where the first result is unreachable but a later one is; a case where no results are reachable; a case where Serper returns zero results.
- Tests should verify that notes always contain all snippets regardless of which URL was chosen, and that reachability checks and snippet collection are decoupled correctly.
- Tests should mock the Serper API and the reachability check so no real network calls are made.

## Open Questions

- What counts as "reachable" — a successful HTTP response (e.g. 2xx/3xx status) versus any response at all, and what timeout should be used? An http request using HEAD with a status < 400
- Should reachability checks be performed concurrently (similar to the existing venue processing thread pool) to avoid slow sequential checks against multiple candidate URLs? no
