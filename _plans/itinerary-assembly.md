# Plan: Itinerary Assembly

spec: _specs/itinerary-assembly.md

## Summary

Add a new assembly step that takes the already-enriched, deduplicated list of `Venue`s (accepted and rejected, including the standard Breakfast/Lunch/Dinner placeholders) plus the trip's travel dates and party size, and produces a day-by-day schedule. The step selects a breakfast/lunch/dinner venue for each day within their required time windows (falling back to a freshly-described copy of the standard meal venue when nothing else qualifies), fills the remaining time with a geographically clustered, non-repeating, ratings-aware mix of other venues in strict chronological order with minimum gaps, and balances total scheduled duration evenly across days. A venue is only eligible for a slot if its (LLM-interpreted) hours of operation permit it — both the time of day and the day of the week — with venues lacking hours information treated as open at all times. Dinner always occupies at least 2 hours in the schedule regardless of the selected venue's own typical duration. The result is a list of per-day schedules, each entry carrying the display fields the spec requires (name, category, description, rating, location, location type, geographic coordinates, hours, URL, start time, duration, total cost for the party).

## Assumptions

- Each entry in `travel_info.travel_dates` maps to exactly one itinerary day, in the given order (day 1 = `travel_dates[0]`, etc.).
- "Interest category" in the per-venue output is the venue's `Category` label (e.g. "Food & Drinks"), looked up from `interest_id` via the existing `Interest`/`Category` domain lookups — not the raw interest id or interest label. Standard meal-venue copies (`interest_id is None`) are categorized as "Food & Drinks" since they represent meals.
- Only accepted venues carrying a "breakfast"/"lunch"/"dinner" tag (as produced by `venue_meal_tags.determine_meal_tags`) are eligible to fill that meal slot. All other accepted venues are treated as general "activity" venues and are never used for a meal slot, which is how the spec's "good mix of different venues" is satisfied alongside dedicated meals.
- Meal slots anchor to a fixed default start time within their allowed window (breakfast 8:00 AM, lunch 12:00 PM, dinner 6:00 PM) unless doing so would violate the 60-minute-gap/no-overlap rules against already-scheduled activities, in which case the slot shifts within its allowed window to the nearest time that satisfies those constraints. The spec does not mandate a specific anchor time within each window.
- Geographic clustering assigns each day's activity venues via a lightweight, hand-rolled nearest-centroid clustering over `geo_location` (latitude/longitude) — no new third-party geo/clustering dependency is introduced. Venues without a `geo_location` are distributed round-robin across days after geo-located venues are clustered.
- Mix-over-clustering priority (per the spec) is applied when choosing which venue fills a given activity slot on a day: a venue that improves interest-type variety for that day is preferred over one that only improves geographic tightness.
- Even duration distribution across days is a secondary, tie-breaking objective: after clustering, mix, and rating-based selection determine which venues go where, days with a disproportionate total duration are rebalanced by swapping eligible activity venues between days where doing so doesn't break clustering, mix, or no-repeat rules.
- A scheduled venue's "total estimated cost" is `(estimated_cost_per_adult * num_adults) + (estimated_cost_per_child * num_children)`, treating a null per-adult or per-child estimate as 0 for that term.
- `trip_planner.create_itinerary` is extended to call the new assembly step after `process_venues` and returns the resulting `Itinerary` (destination, num_adults, num_children, days) to its caller (rendering itineraries in a UI is out of scope per the spec, but producing the structured result for a caller to use is not).
- `Venue.hours_of_operation` is free text (from `venue_details.extract_venue_details`), so interpreting it requires an LLM call, following the same pattern as the other enrichment modules. The interpreted result is simplified to a single daily open time, a single daily close time, and a set of fully-closed weekdays — not a distinct schedule per day of the week — since that's the shape implied by the spec's examples ("doesn't open until 1 PM", "closed on Mondays"). This interpretation is computed once per venue up front (not per candidate slot) to avoid redundant LLM calls during scheduling.
- The day of the week for a travel date is derived by parsing `date` as an ISO `YYYY-MM-DD` string; if a date doesn't parse in that format, day-of-week eligibility is skipped for that date (time-of-day eligibility still applies) rather than treating it as an error, since day-of-week is the only thing that can't be determined.
- Overnight hours (e.g. a bar open 6 PM–2 AM, where the stated close time is numerically earlier than the open time) aren't modeled — the close-time constraint is skipped in that case rather than misinterpreted as "never open," since the free-text hours don't reliably disambiguate this within the single-day model used here.
- Dinner's 2-hour minimum is enforced by using `max(venue's own duration, 120 minutes)` as dinner's effective duration everywhere it matters: the hours-of-operation eligibility check (a venue must be able to accommodate the full 2 hours to be selected), the schedule cursor for later same-day venues, the day's total-duration figure used for even distribution, and the displayed `duration_minutes`. The underlying `Venue`'s own `duration_minutes` is left unmodified (a copy carries the adjusted value into the schedule) so nothing outside this one dinner placement is affected. Breakfast and lunch are not given a minimum duration — only dinner, per the requirement.

## Files to Change

- `src/trip_planner/models.py` — add `ScheduledVenue` (per-venue schedule entry: name, interest category label, description, rating, location, location_type, geo_location, hours_of_operation, url, start_time, duration_minutes, estimated_cost_usd) and `ItineraryDay` (day_number, date, list of `ScheduledVenue`) Pydantic models.
- `src/trip_planner/standard_meal_description.py` (new) — generates the "fun and imaginative" description used only when a standard meal venue is actually copied into the itinerary; own prompt/tone, following the pattern in `venue_description.py`.
- `src/trip_planner/venue_geo_clustering.py` (new) — partitions a list of venues into up to N geographic groups (one per day), with a defined fallback for venues lacking `geo_location`.
- `src/trip_planner/venue_operating_hours.py` (new) — interprets a venue's free-text `hours_of_operation` via an LLM call into a structured daily open/close time plus a set of closed weekdays, and exposes an `is_available(weekday, start_minutes, end_minutes)` check; treats missing hours as open at all times.
- `src/trip_planner/itinerary.py` (new) — `assemble_itinerary(travel_info, venues) -> Itinerary`, the core scheduling logic described below.
- `src/trip_planner/trip_planner.py` — update `create_itinerary` to call `assemble_itinerary` after `process_venues` and return the resulting `Itinerary` instead of only printing venues.
- `tests/test_itinerary.py` (new) — unit tests covering the scheduling rules, including hours-of-operation eligibility.
- `tests/test_venue_geo_clustering.py` (new) — unit tests for the clustering helper.
- `tests/test_standard_meal_description.py` (new) — unit tests for the fun-description generator.
- `tests/test_venue_operating_hours.py` (new) — unit tests for hours-of-operation interpretation and availability checks.
- `tests/test_trip_planner.py` — extend to cover `create_itinerary` invoking `assemble_itinerary`.

## Implementation Steps

1. Add `ScheduledVenue` and `ItineraryDay` models to `models.py`, matching the fields required by the spec's Acceptance Criteria (location omitted/`None` when unknown).
2. Build `standard_meal_description.py`: a single function that takes a standard venue's meal type ("breakfast"/"lunch"/"dinner") and the destination, and returns a freshly generated, fun/imaginative description via `openai_client.chat_completion`, distinct in tone from `venue_description.generate_description`.
3. Build `venue_geo_clustering.py`: a function that takes a list of venues and a target cluster count (number of trip days) and returns venues grouped by day, clustering on `geo_location` and appending venues without a location round-robin across the resulting groups.
4. Build `venue_operating_hours.py`: a function that takes a venue's `hours_of_operation` string (or `None`) and returns a structured result (open time, close time, closed weekdays); returns "open at all times" immediately without an LLM call when the input is empty, otherwise prompts the LLM to extract the three fields. Expose an availability check that, given a day of the week and a candidate start/end time, returns whether the venue may be scheduled there.
5. Build `itinerary.py`:
   a. Filter the input venues to `status == "accepted"`.
   b. Partition accepted venues into breakfast/lunch/dinner pools (by tag) and an activity pool (accepted venues with none of those tags).
   c. Interpret every accepted venue's hours of operation once up front (via `venue_operating_hours`), keyed by venue identity, for reuse throughout scheduling.
   d. For each day (1-indexed, one per `travel_dates` entry), derive that date's day of the week; for each meal, compute the meal's prospective start time first (from the anchor/window rules), then pick the highest-rated unused venue from that meal's pool whose hours of operation permit being visited for that meal's effective duration (dinner's effective duration is `max(venue duration, 120 minutes)`; breakfast/lunch use the venue's own duration) at that day/time; if none qualifies, create a copy of the corresponding standard venue with a newly generated description (via `standard_meal_description`) and use it — standard-venue copies are exempt from both the no-repeat rule and hours-of-operation checks (they have no hours). Once a dinner venue is chosen, store a copy with `duration_minutes` set to its effective (at-least-2-hour) duration so every later calculation for that day sees the enforced length.
   e. Assign the activity pool to days using `venue_geo_clustering`, then within each day schedule the day's activities into the time gaps around its three meals, enforcing strict chronological order, the 60-minute minimum gap between consecutive venues, no time overlap, and each candidate's hours-of-operation availability at its prospective start/end time.
   f. When a day has more eligible activity venues than time allows, prefer higher-rated venues; when choosing between venues that would repeat an already-used interest type for the day versus one that wouldn't, prefer the one improving variety (mix takes priority over tighter geographic clustering).
   g. Track venue usage across the whole trip so no non-standard venue is scheduled more than once.
   h. After the initial per-day assignment, rebalance activity venues between days as needed so total scheduled duration per day is as even as possible, without breaking the no-repeat, mix, overlap/gap, or hours-of-operation rules.
   i. Compute each scheduled venue's total estimated cost from its per-adult/per-child cost estimates and `travel_info.num_adults`/`num_children`.
   j. Build and return the `Itinerary` (destination, num_adults, num_children, and the list of `ItineraryDay`s numbered from 1), each day containing `ScheduledVenue`s with all spec-required fields.
6. Update `trip_planner.create_itinerary` to call `itinerary.assemble_itinerary(travel_info, venues)` after `process_venues` and return the resulting `Itinerary`, in place of the current flat venue-print loop (callers such as `main.py`/`app.py` that want the old debug output can print the returned itinerary themselves).
7. Add/extend tests per the Testing section below.

## Testing

- `test_itinerary.py`:
  - Breakfast/lunch/dinner are each scheduled within their required windows (6–9 AM, 11 AM–1 PM, 5–8 PM) and breakfast is always the first venue of the day.
  - Lunch and dinner are present every day.
  - The standard meal venue is used, with a freshly generated description, only when no eligible venue remains for that slot.
  - No two venues on the same day overlap, and every pair of consecutive venues has at least a 60-minute gap.
  - Venues within a day appear in strict chronological order.
  - Day numbers start at 1 and increase sequentially.
  - A non-standard venue never appears more than once across the whole itinerary; standard-venue copies may repeat.
  - When eligible venues exceed available slots, higher-rated venues are chosen first.
  - Total scheduled duration is distributed as evenly as possible across days.
  - Activity venues assigned to the same day are geographically clustered relative to other days, except where the mix rule overrides clustering.
  - Rejected venues never appear in the assembled itinerary.
  - Each `ScheduledVenue` carries all required display fields, with `location`, `location_type`, and `geo_location` each omitted/`None` when the source venue lacks them, and `estimated_cost_usd` correctly reflects `num_adults`/`num_children`.
  - A day with no eligible venue (including no standard venue) for a required meal is left without that meal slot rather than erroring.
  - A venue whose hours of operation don't cover a slot's prospective start/end time is not selected for that slot in favor of one that is available (e.g. a lower-rated but currently-open venue is chosen over a higher-rated one that isn't open yet).
  - A venue stated to be closed on a given day of the week is never scheduled on a travel date that falls on that weekday, but remains eligible on other travel dates.
  - A venue with no hours-of-operation information is eligible for any slot, at any time, on any day.
  - Dinner's scheduled `duration_minutes` is at least 120 even when the selected venue's own duration is shorter; a venue with a longer duration than 120 keeps its own (longer) duration.
  - Breakfast and lunch durations are not extended to a minimum — only dinner's is.
  - A venue scheduled after dinner still honors the 60-minute gap measured from dinner's enforced (at-least-2-hour) end time, not the venue's own shorter duration.
- `test_venue_geo_clustering.py`: venues with `geo_location` are grouped into the requested number of clusters by proximity; venues without `geo_location` are distributed round-robin across the resulting groups.
- `test_standard_meal_description.py`: the generated description differs per meal type/destination inputs and comes from the mocked `chat_completion` call.
- `test_venue_operating_hours.py`: missing hours produce an "open at all times" result without calling the LLM; a well-formed LLM response is parsed into the correct open/close times and closed weekdays; an unparsable LLM response falls back to "open at all times"; the availability check correctly rejects times outside the open/close window and rejects closed weekdays, while treating an unknown weekday as unrestricted.
- `test_trip_planner.py`: `create_itinerary` calls `assemble_itinerary` with the processed venues and travel info, and returns its result.

## Risks / Open Questions

- Geographic clustering and even-duration distribution are both heuristic; beyond "mix beats clustering," the spec doesn't fully order every rule against every other, so exact scheduling outcomes on edge cases (sparse venues, all-clustered-in-one-area) are an implementation judgment call.
- "Interest category" for standard meal-venue copies (`interest_id is None`) is assumed to be "Food & Drinks" — not explicitly defined by the spec.
- Fixed default meal anchor times (8:00 AM / 12:00 PM / 6:00 PM) are an implementation choice within the spec's allowed windows, not a spec requirement.
- No geo/clustering library exists in the project's dependencies today; this plan assumes a small hand-rolled clustering helper rather than adding a new dependency — worth confirming before implementation if a more robust approach is preferred.
- Hours-of-operation eligibility depends on the LLM correctly interpreting free-text hours into a single daily open/close window plus closed weekdays; venues with genuinely irregular or per-day-varying hours (e.g. different hours each day beyond a simple closed-day list, or overnight hours) are only approximately represented, which could make an actually-available venue look unavailable or vice versa.
- Interpreting hours of operation is an additional LLM call per accepted venue (computed once up front, not per candidate slot), adding to the pipeline's overall LLM call volume.
