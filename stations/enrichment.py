import json
import math
import re
import uuid
from urllib.parse import urlparse

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from pyproj import Geod

from stations.importer import active_dataset, coverage
from stations.models import City, SourceRow, Station
from stations.normalization import city_key, clean


@transaction.atomic
def import_verified(path, skip_missing=False):
    """Import operator-reviewed evidence. Does not invent or auto-verify geocodes."""
    dataset = active_dataset()
    if dataset is None:
        raise ValueError("Import fuel prices first")
    entries = json.loads(path.read_text(encoding="utf-8"))
    aliases_by_id = {}
    for row in SourceRow.objects.filter(dataset=dataset).iterator():
        aliases_by_id.setdefault(clean(row.raw.get("OPIS Truckstop ID")), []).append(
            row.raw["Truckstop Name"].upper()
        )
    seen = set()
    for entry in entries:
        station = Station.objects.filter(dataset=dataset, opis_id=entry["opis_id"]).first()
        if station is None:
            if skip_missing:
                continue
            raise ValueError(
                f"Verification station {entry['opis_id']} is not in the active price dataset"
            )
        if station.opis_id in seen:
            raise ValueError("Duplicate verification ID")
        seen.add(station.opis_id)
        if (
            station.identity_conflict
            or city_key(station.city) != city_key(entry["city"])
            or station.state != entry["state"]
        ):
            raise ValueError("Verification locality does not match source identity")
        source = urlparse(entry["source"])
        if source.scheme != "https" or not source.hostname or not entry.get("review_notes"):
            raise ValueError("HTTPS provenance and human review notes are required")
        number = re.search(r"#\s*(\d+)", entry["station_name"])
        brand = (
            "FLYING"
            if "FLYING" in entry["station_name"].upper()
            else "PILOT"
            if "PILOT" in entry["station_name"].upper()
            else None
        )
        aliases = aliases_by_id.get(station.opis_id, [])
        if entry.get("source_city") and city_key(entry["source_city"]) != city_key(station.city):
            raise ValueError(
                "Official source locality differs; resolve the match explicitly before importing"
            )
        if (
            not number
            or not brand
            or not any(
                brand in name and re.search(r"#\s*" + number[1] + r"\b", name) for name in aliases
            )
        ):
            raise ValueError("Station brand/number does not match any source alias")
        road = entry.get("road_context", "").upper()
        if not road or not any(
            token in station.address.upper() for token in re.findall(r"(?:I|US|SR)-\d+", road)
        ):
            raise ValueError("Road context must match a source road token")
        lat, lon = float(entry["latitude"]), float(entry["longitude"])
        if (
            not math.isfinite(lat)
            or not math.isfinite(lon)
            or not -90 <= lat <= 90
            or not -180 <= lon <= 180
        ):
            raise ValueError("Invalid coordinate")
        cities = list(City.objects.filter(key=city_key(station.city), state=station.state))
        if (
            len(cities) != 1
            or Geod(ellps="WGS84").inv(cities[0].longitude, cities[0].latitude, lon, lat)[2]
            > 50_000
        ):
            raise ValueError("Verification must be within 50 km of uniquely matched US locality")
        at = parse_datetime(entry["verified_at"])
        if at is None or timezone.is_naive(at) or at > timezone.now():
            raise ValueError("Verification requires a non-future timezone-aware timestamp")
        station.latitude, station.longitude = lat, lon
        station.location_precision = "verified_station"
        station.source, station.verified_at = entry["source"], at
        station.match_confidence = "reviewed_operator_brand_number_city_state_road"
        station.verification = entry
        station.save()
    dataset.revision = uuid.uuid4()
    dataset.report["location_coverage"] = coverage(dataset)
    dataset.save(update_fields=["revision", "report"])
    return len(seen)
