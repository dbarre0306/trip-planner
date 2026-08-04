# Itinerary Generation Progress Indicator

branch: feature/itinerary-generation-progress

## Summary

Today, while an itinerary is being generated, the user only sees a single generic message ("Researching your destination…") with no indication of what stage the process is in or how much work remains. This feature replaces that generic message with a clear, staged progress indicator so the user always knows what the system is currently doing while their itinerary is built. The indicator should present as a polished, professional, centered element on the page rather than a plain line of text.

## Acceptance Criteria

- [ ] While an itinerary is being generated, the user sees a progress indicator reflecting the current stage of the process.
- [ ] The progress indicator communicates, in order, these three stages: (1) searching for venues/activities, (2) researching each venue and estimating its cost, and (3) building the itinerary.
- [ ] The indicator is a vertical stepper: each stage is shown as a row with a marker that reflects its state — a checkmark for a completed stage, a spinner for the currently active stage, and a neutral/empty marker for a stage not yet reached.
- [ ] The indicator visibly advances from one stage to the next as generation moves through the pipeline, rather than remaining static.
- [ ] The indicator is shown as soon as itinerary generation begins and is removed once the itinerary results (or an error/no-results message) are displayed.
- [ ] If generation fails or produces no results, the progress indicator is replaced by the existing error/no-results messaging rather than being left on screen.
- [ ] The progress indicator is visually centered on the page and styled to look like a polished, professional element consistent with the rest of the app's design, rather than plain unstyled text.
- [ ] The rest of the itinerary generation experience (form validation, results display, modify/reset flows) continues to behave as it does today.

## Scope

### In Scope

- Adding a 3-stage vertical stepper progress indicator shown to the user during itinerary generation, covering venue search, venue research/cost estimation, and building the itinerary.
- Visually styling and centering the progress indicator so it looks professional and fits the app's existing look and feel.
- Updating/replacing the current single-message "Researching your destination…" status text with the new staged indicator.
- Advancing between stages using a reasonable approximation of progress (e.g. known pipeline milestones and/or elapsed time) rather than exact, real-time counts of work completed.

### Out of Scope

- Changing the underlying itinerary generation pipeline's logic, order of operations, or performance.
- Showing exact per-venue progress counts or percentages (e.g. "6 of 12 venues researched") — the indicator only needs to convey which of the three stages is active, not granular counts within a stage.
- Changes to the trip request form, validation, results layout, or the modify/reset trip flows.
- Any non-UI (e.g. CLI) progress reporting — this applies to the web UI experience only.

## UI / UX Notes

- The progress indicator appears in place of the current plain status message once the user submits the trip form and generation begins.
- It is presented as a vertical stepper with three rows, one per stage, in order: "Searching for venues," "Researching venues and estimating costs," and "Building your itinerary."
- Each row shows a marker indicating its state: a checkmark for a completed stage, an animated spinner for the currently active stage, and a plain/empty marker for a stage that hasn't started yet. The active stage's label should also read as visually emphasized (e.g. bolder or highlighted) compared to pending stages.
- The indicator should be horizontally centered on the page and presented as a polished, self-contained element (e.g. a card) with styling consistent with the rest of the app, rather than as plain markdown text.
- The indicator disappears and is replaced by the finished itinerary, or by the existing error/no-results message, once generation completes.

## Testing

- Verify the progress indicator appears immediately when itinerary generation starts, with the first stage ("Searching for venues") shown as active.
- Verify the indicator advances through all three stages in order as generation proceeds, ending with "Building your itinerary" shown as active (or completed) just before results appear.
- Verify completed stages show a checkmark and the active stage shows a spinner.
- Verify the indicator is replaced by the itinerary results when generation succeeds.
- Verify the indicator is replaced by the appropriate error message when generation fails.
- Verify the indicator is replaced by the "no itinerary could be generated" message when generation completes with no venues.
- Verify the indicator is visually centered and styled consistently across supported screen sizes.
