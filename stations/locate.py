import math

import numpy as np
from pyproj import Geod, Transformer
from shapely import LineString, Point, STRtree

from routing.provider import METERS_PER_MILE


def project_stations(route, stations, corridor_miles, diagnostics=None):
    """Albers metric nearest-segment search plus WGS84 cumulative distances.

    Segment fraction maps onto geodesic distance, scaled to provider road miles.
    Off-route distance is geodesic to projected centerline, never routed detour.
    Albers EPSG:5070 is for CONUS; other regions use local azimuthal equidistant.
    """
    coords = np.asarray(route["geometry"]["coordinates"], dtype=float)[:, :2]
    diagnostics = diagnostics if diagnostics is not None else {}
    diagnostics.update({"ambiguous_projection_rejections": 0, "outside_corridor_rejections": 0})
    if route["distance_meters"] == 0:
        return []
    # Conservative bounding prefilter only; never used to validate US membership.
    margin_lat = corridor_miles * METERS_PER_MILE / 100_000 + 0.01
    max_lat = min(89.5, max(abs(coords[:, 1].min()), abs(coords[:, 1].max())) + margin_lat)
    margin_lon = min(180, margin_lat / max(0.001, math.cos(math.radians(max_lat))))
    bounds = {
        "latitude__gte": float(coords[:, 1].min() - margin_lat),
        "latitude__lte": float(coords[:, 1].max() + margin_lat),
        "longitude__gte": float(coords[:, 0].min() - margin_lon),
        "longitude__lte": float(coords[:, 0].max() + margin_lon),
    }
    if hasattr(stations, "filter"):
        stations = stations.filter(**bounds)
    lon0, lat0 = np.mean(coords, axis=0)
    crs = (
        "EPSG:5070"
        if np.all(
            (coords[:, 0] > -126) & (coords[:, 0] < -66) & (coords[:, 1] > 24) & (coords[:, 1] < 50)
        )
        else f"+proj=aeqd +lat_0={lat0} +lon_0={lon0} +datum=WGS84 +units=m"
    )
    transform = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    inverse = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    x, y = transform.transform(coords[:, 0], coords[:, 1])
    projected = np.column_stack([x, y])
    geod = Geod(ellps="WGS84")
    lengths = geod.inv(coords[:-1, 0], coords[:-1, 1], coords[1:, 0], coords[1:, 1])[2]
    cumulative = np.concatenate([[0], np.cumsum(lengths)])
    if cumulative[-1] <= 0:
        raise ValueError("Positive route distance requires non-degenerate geometry")
    segments = [LineString([projected[i], projected[i + 1]]) for i in range(len(coords) - 1)]
    tree = STRtree(segments)
    results = []
    for station in stations:
        point = Point(*transform.transform(station.longitude, station.latitude))
        indices = tree.query_nearest(point, all_matches=True)
        options = []
        for idx in indices:
            segment = segments[idx]
            fraction = segment.project(point, normalized=True) if segment.length else 0
            mile = (
                (cumulative[idx] + fraction * lengths[idx])
                / cumulative[-1]
                * route["distance_meters"]
                / METERS_PER_MILE
            )
            near = segment.interpolate(fraction, normalized=True)
            lon, lat = inverse.transform(near.x, near.y)
            lateral = geod.inv(station.longitude, station.latitude, lon, lat)[2] / METERS_PER_MILE
            options.append((mile, lateral))
        if not options:
            continue
        mile, lateral = min(options)
        if lateral > corridor_miles:
            diagnostics["outside_corridor_rejections"] += 1
            continue
        # Include near-ties within 25 metric meters, not just exact floating ties.
        # A site alongside two widely separated route visits has no trusted marker.
        best_distance = min(segments[idx].distance(point) for idx in indices)
        nearby = tree.query(point.buffer(best_distance + 25))
        mile_options = [m for m, _ in options]
        for idx in nearby:
            segment = segments[idx]
            if segment.distance(point) <= best_distance + 25:
                fraction = segment.project(point, normalized=True) if segment.length else 0
                mile_options.append(
                    (cumulative[idx] + fraction * lengths[idx])
                    / cumulative[-1]
                    * route["distance_meters"]
                    / METERS_PER_MILE
                )
        if max(mile_options) - min(mile_options) > 1:
            diagnostics["ambiguous_projection_rejections"] += 1
            continue
        results.append((station, float(mile), float(lateral)))
    return sorted(results, key=lambda s: (s[1], s[0].opis_id))
