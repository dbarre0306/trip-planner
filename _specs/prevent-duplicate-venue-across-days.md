# Prevent Duplicate Venue Across Days

branch: feature/prevent-duplicate-venue-across-days

## Summary

A manual test of the itinerary builder showed the same specific venue scheduled on two different days of the same trip. A traveler should never be sent to the same real place twice within one itinerary — each specific venue should be visited at most once across the whole trip. Generic, non-specific placeholder entries (e.g. a generic "Breakfast" or "Lunch" slot used when no real venue is available) are not affected by this rule, since they don't represent a single physical place being revisited.

## Acceptance Criteria

- [ ] No specific, named venue appears more than once across all days of a generated itinerary.
- [ ] This holds across every part of the day (meals and activity slots alike) — a venue used for lunch on one day must not also appear at breakfast, dinner, or an activity slot on another day.
- [ ] Generic placeholder entries (used when no real venue could be found for a meal) may still appear on multiple days, since each occurrence does not represent the same physical venue.
- [ ] The fix holds regardless of trip length (short trips and long multi-day trips) and regardless of how many venues were found for the trip's chosen interests.
- [ ] Existing itinerary behavior (venue selection quality, meal timing, activity pacing, cost totals) is otherwise unchanged.

## Scope

### In Scope

- Ensuring uniqueness of specific venues across the full itinerary, not just within a single day.
- Covering all scheduling paths that can place a venue into a day (meals, activity slots, and any later rebalancing/fill-in step).

### Out of Scope

- Changes to how venues are discovered, enriched, or deduplicated earlier in the pipeline (e.g. venue search or the name/geo-based duplicate merging that happens before scheduling).
- Changes to the generic placeholder meal venues themselves or when they are used.
- Changes to venue selection quality, ranking, or pacing logic beyond what's needed to prevent repeats.

## Testing

- A regression test reproducing the manual test scenario: given a multi-day trip and a venue pool, confirm no specific venue is scheduled on more than one day.
- A test confirming a venue already used earlier in the trip is not reused later even when it would otherwise be the best-ranked candidate for a later day.
- A test confirming generic placeholder meal entries are still permitted to appear on multiple days.
- A test covering a trip long enough that the venue pool could plausibly run out, confirming no venue is reused as a fallback.

## Open Questions

- None.
