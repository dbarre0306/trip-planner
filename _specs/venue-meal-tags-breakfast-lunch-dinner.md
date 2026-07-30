# Venue Meal Tags (Breakfast, Lunch, Dinner)

branch: claude/feature/venue-meal-tags-breakfast-lunch-dinner

## Summary

Food-related venues currently carry no indication of which meal(s) they're suited for. This feature assigns each venue with a food-related interest (`restaurants`, `coffee shops`, or `street food and markets`) one or more meal-period tags — `breakfast`, `lunch`, and/or `dinner` — during venue processing. Coffee shops are always tagged `breakfast` only. For restaurants and street food & markets venues, notes are checked first — when they indicate which meal period(s) the venue serves or is known for, those are used directly. Hours of operation are also taken into account — for example, a restaurant open from 11 am to 11 pm clearly spans both lunch and dinner, even if its notes never say so explicitly. When neither notes nor hours settle the question, the LLM makes its best guess based on the kind of venue it is (street food & markets venues are never guessed as `breakfast`). This lets downstream itinerary building later slot these venues into the right part of the day without re-deriving that judgment from raw notes each time.

## User Story

As a trip planner user, I want each restaurant, coffee shop, and street food/market in my results to be tagged with the meal(s) it's appropriate for (breakfast, lunch, and/or dinner), so that my itinerary can place food visits at the right time of day.

## Acceptance Criteria

- [ ] Meal-period tags are assigned only to venues whose interest is `restaurants`, `coffee shops`, or `street food and markets`; venues with any other interest are unaffected by this feature.
- [ ] Every eligible venue is assigned at least one meal-period tag from `breakfast`, `lunch`, `dinner`.
- [ ] A venue may be assigned more than one meal-period tag when it's suited to multiple meals (e.g. a diner open for both breakfast and lunch, or a restaurant whose hours span lunch and dinner).
- [ ] A venue with interest `coffee shops` is always tagged `breakfast` only, regardless of its notes or hours of operation.
- [ ] For venues with interest `restaurants` or `street food and markets`, when notes explicitly indicate which meal period(s) the venue serves or is known for (e.g. "breakfast and brunch spot," "dinner only," "popular lunch spot"), those stated meal period(s) are used as the tag(s).
- [ ] For venues with interest `restaurants` or `street food and markets`, when hours of operation are known, they are also weighed when assigning tags — a venue open only during a window that clearly falls within a single meal period (e.g. 6 am–11 am) is tagged with just that period, and a venue whose hours span multiple meal periods (e.g. 11 am–11 pm spans lunch and dinner) is tagged with each period its hours cover.
- [ ] For venues with interest `restaurants` or `street food and markets`, when notes and hours of operation together indicate meal period(s), both signals are combined — a meal period is included in the tags if either the notes state it or the hours cover it.
- [ ] For venues with interest `restaurants` or `street food and markets`, when neither notes nor hours of operation indicate any meal period (e.g. hours are unknown or too ambiguous to map to a specific period), the meal-period tag(s) are determined by the LLM's best guess, based on general knowledge of the type of venue and any other available context.
- [ ] A venue with interest `street food and markets` is never tagged `breakfast`, whether from notes, hours, or best guess — only `lunch` and/or `dinner` apply.
- [ ] A venue with interest `restaurants` may be tagged with any combination of `breakfast`, `lunch`, and `dinner`.

## Scope

### In Scope

- Determining meal-period tag(s) for every venue with interest `restaurants`, `coffee shops`, or `street food and markets` produced during venue processing.
- Applying the fixed `breakfast`-only rule for `coffee shops` venues.
- Reading a venue's notes to detect explicitly stated meal period(s), for `restaurants` and `street food and markets` venues.
- Reading a venue's hours of operation to detect which meal period(s) they span, for `restaurants` and `street food and markets` venues.
- Combining notes-based and hours-based signals when both are available.
- Falling back to an LLM best-guess determination when neither notes nor hours indicate a meal period.
- Restricting `street food and markets` venues to `lunch` and/or `dinner` tags only, across all determination methods.
- Supporting a venue having multiple meal-period tags at once.

### Out of Scope

- Assigning meal-period tags to venues with any interest other than `restaurants`, `coffee shops`, or `street food and markets`.
- Any feature or behavior that consumes or filters on meal-period tags (e.g. itinerary scheduling by meal) — this spec only introduces and populates the tags.
- Changing how venues are searched, looked up, or otherwise gathered.
- Presentation/UI changes to display meal-period tags to the end user.
- Backfilling or migrating any previously processed venue data.

## UI / UX Notes

Not applicable — this is a data attribute added during venue processing with no direct user-facing surface.

## Testing

- Notes explicitly state a single meal period (e.g. "dinner only") — the venue is tagged with just that meal period.
- Notes explicitly state multiple meal periods (e.g. "serves breakfast and lunch") — the venue is tagged with all stated meal periods.
- Hours of operation span a single meal period (e.g. 6 am–11 am, with notes silent on meal period) — the venue is tagged with just that period.
- Hours of operation span multiple meal periods (e.g. 11 am–11 pm, with notes silent on meal period) — the venue is tagged with each period the hours cover (lunch and dinner).
- Notes and hours of operation agree — the resulting tags match both signals.
- Notes and hours of operation disagree or cover different periods (e.g. notes say "popular breakfast spot" but hours are 11 am–11 pm) — the resulting tags include the periods indicated by either signal.
- Notes contain no indication of meal period and hours of operation are unknown or too ambiguous to map to a specific period — the venue is tagged based on the LLM's best guess, and still ends up with at least one tag.
- A restaurant venue with no notes and no hours of operation at all still ends up with at least one meal-period tag via best guess.
- A `coffee shops` venue is tagged `breakfast` only, even when its notes mention lunch or its hours extend into the afternoon.
- A `street food and markets` venue with notes or hours suggesting breakfast-only hours is still not tagged `breakfast` — it resolves to `lunch` and/or `dinner`.
- A venue with an unrelated interest (e.g. `hiking`, `museums`) is not assigned any meal-period tags.

## Open Questions

- How should a "restaurant venue" be identified for the purpose of this feature — only venues whose interest is exactly "restaurants," or should closely related food interests (e.g. "street food and markets," "coffee shops") also qualify? coffee shops must always be tagged with breakfast only. "street food & markets" may be lunch and/or dinner. A "restuarant" interest can be any of the three types of meals.
- Should the meal-period tags be stored in the existing generic `tags` field on a venue, or as a new, dedicated field? existing tags
- What time ranges define the boundaries between breakfast, lunch, and dinner when mapping hours of operation to meal periods (e.g. where does breakfast end and lunch begin)? breakfast starts anytime from 6 am to 9 am. Lunch starts at 10 am. Dinner starts at 4 pm.
- Hours of operation are free-text (not a structured schedule) — how reliable does parsing them into meal-period coverage need to be, and how should irregular or unparseable hours (e.g. "hours vary," "by reservation only") be handled? best-effort is good enough. If it fails, then the LLM will do its best to determine the meal tags.
