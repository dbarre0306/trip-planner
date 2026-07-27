# Plan: Serper Places Search

spec: _specs/serper-places-search.md

## Summary

Add a small, dependency-light module that calls the Serper Places API (`POST https://google.serper.dev/places`) for a single `interest` + `destination` pair, using the account's default result count (10, achieved by simply not sending a `num` override). Each place in the response is mapped into the existing `VenueCandidate` model (extended with a `rating` field and with its `address` field renamed to `location`), tagged with the interest that produced it. `create_itinerary` will loop over every interest on the incoming `TravelInfo`, call this function once per interest (per the spec's resolved open question), and print each returned candidate. Any request failure (missing API key, network error, non-2xx response) raises rather than being swallowed, again per the spec's resolved open question.

## Assumptions

- **Reuse `VenueCandidate`/`VenueCandidates` in `src/trip_planner/models.py`.** These were already added (commits `3393f1c`, `d474a94`) with fields `name`, `interest`, `address`, `tag` — almost exactly the shape this spec asks for. The spec (written without visibility into `models.py`) asks for a field named `location`; `models.py` currently calls it `address`. Resolution: rename `VenueCandidate.address` → `location` and add a new `rating: float | None = None` field, rather than introducing a second, competing result type. No other code references `VenueCandidate.address` yet (grep confirms), so the rename is safe.
- **Return type of the new function is `list[VenueCandidate]`**, not the `VenueCandidates` wrapper. `VenueCandidates` exists to let a CrewAI task declare a single structured `output_pydantic` type; this feature is a plain Python function called directly from `create_itinerary`, not a task output, so a plain list is the more natural fit and matches "returns this list of simplified place results to its caller" in the spec. `VenueCandidates` is left as-is for whenever a task/agent needs it.
- **Serper Places response fields map as:** `title` → `name`, `rating` → `rating`, `category` → `tag` (stored as-is, no mapping to `CategoryId`, per the spec's resolved open question), `address` → `location` (raw string, no normalization, per the spec's resolved open question). Any of these that Serper omits for a given place are left `None` on the `VenueCandidate` rather than raising.
- **No `num` parameter is sent in the Serper request body**, since the spec wants Serper's own default (10) rather than an explicit/configurable count.
- **`requests` becomes an explicit project dependency.** It's already pulled in transitively (present in `uv.lock` at `2.34.2` via `crewai[tools]`), but the new module imports it directly, so it should be declared in `pyproject.toml` rather than relied on implicitly.
- **One Serper call per interest.** Per the spec's resolved open question, if `TravelInfo.interests` has multiple entries, `create_itinerary` calls the new function once per interest (a simple loop, no concurrency, matching "Out of Scope").
- **Failures propagate as exceptions.** Per the spec's resolved open question, a missing `SERPER_API_KEY`, a network error, or a non-2xx Serper response all raise out of the new function; `create_itinerary` does not catch them, so a failure aborts itinerary creation.
- **No automated test framework exists yet** (`tests/` is empty, no `pytest` in `pyproject.toml`/`uv.lock`). Since the spec's Testing section calls for verifying request construction, response parsing, and error handling, this plan adds `pytest` (dev dependency) and uses the standard-library `unittest.mock` to stub `requests.post` — no new mocking library is introduced.

## Files to Change

- `pyproject.toml` — add `requests` to `dependencies`; add a `[dependency-groups]` (or `[tool.uv] dev-dependencies`) entry for `pytest` so tests can run via `uv run pytest`.
- `src/trip_planner/models.py` — rename `VenueCandidate.address` to `location`; add `rating: float | None = None`.
- `src/trip_planner/serper_places.py` — new module; exposes `search_places(interest: str, destination: str) -> list[VenueCandidate]`, which calls the Serper Places API and maps the response into `VenueCandidate` objects.
- `src/trip_planner/trip_planner.py` — implement `create_itinerary` to loop over `travel_info.interests`, call `search_places(interest, travel_info.destination)` for each, and print the returned candidates.
- `tests/test_serper_places.py` — new; unit tests for `search_places` covering request construction, response mapping, missing/partial fields, and error propagation, using mocked HTTP responses.
- `tests/test_trip_planner.py` — new; unit tests for `create_itinerary` verifying it calls `search_places` once per interest with the right arguments and prints the results.

## Implementation Steps

1. Run `uv add requests` and add a `pytest` dev dependency (e.g. `uv add --dev pytest`) so both land in `pyproject.toml`/`uv.lock`.
2. In `src/trip_planner/models.py`, rename the `address` field on `VenueCandidate` to `location` and add `rating: float | None = None`.
3. Create `src/trip_planner/serper_places.py`:
   - Define a module-level constant for the Serper Places endpoint (`https://google.serper.dev/places`).
   - Implement `search_places(interest: str, destination: str) -> list[VenueCandidate]` that:
     - Reads `SERPER_API_KEY` from the environment and raises immediately if it's not set.
     - Sends a `POST` request with a JSON body built from `interest` (as the query) and `destination` (as the location), and the API key in the request headers — no result-count parameter, so Serper's own default of 10 applies.
     - Raises if the HTTP call fails or returns a non-2xx status.
     - Iterates the response's list of places and builds one `VenueCandidate` per entry, mapping `title`→`name`, `rating`→`rating`, `category`→`tag`, `address`→`location`, and setting `interest` to the `interest` argument that was passed in; any field Serper omits is left `None`.
     - Returns the resulting list.
4. In `src/trip_planner/trip_planner.py`, implement `create_itinerary` to iterate `travel_info.interests`, call `search_places(interest, travel_info.destination)` for each, and print each returned `VenueCandidate` (name, rating, tag, location, interest) to stdout. Do not catch exceptions from `search_places` — let them propagate.
5. Add `tests/test_serper_places.py` covering: correct request body/headers from a given interest/destination; correct mapping of a full Serper response into `VenueCandidate` fields; a response missing `rating`/`category`/`address` on some entries resulting in `None` for those fields; a missing `SERPER_API_KEY` raising; and a non-2xx/error HTTP response raising.
6. Add `tests/test_trip_planner.py` covering: `create_itinerary` calling `search_places` exactly once per interest in `TravelInfo.interests` with the expected `destination`, and printing the returned candidates.
7. Run `uv run pytest` and manually run `crewai run` (or `python -m trip_planner.main`) once with a valid `SERPER_API_KEY` to confirm real venue output prints as expected for the sample `TravelInfo` already wired up in `main.py`.

## Testing

- Unit tests (new, via `pytest`) for `search_places`: request shape, successful mapping of all fields, graceful handling of missing optional fields, and exception propagation for a missing API key or a failed HTTP call — matching the spec's Testing section.
- Unit tests (new) for `create_itinerary`: one `search_places` call per interest, arguments passed through correctly, results printed.
- Manual run: execute the crew's entry point with a real `SERPER_API_KEY` and the existing sample `TravelInfo` in `main.py` (Tucson, AZ / hiking trails, restaurants) and confirm printed output shows name, rating, tag, location, and interest for each place.

## Risks / Open Questions

- Serper's Places API response shape (field names like `title`/`rating`/`category`/`address`) is assumed from known Serper documentation/behavior; if the live response differs, the mapping in `search_places` will need adjusting after a real test call.
- Serper could in principle return more than 10 places even without a `num` param; the plan does not add defensive truncation since the spec says to rely on Serper's default rather than enforce a count, but this is worth confirming on the first live call.
- Renaming `VenueCandidate.address` to `location` is safe today (no other references found), but if any in-flight branch or uncommitted work elsewhere depends on the old field name, it will need updating too.
