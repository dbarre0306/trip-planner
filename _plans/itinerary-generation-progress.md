# Plan: Itinerary Generation Progress Indicator

spec: _specs/itinerary-generation-progress.md

## Summary

Replace the current single "Researching your destination…" status message shown while `create_itinerary` runs with a 3-stage vertical stepper ("Searching for venues" → "Researching venues and estimating costs" → "Building your itinerary"), each stage marked done/active/pending with a checkmark/spinner/empty marker, centered on the page in a polished card. The three stages map directly onto three real, sequential calls already made in `create_itinerary` (`get_all_candidates` → `process_venues` → `assemble_itinerary`), so stage transitions are driven by real signals from the pipeline rather than guesswork — no heuristic timing is needed now that research and cost estimation are combined into a single stage.

## Assumptions

- The spec's "reasonable approximation of progress (e.g. known pipeline milestones and/or elapsed time)" is satisfied entirely by known pipeline milestones for this 3-stage version: each stage boundary corresponds exactly to one of `create_itinerary`'s three top-level calls returning, so no elapsed-time heuristic is required.
- The brief window between `process_venues` returning and `assemble_itinerary` returning (stage 3, "Building your itinerary") may be very short for small trips; per the spec's testing note, it's acceptable for that stage to be shown only briefly (or be visually "active" for less than one poll tick) before results appear.
- The existing `status_md` component keeps its current role for error/no-results/exception text; it is no longer used for the loading message, since the stepper replaces that role.
- No changes are needed to `venue_processing.py`, `itinerary.py`, `serper_places.py`, or `main.py` — the only pipeline change is an optional callback parameter on `create_itinerary` itself.

## Files to Change

- `src/trip_planner/trip_planner.py` — add an optional `on_stage` callback parameter to `create_itinerary`, invoked at the three real stage boundaries (after `get_all_candidates`, after `process_venues`, after `assemble_itinerary`); keyword-only with a `None` default so `main.py` and existing callers/tests are unaffected.
- `src/trip_planner/assets.py` — add a new CSS block for the vertical stepper card: centered wrapper, step rows connected by a vertical line, and done/active/pending marker states including a CSS-only spinner animation for the active stage, following the existing `trip-summary-*` styling conventions (card background, accent color, spacing).
- `src/trip_planner/app.py` — 
  - Import the new stage constants from `trip_planner.py`.
  - Add a small pure render function that builds the stepper HTML for a given active-stage index (0, 1, or 2).
  - Add a new `progress_html` `gr.HTML` component to the results panel, appended as the last output in both `schedule_itinerary_btn.click(...)` and `confirm_reset_btn.click(...)` output lists so no existing fixed-index output positions shift.
  - In `on_schedule_itinerary`: create a queue to receive stage-boundary events from the background thread running `create_itinerary`, pass a callback into it, and replace the current 30-second dot-cycling poll loop with a short-interval loop that drains the queue and advances/yields the active stage.
  - Update every yield/return site (validation-error, loading-start, exception, no-results, success) and `on_confirm_reset` to include the new trailing `progress_html` value — cleared to empty everywhere except the loading-start yield, which shows stage 0 active immediately; remove the old "Researching your destination…" text.
- `tests/test_trip_planner.py` — add a test asserting `create_itinerary` invokes `on_stage` with the three expected events in order; existing tests continue to call `create_itinerary` without `on_stage` and should remain unaffected.
- `tests/test_app.py` — add unit tests for the new stepper-rendering function at each stage index; extend existing validation-error/exception/no-results/success tests to assert the new trailing output is cleared; add a test asserting the loading-start yield shows stage 0 active; add a reset test asserting the stepper output is cleared.
- `tests/test_assets.py` — optionally extend the CSS-class coverage list with the new stepper class names, mirroring how it already covers `trip-summary-*`.

## Implementation Steps

1. In `trip_planner.py`, define the three stage-boundary event names as module-level constants and add an optional, keyword-only `on_stage` callback parameter to `create_itinerary`. Invoke it once right after `get_all_candidates` returns, once right after `process_venues` returns, and once right after `assemble_itinerary` returns, guarding each call with `if on_stage:`.
2. In `assets.py`, add the vertical-stepper CSS block: a centered flex wrapper, a card matching the existing `trip-summary` card look, step rows with a connecting line between them, and three marker states (done = checkmark, active = spinning border animation, pending = empty outline), plus label emphasis styling for the active row.
3. In `app.py`:
   a. Import the three stage constants from `trip_planner.py` alongside the existing `create_itinerary` import.
   b. Add the ordered list of the three stage labels and a pure function that renders the stepper markup for a given active-stage index, using the new CSS classes.
   c. Add the `progress_html` component in `build_ui`, in the results panel, after `results_html`.
   d. Append `progress_html` as the last item in the `outputs=[...]` list for both `schedule_itinerary_btn.click(...)` and `confirm_reset_btn.click(...)`.
   e. In `on_schedule_itinerary`, before launching the background task, create a queue and a callback that puts `(event, count)` tuples onto it; pass the callback into `create_itinerary` via `asyncio.to_thread`.
   f. Replace the existing 30-second poll/dot-cycle loop with a short-interval loop (e.g. every 0.5s) that drains any queued stage events, advances an `active_index` variable accordingly (0 → 1 on the search-complete event, 1 → 2 on the processing-complete event), and yields the rendered stepper as the new trailing output; the build-complete event needs no visible index beyond 2 since the task finishes shortly after.
   g. Update the loading-start yield to show the stepper at stage 0 and clear the old status message text; update the validation-error, exception, no-results, and success yields, plus `on_confirm_reset`, to clear the stepper output.
4. Add the new `on_stage` ordering test to `tests/test_trip_planner.py`.
5. Add/extend tests in `tests/test_app.py` per the list above.
6. Optionally extend `tests/test_assets.py`'s CSS-class coverage list.
7. Run `uv run pytest` to confirm the full suite passes.
8. Run `uv run app`, submit a trip request, and manually confirm the stepper appears immediately, advances through all three stages in order, and is cleanly replaced by the itinerary/error/no-results outcome; confirm it reads as centered and polished, and that Modify Trip / Plan a New Trip / reset flows are unaffected.

## Testing

- Unit test (`test_trip_planner.py`): `create_itinerary` calls `on_stage` with the three stage events in the correct order and expected payloads, using mocked `search_places`/`process_venues`/`assemble_itinerary` as existing tests already do; confirm calls without `on_stage` still succeed.
- Unit tests (`test_app.py`): the stepper-rendering function produces exactly one active marker, the correct number of done/pending markers, and all three stage labels, for each possible active index.
- Extend existing `test_app.py` tests for the validation-error, exception, no-results, and success paths to also assert the new trailing progress output is cleared (`""`); add a test confirming the loading-start yield shows stage 0 active; add a reset-flow test confirming the stepper output is cleared by `on_confirm_reset`.
- Manual verification via `uv run app`: submit a real trip request and visually confirm the stepper appears immediately, advances through all three stages in order (checkmarks accumulate, spinner moves forward), is centered and styled consistently with the rest of the app, and is replaced correctly by results, an error message, or the no-results message as appropriate.

## Risks / Open Questions

- For small trips where `process_venues` and `assemble_itinerary` both complete quickly, the "Building your itinerary" stage may be visible for less than one poll interval — per the spec, this brief/best-effort display is acceptable, but it means that stage may rarely be seen as "active" versus jumping straight from stage 2 to results.
- The poll interval (proposed ~0.5s) trades responsiveness against overhead; if it proves too chatty or too sluggish in manual testing, it can be tuned without affecting the rest of the design.
