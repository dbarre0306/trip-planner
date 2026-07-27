# Plan: Concurrent Venue Processing

spec: _specs/concurrent-venue-processing.md

## Summary

Add a `Venue` domain model and a new `venue_processing` module containing a no-op `process_venue` function that maps a `VenueCandidate` to a `Venue`. Update `create_itinerary` in `trip_planner.py` so that, for each interest, the `VenueCandidate` list returned by `search_places` is submitted to a shared, module-level `ThreadPoolExecutor` for concurrent processing instead of being handled one at a time in a sequential loop. All submitted venues for an interest are waited on before moving to the next interest; any per-venue processing failures are collected and reported together at the end of that batch rather than raised immediately or dropped.

## Assumptions

- The `Venue` model lives in `models.py` alongside the existing `VenueCandidate`/`VenueCandidates` models, since that file is already the home for venue-shaped Pydantic models.
- The no-op `process_venue` function maps the fields it can from `VenueCandidate` (`name`, `interest`, `location`) onto `Venue` and leaves the rest at their declared defaults (`origin="web"`, `status="accepted"`, empty `tags`/`notes`, etc.) — this satisfies "does nothing" while still returning a well-formed `Venue`, per the spec's answered open question on the no-op's return type.
- The shared thread pool is a single module-level `ThreadPoolExecutor` created once in `venue_processing.py` at import time and reused for the lifetime of the process, per the spec's answer that it should be "shared/reused across the whole crew app" (not recreated per call or per interest).
- Thread pool sizing (`max_workers`) is left at a reasonable default; tuning is explicitly out of scope per the spec.
- "Collect and report all failures at the end" is implemented by gathering exceptions from failed futures for a given interest's batch and printing/logging them together after all futures for that batch complete — it does not abort processing of the other venues in the batch, and does not stop `create_itinerary` from continuing to the next interest.
- `create_itinerary` continues to print venue output (as it does today for `VenueCandidate`), but prints the processed `Venue` objects instead, since the spec allows the processing step to replace the current sequential print loop.

## Files to Change

- `src/trip_planner/models.py` — add the `Venue` model (with `Literal`/`Field` imports) exactly as specified in the spec's answered open question.
- `src/trip_planner/venue_processing.py` — new module. Contains: the shared module-level `ThreadPoolExecutor`; `process_venue(candidate: VenueCandidate) -> Venue`, the no-op mapping function; and a `process_venues(candidates: list[VenueCandidate]) -> list[Venue]`-style function that submits all candidates to the shared executor, waits for all futures, collects successful `Venue` results, and collects/reports any exceptions raised by individual futures without letting one failure stop the rest.
- `src/trip_planner/trip_planner.py` — update `create_itinerary` to, for each interest, pass the `VenueCandidate` list from `search_places` into the new concurrent processing function and print/report the resulting `Venue` objects (and any collected failures) instead of the current sequential `for venue in venues: print(...)` loop.
- `tests/test_venue_processing.py` — new test file covering the no-op processing function and the concurrent batch-processing function, including the failure-collection path.
- `tests/test_trip_planner.py` — update the existing tests to reflect that `create_itinerary` now routes venues through concurrent processing rather than printing `VenueCandidate` objects directly.

## Implementation Steps

1. Add the `Venue` model to `models.py`, importing `Literal` from `typing` and `Field` from `pydantic`, matching the schema given in the spec.
2. Create `venue_processing.py`:
   - Instantiate a single shared `ThreadPoolExecutor` at module scope.
   - Implement `process_venue`, a no-op function that takes a `VenueCandidate` and returns a `Venue`, copying over `name`, `interest`, and `location`, leaving all other fields at their model defaults.
   - Implement a batch-processing function that submits every candidate in a given list to the shared executor via `process_venue`, waits for all submitted futures to complete, collects successful `Venue` results in input order (or completion order — document the choice), and separately collects exceptions raised by any futures.
   - Ensure the batch function reports collected failures (e.g. returns them alongside successes, or logs/prints a summary) rather than letting an exception from one venue propagate and abort the batch.
3. Update `create_itinerary` in `trip_planner.py`:
   - Replace the current `for venue in venues: print(...)` loop with a call into the new batch-processing function from `venue_processing.py`.
   - Print the resulting processed `Venue` objects (mirroring today's `model_dump_json(indent=2)` style) for the successful ones.
   - Surface any collected per-venue failures for that interest (e.g. print them) without stopping processing of subsequent interests.
4. Add `tests/test_venue_processing.py`:
   - Test that `process_venue` returns a `Venue` with the expected mapped fields and default values for a given `VenueCandidate`.
   - Test that the batch-processing function returns a `Venue` for every `VenueCandidate` submitted when all succeed.
   - Test that when the underlying processing raises for one venue (e.g. via monkeypatching), the batch-processing function still returns results for the other venues and surfaces the failure rather than raising immediately or silently dropping it.
   - Test (or reasonably assert via a mechanism that doesn't rely on timing flakiness) that venues are dispatched to the shared thread pool rather than executed strictly one-at-a-time in the calling thread — e.g. asserting the shared executor's `submit` is used for each candidate.
5. Update `tests/test_trip_planner.py`:
   - Adjust `test_create_itinerary_queries_once_per_interest` and `test_create_itinerary_prints_results` (and add coverage as needed) so they mock/patch the venue-processing entry point and assert `create_itinerary` submits every `VenueCandidate` returned by `search_places` for processing, and that the printed output reflects the processed `Venue` data.
6. Run `uv run pytest` (or the project's configured test command) to confirm all new and updated tests pass.

## Testing

- Unit tests in `tests/test_venue_processing.py` covering: no-op mapping correctness, all-success batch processing, and the failure-collection path when one venue's processing raises.
- A test asserting concurrent dispatch (via the shared thread pool) rather than strictly sequential execution, without relying on brittle timing assumptions.
- Updated tests in `tests/test_trip_planner.py` confirming `create_itinerary` submits every discovered venue for processing (one call per `VenueCandidate` per interest) and that output reflects processed `Venue` objects.
- Manual sanity check: run the existing test suite (`uv run pytest`) after the change to confirm no regressions in `search_places`/`create_itinerary` behavior outside of the new processing step.

## Risks / Open Questions

- The spec resolves prior open questions on pool scope (shared across the app), failure handling (collect-and-report), and the no-op return type (a `Venue`), but does not specify the exact reporting mechanism for collected failures (print vs. log vs. return to caller) — this plan defaults to printing, consistent with the module's existing use of `print` for output, but should be confirmed if a different mechanism (e.g. logging) is preferred.
- Result ordering from the batch-processing function (input order vs. completion order) isn't specified by the spec; this plan defaults to preserving input order for predictability, which is worth confirming during implementation/review.
- A shared, process-lifetime `ThreadPoolExecutor` has no explicit shutdown path in this plan (no `crewai` lifecycle hook is being introduced for it); this is acceptable for a no-op placeholder but should be revisited once real (e.g. blocking I/O) processing work is added.
