# Serper Places Search

branch: claude/feature/serper-places-search

## Summary

The trip planner needs a way to discover real, named venues for a given interest (e.g. "hiking", "museums") at a given destination. This feature adds a new module that queries the Serper Places API with an interest and a destination, and returns a simplified list of place results (name, rating, category tag, location/address, and the originating interest) for each place found. Carrying the interest alongside each venue means downstream itinerary logic can trace a place back to why it was suggested, even after results from multiple interests are combined, and carrying the location means each suggestion can be placed on a map or referenced concretely without a second lookup. The `create_itinerary` function will call this new module and print the results, giving visibility into the raw place data before it is used to build a full itinerary.

## User Story

As a developer building out the trip planner, I want to query Serper's Places API for a given interest and destination and get back a clean list of place names, ratings, categories, locations, and the interest each place matched, so that I can use real venue data as the foundation for itinerary generation and know both where a place is and which interest each suggestion came from.

## Acceptance Criteria

- [ ] A new module exists that exposes a function accepting an `interest` and a `destination` as input.
- [ ] The function queries the Serper Places API using those two inputs to form the search.
- [ ] The function requests/returns the default number of results from Serper (10), without adding pagination or a configurable result count.
- [ ] For each place returned by Serper, the function surfaces the place's name, rating, category/tag, location (the place's address, if Serper provides one), and the interest that was searched to find it.
- [ ] If Serper does not provide an address for a place, the `location` field is left empty/absent rather than causing the function to fail.
- [ ] The function returns this list of simplified place results to its caller.
- [ ] `create_itinerary` invokes this function (using the destination and one or more interests from the `TravelInfo` passed to it) and prints the returned results.
- [ ] The Serper API key is sourced from existing environment configuration (`SERPER_API_KEY`), consistent with how it's already documented for this project.

## Scope

### In Scope

- A new module dedicated to querying the Serper Places API.
- A single function taking `interest` and `destination` and returning simplified place data (name, rating, category/tag, location/address, and the interest passed in) for up to the default 10 results.
- Wiring this function into `create_itinerary` and printing the results to stdout.

### Out of Scope

- Persisting, caching, or deduplicating place results.
- Building the full itinerary from these results (that remains a `create_itinerary` TODO beyond this feature).
- Supporting a configurable number of results, pagination, or additional Serper Places filters (location bias, radius, etc.).
- Handling multiple interests concurrently/in parallel within `create_itinerary` beyond a straightforward loop or single call.
- Error/retry handling for API rate limits or outages beyond basic failure visibility.

## UI / UX Notes

Not applicable — this is a backend/data module with no user interface. The only user-facing output is console/log output when `create_itinerary` runs, showing the place name, rating, category tag, location, and matched interest for each result returned.

## Testing

- Verify the new function correctly builds a request from a given interest and destination.
- Verify the function correctly extracts name, rating, category/tag, and location from a Serper Places response, and attaches the searched interest to each result, returning them in a simplified structure.
- Verify behavior when Serper returns fewer than 10 results, or a place is missing a rating, category, or address (e.g. how absent fields, including a missing `location`, are represented in the output).
- Verify `create_itinerary` invokes the function with the expected destination/interest values from `TravelInfo` and prints the results.
- Consider using recorded/mocked Serper API responses for tests rather than live API calls.

## Open Questions

- When `TravelInfo` contains multiple interests, should `create_itinerary` query Serper once per interest, or only use the first interest for now? one per interest
- What should happen if the Serper API request fails (missing/invalid API key, network error, non-200 response) — should `create_itinerary` continue, or should the failure surface as an error? throw exception
- Is "tag (category)" expected to be Serper's own place category/type field as-is, or should it be mapped to this project's existing `CategoryId` taxonomy in `domain.py`? Serper's category should simply be stored as a tag in the returned list of venues.
- Should `location` hold Serper's raw address string as-is, or does it need any normalization/formatting? use the raw address as-is
