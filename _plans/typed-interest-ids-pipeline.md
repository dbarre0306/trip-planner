# Plan: Typed Interest IDs Throughout Venue Pipeline

spec: _specs/typed-interest-ids-pipeline.md

## Summary

Extend the existing `InterestId` enum (currently only used at the interest-selection boundary in `main.py`) so it becomes the representation of interest identity throughout the entire venue pipeline: trip info, venue candidates, generated venues, place search, venue description generation, and meal-tag determination. Raw interest text will only be produced at the two places that genuinely need text — building the external place-search query, and building LLM-facing prompt text — by resolving the typed identifier through the canonical interest list at that exact point. All identity comparisons and branching elsewhere switch from string literals to `InterestId` members, removing the duplicated, manually-synced string constants currently hardcoded in the meal-tag logic. Any variable, parameter, or field that now stores an `InterestId` (rather than a raw string) is named `interest_id` (or `interest_ids` for the list on `TravelInfo`), reserving `interest` for places that still hold resolved text.

## Assumptions

- Per the spec's resolved open question, the hardcoded interest selection list in `main.py`'s entry point stays defined inline there — it is not moved to `domain.py` or elsewhere as part of this plan.
- The spec lists a query-string-to-`InterestId` lookup helper as in scope "if needed to preserve any existing string-based entry point." Tracing the full data flow shows no call site ever needs to convert a raw string back into an `InterestId` — strings are only ever produced from `InterestId` (via `find_interest_by_id`), never consumed as input. This plan therefore omits `find_interest_by_query` as unneeded speculative code; it can be added later if a real call site emerges.
- "Generated venues" in the spec refers to the `Venue` model produced after processing a `VenueCandidate`; both are updated together since they share the same interest field semantics.
- Renaming `interest` to `interest_id` wherever the value is now an `InterestId` applies to fields, parameters, and local variables across all touched files, not just the model definitions — including `search_places`, `venue_meal_tags.py`'s functions, and any local variable holding the candidate's/venue's identifier.

## Files to Change

- `src/trip_planner/domain.py` — rename `TravelInfo.interests` to `TravelInfo.interest_ids` and change its type from `list[str]` to `list[InterestId]`; rename the `Interest.query` field to `Interest.search_text` (and update the `INTERESTS` list construction accordingly). (No new lookup helper is added — see Assumptions.)
- `src/trip_planner/models.py` — rename `VenueCandidate.interest` to `VenueCandidate.interest_id` and `Venue.interest` to `Venue.interest_id`, changing both from `str | None` to `InterestId | None`.
- `src/trip_planner/serper_places.py` — change `search_places`'s parameter from `interest: str` to `interest_id: InterestId`; resolve it to raw search text via `find_interest_by_id().search_text` only when building the Serper search request text; store the `InterestId` as `interest_id` (not the resolved string) on each returned `VenueCandidate`.
- `src/trip_planner/trip_planner.py` — update to iterate `travel_info.interest_ids` (renamed from `.interests`) as `InterestId` values and pass each as `interest_id` through to `search_places` unchanged; no branching/comparison logic changes expected here.
- `src/trip_planner/venue_processing.py` — update so `candidate.interest_id` (renamed from `.interest`) is treated as `InterestId | None` as it flows into `generate_description()` and `determine_meal_tags()`; no branching logic changes expected here.
- `src/trip_planner/venue_description.py` — rename the `interest` parameter to `interest_id`; where it's currently embedded as free text in the LLM prompt, resolve the `InterestId` to its `.search_text` (via `find_interest_by_id`) at the point the prompt text is built, instead of interpolating a raw string.
- `src/trip_planner/venue_meal_tags.py` — replace `_ELIGIBLE_INTERESTS` (currently a set of raw strings) with a set of `InterestId` members; replace the `== "coffee shops"` and `== "street food and markets"` comparisons with `== InterestId.COFFEE_SHOPS` / `== InterestId.STREET_FOOD`; rename the `interest` parameter to `interest_id` in `determine_meal_tags`, `_build_prompt`, and `_extract_tags`, typed as `InterestId | None` / `InterestId`; remove the now-unnecessary `.strip().casefold()` string normalization.
- `src/trip_planner/main.py` — remove the `_to_queries()` helper; pass the `list[InterestId]` selection directly into `TravelInfo(interest_ids=...)`.
- `tests/test_serper_places.py`, `tests/test_venue_processing.py`, `tests/test_venue_meal_tags.py`, and any other test files constructing `VenueCandidate(..., interest="...")` or `Venue(..., interest="...")` with raw string literals — update fixtures and assertions to use `interest_id=InterestId.<MEMBER>` instead.

