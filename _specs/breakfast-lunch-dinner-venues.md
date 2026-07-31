# Breakfast, Lunch, and Dinner Placeholder Venues

branch: claude/feature/breakfast-lunch-dinner-venues

## Summary

Add three new "standard" placeholder venues — Breakfast, Lunch, and Dinner — to the list of venues available to the trip planner. These are generic, non-web-sourced entries representing a meal slot at an unspecified restaurant or establishment, distinct from the web-sourced venues that are looked up and processed through the existing venue pipeline. They give the itinerary a way to represent "eat breakfast/lunch/dinner somewhere" without requiring a specific, named venue to have been found.

## User Story

As a trip planner, I want generic Breakfast, Lunch, and Dinner venues available in the list of venues, so that an itinerary can include a meal slot even when no specific restaurant or establishment has been identified for it.

## Acceptance Criteria

- [ ] A "Breakfast" venue exists with `origin: "standard"`, `status: "accepted"`, `tags: ["breakfast"]`, `duration_minutes: 60`, and the description "A generic placehold for breakfast at a restaurant or other establishment."
- [ ] A "Lunch" venue exists with `origin: "standard"`, `status: "accepted"`, `tags: ["lunch"]`, `duration_minutes: 60`, and the description "A generic placehold for lunch at a restaurant or other establishment."
- [ ] A "Dinner" venue exists with `origin: "standard"`, `status: "accepted"`, `tags: ["dinner"]`, `duration_minutes: 120`, and the description "A generic placehold for dinner at a restaurant or other establishment."
- [ ] All other fields on each of the three venues (`interest_id`, `location`, `location_type`, `geo_location`, `url`, `hours_of_operation`, `rating`, `notes`, `rejection_reason`) are left unset/`None` and `notes` is an empty list. The Breakfast and Lunch venues set `duration_minutes` to `60`; the Dinner venue sets `duration_minutes` to `120`.
- [ ] The three venues are available to the same list of venues that other (web-sourced) venues are added to, so downstream itinerary-building logic can select them like any other venue.
- [ ] Adding these venues does not change the behavior or output of the existing web-sourced venue search/lookup/processing pipeline.

## Scope

### In Scope

- Defining the three standard placeholder venues (Breakfast, Lunch, Dinner) with the exact field values specified above.
- Making the three venues available in the list of venues used by the rest of the application.

### Out of Scope

- Changing the `Venue` model's fields, types, or validation rules.
- Adding a new `InterestId` value for meals.
- Building or wiring up any UI, itinerary-scheduling, or selection logic that consumes these placeholder venues.
- Adding placeholder venues for anything other than breakfast, lunch, and dinner (e.g. brunch, snacks).

## UI / UX Notes

Not applicable — this is a data-only addition. There is no UI in this project to update.

## Testing

- Confirm each of the three venues can be constructed with the specified field values without validation errors.
- Confirm each venue's field values (`name`, `description`, `origin`, `status`, `tags`, and the `None`/empty defaults for the remaining fields) exactly match what's specified in this spec.
- Confirm the three venues appear in the list of venues alongside any web-sourced venues, without altering existing venue search/lookup/processing behavior.

## Open Questions

- Where should the list of standard placeholder venues live (e.g. a new constants module vs. inline in an existing module), and how should it be merged into the broader list of venues used by the itinerary pipeline? create a new module for these venues. Merge them into `process_venues` after processing for the duplicate venues.
- Should there be exactly one Breakfast/Lunch/Dinner venue per trip, or should the list allow multiple instances (e.g. one per day) to be created from these definitions? one per trip
