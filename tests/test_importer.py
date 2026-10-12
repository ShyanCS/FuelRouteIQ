import csv
import json
from decimal import Decimal

import pytest
from django.conf import settings

from stations.enrichment import import_verified
from stations.importer import HEADERS, import_cities, import_fuel
from stations.models import SourceRow, Station

pytestmark = pytest.mark.django_db


def write_csv(tmp_path, values):
    path = tmp_path / "fuel.csv"
    headers = sorted(HEADERS)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for values_row in values:
            writer.writerow(
                {
                    "OPIS Truckstop ID": "1",
                    "Truckstop Name": "  Station   One ",
                    "Address": "I-44, EXIT 1",
                    "City": " Chicago ",
                    "State": "IL",
                    "Rack ID": "1",
                    "Retail Price": "3.1",
                    **values_row,
                }
            )
    return path


def test_observed_median_tie_normalization_and_raw_audit(tmp_path):
    dataset = import_fuel(
        write_csv(tmp_path, [{"Retail Price": p} for p in ["3.1", "3.2", "3.3", "3.4"]])
    )
    s = Station.objects.get(dataset=dataset)
    assert s.price == Decimal("3.2")  # median 3.25 never fabricated
    assert s.price_conflict and s.source_row_count == 4
    assert s.price_min == Decimal("3.1") and s.price_max == Decimal("3.4")
    assert s.name == "Station One" and s.city == "Chicago"
    assert SourceRow.objects.first().raw["Truckstop Name"] == "  Station   One "


@pytest.mark.parametrize("price", ["0", "-1", "NaN", "Infinity", "", "not-money"])
def test_invalid_prices_preserved_rejected(tmp_path, price):
    dataset = import_fuel(write_csv(tmp_path, [{"Retail Price": price}]))
    assert not Station.objects.filter(dataset=dataset).exists()
    assert SourceRow.objects.get(dataset=dataset).rejection_reason == "INVALID_PRICE"


def test_non_us_and_identity_conflict(tmp_path):
    dataset = import_fuel(
        write_csv(
            tmp_path,
            [{}, {"City": "Dallas", "State": "TX"}, {"OPIS Truckstop ID": "2", "State": "ON"}],
        )
    )
    assert dataset.report["canadian_source_rows"] == 1
    assert Station.objects.get(dataset=dataset).identity_conflict
    assert Station.objects.get(dataset=dataset).location_precision == "unresolved"


def test_exact_supplied_dataset_audit():
    path = settings.BASE_DIR / "data/raw/fuel-prices-for-be-assessment.csv"
    if not path.exists():
        pytest.skip("Private assessment CSV deliberately not bundled for distribution")
    report = import_fuel(path).report
    assert {
        k: report[k]
        for k in [
            "source_rows",
            "us_source_rows",
            "canadian_source_rows",
            "deduped_us_ids",
            "conflicting_price_ids_all",
            "exit_address_rows",
        ]
    } == {
        "source_rows": 8151,
        "us_source_rows": 7531,
        "canadian_source_rows": 620,
        "deduped_us_ids": 6626,
        "conflicting_price_ids_all": 597,
        "exit_address_rows": 4617,
    }
    assert SourceRow.objects.count() == 8151


def test_census_index_and_verified_evidence(tmp_path):
    import_cities(settings.BASE_DIR / "data/reference/census_places.txt")
    dataset = import_fuel(
        write_csv(
            tmp_path,
            [
                {
                    "OPIS Truckstop ID": "4563",
                    "Truckstop Name": "PILOT TRAVEL CENTER #299",
                    "City": "Bloomington",
                    "Address": "I-55, EXIT 160",
                }
            ],
        )
    )
    evidence = json.loads(
        (settings.BASE_DIR / "data/reference/verified_stations.json").read_text()
    )[0]
    path = tmp_path / "verified.json"
    path.write_text(json.dumps([evidence]))
    old_revision = dataset.revision
    assert import_verified(path) == 1
    station = Station.objects.get(dataset=dataset)
    assert station.location_precision == "verified_station" and station.verified_at
    dataset.refresh_from_db()
    assert dataset.revision != old_revision
    evidence["city"] = "Dallas"
    path.write_text(json.dumps([evidence]))
    with pytest.raises(ValueError, match="locality"):
        import_verified(path)
