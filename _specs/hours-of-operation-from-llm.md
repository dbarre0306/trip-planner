# Always Get Hours Of Operation From LLM

branch: claude/feature/hours-of-operation-from-llm

## Summary

Venue hours of operation are currently extracted only from the free-text `notes` snippets returned by the Serper lookup, with the LLM explicitly instructed to use the hours "exactly as stated in the notes" and to return null if no hours are stated there. Because `notes` is just a handful of Google search snippets, hours are frequently missing or incomplete even when the venue's actual hours are well known. This feature changes the behavior so hours of operation are always sourced from the LLM's own knowledge of the venue, rather than being restricted to whatever text happens to appear in `notes`.

## User Story

As a trip planner user, I want the itinerary to include a venue's hours of operation whenever the LLM can reasonably determine them, so that I'm not left with missing hours just because the search snippets didn't happen to mention them.

## Acceptance Criteria

- [ ] The LLM is always asked to provide the venue's hours of operation, regardless of whether `notes` contains hours-related text.
- [ ] `notes` continues to be provided to the LLM as supporting context, but is no longer the sole permitted source of hours of operation.
- [ ] If the LLM does not have enough information to determine hours of operation (from notes, general knowledge, or otherwise), `hours_of_operation` is still null rather than an invented/fabricated value.
- [ ] Other fields currently extracted alongside hours of operation (`location`, `location_type`, `duration_minutes`, `closed`) are unaffected by this change.
- [ ] Behavior is consistent for venues with empty `notes` and venues with non-empty `notes`.

## Scope

### In Scope

- Updating the extraction instructions/prompt used to determine `hours_of_operation` so the LLM is not restricted to only what's stated in `notes`.
- Ensuring the "skip the LLM call when notes is empty" shortcut no longer applies to hours of operation, since hours may now be derivable without notes.
- Updating existing tests that assert notes-only hours extraction behavior.

### Out of Scope

- Fetching real-time, seasonal, or live hours from an external hours/places API.
- Validating or normalizing the format of the hours string returned by the LLM.
- Changes to how `hours_of_operation` is consumed downstream (e.g., meal-tag determination, itinerary rendering).
- Changes to the venue status/rejection-reason logic beyond any effect naturally caused by hours now being populated more often.

## UI / UX Notes

No user-facing UI changes. This is an internal data-enrichment change: itineraries may now show hours of operation for more venues than before, and previously-null hours fields may now be populated.

## Testing

- Update/extend the hours-of-operation test cases in `tests/test_venue_details.py` to cover: notes containing explicit hours (still extracted), notes containing no hours-related text but the LLM can still supply hours from general knowledge, and cases where the LLM genuinely cannot determine hours (remains null).
- Confirm the "skip LLM call when notes is empty" test case is updated to reflect that an LLM call may now still be needed to determine hours even with empty notes (or that the skip logic is scoped appropriately if other fields still allow skipping).
- Confirm existing tests in `tests/test_venue_processing.py` and `tests/test_venue_meal_tags.py` that depend on `hours_of_operation` still pass with the updated extraction behavior.

## Open Questions

- Should the LLM call still be skipped entirely when `notes` is empty (current shortcut), or should it always run so hours can be derived from the LLM's general knowledge even without notes? query the LLM; don't skip it
- When the LLM supplies hours from general knowledge rather than from `notes`, should there be any way to distinguish/flag that source for downstream consumers or debugging? no
