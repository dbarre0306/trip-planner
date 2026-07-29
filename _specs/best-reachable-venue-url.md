# Best Reachable Venue URL Selection

branch: claude/feature/best-reachable-venue-url

## Summary

Today, venue URL selection (`lookup_venue` in `serper_lookup.py`) walks the Serper search results in ranking order and picks the first link that responds successfully to a reachability check, with no judgment about whether that link is actually the venue's own website. This means a venue's Instagram profile, a Yelp/TripAdvisor listing, a directory page, or an unrelated reachable link can win over the venue's real homepage simply because it was ranked higher or checked first. This feature changes the selection so an LLM sorts all candidate URLs from most likely to least likely to be the venue's official website, and the system then walks that LLM-ordered list and uses the first one that is actually reachable — so the itinerary links out to the venue's real site whenever one is available and reachable in the search results.

## User Story

As a trip planner user, I want each venue's link to point to that venue's actual official website (not a social media profile or a review/directory listing), so that I can trust the link to give me authoritative, up-to-date information about the venue.

## Acceptance Criteria

- [ ] When venue search results contain multiple candidate URLs, the system asks the LLM to sort all candidate URLs from most likely to least likely to be the venue's own official website, rather than automatically taking the first reachable result in Serper's ranking order.
- [ ] After the LLM returns its sorted list, the system walks that list in order and selects the first URL that is verified reachable; unreachable candidates are skipped even if the LLM ranked them highest.
- [ ] If the LLM's sorted list includes a URL that wasn't part of the original candidates, or omits one it was given, the system does not lose track of any original candidate — hallucinated entries are ignored and any omitted candidate is still eventually eligible for the reachability check.
- [ ] Common non-official sources (e.g. Instagram, Facebook, Yelp, TripAdvisor, Google Maps listings, generic directory/aggregator sites) are ranked below a candidate that looks like the venue's own domain, when both are present.
- [ ] If no candidate is reachable, or there are no candidates at all, venue processing behaves the same as it does today (no URL is set, and processing does not fail because of the missing URL).
- [ ] If the LLM call for URL ranking fails or errors, venue processing falls back to today's behavior (first reachable result in Serper's original ranking order) rather than failing the whole venue lookup.
- [ ] The existing `notes` behavior (collecting all snippets regardless of URL selection) is unchanged.

## Scope

### In Scope

- Changing how the "best" URL is chosen among the candidate links returned for a venue by Serper search.
- Using the LLM (via the existing `openai_client.chat_completion` wrapper) to sort all candidate URLs from most to least likely to be the venue's official site, based on venue name, destination, and the candidate URLs/snippets.
- Preserving the existing reachability check (HEAD request, treated as reachable on non-error status codes) as a hard requirement, applied by walking the LLM's sorted list in order and taking the first reachable one.
- Graceful fallback to the current "first reachable in order" behavior if the LLM ranking step fails, times out, or returns no usable answer.

### Out of Scope

- Changing how venues or search queries are generated upstream (`serper_places.py`, `venue_processing.py` candidate generation).
- Changing the reachability check mechanism itself (e.g. switching from HEAD to GET, retry logic, timeout tuning).
- Validating or scoring content on the page beyond the URL/domain and existing search snippet (no page-content fetching/analysis).
- Any UI/display changes for how the venue URL is shown to the end user.
- Caching or persisting LLM URL-selection decisions across runs.

## UI / UX Notes

Not applicable — this is a backend data-quality change to `lookup_venue`'s URL selection; there is no UI surface affected. The end-visible effect is that the `url` field on a `Venue` is more likely to point to the venue's real homepage.

## Testing

- Unit tests for the new URL-ranking logic covering: a mix of official-looking and non-official (Instagram/Yelp/etc.) candidate URLs where the official one should be ranked first; cases where the LLM's top-ranked candidate is unreachable and the walk should move on to the next-ranked reachable candidate instead; cases where no candidates are reachable (result has no URL); cases where the LLM call raises/errors and the code falls back to first-reachable-in-order; cases where the LLM's list includes a hallucinated URL not among the candidates, or omits a candidate it was given; the case of zero search results.
- Confirm existing `test_serper_lookup.py` behaviors that must still hold (e.g. `notes` collection, missing `SERPER_API_KEY` raising, HTTP errors propagating from the search request) continue to pass or are updated to reflect the new selection strategy.
- Confirm reachability checks stop as soon as a reachable URL is found while walking the ordered list (no unnecessary HEAD requests past the first success), matching the spirit of current tests around call counts.

## Open Questions

- Should the LLM be given the full list of candidate URLs (with snippets) and asked to rank them, or should reachability be checked first and only reachable candidates passed to the LLM for a "which is official" judgment? Resolved: give the LLM the full list with snippets and have it return all of them sorted from most likely to least likely to be the venue's official site; the system then walks that sorted list and uses the first reachable URL.
- Is there a maximum number of candidate URLs/snippets worth sending to the LLM (e.g. cap at top N Serper results) to control prompt size and cost? Resolved: there can only be a max of 10 URLs/snippets so send all of them.
