"""Append missing real OSRM road recordings. Never invoked by tests/server.

Existing recordings and hashes are preserved byte-for-byte.
"""

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import django
import httpx

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fuelroute.settings")
django.setup()
from routing.geocoding import resolve_location  # noqa: E402
from routing.geometry import validate_endpoint_snaps  # noqa: E402
from routing.provider import CallCounts  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    folder = ROOT / "fixtures/routes"
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = folder / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
    )
    pairs = [
        ("Chicago", "IL", "Dallas", "TX"),
        ("Chicago", "IL", "Milwaukee", "WI"),
        ("New York", "NY", "Miami", "FL"),
        ("Los Angeles", "CA", "Denver", "CO"),
        ("Seattle", "WA", "San Francisco", "CA"),
    ]
    for origin, origin_state, city, state in pairs:
        start = resolve_location(f"{origin}, {origin_state}", CallCounts())["coordinates"]
        finish = resolve_location(f"{city}, {state}", CallCounts())["coordinates"]
        if any(e["start"] == start and e["finish"] == finish for e in manifest):
            print("Preserved", origin, city)
            continue
        pair = ";".join(",".join(str(v) for v in point) for point in (start, finish))
        url = f"https://router.project-osrm.org/route/v1/driving/{pair}?overview=full&geometries=geojson&steps=false"
        response = httpx.get(url, timeout=60)
        response.raise_for_status()
        raw = response.json()
        if raw["code"] != "Ok":
            raise ValueError(raw)
        road = raw["routes"][0]
        route = {
            "geometry": road["geometry"],
            "distance_meters": road["distance"],
            "duration_seconds": road["duration"],
            "provider": "osrm-public-demo-recording",
            "profile": "driving-car",
            "recorded": True,
            "attribution": "OSRM | OpenStreetMap contributors (ODbL)",
            "source_url": url,
            "recorded_at": datetime.now(UTC).isoformat(),
            "source_response_sha256": hashlib.sha256(response.content).hexdigest(),
            "snapped_waypoints": raw["waypoints"],
        }
        filename = f"{origin.lower().replace(' ', '-')}-{city.lower().replace(' ', '-')}.json"
        if (folder / filename).exists():
            filename = filename.replace(".json", "-reviewed-endpoint.json")
            # Retain the old file as historical evidence; use corrected endpoints in the active manifest.
            manifest = [
                e
                for e in manifest
                if e["file"]
                != f"{origin.lower().replace(' ', '-')}-{city.lower().replace(' ', '-')}.json"
            ]
        validate_endpoint_snaps(route, start, finish)
        (folder / filename).write_text(
            json.dumps(route, separators=(",", ":")) + "\n", encoding="utf-8"
        )
        manifest.append(
            {
                "start": start,
                "finish": finish,
                "file": filename,
                "sha256": hashlib.sha256((folder / filename).read_bytes()).hexdigest(),
            }
        )
        print(filename, road["distance"], len(road["geometry"]["coordinates"]))
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
