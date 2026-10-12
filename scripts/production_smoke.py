"""Check the real durable DB locally; this is not public HTTP evidence."""

import json
import os
import time
from pathlib import Path

import django
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env.production", override=True)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fuelroute.settings")
django.setup()

from django.core.cache import cache  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

from stations.importer import active_dataset  # noqa: E402


def main():
    cache.clear()
    client = APIClient()
    rows = []
    bodies = [
        {"start": "Chicago, IL", "finish": "Dallas, TX"},
        {"start": "Chicago, IL", "finish": "Dallas, TX"},
        {"start": "Chicago, IL", "finish": "Dallas, TX", "initial_fuel_gallons": 45},
        {"start": "Chicago, IL", "finish": "Dallas, TX", "location_mode": "estimated"},
        {"start": "Chicago, IL", "finish": "Milwaukee, WI"},
        {"start": "New York, NY", "finish": "Miami, FL"},
        {"start": "Los Angeles, CA", "finish": "Denver, CO"},
        {"start": "Seattle, WA", "finish": "San Francisco, CA"},
        {"start": "Chicago, IL", "finish": "Toronto, ON"},
    ]
    for body in bodies:
        began = time.perf_counter()
        response = client.post("/api/v1/routes/optimize/", body, format="json", secure=True)
        data = response.json()
        route = data.get("route") or data.get("error", {}).get("details", {}).get("route")
        if response.status_code == 200:
            summary, vehicle = data["fuel_summary"], data["vehicle"]
            assert (
                abs(
                    vehicle["initial_fuel_gallons"]
                    + summary["gallons_purchased"]
                    - summary["gallons_consumed"]
                    - summary["end_fuel_gallons"]
                )
                < 1e-8
            )
            assert all(
                0
                <= s["fuel_before_purchase_gallons"]
                <= s["fuel_after_purchase_gallons"]
                <= vehicle["tank_capacity_gallons"] + 1e-8
                for s in data["fuel_stops"]
            )
        rows.append(
            {
                "request": body,
                "status": response.status_code,
                "wall_ms": round((time.perf_counter() - began) * 1000, 3),
                "geometry_coordinates": len(route["geometry"]["coordinates"]) if route else 0,
                "fuel_summary": data.get("fuel_summary"),
                "fuel_stops": len(data["fuel_stops"]) if "fuel_stops" in data else None,
                "meta": data.get("meta"),
                "error_code": data.get("error", {}).get("code"),
            }
        )
    assert [r["status"] for r in rows] == [200, 200, 200, 200, 200, 200, 200, 422, 422]
    assert rows[0]["meta"]["recorded_route_reads"] == 1
    assert all(r["meta"]["directions_api_calls"] == 0 for r in rows if r["meta"])
    assert all(rows[i]["meta"]["route_cache_hit"] for i in (1, 2, 3))
    dataset = active_dataset()
    report = {
        "scope": "Local Django APIClient over actual remote Neon PostgreSQL, production HTTPS settings; NOT a public hosted HTTP test",
        "dataset_revision": str(dataset.revision),
        "price_basis": dataset.price_basis,
        "rows": rows,
        "checks": {
            "fuel_conservation": "passed",
            "tank_bounds": "passed",
            "recorded_cache_reuse": "passed",
            "durable_dataset_seed": "passed",
        },
    }
    (ROOT / "artifacts/public/production-checks.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "statuses": [r["status"] for r in rows],
                "first_ms": rows[0]["wall_ms"],
                "warm_ms": rows[1]["wall_ms"],
                "scope": report["scope"],
            }
        )
    )


if __name__ == "__main__":
    main()
