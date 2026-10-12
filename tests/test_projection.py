from types import SimpleNamespace

import pytest
from pyproj import Geod

from stations.locate import project_stations


def test_geodesic_projection_scaling_order_and_corridor():
    points = [[-100, 40], [-99, 40], [-98, 40]]
    g = Geod(ellps="WGS84")
    distance = sum(g.inv(*a, *b)[2] for a, b in zip(points, points[1:], strict=False))
    route = {
        "geometry": {"type": "LineString", "coordinates": points},
        "distance_meters": distance * 1.05,
    }
    stations = [
        SimpleNamespace(opis_id=str(i), longitude=lon, latitude=lat)
        for i, (lon, lat) in enumerate([(-99, 40), (-98.5, 40), (-99, 41)])
    ]
    projected = project_stations(route, stations, 5)
    assert len(projected) == 2
    assert projected[0][1] == pytest.approx(distance * 1.05 / 1609.344 / 2, rel=0.002)
    assert projected[1][1] > projected[0][1]
    assert projected[0][2] < 0.01


def test_zero_route_empty_candidates():
    assert (
        project_stations(
            {"geometry": {"coordinates": [[0, 0], [0, 0]]}, "distance_meters": 0}, [], 5
        )
        == []
    )
