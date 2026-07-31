# Plan: Venue Estimated Costs

spec: _specs/venue-estimated-costs.md

## Summary

Add two nullable USD fields to `Venue` — `estimated_cost_per_adult` and `estimated_cost_per_child` — and generate their values with a new LLM-backed estimator, following the same pattern already used for `generate_description` and `estimate_duration_minutes`. The estimator is fed the destination plus the venue's name, description, interest, notes, and tags, and is instructed to return 0 for free venues, a plausible USD ticket price otherwise, or `null` if it can't produce a confident estimate. This estimator is wired into `process_venue` for web-sourced venues and, because the spec requires meal placeholders to go through the same flow, `STANDARD_VENUES` is converted from a static module-level list into a per-destination builder function so Breakfast/Lunch/Dinner also get real, destination-aware cost estimates instead of being skipped.

## Assumptions

- Both new fields are `float | None` values in USD, defaulting to `None` (per the spec's resolved open questions: nullable, USD). No currency field is added since multi-currency is explicitly out of scope.
- `None` is used only when the LLM can't produce a confident estimate at all — it is distinct from a confident `0` for a free venue. The estimator must not fall back to a guessed numeric default; an unparsable or missing response maps to `None` rather than a placeholder number.
- `STANDARD_VENUES` (Breakfast/Lunch/Dinner) currently has no destination context — it's a static list of shared `Venue` instances built once at import time and handed back as-is on every call. Since the spec requires meal venues to go through the same estimation flow, this module changes from a static list to a function that takes the destination and returns a freshly-copied, freshly-estimated `Venue` per call (never the same instances twice), so concurrent or repeated `process_venues` calls for different trips can't have one trip's mutations bleed into another's venues. This is a small architectural change beyond just adding two fields, called out here since it touches `process_venues` and existing tests that assert against the old `STANDARD_VENUES` constant.
- Cost estimation runs as its own LLM call (its own prompt/response cycle), consistent with how duration and description are separate calls today, rather than folding it into the existing `extract_venue_details` JSON extraction call. This keeps each estimator focused and independently testable, matching the existing file-per-concern layout (`venue_description.py`, `venue_details.py`, `venue_meal_tags.py`).
- Cost estimation for web-sourced venues happens after `description` and the final `tags` list (candidate tag + meal tags) are computed in `process_venue`, since both are part of the estimator's input context.

## Files to Change

- `src/trip_planner/models.py` — add `estimated_cost_per_adult: float | None = None` and `estimated_cost_per_child: float | None = None` to `Venue`.
- `src/trip_planner/venue_cost.py` — new module. Defines the LLM prompt-building and response-parsing logic for cost estimation, following the shape of `venue_details.py`'s `extract_venue_details` (JSON extraction with `null`-capable fields): a small dataclass result (`VenueCost` with `per_adult: float | None` / `per_child: float | None`), a prompt builder that includes destination, name, description, interest category, notes, and tags, and a JSON response parser that maps a missing, non-numeric, or explicit `null` value to `None` rather than any guessed numeric default.
- `src/trip_planner/venue_processing.py` — call the new estimator inside `process_venue` after `description`, `details`, and `tags` are known, and pass the resulting values into the returned `Venue`.
- `src/trip_planner/standard_venues.py` — convert `STANDARD_VENUES` from a static, directly-returned list into a function (e.g. `build_standard_venues(destination)`) that returns a fresh copy of each base Breakfast/Lunch/Dinner template (e.g. via `Venue.model_copy(deep=True, update={...})`) with cost fields populated by the same estimator, rather than reusing the same static instances across calls. `Venue` is not frozen and has mutable list fields (`tags`, `notes`), so returning the same shared instances on every call risks one trip's mutation leaking into another; each call must produce distinct objects.
- `src/trip_planner/venue_processing.py` (`process_venues`) — update the call site that currently appends the static `STANDARD_VENUES` constant to instead call `build_standard_venues(travel_info.destination)`.
- `tests/test_venue_cost.py` — new test file covering the new estimator module (prompt content, parsing, the `None`-on-unconfident-estimate case, zero-cost handling).
- `tests/test_venue_processing.py` — update existing `Venue(...)` assertions to account for the two new (nullable) fields, and update mocks/assertions around the `STANDARD_VENUES` → `build_standard_venues(...)` change.
- `tests/test_standard_venues.py` — update to call `build_standard_venues(destination)` instead of importing a static `STANDARD_VENUES` constant, and to account for the mocked cost estimator.

## Implementation Steps

1. Add `estimated_cost_per_adult` and `estimated_cost_per_child` (both `float | None`, default `None`) to the `Venue` model in `models.py`.
2. Create `venue_cost.py`: define the prompt instructions (destination, name, description, interest category, notes, tags as input; instruct the LLM to give realistic USD estimates, use 0 for free venues, and return `null` for either field only when it truly cannot produce a confident estimate), the response parser (mapping missing/non-numeric/`null` values to `None`), and the public estimation function (e.g. `estimate_venue_cost(name, interest_id, destination, description, notes, tags) -> VenueCost`).
3. Wire the estimator into `process_venue` in `venue_processing.py`: call it after `description`, `details`, and the merged `tags` list are computed, and pass `estimated_cost_per_adult`/`estimated_cost_per_child` into the constructed `Venue`.
4. Convert `standard_venues.py`'s `STANDARD_VENUES` constant into a `build_standard_venues(destination)` function: keep the three base venue templates (name/description/tags/duration, as today), but on each call return a deep copy of each template (e.g. `.model_copy(deep=True, update={...})`) with cost fields populated via the same estimator, so repeated calls never hand back the same object instances.
5. Update `process_venues` in `venue_processing.py` to call `build_standard_venues(travel_info.destination)` instead of referencing the old static list.
6. Add `tests/test_venue_cost.py` covering: prompt includes all expected inputs (destination, name, description, interest, notes, tags), successful parsing of a valid LLM response, zero-cost/free-venue handling, and that a malformed/unparsable or explicit-`null` LLM response results in `None` (not a guessed numeric value).
7. Update `tests/test_venue_processing.py` and `tests/test_standard_venues.py` to mock the new estimator, assert it's invoked with the correct inputs, and reflect the `build_standard_venues(destination)` signature change.
8. Run the full test suite (`uv run pytest`) and fix any remaining fallout from the new fields or the `STANDARD_VENUES` signature change.

## Testing

- Unit tests for `venue_cost.py`: correct prompt construction (destination, name, description, interest, notes, tags all present), correct parsing of a well-formed LLM response into `per_adult`/`per_child`, a free-venue case returning `0`, and a malformed/unparsable or explicit-`null` response resulting in `None` rather than raising or guessing a numeric value.
- Unit tests for `process_venue` in `test_venue_processing.py`: verify the returned `Venue` has both cost fields populated (including the `None` case) from a mocked estimator call, and that the estimator receives the destination plus the venue's name, description, interest, notes, and tags.
- Unit tests for `build_standard_venues(destination)` in `test_standard_venues.py`: verify Breakfast/Lunch/Dinner each get cost fields populated via the (mocked) estimator, that the destination is passed through, and that two separate calls return distinct `Venue` instances (e.g. `is not` identity checks) so mutating one call's result can't affect another's.
- Regression: full existing suite (`uv run pytest`) passes with the new fields present (populated or `None`) on every `Venue` produced anywhere in the codebase and tests.

## Risks / Open Questions

- Converting `STANDARD_VENUES` from a static constant to a function is a small API change beyond the spec's literal "add two properties" framing, but is necessary to satisfy the spec's explicit instruction that meal venues use the same estimation flow (an already-resolved open question in the spec). Flagging here since it touches an existing public name (`STANDARD_VENUES`) that other code/tests currently import directly.
- Because the two new fields default to `None`, existing direct `Venue(...)` construction sites outside the pipeline (ad hoc scripts, notebooks, other tests) continue to work unchanged — no forced update required at other call sites, only at the pipeline sites that should actively populate the fields (`process_venue`, `build_standard_venues`).
- A `None` cost is ambiguous between "the LLM couldn't estimate it" and "estimation hasn't run yet" (e.g. a `Venue` constructed directly in a test without going through the pipeline). Downstream consumers must treat `None` as "no estimate available" and not assume it means free/zero.
- LLM-based USD cost estimates are inherently approximate and may drift from real-world pricing for a given destination/venue; no accuracy guarantee beyond "plausible," consistent with how `estimate_duration_minutes` is already treated as a best-effort estimate rather than ground truth.
