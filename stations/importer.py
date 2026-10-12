import csv
import hashlib
import json
import uuid
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median

from django.db import transaction

from stations.models import City, Dataset, SourceRow, Station
from stations.normalization import CANADIAN_STATES, US_STATES, city_key, clean

HEADERS = {
    "OPIS Truckstop ID",
    "Truckstop Name",
    "Address",
    "City",
    "State",
    "Rack ID",
    "Retail Price",
}


def coverage(dataset):
    return dict(
        Counter(
            Station.objects.filter(dataset=dataset).values_list("location_precision", flat=True)
        )
    )


def active_dataset():
    return Dataset.objects.order_by("-created_at", "-id").first()


@transaction.atomic
def import_cities(path):
    source_path = Path(path).with_name("census_source.json")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != source["text_sha256"]:
        raise ValueError("Census data checksum does not match its source manifest")
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(
        text.splitlines(), delimiter="|" if "|" in text.splitlines()[0] else "\t"
    )
    records = []
    for row in reader:
        row = {k.strip(): v.strip() for k, v in row.items()}
        if row["USPS"] in US_STATES:
            records.append(
                City(
                    geoid=row["GEOID"],
                    name=clean(row["NAME"]),
                    key=city_key(row["NAME"]),
                    state=row["USPS"],
                    latitude=float(row["INTPTLAT"]),
                    longitude=float(row["INTPTLONG"]),
                    source=source["url"],
                )
            )
    City.objects.all().delete()
    City.objects.bulk_create(records, batch_size=500)
    # Refresh city fallbacks only. Verified provenance must never be overwritten.
    dataset = active_dataset()
    if dataset:
        attach_city_locations(dataset)
        dataset.revision = uuid.uuid4()
        dataset.report["location_coverage"] = coverage(dataset)
        dataset.save(update_fields=["revision", "report"])
    return len(records)


def city_index():
    index = defaultdict(list)
    for c in City.objects.all():
        index[(c.key, c.state)].append(c)
    return index


def attach_city_locations(dataset):
    index = city_index()
    stations = list(
        Station.objects.filter(dataset=dataset).exclude(location_precision="verified_station")
    )
    for station in stations:
        matches = index.get((city_key(station.city), station.state), [])
        station.latitude = station.longitude = None
        station.source, station.location_precision, station.match_confidence = (
            "",
            "unresolved",
            "unresolved",
        )
        if len(matches) == 1 and not station.identity_conflict:
            city = matches[0]
            station.latitude, station.longitude = city.latitude, city.longitude
            station.source, station.location_precision = city.source, "approximate_city"
            station.match_confidence = "exact_city_state_match_only"
    Station.objects.bulk_update(
        stations,
        ["latitude", "longitude", "source", "location_precision", "match_confidence"],
        batch_size=500,
    )


@transaction.atomic
def import_fuel(path, *, reuse=False):
    path = Path(path)
    price_basis = "assessment_snapshot"
    manifest_path = path.with_suffix(".source.json")
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["sha256"]:
            raise ValueError("Price fixture checksum does not match its manifest")
        price_basis = manifest["price_basis"]
        if price_basis not in {"assessment_snapshot", "illustrative_test_fixture"}:
            raise ValueError("Unsupported price basis")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    current = active_dataset()
    if reuse and current and current.sha256 == digest and current.price_basis == price_basis:
        return current
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not HEADERS.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"Required CSV columns missing: {sorted(HEADERS)}")
        rows = list(reader)
    dataset = Dataset.objects.create(
        source_name=path.name,
        sha256=digest,
        price_basis=price_basis,
    )
    grouped, all_prices = defaultdict(list), defaultdict(set)
    raw_records = []
    counts = Counter(source_rows=len(rows))
    for number, raw in enumerate(rows, 2):
        row = {k: clean(v) for k, v in raw.items()}
        state = row["State"].upper()
        counts["exit_address_rows"] += "EXIT" in row["Address"].upper()
        counts["us_source_rows" if state in US_STATES else "non_us_source_rows"] += 1
        counts["canadian_source_rows"] += state in CANADIAN_STATES
        reason = ""
        try:
            price = Decimal(row["Retail Price"])
            if (
                not price.is_finite()
                or not Decimal(0) < price < Decimal("10000000")
                or price.as_tuple().exponent < -10
            ):
                raise ValueError("Price must be finite, positive, and fit 10 decimal places")
            if row["OPIS Truckstop ID"]:
                all_prices[row["OPIS Truckstop ID"]].add(price)
            if state not in US_STATES:
                reason = "NON_US_RECORD"
            elif any(
                not row[k] for k in ["OPIS Truckstop ID", "Truckstop Name", "Address", "City"]
            ):
                reason = "MISSING_IDENTITY_FIELD"
            else:
                grouped[row["OPIS Truckstop ID"]].append((row, price))
        except (InvalidOperation, ValueError, TypeError):
            reason = "INVALID_PRICE"
        counts["rejected_rows"] += bool(reason)
        raw_records.append(
            SourceRow(dataset=dataset, row_number=number, raw=raw, rejection_reason=reason)
        )
    SourceRow.objects.bulk_create(raw_records, batch_size=500)
    stations = []
    for identity, observations in grouped.items():
        prices = [p for _, p in observations]
        mid = median(prices)
        representative = min(set(prices), key=lambda p: (abs(p - mid), p))
        # Stable source-row tie break; preserve aliases in raw observations.
        row = observations[0][0]
        localities = {(city_key(r["City"]), r["State"].upper()) for r, _ in observations}
        stations.append(
            Station(
                dataset=dataset,
                opis_id=identity,
                name=row["Truckstop Name"],
                address=row["Address"],
                city=row["City"],
                state=row["State"].upper(),
                price=representative,
                price_min=min(prices),
                price_max=max(prices),
                price_conflict=len(set(prices)) > 1,
                identity_conflict=len(localities) > 1,
                source_row_count=len(observations),
            )
        )
    Station.objects.bulk_create(stations, batch_size=500)
    attach_city_locations(dataset)
    counts["distinct_all_ids"] = len(all_prices)
    counts["deduped_us_ids"] = len(stations)
    counts["conflicting_price_ids_all"] = sum(len(v) > 1 for v in all_prices.values())
    counts["conflicting_price_ids_us"] = sum(s.price_conflict for s in stations)
    counts["identity_conflicts_us"] = sum(s.identity_conflict for s in stations)
    dataset.report = {
        **dict(counts),
        "location_coverage": coverage(dataset),
        "price_policy": "observed price closest to median; lower observed price breaks ties",
        "sha256": dataset.sha256,
        "price_basis": price_basis,
    }
    dataset.save(update_fields=["report"])
    return dataset
