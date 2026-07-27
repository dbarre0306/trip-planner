# Plan: Venue Serper Lookup

spec: \_specs/venue-serper-lookup.md

## Summary

Add a new `serper_lookup` module that takes a venue name and destination, issues a Serper web search (the general `/search` endpoint, distinct from the existing `/places` endpoint used by `serper_places.py`), and returns a small result containing the first reachable result URL and the full list of snippets from all results. Reachability is determined with a `HEAD` request per candidate URL, checked in order, stopping at the first one with a status code under 400. The result is shaped so its `url` and `notes` can be assigned directly to a `Venue`.

## Assumptions

- Reachability check per Open Questions answers: an HTTP `HEAD` request with response status code < 400 counts as reachable.
- Reachability checks run sequentially in result order (no concurrency), per Open Questions answers — the first reachable one short-circuits the rest.
- Uses the Serper `/search` (organic results) endpoint rather than `/places`, since this step needs generic web results (link + snippet) for a venue name, not the places/business data the existing `serper_places.py` module already handles. This is a new, separate module rather than an extension of `serper_places.py`, matching the spec's "new module" requirement and Out of Scope note not to change `serper_places.py`.
- The new module returns a plain result object (e.g. a small dataclass or pydantic model with `url: str | None` and `notes: list[str]`) rather than a `Venue` directly, since assembling the full `Venue` is a later pipeline step outside this spec's scope.
- Network calls (search request and reachability HEAD requests) use the existing `requests` library already used by `serper_places.py`, keeping dependencies unchanged.
- A reasonable fixed timeout is used for both the search request and each HEAD reachability check, since the spec asks only for status code < 400 and does not specify a timeout value.

## Files to Change

- `src/trip_planner/serper_lookup.py` — new module. Contains the Serper `/search` API call (mirroring the auth/error-handling pattern of `serper_places.py`'s `_get_serper_places`), a reachability check helper using `requests.head`, and the public `lookup_venue(name, destination)` function that ties them together and returns the url/notes result.
- `tests/test_serper_lookup.py` — new test file mirroring the style of `tests/test_serper_places.py`, covering the acceptance criteria and testing scenarios called out in the spec.

## Implementation Steps

1. In `src/trip_planner/serper_lookup.py`, define the Serper search endpoint constant (e.g. `SERPER_SEARCH_URL = "https://google.serper.dev/search"`) and a private function that POSTs `{"q": f"{name} {destination}"}` (or equivalent query construction) to it using the `SERPER_API_KEY` env var, following the same header/auth/`raise_for_status` pattern as `_get_serper_places` in `serper_places.py`.
2. Parse the search response's organic results list, extracting each result's link and snippet, defaulting missing fields safely (e.g. skip results without a link when checking reachability, but still include any snippet text present).
3. Add a private reachability helper that issues a `requests.head` call against a candidate URL with a short timeout and returns whether the response status code is < 400, treating request exceptions (timeouts, connection errors) as not reachable rather than raising.
4. Define the small result type (e.g. a pydantic `BaseModel` or `dataclass`) with `url: str | None` and `notes: list[str]`, matching the shape needed to populate `Venue.url` / `Venue.notes`.
5. Implement `lookup_venue(name: str, destination: str)`: call the search function, walk the ordered list of results checking reachability sequentially and stopping at the first reachable URL (or ending with `url=None` if none are reachable or there are no results), and separately collect every result's snippet (regardless of reachability) into the notes list.
6. Ensure the zero-results case (empty organic results list) returns a result with `url=None` and `notes=[]` without raising.
7. Write `tests/test_serper_lookup.py` covering: request construction/auth (mirroring `test_search_places_builds_request` / `test_search_places_raises_when_api_key_missing`), first-result-reachable case, first-unreachable-then-later-reachable case, all-unreachable case, zero-results case, and confirming notes always contains every snippet regardless of which URL was selected. Mock both the Serper POST call and the `requests.head` reachability check so no real network calls occur.

## Testing

- Unit tests as described above in `tests/test_serper_lookup.py`, run via the project's existing `pytest` setup, mocking `requests.post` (search) and `requests.head` (reachability) so tests are fully offline.
- Verify via test assertions that: the correct query is sent to Serper; the first reachable URL (in result order) is chosen and later reachable URLs are ignored once one is found; `url` is `None` when no candidates are reachable or when there are no results; `notes` always equals the full set of snippets from all returned results independent of the reachability outcome.

## Risks / Open Questions

- No timeout value was specified in the spec for either the search request or the HEAD reachability checks; a reasonable fixed timeout will be chosen during implementation.
- The spec doesn't specify exact query construction (e.g. whether to quote the venue name, include extra keywords like "official site"); implementation will follow the simple `f"{name} {destination}"` pattern used by the existing places search for consistency, unless reachability in practice proves this insufficient.
- Serper's `/search` response schema (organic result field names) is assumed to follow Serper's standard `organic[].link` / `organic[].snippet` shape; this should be confirmed against real API docs/responses during implementation.
