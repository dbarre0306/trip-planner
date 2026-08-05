from trip_planner.core.domain import InterestId
from trip_planner.core.models import GeoLocation, Venue
from trip_planner.consolidation.venue_geo_clustering import cluster_venues


def _venue(name: str, latitude: float | None = None, longitude: float | None = None) -> Venue:
    geo_location = GeoLocation(latitude=latitude, longitude=longitude) if latitude is not None else None
    return Venue(name=name, interest_id=InterestId.MUSEUMS, geo_location=geo_location)


def test_cluster_venues_groups_nearby_venues_together():
    north_a = _venue("North A", 40.0, -110.0)
    north_b = _venue("North B", 40.1, -110.0)
    south_a = _venue("South A", 10.0, -110.0)
    south_b = _venue("South B", 10.1, -110.0)

    clusters = cluster_venues([north_a, south_a, north_b, south_b], 2)

    assert len(clusters) == 2
    names_by_cluster = [{venue.name for venue in cluster} for cluster in clusters]
    assert {"South A", "South B"} in names_by_cluster
    assert {"North A", "North B"} in names_by_cluster


def test_cluster_venues_returns_requested_number_of_clusters():
    venues = [_venue(f"Venue {i}", float(i), 0.0) for i in range(6)]

    clusters = cluster_venues(venues, 3)

    assert len(clusters) == 3
    assert sum(len(cluster) for cluster in clusters) == len(venues)


def test_cluster_venues_distributes_unlocated_venues_round_robin():
    unlocated = [_venue(f"Mystery {i}") for i in range(4)]

    clusters = cluster_venues(unlocated, 2)

    assert len(clusters) == 2
    assert {venue.name for venue in clusters[0]} == {"Mystery 0", "Mystery 2"}
    assert {venue.name for venue in clusters[1]} == {"Mystery 1", "Mystery 3"}


def test_cluster_venues_handles_zero_clusters():
    assert cluster_venues([_venue("Solo", 1.0, 1.0)], 0) == []


def test_cluster_venues_handles_no_venues():
    clusters = cluster_venues([], 3)

    assert clusters == [[], [], []]
