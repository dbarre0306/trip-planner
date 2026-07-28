# Plan: Venue Description Generation

spec: _specs/venue-description-generation.md

## Summary

Add a new `venue_description` module that calls the OpenAI API (via the existing `openai_client.chat_completion` helper) to generate a short, tourist-facing description for a venue. When the venue has notes, the description is generated primarily from those notes, with the venue's name, interest, and destination included as light supporting context. When there are no notes, the description is generated from name, interest, and destination alone. In all cases the prompt instructs the model to omit URLs, websites, addresses/locations, and hours of operation, and to stay within the `Venue.description` 300-character limit; the module also defensively truncates the result as a safety net. `venue_processing.process_venue` is updated to call this module and populate `Venue.description` for every processed venue.

## Assumptions

- "Destination" in the spec maps to `candidate.location` (the same string already passed as `destination` to `lookup_venue` in `serper_lookup.py`), not a new `TravelInfo.destination` parameter threaded through `process_venue`/`process_venues`. This avoids adding new plumbing since `candidate.location` already fills that role in the existing lookup call.
- "If the LLM call fails or errors, venue processing for that venue does not crash the overall batch" is satisfied by letting the exception propagate out of `process_venue`, exactly like a `lookup_venue` failure does today — `process_venues` already catches per-future exceptions via `future.result()` and appends them to `errors` without stopping other venues. No new try/except is added inside `process_venue` itself, keeping this consistent with existing error handling instead of introducing a second failure-handling path.
- Excluding URLs/websites/addresses/hours-of-operation and hitting the engaging tourist tone are treated as prompt-instruction requirements. Since LLM output can't be deterministically asserted in unit tests, tests will verify the *instructions* are present in the prompt sent to `chat_completion`, not the semantic content of a real model response.
- The defensive 300-character truncation trims at a character boundary (no ellipsis or word-boundary logic) since the spec doesn't call for smarter truncation and this is purely a safety net against the model exceeding the limit.

## Files to Change

- `src/trip_planner/venue_description.py` — new module. Exposes a function that takes `name`, `interest`, `destination`, and `notes`, builds the appropriate prompt (notes-primary vs. name/interest/destination-only), calls `openai_client.chat_completion`, and returns a description string truncated to 300 characters.
- `src/trip_planner/venue_processing.py` — `process_venue` calls the new module with `candidate.name`, `candidate.interest`, `candidate.location`, and `lookup_result.notes`, and passes the result as `description=` when constructing the `Venue`.
- `tests/test_venue_description.py` — new test file covering the new module directly.
- `tests/test_venue_processing.py` — update existing tests to mock the new module (or `chat_completion`) and assert `Venue.description` is populated for both the notes and no-notes paths; update the existing assertion that currently expects `venue.description == ""`.

## Implementation Steps

1. Create `src/trip_planner/venue_description.py` with a function (e.g. `generate_description(name, interest, destination, notes) -> str`) that:
   - Builds a notes-primary prompt when `notes` is non-empty: notes content as the main source, with name/interest/destination included as light supporting context (for disambiguation/grounding only).
   - Builds a name/interest/destination-only prompt when `notes` is empty.
   - In both prompt variants, instructs the model to write an engaging, tourist-facing description, and to exclude any URL, website reference, physical location/address, or hours of operation.
   - Calls `openai_client.chat_completion` with the constructed messages and returns the resulting text, stripped of surrounding whitespace and truncated to 300 characters as a safety net against the max-length constraint on `Venue.description`.
2. Update `process_venue` in `src/trip_planner/venue_processing.py` to call `generate_description(candidate.name, candidate.interest, candidate.location, lookup_result.notes)` and pass the result into the `Venue(...)` constructor's `description` argument, replacing the current default empty string.
3. Add `tests/test_venue_description.py` covering:
   - Notes present: mocks `chat_completion`, asserts it's called with a prompt containing the notes content and the name/interest/destination as supporting context, and returns the mocked completion text.
   - Notes empty: asserts the prompt is built from name/interest/destination only (no notes content).
   - Both prompt variants: assert the prompt text includes instructions to avoid URLs/websites/addresses/hours-of-operation and to sound engaging/tourist-facing.
   - Truncation: mock `chat_completion` to return a string longer than 300 characters and assert the returned description is capped at 300 characters.
   - Error propagation: mock `chat_completion` to raise, and assert the exception propagates out of the module (no swallowing).
4. Update `tests/test_venue_processing.py`:
   - Mock the new `venue_description.generate_description` function (patched at `trip_planner.venue_processing.generate_description`) in each existing test that currently asserts `venue.description == ""`, and update the assertion to check the mocked/generated value instead.
   - Add a test asserting `process_venue` calls `generate_description` with `candidate.name`, `candidate.interest`, `candidate.location`, and the notes from the mocked `lookup_venue` result.
   - Add/verify a test where `generate_description` raises, confirming the exception surfaces through `process_venues` into the existing `errors` list (consistent with how `lookup_venue` failures are already handled), rather than crashing the batch.
5. Run `uv run pytest` to confirm the full suite passes.

## Testing

- Unit tests in `tests/test_venue_description.py` per Implementation Step 3, matching the spec's Testing section: notes-driven description, no-notes fallback, exclusion instructions present in the prompt, 300-character truncation, and error propagation.
- Updated/added unit tests in `tests/test_venue_processing.py` confirming `Venue.description` is populated via the new module for both the notes and no-notes paths, and that a description-generation failure is collected as an error by `process_venues` without aborting other venues (mirrors the existing `test_process_venues_collects_errors_without_aborting_others` pattern).
- Full test suite run (`uv run pytest`) to catch regressions in existing venue-processing tests caused by the new required call.

## Risks / Open Questions

- The 300-character truncation is a plain character-boundary cut; if the model's output exceeds the limit, the resulting description could end mid-word. Acceptable per spec (no smarter truncation requested), but worth flagging.
- Because notes-path failures now propagate as venue-level errors (per the Assumptions decision), a flaky LLM call could cause venues that previously succeeded (with an empty description) to now show up in `errors` instead. This matches the spec's stated behavior but is a visible change in which venues make it into the final itinerary.
- Prompt wording for "engaging, tourist-facing tone" and the exclusion instructions is a judgment call during implementation; the spec does not prescribe exact phrasing.
