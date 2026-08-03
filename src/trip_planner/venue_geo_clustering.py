from trip_planner.models import Venue


def cluster_venues(venues: list[Venue], num_clusters: int) -> list[list[Venue]]:
    """Groups venues into `num_clusters` geographically-contiguous groups.

    Venues with a `geo_location` are sorted by latitude/longitude and split into
    contiguous, evenly-sized chunks so that nearby venues land in the same group.
    Venues without a `geo_location` can't be clustered by proximity, so they're
    distributed round-robin across the resulting groups.
    """

    if num_clusters <= 0:
        return []

    clusters: list[list[Venue]] = [[] for _ in range(num_clusters)]

    located = sorted(
        (venue for venue in venues if venue.geo_location is not None),
        key=lambda venue: (venue.geo_location.latitude, venue.geo_location.longitude),
    )
    unlocated = [venue for venue in venues if venue.geo_location is None]

    for index, venue in enumerate(located):
        cluster_index = (index * num_clusters) // len(located)
        clusters[cluster_index].append(venue)

    for index, venue in enumerate(unlocated):
        clusters[index % num_clusters].append(venue)

    return clusters
