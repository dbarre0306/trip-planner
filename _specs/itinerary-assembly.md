# Itinerary Assembly

branch: feature/itinerary-assembly

## Summary

Given a set of venues, the destination, the trip's travel dates, and the number of adults and children traveling, assemble a day-by-day itinerary. The itinerary schedules venues into each day in strict chronological order, honoring meal-time windows for breakfast, lunch, and dinner, avoiding scheduling conflicts, clustering venues geographically to minimize travel, and distributing venues evenly across the trip.

## Acceptance Criteria

- [ ] Breakfast is the first venue scheduled each day.
- [ ] Breakfast starts between 6:00 AM and 9:00 AM local time, inclusive.
- [ ] The standard breakfast venue is used only when no other suitable venue is available for the breakfast slot.
- [ ] When the standard breakfast venue is used, a copy of it is created and given a fun, imaginative description.
- [ ] Lunch is scheduled every day.
- [ ] Lunch starts between 11:00 AM and 1:00 PM local time, inclusive.
- [ ] The standard lunch venue is used only when no other suitable venue is available for the lunch slot, and a copy of it is given a fun, imaginative description when used.
- [ ] Dinner is scheduled every day.
- [ ] Dinner starts between 5:00 PM and 8:00 PM local time, inclusive.
- [ ] The standard dinner venue is used only when no other suitable venue is available for the dinner slot, and a copy of it is given a fun, imaginative description when used.
- [ ] Dinner is scheduled for a minimum duration of 2 hours, even if the selected venue's typical visit duration is shorter.
- [ ] Venues scheduled within the same day are clustered geographically to minimize travel time between them.
- [ ] No two scheduled venues overlap in time on the same day.
- [ ] Each day includes a good mix of different venue types rather than repeating the same kind of activity. When a good mix and geographic clustering conflict, a good mix of venues takes priority.
- [ ] The same venue is not scheduled more than once across the entire trip. This restriction does not apply to standard meal venues.
- [ ] When there are more eligible venues than the schedule can accommodate, venues with higher ratings are preferred.
- [ ] Venues are scheduled in strict chronological order within a day, with at least 60 minutes between the end of one venue and the start of the next.
- [ ] Day numbering starts at 1.
- [ ] Venues are distributed as evenly as possible across all days of the trip, based on total scheduled duration per day.
- [ ] Each scheduled venue in the itinerary includes: name, interest category, description, rating, location (omitted entirely if unknown), location type (omitted entirely if unknown), geographic coordinates (omitted entirely if unknown), hours of operation, URL (if available), start time in HH:MM format, duration in minutes, and total estimated cost in USD for the given number of adults and children.
- [ ] Venues with a `rejected` status are excluded from consideration when assembling the itinerary.
- [ ] Local time for scheduling purposes is based on the destination's timezone.
- [ ] If no venue, including the standard venue, is available for a required meal slot, that day is left without a venue for that meal slot.
- [ ] A venue is only scheduled at a start time that falls within its stated hours of operation for that day (e.g. a venue that doesn't open until 1 PM is never scheduled in the morning).
- [ ] A venue is never scheduled on a travel date whose day of the week falls within the venue's stated closed day(s) (e.g. a venue closed on Mondays is never scheduled on a Monday).
- [ ] When a venue's hours of operation are not available, the venue is treated as available all day, every day, for scheduling purposes.

## Scope

### In Scope

- Assembling a complete day-by-day itinerary from a given list of venues, the trip's travel dates, and the number of adults and children.
- Applying the breakfast, lunch, and dinner scheduling rules, including substitution with standard meal venues when needed and enforcing dinner's 2-hour minimum duration.
- Enforcing chronological ordering, minimum gaps, and no-overlap between venues within a day.
- Clustering venues geographically within a day.
- Selecting among eligible venues by rating when supply exceeds the number of slots available.
- Avoiding repeated venues across the trip, except for standard meal venues.
- Distributing venues evenly across days based on total duration.
- Producing the per-venue details required for display: name, interest category, description, rating, location, hours of operation, URL, start time, duration, and total estimated cost for the party.
- Excluding venues with a `rejected` status from consideration.
- Determining local time based on the destination's timezone.
- Respecting each venue's hours of operation, including specific closed day(s) of the week, when deciding whether it's eligible for a given slot on a given travel date.

### Out of Scope

- Searching for or enriching venues (venue discovery, descriptions, hours, cost estimation, deduplication) — this feature assumes a finalized set of venues is already available.
- Any user interface for displaying or editing the assembled itinerary.
- Persisting or exporting the assembled itinerary.

## Testing

- Breakfast, lunch, and dinner are each scheduled within their required time windows.
- Breakfast is always the first venue of the day.
- Lunch and dinner are present every day.
- Standard meal venues are used only when no other eligible venue is available for that slot, and receive a newly generated description when used.
- No two venues scheduled on the same day overlap, and there is always at least a 60-minute gap between consecutive venues.
- Venues within a day are scheduled in strict chronological order.
- Day numbers start at 1 and increase sequentially across the trip.
- The same non-standard venue never appears more than once across the whole itinerary.
- When eligible venues exceed available slots, higher-rated venues are chosen over lower-rated ones.
- Total scheduled venue duration is distributed evenly across the days of the trip.
- Venues assigned to the same day are geographically clustered relative to venues assigned to other days.
- Each venue in the output itinerary carries all required fields, with location, location type, and geographic coordinates omitted when unknown.
- Total estimated cost per venue reflects the given number of adults and children.
- A venue is never scheduled at a start time before its stated opening time or after its stated closing time.
- A venue is never scheduled on a travel date that falls on one of its stated closed day(s) of the week.
- A venue with no hours-of-operation information can be scheduled at any time on any day.
- Dinner always occupies at least 2 hours in the schedule, whether or not the selected venue's own typical duration is shorter; subsequent venues that day still honor the 60-minute gap after dinner's actual (at-least-2-hour) end time.

## Open Questions

- If no venue at all (including no standard venue) is available for a required meal slot, what should happen — is the day left without that meal, or is this an error condition? This condition should never occur, but if it does then they day is left without that meal.
- How should "local time" be determined for a venue when hours of operation or timezone information is incomplete or missing? the "local time" is based on the destination.
- Should venues with a `rejected` status be excluded from itinerary assembly entirely, or is that filtering assumed to happen before this feature runs? yes, exclude rejected venues
- When "a good mix of different venues" and "geographic clustering" pull in different directions, which takes priority? favor a good mix of different venues
