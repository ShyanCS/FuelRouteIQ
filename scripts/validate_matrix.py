"""Actual representative-route API evidence; failures are data, not hidden skips."""

import json
import os
import statistics
import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fuelroute.settings")
django.setup()

from django.conf import settings  # noqa: E402
from django.core.cache import cache  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

PAIRS = [
    ("Chicago, IL", "Dallas, TX"),
    ("Chicago, IL", "Milwaukee, WI"),
    ("New York, NY", "Miami, FL"),
    ("Los Angeles, CA", "Denver, CO"),
    ("Seattle, WA", "San Francisco, CA"),
]


def capture_matrix(label=None):
    cache.clear()
    client = APIClient()
    basis = client.get("/api/v1/stats/").json().get("dataset") or {}
    label = label or (
        "recorded-illustrative"
        if basis.get("price_basis") == "illustrative_test_fixture"
        else "recorded-assessment"
    )
    rows = []
    for start, finish in PAIRS:
        for mode in ("strict", "estimated"):
            body = {"start": start, "finish": finish, "location_mode": mode}
            began = time.perf_counter()
            response = client.post("/api/v1/routes/optimize/", body, format="json")
            wall = (time.perf_counter() - began) * 1000
            payload = response.json()
            route = payload.get("route") or payload.get("error", {}).get("details", {}).get("route")
            row = {
                "start": start,
                "finish": finish,
                "mode": mode,
                "http_status": response.status_code,
                "real_road_geometry_obtained": bool(route),
                "geometry_evidence": "recorded_OSRM"
                if route and route.get("recorded")
                else "live_ORS"
                if route
                else "unavailable",
                "distance_miles": route.get("distance_miles") if route else None,
                "geometry_coordinate_count": len(route["geometry"]["coordinates"]) if route else 0,
                "feasible_plan": response.status_code == 200,
                "fuel_stop_count": len(payload.get("fuel_stops", []))
                if response.status_code == 200
                else None,
                "fuel_summary": payload.get("fuel_summary"),
                "location_quality": sorted(
                    {s["location_precision"] for s in payload.get("fuel_stops", [])}
                ),
                "candidate_count": payload.get("meta", {}).get(
                    "candidate_count",
                    payload.get("error", {}).get("details", {}).get("candidate_count"),
                ),
                "meta": payload.get("meta"),
                "error": {k: v for k, v in payload.get("error", {}).items() if k != "details"}
                or None,
                "coverage_gap": {
                    k: v
                    for k, v in payload.get("error", {}).get("details", {}).items()
                    if k != "route"
                }
                or None,
                "wall_duration_ms": wall,
            }
            rows.append(row)
            row["required_complete_route_fuel_gallons"] = (
                route.get("distance_miles", 0) / 10 if route else None
            )
            row["candidate_location_quality"] = payload.get("meta", {}).get(
                "candidate_location_quality",
                payload.get("error", {}).get("details", {}).get("eligible_location_quality", {}),
            )
            print(json.dumps({k: v for k, v in row.items() if k not in ("meta", "coverage_gap")}))
    verification = []
    for change in ({}, {"initial_fuel_gallons": 45}, {"location_mode": "estimated"}):
        payload = client.post(
            "/api/v1/routes/optimize/",
            {"start": "Chicago, IL", "finish": "Dallas, TX", **change},
            format="json",
        ).json()
        verification.append(
            {
                "change": change,
                "meta": payload.get("meta"),
                "error_code": payload.get("error", {}).get("code"),
            }
        )
    warm = []
    for _ in range(20):
        before = time.perf_counter()
        response = client.post(
            "/api/v1/routes/optimize/",
            {"start": "Chicago, IL", "finish": "Dallas, TX"},
            format="json",
        )
        warm.append((time.perf_counter() - before) * 1000)
        if response.json().get("meta", {}).get("directions_api_calls") != 0:
            raise AssertionError("Warm request unexpectedly made a directions call")
    evidence = {
        "label": label,
        "routing_provider": settings.ROUTING_PROVIDER,
        "scope": "Actual local APIClient/SQLite processing. Recorded rows have real road geometry but zero live ORS calls; network and algorithm durations are reported separately.",
        "stats": client.get("/api/v1/stats/").json(),
        "rows": rows,
        "reuse_checks": verification,
        "warm_samples": 20,
        "warm_median_wall_ms": statistics.median(warm),
        "warm_min_wall_ms": min(warm),
        "warm_max_wall_ms": max(warm),
    }
    folder = (
        settings.BASE_DIR
        / "artifacts"
        / (
            "private"
            if evidence["stats"].get("dataset", {}).get("price_basis") == "assessment_snapshot"
            else "public"
        )
    )
    folder.mkdir(parents=True, exist_ok=True)
    (folder / (label + "-matrix.json")).write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    print("Saved", folder / (label + "-matrix.json"))
    return evidence


if __name__ == "__main__":
    capture_matrix()
