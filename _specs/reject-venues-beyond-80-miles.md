# Reject Venues Beyond 80 Miles

branch: feature/reject-venues-beyond-80-miles

## Summary

Venue search results can occasionally include places that are geographically far from the requested destination (e.g. a same-named venue in a different city or region). This feature rejects any venue whose distance from the destination is 80 miles or more, using the Haversine formula to calculate the great-circle distance between the venue's location and the destination's location. This keeps the itinerary focused on venues a traveler could realistically visit.

## Acceptance Criteria

- [ ] A venue whose distance from the destination is 80 miles or more is marked as rejected rather than included as an accepted itinerary item.
- [ ] A venue whose distance from the destination is less than 80 miles is unaffected by this check and continues through the existing acceptance flow.
- [ ] A venue rejected for being too far away carries a rejection reason that clearly communicates the venue is outside the acceptable distance.
- [ ] Distance between the venue and the destination is calculated using the Haversine formula.
- [ ] The 80-mile threshold applies consistently to all venues regardless of interest/category.

## Scope

### In Scope

- Resolving the destination's coordinates via Serper for use in the distance calculation.
- Calculating the distance between a venue's location and the destination's location.
- Rejecting venues at or beyond the 80-mile threshold (a hard cutoff), with an appropriate rejection reason.
- Applying this distance check as part of the existing venue enrichment/acceptance flow.

### Out of Scope

- Changing the 80-mile threshold to be configurable per trip or per user.
- Changing how venues are searched for or discovered in the first place.
- Any UI changes to display distance information to the user.

## Testing

- Unit tests verifying the Haversine distance calculation itself (e.g. known coordinate pairs with known distances).
- Unit tests verifying a venue just under 80 miles from the destination is accepted (all else being valid).
- Unit tests verifying a venue at or over 80 miles from the destination is rejected with the correct rejection reason.
- Unit tests verifying venues at the destination itself (distance of zero) are unaffected by this check.

## Open Questions

None.
