import csv
import json
from unittest.mock import Mock

import httpx
import pytest
from django.conf import settings
from django.core.cache import cache

from stations.enrichment import import_verified
from stations.importer import import_fuel
from stations.models import City
from stations.normalization import city_key


@pytest.fixture(autouse=True)
def isolated_cache(settings, monkeypatch):
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "tests"}
    }
    settings.ORS_API_KEY = "test-key-never-a-real-credential"
    settings.ROUTING_PROVIDER = "ors"
    cache.clear()

    # Tests must opt into MockTransport / monkeypatch rather than use the network.
    def blocked(*args, **kwargs):
        raise AssertionError("Unexpected external request from an offline test")

    monkeypatch.setattr("httpx.request", blocked)
    yield
    cache.clear()


@pytest.fixture
def prepared_db():
    wanted = {
        (city_key(n), s)
        for n, s in [
            ("Chicago", "IL"),
            ("Dallas", "TX"),
            ("Milwaukee", "WI"),
            ("Bloomington", "IL"),
            ("Sullivan", "MO"),
            ("Atoka", "OK"),
            ("Hayti", "MO"),
            ("West Memphis", "AR"),
            ("Benton", "AR"),
        ]
    }
    source = json.loads((settings.BASE_DIR / "data/reference/census_source.json").read_text())[
        "url"
    ]
    with (settings.BASE_DIR / "data/reference/census_places.txt").open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter="|"):
            if (city_key(row["NAME"]), row["USPS"]) in wanted:
                City.objects.create(
                    geoid=row["GEOID"],
                    name=row["NAME"],
                    key=city_key(row["NAME"]),
                    state=row["USPS"],
                    latitude=float(row["INTPTLAT"]),
                    longitude=float(row["INTPTLONG"]),
                    source=source,
                )
    dataset = import_fuel(settings.BASE_DIR / "fixtures/public_unit_prices.csv")
    import_verified(settings.BASE_DIR / "data/reference/verified_stations.json", skip_missing=True)
    return dataset


@pytest.fixture
def mock_directions(monkeypatch):
    route = json.loads((settings.BASE_DIR / "fixtures/routes/chicago-dallas.json").read_text())
    mock = Mock(
        return_value=httpx.Response(
            200,
            json={
                "features": [
                    {
                        "geometry": route["geometry"],
                        "properties": {
                            "summary": {
                                "distance": route["distance_meters"],
                                "duration": route["duration_seconds"],
                            }
                        },
                    }
                ]
            },
        )
    )
    monkeypatch.setattr("httpx.request", mock)
    return mock
