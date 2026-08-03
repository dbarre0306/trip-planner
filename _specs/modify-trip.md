# Modify Trip

branch: feature/modify-trip

## Summary

Users who have already generated an itinerary can currently only start over completely via "Plan a New Trip," which clears every field. This feature adds a "Modify Trip" option that lets a user return to the trip form with their current trip's details already filled in, so they can tweak one or two things (e.g. add a day, change interests) without re-entering everything from scratch.

## Acceptance Criteria

- [ ] On the results page, a "Modify Trip" button appears directly above the existing "Plan a New Trip" button.
- [ ] The "Modify Trip" button is disabled while the itinerary is still being generated, and becomes enabled once generation has finished, whether it produced a successful itinerary or an error state.
- [ ] Clicking "Modify Trip" shows a confirmation prompt before taking any action, using the same confirmation interaction style as "Plan a New Trip" (an inline Yes/Cancel prompt, not an immediate navigation).
- [ ] Cancelling the confirmation leaves the user on the results page with the current itinerary unchanged.
- [ ] Confirming the prompt navigates the user to the form page.
- [ ] When the form page loads as a result of "Modify Trip," all fields are pre-filled with the values from the trip that produced the currently displayed itinerary: destination, start date, number of days, number of adults, number of children, and the previously selected interests, restored exactly as the user originally selected them.
- [ ] From the pre-filled form, the user can edit any field and resubmit to generate a new itinerary, following the same submission and validation flow as creating a trip normally.
- [ ] "Modify Trip" remains available even when the results page is showing an error state rather than a successful itinerary.
- [ ] "Plan a New Trip" continues to behave exactly as it does today (full reset to blank/default values) and is unaffected by this change.

## Scope

### In Scope

- A new "Modify Trip" button on the results page, positioned above "Plan a New Trip."
- A confirmation step before leaving the results page, consistent with the existing "Plan a New Trip" confirmation experience.
- Pre-filling the form page with the destination, dates, party size, and interests from the currently displayed trip when the user confirms "Modify Trip."
- Reusing the existing form validation and submission flow once the user is back on the pre-filled form.

### Out of Scope

- Editing the trip directly on the results page (all edits happen back on the form page).
- Preserving or merging any part of the previously generated itinerary results into the newly submitted trip — modifying and resubmitting produces a fresh itinerary.
- Changes to the "Plan a New Trip" button or its behavior.
- Any multi-trip history, saved trips, or the ability to modify a trip other than the one currently displayed.

## UI / UX Notes

- "Modify Trip" is placed immediately above "Plan a New Trip" in the same button group on the results page summary card, so the two actions are visually grouped but distinct.
- "Modify Trip" stays disabled during the itinerary generation ("Researching…") phase, matching the existing disabled treatment of "Plan a New Trip" during that same phase, and becomes clickable only once the itinerary has finished rendering.
- Clicking "Modify Trip" reveals an inline confirmation with a short explanatory message and two actions: a confirming action (e.g. "Yes, modify trip") and a "Cancel" action, mirroring the look and placement of the existing "Plan a New Trip" confirmation.
- Cancelling dismisses the confirmation and returns the button to its normal state, with no other change.
- Confirming takes the user straight to the form page with all fields already populated; no intermediate loading state is required for this navigation.
- Any field validation errors on resubmission are shown using the same inline validation messaging already used on the form page.
- "Modify Trip" is shown alongside "Plan a New Trip" even when the results page is displaying an error state, not only when an itinerary has successfully rendered.

## Testing

- Confirming "Modify Trip" navigates to the form page with destination, start date, number of days, number of adults, number of children, and interests all matching the trip that was displayed on the results page.
- Cancelling the "Modify Trip" confirmation keeps the user on the results page with the itinerary still displayed and unchanged.
- Editing a pre-filled field and resubmitting successfully produces a new itinerary reflecting the edited values.
- Submitting the pre-filled form without changes reproduces an itinerary for the same trip parameters.
- Existing "Plan a New Trip" behavior (full reset) is unaffected by the presence of the new button.
- Standard form validation rules (required destination, valid future date, days/adult/children ranges, interest count) still apply when resubmitting from "Modify Trip."
- "Modify Trip" is available and functions correctly when the results page is in an error state (not just when an itinerary has successfully rendered).

## Open Questions

None.