## Implementation Steps

1. In `domain.py`, rename `TravelInfo.interests` to `TravelInfo.interest_ids`, changing its type to `list[InterestId]`; rename the `Interest.query` field to `Interest.search_text` and update the `INTERESTS` list construction.
2. In `models.py`, rename and retype `VenueCandidate.interest` to `VenueCandidate.interest_id: InterestId | None`, and `Venue.interest` to `Venue.interest_id: InterestId | None`.
3. In `serper_places.py`, rename `search_places`'s `interest` parameter to `interest_id`, resolving to `.search_text` only for the Serper request string, and store it as `interest_id` on the returned `VenueCandidate`.
4. In `trip_planner.py`, adjust usage so `InterestId` values flow from `travel_info.interest_ids` into `search_places`'s `interest_id` parameter without conversion.
5. In `venue_description.py`, rename the `interest` parameter to `interest_id` and resolve it to `.search_text` when constructing LLM prompt text.
6. In `venue_meal_tags.py`, replace all raw-string comparisons and the `_ELIGIBLE_INTERESTS` set with `InterestId`-based equivalents, and rename the `interest` parameter to `interest_id` in every function signature.
7. In `venue_processing.py`, update references from `candidate.interest` to `candidate.interest_id`, passed through as `InterestId | None` with no behavioral change.
8. In `main.py`, remove `_to_queries()` and pass the existing hardcoded `list[InterestId]` selection directly into `TravelInfo(interest_ids=...)`.
9. Update all affected tests to construct and assert against `interest_id=InterestId.<MEMBER>` instead of raw interest strings.
10. Run the full automated test suite and fix any remaining type/assertion mismatches.
11. Do a manual end-to-end run of the trip planner with the existing hardcoded interest selection(s) to confirm itinerary generation, place search, and venue descriptions still work correctly.
12. Manually verify meal-tag outcomes for each eligible interest (restaurants, coffee shops, street food and markets) are unchanged: coffee shops always yield `["breakfast"]`, street food/market venues never receive a `"breakfast"` tag.

## Testing

- Run `uv run pytest` and confirm the full suite passes with fixtures/assertions updated to use `interest_id=InterestId.<MEMBER>` instead of raw strings.
- Manually run `uv run trip_planner` (via `main.py`'s existing hardcoded interest selection) and confirm an itinerary is generated successfully, with correct Serper search results and venue description text.
- Manually exercise `determine_meal_tags` behavior (directly or via the manual run) for each eligible interest category to confirm meal-tag outcomes match pre-refactor behavior: coffee shops → `["breakfast"]` only; street food/markets → never includes `"breakfast"`; ineligible interests → empty list.

## Risks / Open Questions

- Renaming `interest` to `interest_id` across `VenueCandidate`, `Venue`, and several function signatures touches several files at once; a missed call site or keyword argument still using the old `interest=` name will fail at construction time (dataclass/keyword mismatch) or type-check time rather than silently, but should be swept for during implementation and the test run.
- Renaming `Interest.query` to `Interest.search_text` requires updating every reader of that field (`serper_places.py`, `venue_description.py`, and the `INTERESTS` list construction in `domain.py`); a missed `.query` reference will fail at attribute-access time and should surface immediately via the test suite or a type checker run.
