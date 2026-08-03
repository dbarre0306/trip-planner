# Plan: Modify Trip

spec: _specs/modify-trip.md

## Summary

Add a "Modify Trip" button to the results page, positioned directly above the existing "Plan a New Trip" button, that lets the user return to the form with the current trip's fields already filled in. The confirmation interaction mirrors "Plan a New Trip" exactly (inline Yes/Cancel prompt driven by the same HTML/JS/hidden-trigger pattern), but the underlying Python handler differs: instead of resetting every field, it only flips the form/results panel visibility back, leaving the form's field values untouched. This works because the form components (destination, start date, days, adults, children, and the five interest `CheckboxGroup`s) are never cleared on a successful submission today — they sit hidden but populated behind the results panel — so simply re-showing them already satisfies the "pre-filled with the trip that produced the currently displayed itinerary" requirement.

## Assumptions

- The existing form components already retain their submitted values on the results page (they are hidden via `visible=False`, never cleared, after a successful `on_schedule_itinerary` run). Confirmed by reading `app.py`: only `on_confirm_reset` blanks them; the success/error paths of `on_schedule_itinerary` leave them alone. So "pre-filling" needs no new state plumbing beyond not clearing them.
- The pre-existing hardcoded `interests = [InterestId.RESTAURANTS, InterestId.HIKING]` override in `on_schedule_itinerary` (`app.py:222`), which ignores the user's selected interest checkboxes when building `TravelInfo`, is a separate, pre-existing issue unrelated to this feature. It doesn't affect what the interest `CheckboxGroup`s display or pre-fill — only which interests are actually searched — so it's left untouched.
- "Modify Trip" directly above "Plan a New Trip" is implemented as DOM order within the existing `.trip-plan-ctrl` flex column (`flex-direction: column`), where the first child renders on top.
- Disabling "Modify Trip" during generation and enabling it once generation finishes (success or error) is achieved by driving it off the same `button_enabled` flag `_trip_summary_html` already receives, since that flag is already `True` in both the error-handling and success-handling branches of `on_schedule_itinerary` — no new state is needed to satisfy the "available in error state" criterion.
- Giving the "Plan a New Trip" button and its confirm box their own scoped wrapper class (so JS can tell the two buttons' confirm boxes apart) is a non-behavioral, implementation-only rename. The spec's "no changes to Plan a New Trip" constraint is about its visible behavior/appearance, which is unaffected.
- `on_confirm_modify` will be a nested closure inside `build_ui()`, matching how `on_confirm_reset` is currently implemented (not unit-testable in isolation) — verification for it relies on the manual run-through in Testing below, consistent with the existing test suite's coverage boundary.

## Files to Change

- `src/trip_planner/app.py` — `_trip_summary_html()`: add the "Modify Trip" button + inline confirm box, positioned above the existing "Plan a New Trip" control, sharing the same `button_enabled` state; restructure the existing button/box markup into distinctly named wrapper containers so JS can target each pair independently. `build_ui()`: add a hidden `confirm_modify_btn` trigger button and an `on_confirm_modify()` handler wired to it that shows `form_panel` / hides `results_panel` without touching field values.
- `src/trip_planner/assets.py` — `CSS`: add styling for the new button and its wrapper (visually distinct from "Plan a New Trip", e.g. a different accent color), reusing the existing `.trip-confirm-box` / `.trip-confirm-btns` / `.trip-confirm-yes` / `.trip-confirm-no` classes for the confirm prompt. `HEAD`: add `showModifyConfirm()`, `hideModifyConfirm()`, `triggerConfirmModify()` JS functions mirroring the existing reset trio, scoped to the new wrapper class and targeting the new hidden trigger's `elem_id`.
- `tests/test_app.py` — extend `_trip_summary_html` tests to cover the new button's markup and disabled/enabled state; extend `on_schedule_itinerary` tests if the output tuple shape changes.
- `tests/test_assets.py` — extend `test_head_defines_functions_wired_to_app_onclick_handlers`, `test_head_targets_elem_ids_used_by_app`, and `test_css_defines_classes_referenced_by_app_html` to include the new JS function names, the new hidden-trigger `elem_id`, and the new CSS classes, matching that file's existing wiring-safety pattern.

## Implementation Steps

1. In `_trip_summary_html()` (`app.py`), restructure the existing "Plan a New Trip" button and its confirm box into their own named wrapper (e.g. a `trip-reset-ctrl` div) nested inside `.trip-plan-ctrl`, with no visual or behavioral change — this only disambiguates it from the new button for JS targeting.
2. Add a second wrapper (e.g. `trip-modify-ctrl`) above it inside `.trip-plan-ctrl`, containing a "Modify Trip" button and its own inline confirm box (message + "Yes, modify trip" / "Cancel" actions), following the exact same markup shape as the reset control. Drive its disabled/enabled state off the same `button_enabled` parameter so it always matches "Plan a New Trip"'s state, including in the error/no-itinerary branches of `on_schedule_itinerary` (both already render with `button_enabled=True`).
3. In `assets.py` CSS, add rules for the new button and wrapper (distinct color/accent from the green "Plan a New Trip" button so the two are visually distinguishable), and update any selectors that assumed a single `.trip-confirm-box` per `.trip-plan-ctrl` no longer apply globally.
4. In `assets.py` HEAD, add `showModifyConfirm()` / `hideModifyConfirm()` / `triggerConfirmModify()`, scoped to `.trip-modify-ctrl` (mirroring `showTripConfirm()` / `hideTripConfirm()` / `triggerConfirmReset()`, which get re-scoped to `.trip-reset-ctrl`). `triggerConfirmModify()` clicks a new hidden button located via `getElementById('confirm-modify-trigger')`.
5. In `build_ui()` (`app.py`), add `confirm_modify_btn = gr.Button("", elem_id="confirm-modify-trigger", elem_classes=["hidden-trigger"])` inside `results_panel`, alongside `confirm_reset_btn`.
6. Add an `on_confirm_modify()` handler in `build_ui()` that returns `[gr.update(visible=True), gr.update(visible=False)]` for `form_panel` and `results_panel` only — it must not touch `destination`, `start_date`, `num_days`, `num_adults`, `num_children`, or the interest `CheckboxGroup`s, so their current values carry over as the pre-fill. Wire it with `confirm_modify_btn.click(fn=on_confirm_modify, outputs=[form_panel, results_panel])`.
7. Update `tests/test_app.py`: add cases asserting `_trip_summary_html()` includes the "Modify Trip" button, that it's `disabled` by default and not disabled when `button_enabled=True` (mirroring the existing "Plan a New Trip" button tests), and that it appears before "Plan a New Trip" in the rendered HTML (DOM order).
8. Update `tests/test_assets.py`: add the three new JS function names to `test_head_defines_functions_wired_to_app_onclick_handlers`, add `getElementById('confirm-modify-trigger')` to `test_head_targets_elem_ids_used_by_app`, and add the new CSS class names to `test_css_defines_classes_referenced_by_app_html`.
9. Run `uv run app`, generate a trip through to a successful itinerary, and manually walk through the Testing scenarios below, then repeat against a forced error state (e.g. temporarily raising in `create_itinerary` or entering conditions that trigger the "no itinerary could be generated" branch) to confirm "Modify Trip" behaves identically there.

## Testing

- `uv run pytest tests/test_app.py tests/test_assets.py` after the above changes.
- Manual run (`uv run app`), per the spec's Testing section:
  - Generate a trip to a successful itinerary; confirm "Modify Trip" is disabled while "Researching…" is shown and becomes enabled once the itinerary renders.
  - Click "Modify Trip", confirm the inline prompt appears (not an immediate navigation), and click "Cancel" — verify the results page and itinerary are unchanged.
  - Click "Modify Trip" again and confirm — verify the form page appears with destination, start date, days, adults, children, and interests all matching what was submitted.
  - Edit one field (e.g. change days) and resubmit — verify a new itinerary reflects the change.
  - Resubmit the pre-filled form unedited — verify it reproduces an itinerary for the same parameters.
  - Trigger a results-page error state (e.g. an exception from `create_itinerary`, or a destination that yields no venues) and confirm "Modify Trip" is present, enabled, and functions the same as in the success case.
  - Confirm "Plan a New Trip" still fully resets the form as before, unaffected by the new button.
  - Resubmit with an invalid field (e.g. cleared destination) from the pre-filled form and confirm the standard validation messaging still appears.

## Risks / Open Questions

- None outstanding — the spec's Open Questions were resolved before planning (interests restore exactly as originally selected; "Modify Trip" is available in the error state too).
