"""Bounded real HTTPS verification; no server/provider credentials are needed."""

import argparse
import json
import re
import time
from decimal import Decimal
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    if not base.startswith("https://"):
        raise SystemExit("Use the actual public HTTPS host")
    results = []
    with httpx.Client(timeout=90, follow_redirects=False) as client:
        page = client.get(base + "/")
        page.raise_for_status()
        assets = re.findall(r'(?:src|href)="(/static/[^\"]+)"', page.text)
        asset_checks = []
        for path in assets:
            response = client.get(base + path)
            response.raise_for_status()
            asset_checks.append(
                {"path": path, "status": response.status_code, "bytes": len(response.content)}
            )
        health = client.get(base + "/api/v1/health/")
        health.raise_for_status()
        assert health.json()["routing_provider"] == "ors"

        def request(name, body, expected, *, raw=None):
            began = time.perf_counter()
            response = (
                client.post(base + "/api/v1/routes/optimize/", json=body)
                if raw is None
                else client.post(
                    base + "/api/v1/routes/optimize/",
                    content=raw,
                    headers={"Content-Type": "application/json"},
                )
            )
            wall = (time.perf_counter() - began) * 1000
            data = response.json()
            assert response.status_code in expected, (name, response.status_code, data.get("error"))
            route = data.get("route") or data.get("error", {}).get("details", {}).get("route")
            if response.status_code == 200:
                fuel, vehicle = data["fuel_summary"], data["vehicle"]
                assert (
                    abs(
                        vehicle["initial_fuel_gallons"]
                        + fuel["gallons_purchased"]
                        - fuel["gallons_consumed"]
                        - fuel["end_fuel_gallons"]
                    )
                    < 1e-8
                )
                assert (
                    abs(fuel["gallons_consumed"] - route["distance_miles"] / vehicle["mpg"]) < 1e-8
                )
                assert all(
                    0
                    <= s["fuel_before_purchase_gallons"]
                    <= s["fuel_after_purchase_gallons"]
                    <= vehicle["tank_capacity_gallons"] + 1e-8
                    for s in data["fuel_stops"]
                )
                exact = sum(
                    (Decimal(s["purchase_cost_unrounded_usd"]) for s in data["fuel_stops"]),
                    Decimal(0),
                )
                assert abs(exact - Decimal(fuel["total_refueling_spend_unrounded_usd"])) < Decimal(
                    "1e-20"
                )
                assert (
                    not route["recorded"]
                    and data["meta"]["price_basis"] == "illustrative_test_fixture"
                )
                for before, after in zip(
                    data["fuel_timeline"][1:-1:2], data["fuel_timeline"][2:-1:2], strict=True
                ):
                    assert before["mile_marker"] == after["mile_marker"]
                assert data["meta"]["directions_api_calls"] == (
                    0 if data["meta"]["route_cache_hit"] else 1
                )
            summary = {
                "name": name,
                "request": body,
                "http_status": response.status_code,
                "wall_ms": round(wall, 3),
                "fuel_summary": data.get("fuel_summary"),
                "stops": len(data["fuel_stops"]) if "fuel_stops" in data else None,
                "station_ids": [s["station_id"] for s in data.get("fuel_stops", [])],
                "location_quality": [s["location_precision"] for s in data.get("fuel_stops", [])],
                "road_miles": route.get("distance_miles") if route else None,
                "road_points": len(route["geometry"]["coordinates"]) if route else 0,
                "meta": data.get("meta"),
                "error_code": data.get("error", {}).get("code"),
                "error_message": data.get("error", {}).get("message"),
                "error_details": {
                    k: v
                    for k, v in data.get("error", {}).get("details", {}).items()
                    if k != "route"
                },
            }
            results.append(summary)
            print(
                json.dumps(
                    {
                        k: summary[k]
                        for k in (
                            "name",
                            "http_status",
                            "wall_ms",
                            "road_miles",
                            "stops",
                            "error_code",
                        )
                    }
                )
            )
            return data

        long = {"start": "Chicago, IL", "finish": "Dallas, TX"}
        request("long", long, [200])
        repeat = request("long-repeat", long, [200])
        assert repeat["meta"]["route_cache_hit"] and repeat["meta"]["directions_api_calls"] == 0
        for name, change in (
            ("changed-fuel", {"initial_fuel_gallons": 45}),
            ("estimated", {"location_mode": "estimated"}),
        ):
            data = request(name, {**long, **change}, [200])
            assert data["meta"]["route_cache_hit"] and data["meta"]["directions_api_calls"] == 0
        request(
            "short",
            {"start": "Chicago, IL", "finish": "Milwaukee, WI", "initial_fuel_cost_usd": "200.00"},
            [200],
        )
        for name, start, finish in (
            ("new-york-miami", "New York, NY", "Miami, FL"),
            ("la-denver", "Los Angeles, CA", "Denver, CO"),
            ("seattle-sf", "Seattle, WA", "San Francisco, CA"),
        ):
            request(name, {"start": start, "finish": finish}, [200, 422])
        request(
            "unseen-austin-houston", {"start": "Austin, TX", "finish": "Houston, TX"}, [200, 422]
        )
        request("foreign", {**long, "finish": "Toronto, ON"}, [422])
        request("malformed", None, [400], raw="{not-json}")
        address = {"start": "233 S Wacker Dr, Chicago, IL", "finish": "Milwaukee, WI"}
        request("precise-address", address, [200])
        geocoded_repeat = request("precise-address-repeat", address, [200])
        assert (
            geocoded_repeat["meta"]["geocoding_api_calls"] == 0
            and geocoded_repeat["meta"]["directions_api_calls"] == 0
        )
        far = {"start": "Key West, FL", "finish": "Prudhoe Bay, AK"}
        for i in range(2):
            unavailable = request(f"unsupported-distance-{i + 1}", far, [422])
            assert unavailable["meta"]["directions_api_calls"] == 1
        stats = client.get(base + "/api/v1/stats/").json()
        report = {
            "base_url": base,
            "scope": "Actual external HTTPS against Render, live ORS, public illustrative prices",
            "homepage_status": page.status_code,
            "assets": asset_checks,
            "health": health.json(),
            "security_headers": {
                k: page.headers.get(k)
                for k in (
                    "strict-transport-security",
                    "x-content-type-options",
                    "x-frame-options",
                    "referrer-policy",
                )
            },
            "rows": results,
            "stats": stats,
            "checks": {
                "fuel_accounting": "passed",
                "cash_sum": "passed",
                "capacity": "passed",
                "timeline_pairs": "passed",
                "cache_reuse": "passed",
                "geocoder_cache": "passed",
                "failure_not_cached": "passed",
            },
        }
        (ROOT / "artifacts/public/production-http.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
