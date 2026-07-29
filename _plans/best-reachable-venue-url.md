# Plan: Best Reachable Venue URL Selection

spec: _specs/best-reachable-venue-url.md

## Summary

`lookup_venue` in `serper_lookup.py` currently assigns a venue's `url` by walking Serper's `organic` results in ranking order and taking the first link whose HEAD request succeeds — with no judgment about whether that link is the venue's own site versus its Instagram, a Yelp/TripAdvisor listing, or some other reachable-but-wrong page. This plan adds an LLM-driven ranking step, in a new `venue_url_selection.py` module: the LLM is given every candidate link and snippet for a venue and returns them all sorted from most likely to least likely to be that venue's official website. `lookup_venue` then walks that LLM-ordered list (backfilled with any candidate the LLM's response omitted, so nothing is silently dropped) and uses the existing reachability check to take the first one that actually responds — falling back to today's exact "first reachable in Serper's original order" behavior whenever the LLM call errors or returns nothing usable, so the feature can only improve URL quality, never make a working venue lookup fail.

## Assumptions

- Per the spec's resolved open questions: the LLM is given the full candidate list (all `organic` results, up to Serper's max of ~10, each with its link and snippet) in one call, and returns all of them reordered from most to least likely to be official — not a single pick, and not a subset.
- No tool-calling / function-calling is involved. The LLM only ever reasons over the venue name, destination, and the candidates' links + snippets already in hand; the existing HEAD-request reachability check (`_is_reachable`) remains a purely code-side step applied after ranking, exactly as it works today — it's just applied in the LLM's order instead of Serper's.
- The LLM's returned list is validated against the actual candidate links before use: any entry it invents that wasn't in the original results is dropped (hallucination guard), and duplicates are collapsed to their first occurrence.
- Because the LLM might omit a candidate it was given (rather than including all of them), `lookup_venue` appends any original candidate missing from the validated ranking to the end, in Serper's original order, before walking the list. This guarantees every original candidate is still eventually eligible for the reachability check, so "no candidate reachable" still means the same thing it does today.
- If the LLM call raises an exception, or its response can't be parsed into any usable ranking at all, the validated ranking is treated as empty — which, combined with the backfill above, makes the walked order identical to today's Serper order, so the fallback requirement (AC5) falls out of the same code path rather than needing a separate branch.
- No candidates (`results == []`) skips the LLM call entirely, matching current behavior where reachability checks are also skipped in that case.

## Files to Change

- `src/trip_planner/venue_url_selection.py` — new module. Builds the prompt (venue name, destination, and every candidate as its link + snippet), calls the existing `chat_completion` wrapper, parses the response into a list of URLs, and validates it against the original candidates (drop hallucinated entries, dedupe). Exposes `rank_urls(name, destination, results) -> list[str]`, returning the validated, possibly-partial ranking (empty list if nothing usable was parsed).
- `src/trip_planner/serper_lookup.py` — `lookup_venue` calls `rank_urls` (wrapped in try/except) after fetching search results, backfills any omitted original candidates onto the end of the ranking in their original order, and walks that combined list with the existing `_is_reachable` check, stopping at the first reachable URL. `notes` construction and `_is_reachable` itself are untouched.
- `tests/test_venue_url_selection.py` — new test file covering prompt content and response parsing/validation for `rank_urls` in isolation (mocked `chat_completion`).
- `tests/test_serper_lookup.py` — update/extend to cover LLM-driven ranking (including a non-first-ranked pick winning because an earlier one is unreachable), the hallucination/omission backfill, LLM-error fallback, and the zero-results skip case, while preserving unrelated existing tests (notes collection, missing API key, HTTP error propagation).

## Implementation Steps

1. Create `venue_url_selection.py`:
   - Add prompt-building logic that lists every candidate as its link plus snippet, gives the venue name and destination as context, and instructs the LLM to sort **all** of the given URLs from most likely to least likely to be the venue's own official website — preferring the venue's own domain over social media (Instagram, Facebook), review/directory/aggregator sites (Yelp, TripAdvisor, Google Maps listings, etc.) — and to respond with ONLY a JSON object of the form `{"urls": ["<most likely>", "<next>", ...]}`.
   - Add a small JSON-object parser for the response, following the same tolerant pattern already used in `venue_details.py` (strips fenced code blocks, returns `{}` on decode failure).
   - After parsing, validate the `urls` value: keep only entries that are non-empty strings exactly matching one of the input candidates' links, in the order given, dropping anything else (hallucinated entries) and collapsing duplicates to their first occurrence. If `urls` is missing, not a list, or nothing survives validation, return an empty list.
   - `rank_urls(name, destination, results)` returns the validated (possibly partial or empty) list. Let any exception from the underlying `chat_completion` call propagate — the caller in `serper_lookup.py` is responsible for catching it.

