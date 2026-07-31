# Typed Interest IDs Throughout Venue Pipeline

branch: claude/feature/typed-interest-ids-pipeline

## Summary

The `InterestId` enum was introduced to give interest selection a stable, typed identity instead of relying on free-text query strings, but the conversion currently only happens at the outermost selection boundary. Everywhere downstream — trip info, venue candidates, generated venues, place search, and meal-tag determination — still passes around and compares raw interest strings. This means files like the meal-tag logic have to hardcode their own copies of interest text that must be kept manually in sync with the canonical interest list, with no enforcement if they drift. This feature extends the typed-id approach through the entire venue pipeline so that interest identity is represented and compared as `InterestId` everywhere, and raw text is produced only at the specific points where human-readable or search-query text is actually required.

## User Story

As a developer maintaining the trip planner, I want interest values to be represented by a typed identifier throughout the venue pipeline, so that interest comparisons are type-checked and centrally defined, and adding, renaming, or removing an interest can't silently desynchronize logic in unrelated files.

## Acceptance Criteria

- [ ] Trip info, venue candidates, and generated venues all represent their interest by typed identifier rather than a raw string.
- [ ] Interest identity comparisons and branching (e.g. meal-tag eligibility and rules) are made against the typed identifier, not string literals.
- [ ] Raw interest text (search-query wording, human-readable labels) is derived from the typed identifier only at the specific points where that text is needed — building a search query and building LLM-facing prompt text — not stored or compared elsewhere.
- [ ] No interest text is duplicated or hardcoded outside of the single canonical interest definition list.
- [ ] End-to-end itinerary generation continues to work unchanged for the existing hardcoded interest selections (restaurants, coffee shops, street food and markets).
- [ ] Meal-tag behavior is unchanged in outcome: coffee shop venues are still tagged breakfast, street food/market venues are never tagged breakfast, and eligible/ineligible interest categories are unchanged.

## Scope

### In Scope

- Extending the typed interest identifier through trip info, venue candidate, and generated venue representations.
- Updating venue search/query construction to resolve the typed identifier to search text only when calling the external place search.
- Updating venue description generation to resolve the typed identifier to human-readable label text only when building LLM prompt text.
- Updating meal-tag determination to compare against the typed identifier instead of hardcoded string literals.
- Adding a lookup helper to resolve a raw query string back to its typed identifier, if needed to preserve any existing string-based entry point.
- Updating existing tests that currently construct venue candidates/venues using raw interest strings.

### Out of Scope

- Changing the set of available interests, their categories, their query wording, or their display labels.
- Adding any new user-facing or CLI-based interest selection input; interest selection remains a fixed, developer-chosen list.
- Fixing unrelated pre-existing bugs discovered during exploration (e.g. category lookup helper scanning the wrong list).

## UI / UX Notes

Not applicable — this is an internal, non-user-facing refactor with no UI. There is no change to what output the trip planner produces, only to how interest identity is represented and compared internally.

## Testing

- Full existing automated test suite must continue to pass, with fixtures and assertions updated to construct and compare interests via the typed identifier instead of raw strings.
- Manual end-to-end run of the trip planner with the existing hardcoded interest selection(s) to confirm itineraries still generate correctly, including correct place-search results and correct venue descriptions.
- Targeted verification of meal-tag determination behavior for each eligible interest category (restaurants, coffee shops, street food and markets), confirming coffee shops always resolve to breakfast and street food/market venues never receive a breakfast tag.

## Open Questions

- Should the fixed, hardcoded interest selection list in the entry point continue to be defined ad hoc there, or moved to a more discoverable/shared location, now that it's used more centrally? leave it as is
