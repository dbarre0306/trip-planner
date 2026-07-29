# Plan: Venue Location, Hours, and Duration Extraction

spec: _specs/venue-location-hours-duration.md

## Summary

Add a new extraction step to venue processing that derives `location`, `hours_of_operation`, and `duration_minutes` for each `Venue` from the notes already gathered during venue lookup. A new `venue_details` module will ask the OpenAI model to pull these fields strictly from the notes (never inventing hours, never using the venue's own name as its location, preferring a street address and falling back to a distinct containing place). When no duration can be found in the notes, the same module will ask the model for a best-estimate duration drawn solely from its own general knowledge — no web search is performed — and, if the model has no specific knowledge of the venue, it must still produce its best guess based on venue type/category, so `duration_minutes` is always set and is never `null`. `venue_processing.process_venue` will be updated to call this new extraction and populate the three fields on `Venue`, which today are always `None`.

## Assumptions

- The extraction call returns structured data by having the model respond with JSON and parsing it in Python (mirroring how `venue_description.py` prompts the model, but requesting a JSON object instead of free text). No `response_format`/structured-output API is currently used anywhere in the codebase, so this plan keeps to the existing `chat_completion(messages) -> str` interface and parses its output, rather than introducing a new client capability.
- If the model's JSON response is malformed or missing expected keys, `location` and `hours_of_operation` are treated as `null` rather than raising — this mirrors the "leave as null when not found" behavior the spec specifies for those two fields, and keeps a parsing hiccup on these optional enrichment fields from failing the whole venue (unlike a hard API/network error from `chat_completion`, which is allowed to propagate and fail the venue, consistent with how `generate_description` errors are handled today in `process_venue`). `duration_minutes` is the one field this tolerance does not apply to as a final state — if extraction doesn't yield a usable duration (missing, malformed, or absent from the notes), the code always proceeds to the best-guess fallback so the field is never left `null`.
- Per the user's answers on the spec: a place named after its parent institution (e.g., a museum wing) should resolve to the parent institution's name as `location`; `hours_of_operation` is stored verbatim in whatever format the notes use (no normalization).
- "Best-estimate duration using outside knowledge" is implemented as a single additional prompt to the model asking for its best guess based on general knowledge of the venue type, with an explicit instruction that it must always return a numeric estimate — even a rough, category-based guess (e.g., "typical museum visit") — rather than declining to answer. No web search or other external lookup is performed for duration estimation.

## Files to Change

- `src/trip_planner/venue_details.py` — new module. Contains:
  - A small result type (dataclass, matching the style of `VenueLookupResult` in `serper_lookup.py`) holding `location`, `hours_of_operation`, and `duration_minutes`.
  - `extract_venue_details(name, notes)` — builds a prompt that instructs the model to return JSON with the three fields, following the spec's rules (street address first, else a distinct containing place that is not the venue name, else `null`; parent institution for sub-named places; hours only if explicitly stated; duration only if explicitly stated in the notes, else `null` at this stage), calls `chat_completion`, and parses the JSON response into the result type.
  - `estimate_duration_minutes(name, location)` — the knowledge-only duration fallback: a single prompt asking the model for its best-guess duration based on general knowledge of the venue and its location, instructed to always return a numeric minutes estimate (falling back to a category-level guess if it has no specific knowledge) rather than declining. No search or external lookup involved. This function always returns an `int`, never `None`.
- `src/trip_planner/venue_processing.py` — update `process_venue` to call `extract_venue_details` with the venue's name and `lookup_result.notes`, set `location` and `hours_of_operation` from the result instead of hardcoding `location=None`, and set `duration_minutes` from the result if present, otherwise from `estimate_duration_minutes` — guaranteeing `duration_minutes` is always populated on the returned `Venue`.
- `tests/test_venue_details.py` — new tests for `extract_venue_details` and `estimate_duration_minutes`, mocking `chat_completion`.
- `tests/test_venue_processing.py` — add/update tests asserting `location`, `hours_of_operation`, and `duration_minutes` are populated on the returned `Venue` from `process_venue`, with `venue_details` mocked.

## Implementation Steps

1. Create `venue_details.py` with the result type and `extract_venue_details(name, notes)`, implementing the notes-only extraction rules from the spec (address > distinct place > null; verbatim hours if explicit; verbatim/converted duration if explicit; never the venue's own name as location; parent institution for sub-named places) and tolerant JSON parsing that falls back to `null` fields on malformed output.
2. Add `estimate_duration_minutes(name, location)` to `venue_details.py`: a single knowledge-only best-guess prompt that always returns an integer minutes estimate, instructing the model to fall back to a category-level guess (e.g., based on venue type) when it lacks specific knowledge, rather than declining to estimate.
3. Update `venue_processing.process_venue` to call `extract_venue_details`, populate `location` and `hours_of_operation` directly from it, and populate `duration_minutes` from it or, if not found in the notes, from `estimate_duration_minutes`, so the final value is always set.
4. Write unit tests for `venue_details.py` covering: street-address notes, distinct-place notes (including the parent-institution case), notes with neither (expect `null` location); notes with explicit hours vs. none; notes with explicit duration vs. none (falling to the knowledge-only estimate) vs. no venue-specific knowledge (falling to a category-level best guess) — confirming `estimate_duration_minutes` never returns `null`; and malformed-JSON handling for `location`/`hours_of_operation`.
5. Write/update unit tests for `venue_processing.py` verifying `process_venue` wires the extracted `location`, `hours_of_operation`, and `duration_minutes` onto the returned `Venue`, and that other fields (name, description, geo_location, url, rating, tags, notes) are unaffected.
6. Run `uv run pytest` and confirm the full suite passes.

## Testing

- Location extraction: notes with a clear street address → that address; notes with only a distinct containing place (e.g., Blackett's Ridge / Sabino Canyon Recreation Area) → the place, not the trail name; notes with a parent-institution-named sub-place (e.g., a museum wing) → the parent institution; notes with neither → `null`.
- Hours-of-operation extraction: notes with explicit hours in either of two different stated formats → stored verbatim; notes with no hours mentioned → `null`.
- Duration extraction: notes with an explicit duration/visit length → that value in minutes; notes without one but where the model's own knowledge yields a confident estimate → that estimate; notes without one and no venue-specific knowledge → a category-level best-guess estimate — confirming `duration_minutes` is never `null` in any of these cases.
- A test asserting no network/search calls are made as part of duration estimation — only `chat_completion`.
- A regression test asserting the venue's own name is never returned as `location`.
- A regression test asserting other `Venue` fields are unaffected by this change.
- Full `uv run pytest` run to confirm no existing tests (e.g. `test_venue_processing.py`, `test_venue_description.py`) regress.

## Risks / Open Questions

- The model may not always return well-formed JSON for the extraction call; tolerant parsing mitigates this but could silently drop a field the notes actually contained.
- "Distinct place" vs. "part of the venue's own name" is inherently judgment-based for the model; the parent-institution rule covers the spec's example but edge cases may still be inconsistent.
- Forcing a non-null duration for obscure or newer venues the model has no specific knowledge of means some estimates will be coarse, category-level guesses rather than venue-grounded figures; this is accepted per the spec's instruction that `duration_minutes` must never be `null`.
- No caching of extraction results across runs (explicitly out of scope per the spec), so repeated processing of the same venue re-incurs the LLM cost each time.
