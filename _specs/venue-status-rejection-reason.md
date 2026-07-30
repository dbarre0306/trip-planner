# Venue Status and Rejection Reason

branch: claude/feature/venue-status-rejection-reason

## Summary

Every processed venue currently carries a `status` field (default `"accepted"`) and a `rejection_reason` field (default `null`), but nothing in the pipeline ever sets them to anything other than their defaults. This feature adds the logic that actually decides, for each venue produced during venue processing, whether it should be `"accepted"` or `"rejected"`, and if rejected, why. This lets downstream consumers of the venue list (itinerary building, presentation, etc.) filter out venues that are closed, lack a website, or are duplicates of a more specific venue already in the list, without those consumers having to re-implement the same checks.

## User Story

As a trip planner user, I want venues that are closed, have no website, or are duplicates of another venue already in my results to be marked as rejected (with a reason), so that my itinerary is built only from venues that are actually worth visiting and aren't redundant.

## Acceptance Criteria

- [ ] By default, a venue's `status` is `"accepted"` and its `rejection_reason` is `null`.
- [ ] If a venue's notes contain any indication that the venue has closed (e.g. permanently closed, out of business, closed for the season with no reopening indicated, etc.), its `status` is `"rejected"` and its `rejection_reason` is `"closed"`.
- [ ] Otherwise, if a venue has no URL, its `status` is `"rejected"` and its `rejection_reason` is `"no website"`.
- [ ] Otherwise, if a venue describes the same real-world place as another venue in the same result list — determined by the same or a near-identical name (ignoring case, whitespace, and minor spelling variation), a matching website URL, and/or a matching street address or matching latitude/longitude — the two are treated as duplicates of each other regardless of whether they share the same `interest`.
- [ ] Among a group of duplicate venues, exactly one is kept accepted: the most specific one describing the real-world place (e.g. a restaurant inside a hotel is kept over the hotel itself). The most specific venue is still subject to its own closed/no-website checks — if it fails one of those checks, it is rejected for that reason rather than being kept as the accepted duplicate.
- [ ] The other venues in a duplicate group are rejected with `status` `"rejected"` and `rejection_reason` `"duplicate"`, unless they were already rejected for `"closed"` or `"no website"`, in which case that original reason is preserved.
- [ ] Rejected venues remain present in the venue list (they are not removed or hidden) — only their `status` and `rejection_reason` fields change.
- [ ] The rule order is: closed check first, then no-website check, then duplicate check — a venue is only evaluated for duplication if it isn't already rejected as closed or lacking a website.

## Scope

### In Scope

- Determining `status` and `rejection_reason` for every venue produced by venue processing, across the full set of venues generated for a trip.
- Detecting closed-venue indications from the venue's notes.
- Detecting missing website/URL.
- Detecting duplicate venues within the same result list by name similarity, URL match, and/or street address match.
- Choosing which venue in a duplicate group to keep accepted based on specificity.

### Out of Scope

- Deduplicating or cross-checking venues across different trips or different runs of the planner.
- Changing how venues are searched, looked up, or otherwise gathered.
- Removing rejected venues from the itinerary-building input, or any changes to how the itinerary builder consumes `status`/`rejection_reason`.
- Adding new fields to the venue model beyond the existing `status` and `rejection_reason`.
- Presentation/UI changes to show rejected venues or rejection reasons to the end user.

## UI / UX Notes

Not applicable — this feature only affects the data (`status` and `rejection_reason`) attached to each venue during processing. There is no direct user-facing surface changed by this feature.

## Testing

- Default case: a venue with no closed indication, a URL, and no duplicates in the list is `"accepted"` with `rejection_reason` `null`.
- Closed case: a venue whose notes mention it has closed is `"rejected"` / `"closed"`, even if it also has no URL or is a duplicate of another venue.
- No-website case: a venue with no URL (and no closed indication) is `"rejected"` / `"no website"`.
- Duplicate case, by name: two venues with the same or near-identical name (varying case/whitespace/minor spelling) are recognized as duplicates.
- Duplicate case, by URL: two venues with a matching website URL are recognized as duplicates even if names differ.
- Duplicate case, by address: two venues with a matching street address are recognized as duplicates even if names and URLs differ.
- Duplicate case, cross-interest: two venues describing the same real place but tagged with different `interest` values are still recognized as duplicates.
- Duplicate resolution/specificity: given a duplicate group containing a generic venue (e.g. a hotel) and a more specific venue inside it (e.g. the hotel's restaurant), the specific venue is kept `"accepted"` and the generic one is `"rejected"` / `"duplicate"`.
- Duplicate resolution with cascading reasons: if the most specific venue in a duplicate group is itself closed or has no website, it is rejected for that reason (not kept as the accepted duplicate), and the group's next-most-specific eligible venue is evaluated in its place.
- Reason precedence: a venue that is both closed and a duplicate is rejected as `"closed"`, not `"duplicate"`. A venue that has no website and is also a duplicate is rejected as `"no website"`, not `"duplicate"`.
- Multi-way duplicates: a group of three or more venues describing the same place resolves to exactly one accepted venue and the rest rejected as `"duplicate"`.

## Open Questions

- Is there existing guidance (in this codebase or elsewhere) on how "most specific" should be judged when it isn't as clear-cut as the hotel/restaurant example — e.g. two seemingly equally-specific venues that turn out to be the same place? Should ties fall back to list order, rating, or some other signal? There is no clear cut guidance. When a tie occurs, randomly select one of the venues.
- How reliable does "near-identical name, ignoring minor spelling variation" need to be — is a small edit-distance/fuzzy-match sufficient, or are there known tricky cases (e.g. translated names, franchise locations) this should also handle or explicitly not handle? what you have above is good enough.
- Should street address matching require an exact match, or should it tolerate formatting differences (e.g. "St" vs "Street", suite/unit numbers)? should tolerate formatting differences
- Notes are free-text snippets pulled from web search results — is there a defined list of "closed" phrases to recognize, or should this rely on general-purpose judgment of the notes' content? general-purpose judgement
