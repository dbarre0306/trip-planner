# Plan: Prevent Duplicate Venue Across Days

spec: _specs/prevent-duplicate-venue-across-days.md

## Summary

The itinerary scheduler in `itinerary.py` currently tracks which venues have already been placed into the trip using Python object identity (`id(venue)`), stored in a `used: set[int]`. That works only if each real-world venue is represented by exactly one `Venue` object. If two separate `Venue` objects end up describing the same real place (e.g. because the earlier LLM-based duplicate-merging step didn't catch a particular pair), each object has its own `id()` and the scheduler has no way to know they're the same place — so both can independently be selected for different days, producing the exact symptom reported: the same venue appearing on two different days. The fix replaces object-identity-based tracking with a venue-identity key (derived from the venue's normalized name) everywhere the scheduler decides whether a venue is "already used," so a repeat is caught even when it arrives as a distinct object. Generic placeholder meal venues (`origin == "standard"`) are left out of this tracking, exactly as they are today, since they're intentionally allowed to appear once per day as a fallback.

## Assumptions

- The spec's "same venue" is resolved as "same venue name" (case- and whitespace-insensitive). This is the identity signal already used as the primary/strongest signal in `venue_deduplication.py`'s LLM-based matching, and it directly matches what a user would visually recognize as "the same venue" in the itinerary output. Matching on URL/geo-location as well (like the upstream dedup step does) is not needed here — that richer matching is explicitly out of scope, and name-based matching is sufficient to close the gap the scheduler currently has.
- The `operating_hours` dict in `assemble_itinerary`, which is keyed by `id(venue)` to cache each venue's parsed hours, is a per-object cache unrelated to the duplicate-across-days bug and is left unchanged.

## Files to Change

- `src/trip_planner/itinerary.py` — add a small private helper that returns a normalized identity key for a venue (lowercased, whitespace-collapsed name). Replace every place that tracks or checks the `used: set[int]` of `id(venue)` with the identity key instead: the candidate filter in `_select_meal_venue`, the `used.add(...)` call in `_schedule_meal` (only reached for real, non-standard picks — unchanged), the candidate filter and `used.add(...)` in `_fill_segment`, the `leftover` list comprehension in `assemble_itinerary`, and the `used.add(...)` call in `_rebalance`.

## Implementation Steps

1. In `itinerary.py`, add a private helper function that takes a `Venue` and returns its normalized identity key (lowercase, collapsed whitespace on `venue.name`).
2. Change the type of `used` from `set[int]` to `set[str]` (identity keys) everywhere it's created, passed, and read (`assemble_itinerary`, `_assemble_day`, `_schedule_meal`, `_select_meal_venue`, `_fill_segment`, `_rebalance`).
3. Update `_select_meal_venue`'s candidate filter to exclude venues whose identity key is already in `used`, instead of filtering on `id(venue)`.
4. Update `_schedule_meal` to add the identity key of a selected real venue to `used` (leave the standard-placeholder fallback path untouched, so placeholders are never added to `used`).
5. Update `_fill_segment`'s candidate filter and its `used.add(...)` call to use identity keys.
6. Update the `leftover` computation in `assemble_itinerary` (venues from `activity_pool` not yet in `used`) to filter by identity key.
7. Update `_rebalance`'s `used.add(...)` call to use the identity key of the venue being placed.
8. Re-read through `itinerary.py` once the changes are in to confirm no remaining reference to `id(venue)` is used for uniqueness tracking (the `operating_hours` cache dict's use of `id(venue)` is intentionally left as-is, per the Assumptions above).

## Testing

- Add a test reproducing the reported bug: two distinct `Venue` objects with the same (or same-but-differently-cased/spaced) name, both eligible to be scheduled, across a multi-day trip — assert the name appears on at most one day in total, covering the case the existing `test_venue_never_repeats_across_the_trip` test (which only uses a single shared object) doesn't cover.
- Add a test where a duplicate-named venue is only eligible as an activity-slot candidate on a later day (via clustering/rebalancing) after being used for a meal earlier in the trip — assert it isn't placed again, covering meal-to-activity-slot repeats as well as same-slot-type repeats (spec Acceptance Criterion 2).
- Extend/add a test confirming a generic placeholder meal venue (`origin == "standard"`) can still legitimately appear on multiple days, so the fix doesn't over-apply the uniqueness rule to placeholders (spec Acceptance Criterion 3).
- Add a test with a longer trip (more days than there are distinct non-standard venues available) confirming no specific venue is reused as a fallback to fill out extra days, and that generic placeholders (or an empty slot) are used instead (spec Acceptance Criterion 4 / Testing section).
- Run the full existing `tests/test_itinerary.py` suite to confirm venue selection quality, meal timing, activity pacing, and cost totals are unchanged (spec Acceptance Criterion 5).

## Risks / Open Questions

- Name-only identity matching means two genuinely different real-world venues that happen to share an identical name (e.g. a chain with two branches in the same destination) would now incorrectly be treated as the same venue and deduplicated across days. This mirrors the strongest signal already used upstream in `venue_deduplication.py` and is accepted as a reasonable trade-off for this fix; if it proves too aggressive in practice, a follow-up could widen the identity key to also consider location/geo the way the upstream dedup step does.
