# Plan: Always Get Hours Of Operation From LLM

spec: _specs/hours-of-operation-from-llm.md

## Summary

`extract_venue_details` in `src/trip_planner/venue_details.py` currently short-circuits with an empty `VenueDetails()` whenever `notes` is empty, and even when notes are present, its prompt instructs the LLM to derive `hours_of_operation` "exactly as stated in the notes" only, returning null otherwise. This plan changes the extraction so the LLM is always invoked and always asked to supply `hours_of_operation` from its own general knowledge of the venue when notes don't state it, while `location`, `location_type`, `duration_minutes`, and `closed` continue to be derived strictly from notes as before (and remain null/false by default when notes are empty or silent on them).

## Assumptions

- Per the spec's resolved open questions: the "skip the LLM call when notes is empty" shortcut is removed entirely — the LLM is always queried, even with empty notes — and there is no need to flag/distinguish whether hours came from notes vs. general knowledge.
- `extract_venue_details(name, notes)` keeps its current signature; `notes` is still passed through as supporting context (now possibly empty), matching the spec's requirement that notes remain available to the LLM.
- Only the `hours_of_operation` field's extraction instructions change to permit general knowledge; the `location`, `location_type`, `duration_minutes`, and `closed` instructions keep their existing "use ONLY the notes" constraint, satisfying the acceptance criterion that those fields are unaffected.
- `venue_processing.py` requires no changes — it already just forwards `lookup_result.notes` (which may be `[]`) into `extract_venue_details` and copies through whatever `hours_of_operation` comes back.

## Files to Change

- `src/trip_planner/venue_details.py` — remove the `if not notes: return VenueDetails()` early return in `extract_venue_details`; handle an empty `notes` list when building `notes_text` (e.g. render as "(none)" instead of an empty joined string); split `_EXTRACTION_INSTRUCTIONS` so the blanket "use ONLY the notes" framing no longer applies to `hours_of_operation`, and rewrite the `hours_of_operation` instruction to: prefer hours stated in the notes when present, otherwise fall back to the LLM's own general knowledge of the venue's typical hours, and use null only when hours can't be reasonably determined either way.
- `tests/test_venue_details.py` — update tests tied to the old skip-when-empty behavior and add coverage for the new general-knowledge path (see Testing below).

## Implementation Steps

1. In `venue_details.py`, rewrite `_EXTRACTION_INSTRUCTIONS` (or split it into a shared preamble plus a per-field block) so that `location`, `location_type`, `duration_minutes`, and `closed` keep the existing "ONLY from the notes below, do not invent or infer" constraint, while the `hours_of_operation` line is reworded to allow the model to answer from its own knowledge of the venue when the notes don't state hours, still defaulting to null when it has no reasonable basis for an answer.
2. In `extract_venue_details`, delete the `if not notes: return VenueDetails()` early return so the function always calls `chat_completion`.
3. Update the prompt-building logic so it still produces a sensible prompt when `notes` is `[]` (e.g. `notes_text = "\n".join(...) if notes else "(none provided)"`), since `notes_text` would otherwise be an empty string.
4. Leave `_parse_json_object`, the `_as_optional_*`/`_as_bool` coercion helpers, `_resolve_location`, and the `VenueDetails` dataclass unchanged — only the prompt content and the empty-notes control flow change.
5. Confirm `venue_processing.py` and `venue_meal_tags.py` need no code changes, since they only consume `extract_venue_details`'s return value and already tolerate `hours_of_operation` being populated or null.

## Testing

- `tests/test_venue_details.py::test_extract_venue_details_skips_call_when_no_notes` — replace with a test asserting `chat_completion` **is** called even when `notes` is `[]` (e.g. rename to `test_extract_venue_details_calls_llm_when_no_notes`), mocking a response and checking the result reflects it.
- `tests/test_venue_details.py::test_venue_details_defaults_closed_to_false_when_no_notes` (currently unmocked, relying on the old skip shortcut to avoid a real API call) — add the `@patch("trip_planner.venue_details.chat_completion")` decorator and a mocked JSON response, since the LLM will now actually be invoked for this case.
- Add a new test where `notes` contains no hours-related text but the mocked LLM response supplies a non-null `hours_of_operation` anyway, asserting the value is passed through (covers the "general knowledge" path).
- Keep `test_extract_venue_details_returns_null_hours_when_not_stated` (mocked response returns null hours) to confirm null is still preserved when the LLM has no basis to answer.
- Add/verify a test confirming that when `notes` is empty, `location`, `location_type`, and `duration_minutes` still resolve to null and `closed` to false as long as the mocked response returns null/false for those fields — demonstrating those fields' behavior is unaffected by the notes-empty case now that the call always happens.
- Spot-check (or add) a prompt-content assertion confirming the `hours_of_operation` instruction no longer says hours must come "exactly as stated in the notes" / "if no hours are stated, use null" verbatim, while the location/duration/closed instructions still reference notes-only extraction.
- Run the full suite (`uv run pytest`) to confirm `tests/test_venue_processing.py` and `tests/test_venue_meal_tags.py` pass unchanged, since both mock `extract_venue_details` at the boundary and don't exercise its internals.

## Risks / Open Questions

- Allowing the LLM to answer `hours_of_operation` from general knowledge reintroduces some risk of confidently-wrong or hallucinated hours for obscure/less-known venues; the prompt should be worded to encourage null over a low-confidence guess, but this is a quality tradeoff inherent to the spec's intent and not something tests can fully guard against.
- Removing the empty-notes short-circuit means every venue now incurs at least one LLM call for detail extraction instead of skipping it when notes are empty, slightly increasing API call volume/cost/latency for venues with no search snippets.
