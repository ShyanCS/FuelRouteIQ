"""Exercise actual local Django API/database and save measured evidence."""

import json
import os
import statistics
import time
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fuelroute.settings")
django.setup()

from django.conf import settings  # noqa: E402
from django.core.cache import cache  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    folder = ROOT / "artifacts"
    folder.mkdir(exist_ok=True)
    cache.clear()
    client = APIClient()
    reports = []
    for name, finish, mode in [
        ("long-strict", "Dallas, TX", "strict"),
        ("short-strict", "Milwaukee, WI", "strict"),
        ("long-repeat", "Dallas, TX", "strict"),
        ("long-estimated", "Dallas, TX", "estimated"),
    ]:
        body = {"start": "Chicago, IL", "finish": finish, "location_mode": mode}
        response = client.post("/api/v1/routes/optimize/", body, format="json")
        payload = response.json()
        (folder / f"{name}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        report = {
            "case": name,
            "http_status": response.status_code,
            "request": body,
            "meta": payload.get("meta"),
            "fuel_summary": payload.get("fuel_summary"),
            "stops": [
                {
                    k: s[k]
                    for k in (
                        "station_id",
                        "station_name",
                        "mile_marker",
                        "gallons_purchased",
                        "purchase_cost_usd",
                        "location_precision",
                    )
                }
                for s in payload.get("fuel_stops", [])
            ],
        }
        reports.append(report)
        print(json.dumps(report))
        if response.status_code != 200:
            raise RuntimeError(payload.get("error", {}).get("code", "API verification failed"))
    timings = []
    for _ in range(20):
        before = time.perf_counter()
        r = client.post(
            "/api/v1/routes/optimize/",
            {"start": "Chicago, IL", "finish": "Dallas, TX"},
            format="json",
        )
        assert r.status_code == 200 and r.json()["meta"]["directions_api_calls"] == 0
        timings.append((time.perf_counter() - before) * 1000)
    evidence = {
        "routing_provider": settings.ROUTING_PROVIDER,
        "scope": "Actual in-process Django APIClient and SQLite cache; price basis reported by dataset/API, not assumed; no live-provider latency claim in recorded mode",
        "cases": reports,
        "warm_cache_samples": 20,
        "warm_cache_median_wall_ms": statistics.median(timings),
        "warm_cache_max_wall_ms": max(timings),
        "warm_cache_min_wall_ms": min(timings),
        "stats": client.get("/api/v1/stats/").json(),
    }
    (folder / "verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in evidence.items() if k != "cases"}))


if __name__ == "__main__":
    main()
