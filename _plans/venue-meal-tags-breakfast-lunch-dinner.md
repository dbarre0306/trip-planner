# Plan: Venue Meal Tags (Breakfast, Lunch, Dinner)

spec: _specs/venue-meal-tags-breakfast-lunch-dinner.md

## Summary

Add meal-period tagging (`breakfast`, `lunch`, `dinner`) for venues whose `interest` is `restaurants`, `coffee shops`, or `street food and markets`, appended to the existing `tags` list on `Venue`. A new module, `venue_meal_tags.py`, owns the decision: `coffee shops` venues get a fixed `["breakfast"]` with no model call, while `restaurants` and `street food and markets` venues are resolved with a single `chat_completion` call that gives the model the venue's notes, its `hours_of_operation` (already extracted by `extract_venue_details`), and the meal-period boundary rules from the spec, asking it to combine both signals and fall back to its own best guess when neither says anything — mirroring how `closed` detection and duplicate resolution already delegate this kind of fuzzy judgment to the LLM rather than hand-rolling text/time parsing. `street food and markets` is additionally constrained, in both the prompt and a code-level safety net, to never receive `breakfast`. The new step slots into `process_venue` right after `extract_venue_details` runs, since it needs both the notes and the extracted hours.

## Assumptions

- Per the spec's resolved open questions: meal tags are appended to the existing `tags` field (not a new dedicated field) — the `[candidate.tag] if candidate.tag else []` list already assigned in `process_venue` becomes the base, with meal tags appended after it. Order is `[category tag if any] + [meal tags]`.
- Eligibility is decided by comparing `candidate.interest` (case-insensitive, trimmed) against the three interest query strings already used elsewhere in the codebase (`domain.py`'s `INTERESTS`): `"restaurants"`, `"coffee shops"`, `"street food and markets"`. Any other interest (including `None`) is ineligible and gets no meal tags — the `tags` list is unaffected.
- The meal-period boundary rules from the spec's resolved open question (breakfast starts 6–9am, lunch starts 10am, dinner starts 4pm) are embedded as prompt guidance for the LLM rather than implemented as bespoke time-string parsing, consistent with the spec's answer that hours are free-text and "best-effort is good enough," and with how this codebase already delegates similarly fuzzy judgment calls (`closed` detection, duplicate/specificity resolution) to `chat_completion` instead of hand-rolled parsing.
- `coffee shops` never calls the model — the spec's rule ("always tagged breakfast only, regardless of notes or hours") is absolute, so it's applied as a plain code branch, saving an LLM call for that interest.
- For `restaurants` and `street food and markets`, notes, hours-of-operation combination, and best-guess fallback are all handled by one `chat_completion` call (one prompt covers "use notes/hours if they say something, otherwise use your best judgment"), rather than three separate code paths — the same pattern `venue_details.py` already uses where one call produces a field with a built-in fallback described entirely in the prompt.
- If the model's response can't be parsed into at least one valid tag (malformed JSON, empty list, or — for `street food and markets` — a response containing only `breakfast`), the code falls back to a fixed default of `["lunch", "dinner"]` so the spec's "every eligible venue gets at least one tag" guarantee holds even when the LLM call fails or returns something unusable. This default isn't specified in the spec and is called out below as a risk.
- `determine_meal_tags` takes `hours_of_operation` as a parameter (rather than re-deriving it) so it can be called with the `VenueDetails.hours_of_operation` already produced by `extract_venue_details`, avoiding a second, redundant extraction of the same information.

## Files to Change

- `src/trip_planner/venue_meal_tags.py` — new module. Exposes `MEAL_TAGS = ("breakfast", "lunch", "dinner")` (or similar) and `determine_meal_tags(interest: str | None, notes: list[str], hours_of_operation: str | None) -> list[str]`:
  - Normalizes `interest` (`strip().casefold()`) and checks membership against `{"restaurants", "coffee shops", "street food and markets"}`; returns `[]` immediately if not a match.
  - If the normalized interest is `"coffee shops"`, returns `["breakfast"]` with no model call.
  - Otherwise, builds a prompt containing the venue's notes (bullet-joined, same style as `_EXTRACTION_INSTRUCTIONS`) and `hours_of_operation` (if present), plus instructions covering: use explicitly stated meal period(s) from the notes; also weigh `hours_of_operation` using the boundary rules (breakfast ~6–9am start, lunch starts 10am, dinner starts 4pm) to determine which period(s) the hours span; combine both signals (a period is included if either signal supports it); if neither notes nor hours indicate anything, use general knowledge of the venue to make a best guess; respond with only a JSON object/array naming the applicable period(s) from `breakfast`, `lunch`, `dinner`. When the normalized interest is `"street food and markets"`, the prompt also states that `breakfast` must never be used for this venue type.
  - Calls `chat_completion`, parses the response defensively (reusing a `_parse_json_object`-style helper), filters to the three valid tag strings, dedupes, and — for `"street food and markets"` — strips `breakfast` from the result even if the model included it (safety net backing the prompt instruction).
  - If, after filtering/stripping, the result is empty, falls back to `["lunch", "dinner"]` so a non-empty, spec-compliant result is always returned for eligible interests.
- `src/trip_planner/venue_processing.py` — in `process_venue`, after `details = extract_venue_details(...)`, call `meal_tags = determine_meal_tags(candidate.interest, lookup_result.notes, details.hours_of_operation)` and change the `tags=` argument in the `Venue(...)` construction to `tags=([candidate.tag] if candidate.tag else []) + meal_tags`.
- `tests/test_venue_meal_tags.py` — new test file covering the scenarios in the spec's Testing section (see below), mocking `chat_completion` at `trip_planner.venue_meal_tags.chat_completion`, matching the mocking style already used in `test_venue_details.py`.
- `tests/test_venue_processing.py` — extend `test_process_venue_maps_fields_and_defaults` and `test_process_venue_leaves_tags_empty_when_candidate_has_no_tag` (or add new tests) to mock `determine_meal_tags` and assert: (a) it's called with `candidate.interest`, `lookup_result.notes`, and `details.hours_of_operation`; (b) its return value is appended after any existing `candidate.tag`-derived entry in `venue.tags`; (c) for an ineligible interest (e.g. `"hiking"`, the interest already used throughout this test file), a mocked empty return leaves `tags` matching today's behavior.

## Implementation Steps

1. Create `venue_meal_tags.py` with the eligible-interest set, the fixed `coffee shops` branch, the prompt-building logic (notes + hours + boundary-rule guidance + the `street food and markets` breakfast exclusion), the `chat_completion` call, and defensive response parsing/filtering/fallback as described above.
2. Wire `determine_meal_tags` into `process_venue` in `venue_processing.py`, calling it after `extract_venue_details` and merging its result into the `tags` list passed to `Venue(...)`.
3. Add `tests/test_venue_meal_tags.py` covering every scenario in the spec's Testing section.
4. Update `tests/test_venue_processing.py` to cover the new wiring (call arguments and tag merging) per the Files to Change notes above.
5. Run `uv run pytest` and fix any regressions.

## Testing

Matches the spec's Testing section directly, in `tests/test_venue_meal_tags.py` unless noted:

- Notes state a single meal period (e.g. "dinner only") for a `restaurants`-interest venue — result is `["dinner"]`.
- Notes state multiple meal periods (e.g. "serves breakfast and lunch") — result contains all stated periods.
- Hours span a single meal period (e.g. "6am-11am", notes silent) — result is just that period.
- Hours span multiple meal periods (e.g. "11am-11pm", notes silent) — result contains `lunch` and `dinner`.
- Notes and hours agree — result matches both.
- Notes and hours disagree/cover different periods (e.g. notes say "popular breakfast spot" but hours are "11am-11pm") — result is the union of what either signal supports.
- Notes and hours both absent/uninformative — result is a non-empty best guess (mock the model response to simulate a guess and assert the result is non-empty and drawn from the three valid tags).
- No notes and no hours at all (empty notes list, `hours_of_operation=None`) — still returns at least one valid tag.
- `interest="coffee shops"` — returns `["breakfast"]` without calling `chat_completion` (assert not called), regardless of notes/hours passed in.
- `interest="street food and markets"` with notes/hours suggesting breakfast — result never contains `"breakfast"`, only `lunch`/`dinner`.
- `interest` outside the three eligible values (e.g. `"hiking"`, `None`) — returns `[]` without calling `chat_completion`.
- Malformed/unparseable model response for an eligible non-coffee-shop interest — falls back to a non-empty result (`["lunch", "dinner"]` per the Assumptions above) rather than an empty list.
- In `tests/test_venue_processing.py`: `determine_meal_tags` is called with the candidate's interest, the looked-up notes, and the extracted `hours_of_operation`; its return value is appended to `venue.tags` after any existing category tag; an ineligible-interest venue's `tags` is unaffected beyond the existing category-tag behavior.

Run `uv run pytest` to confirm the full suite passes after these changes.

## Risks / Open Questions

- The spec doesn't define what should happen when the LLM call for an eligible `restaurants`/`street food and markets` venue fails or returns something entirely unusable (it only specifies the "no signal at all → best guess" case, which is itself an LLM call). This plan assumes a fixed `["lunch", "dinner"]` fallback in that situation so the "always at least one tag" acceptance criterion holds; this default is a judgment call, not something the spec states explicitly, and may be worth confirming.
- Matching `interest` against the three eligible strings assumes callers pass the same query strings defined in `domain.INTERESTS` (e.g. `"restaurants"`, `"coffee shops"`, `"street food and markets"`). `TravelInfo.interests` is a plain `list[str]` with no validation against that list, so a differently-worded interest (e.g. a synonym not matching these exact strings) would silently be treated as ineligible. This mirrors how `interest` is already used elsewhere in the codebase (passed through as free text with no validation), so no new validation is introduced here.
- The boundary-rule guidance (breakfast 6–9am start, lunch 10am, dinner 4pm) is given to the model as prompt text rather than enforced in code, so — as with the existing `closed`/duplicate-resolution LLM calls — correctness depends on the model following the instructions rather than a deterministic guarantee.
