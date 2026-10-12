"""Reject provider geometry silently snapped far from the requested endpoints."""

from pyproj import Geod

from api.errors import PlanningError


def validate_endpoint_snaps(route, start, finish, maximum_meters=1000):
    coordinates = route["geometry"]["coordinates"]
    distances = [
        Geod(ellps="WGS84").inv(*expected, *actual[:2])[2]
        for expected, actual in zip((start, finish), (coordinates[0], coordinates[-1]), strict=True)
    ]
    if any(distance > maximum_meters for distance in distances):
        raise PlanningError(
            "ENDPOINT_SNAP_TOO_FAR",
            "The road provider snapped an endpoint more than 1 km from its requested location. Supply a precise US street address or a reviewed city reference; this route will not be cached as valid.",
            422,
            {"endpoint_snap_distances_meters": distances, "maximum_snap_meters": maximum_meters},
        )
    return {**route, "endpoint_snap_distances_meters": distances}