2. Update `lookup_venue` in `serper_lookup.py`:
   - Keep `_get_serper_search_results`, `_is_reachable`, and the `notes` construction exactly as they are.
   - If `results` is empty, keep today's behavior: `url = None`, no reachability checks, no LLM call.
   - If `results` is non-empty: collect `original_links` (the candidates' links, in Serper's original order, skipping any missing `link` field — same set the current loop iterates over). Call `rank_urls(name, destination, results)` inside a try/except; on any exception, treat the result as `[]`.
   - Build `search_order` as the validated ranking followed by any `original_links` not already present in it, preserving original order for that remainder (this is a no-op concatenation when the ranking is empty, naturally reducing to today's order).
   - Walk `search_order` and return the first URL for which `_is_reachable` is `True`; if none are reachable, `url` stays `None` — identical in outcome to today's behavior in both the "LLM failed" and "nothing reachable" cases.

3. Add `tests/test_venue_url_selection.py` covering:
   - The prompt/context passed to `chat_completion` includes the venue name, destination, and every candidate's link and snippet.
   - A well-formed `{"urls": [...]}` response listing all candidates in some order resolves to that same order.
   - A response that includes a URL not among the candidates resolves to the list with that entry dropped (hallucination guard).
   - A response that omits one of the candidates resolves to the partial list containing only what was returned (backfill is `serper_lookup.py`'s responsibility, not `rank_urls`'s).
   - A response with duplicate URLs resolves to each appearing only once, at its first position.
   - A non-JSON, malformed-JSON, or missing-`urls`-key response resolves to `[]`.
   - A response wrapped in a fenced code block (` ```json ... ``` `) is still parsed correctly, mirroring `venue_details.py`'s handling.

4. Update `tests/test_serper_lookup.py`:
   - Replace/extend `test_lookup_venue_picks_first_reachable_result` and `test_lookup_venue_skips_unreachable_result_for_later_reachable_one` so they mock `rank_urls` and assert that `lookup_venue` walks its order rather than Serper's raw order — e.g. the LLM ranks a later-listed official domain above an earlier-listed Instagram link, and that official domain is chosen even though it wasn't first in `results`.
   - Add a test where `rank_urls`'s top choice is unreachable but a lower-ranked one is reachable: assert the lower-ranked one is used.
   - Add a test where `rank_urls` returns a partial list (omits a candidate that turns out to be the only reachable one): assert `lookup_venue` still finds and uses it via the backfilled remainder.
   - Add a test where `rank_urls` raises an exception: assert `lookup_venue` falls back to first-reachable-in-Serper-order, matching today's exact behavior.
   - Confirm `test_lookup_venue_handles_zero_results` still passes with `rank_urls` asserted as not called.
   - Leave the notes-collection, missing-`SERPER_API_KEY`, and HTTP-error-propagation tests unchanged since those code paths aren't touched.

5. Run `uv run pytest` to confirm the full suite passes.

## Testing

- New unit tests in `test_venue_url_selection.py` isolate prompt construction and response parsing/validation (including the hallucination guard and duplicate collapsing) with a mocked `chat_completion`, without touching real network calls.
- Updated `test_serper_lookup.py` tests cover: LLM ranking reordering which candidate is tried first; falling through to a lower-ranked reachable candidate when the top one is unreachable; the backfill path when the LLM's list is partial; falling back to Serper's original order when `rank_urls` errors; zero results skipping the LLM call and reachability checks entirely. Existing tests for notes collection, missing API key, and HTTP error propagation continue to pass unmodified.
- `uv run pytest` run at the end to confirm no regressions across the suite.

## Risks / Open Questions

- The prompt's guidance on "official vs. non-official" sources is instructional text for the LLM, not a hardcoded domain blocklist — actual ranking quality depends on the model's judgment and is only deterministically testable via mocked responses.
- Every non-empty-results venue lookup now costs one additional LLM call (for the ranking); no caching of rankings is in scope (per spec), so repeated runs for the same venue re-incur this cost.
- Reachability is still checked one URL at a time in the walked order (same as today), so a venue with many unreachable high-ranked candidates before a reachable low-ranked one still costs multiple HEAD requests — no change from current behavior, just a different order to walk in.
