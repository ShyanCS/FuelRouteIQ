import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal as D
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from rest_framework.test import APIClient

from api.accounting import fifo_valuation
from api.errors import PlanningError
from api.service import money
from optimizer.baseline import simulate_baseline
from optimizer.engine import optimize
from optimizer.schemas import Candidate, FuelGap, Plan, Purchase, Vehicle
from routing.geocoding import resolve_location
from routing.provider import CallCounts, request_json, validate_route
from stations.enrichment import import_verified
from stations.importer import import_cities, import_fuel
from stations.locate import project_stations
from tests.test_api import BODY, URL
from tests.test_optimizer import oracle


def test_fractional_inventory_against_independent_oracle():
    for seed in range(200):
        rng = random.Random(seed)
        cap, distance, initial = rng.randint(2, 12), rng.randint(0, 45), rng.randint(0, 2)
        stations = sorted(
            (p, rng.randint(1, 9))
            for p in rng.sample(range(distance + 1), min(rng.randint(0, 8), distance + 1))
        )
        expected = oracle(distance, stations, cap, initial)
        mpg, unit = D("3.333"), D("0.5")
        vehicle = Vehicle(mpg, D(cap) * mpg * unit, D(initial) * unit)
        nodes = [
            Candidate(str(i), "fractional test node", D(m) * mpg * unit, D(p))
            for i, (m, p) in enumerate(stations)
        ]
        if expected is None:
            with pytest.raises(FuelGap):
                optimize(D(distance) * mpg * unit, nodes, vehicle)
        else:
            plan = optimize(D(distance) * mpg * unit, nodes, vehicle)
            baseline = simulate_baseline(D(distance) * mpg * unit, nodes, vehicle)
            assert plan.spend == expected * unit and baseline.spend >= plan.spend
            assert all(0 <= p.before <= p.after <= vehicle.capacity for p in plan.purchases)


def test_fifo_value_distinguishes_inventory_and_cash():
    short = Plan((), D(10), D(40))
    value = fifo_valuation(short, D(50), D(200))
    assert money(value["economic_fuel_cost_usd"]) == "40.00"
    assert money(value["remaining_fuel_value_usd"]) == "160.00" and short.spend == 0
    assert fifo_valuation(short, D(50), None)["economic_fuel_cost_usd"] is None
    station = Candidate("test", "test", D(0), D(3))
    plan = Plan((Purchase(station, D(10), D(0), D(10), "test"),), D(10), D(0))
    assert fifo_valuation(plan, D(0), None)["economic_fuel_cost_usd"] == 30


@pytest.mark.django_db
def test_current_heigit_contract_and_cache_identity(prepared_db, mock_directions, settings):
    client = APIClient()
    assert client.post(URL, BODY, format="json").status_code == 200
    call = mock_directions.call_args
    assert (
        call.args[1] == "https://api.heigit.org/openrouteservice/v2/directions/driving-car/geojson"
    )
    assert call.kwargs["headers"]["Authorization"] == "test-key-never-a-real-credential"
    assert call.kwargs["follow_redirects"] is False
    assert call.kwargs["timeout"].connect == 5 and call.kwargs["timeout"].read == 20
    settings.ORS_API_BASE_URL = "https://api.heigit.org/explicit-test-endpoint"
    response = client.post(URL, BODY, format="json")
    assert response.status_code == 200 and response.data["meta"]["directions_api_calls"] == 1
    assert mock_directions.call_count == 2


@pytest.mark.django_db
def test_pelias_contract_and_cache(prepared_db, monkeypatch):
    mock = Mock(
        return_value=httpx.Response(
            200,
            json={
                "features": [
                    {
                        "geometry": {"coordinates": [-87.63, 41.88]},
                        "properties": {
                            "country_a": "USA",
                            "region_a": "IL",
                            "layer": "address",
                            "confidence": 0.95,
                        },
                    }
                ]
            },
        )
    )
    monkeypatch.setattr("httpx.request", mock)
    counts = CallCounts()
    resolve_location("100 Main St, Chicago, IL", counts)
    assert mock.call_args.args[1] == "https://api.heigit.org/pelias/v1/search"
    resolve_location("100 Main St, Chicago, IL", counts)
    assert counts.geocoding == 1 and counts.directions == 0


@pytest.mark.django_db
def test_gateway_quota_auth_redirect_and_error_classification(monkeypatch):
    cases = [
        (403, {"error": "Quota exceeded"}, {}, "PROVIDER_RATE_LIMIT"),
        (403, {"error": "Forbidden"}, {"x-ratelimit-remaining": "0"}, "PROVIDER_RATE_LIMIT"),
        (403, {"error": "Invalid API key"}, {}, "PROVIDER_AUTH_ERROR"),
        (302, {}, {"Location": "https://example.invalid"}, "PROVIDER_REDIRECT"),
        (400, {"error": {"code": 2009}}, {}, "ROUTE_LIMIT_OR_UNAVAILABLE"),
        (400, {"error": {"code": 2012}}, {}, "PROVIDER_REJECTED_REQUEST"),
    ]
    for status, payload, headers, code in cases:
        mock = Mock(return_value=httpx.Response(status, json=payload, headers=headers))
        monkeypatch.setattr("httpx.request", mock)
        counts = CallCounts()
        with pytest.raises(PlanningError) as error:
            request_json(
                "POST", "https://api.heigit.org/openrouteservice/test", counts, "directions"
            )
        assert error.value.payload["error"]["code"] == code
        assert mock.call_count == 1 and counts.directions == 1


def test_provider_summary_types_and_units():
    route = {
        "geometry": {"type": "LineString", "coordinates": [[-90, 35], [-90, 36]]},
        "distance_meters": 100,
        "duration_seconds": 5,
    }
    assert isinstance(validate_route(route)["distance_meters"], float)
    for bad in ("100", True, None):
        with pytest.raises(PlanningError):
            validate_route({**route, "distance_meters": bad})


@pytest.mark.django_db
def test_full_state_names_and_mode_share_geometry(prepared_db, mock_directions):
    client = APIClient()
    assert client.post(URL, BODY, format="json").status_code == 200
    response = client.post(
        URL,
        {
            "start": "Chicago, Illinois, USA",
            "finish": "Dallas, Texas",
            "location_mode": "estimated",
        },
        format="json",
    )
    assert response.status_code == 200 and response.data["meta"]["route_cache_hit"]
    assert response.data["meta"]["directions_api_calls"] == 0 and mock_directions.call_count == 1


@pytest.mark.django_db
def test_public_price_basis_and_economic_semantics(prepared_db, settings):
    settings.ROUTING_PROVIDER = "recorded"
    response = APIClient().post(
        URL,
        {"start": "Chicago, IL", "finish": "Milwaukee, WI", "initial_fuel_cost_usd": "200.00"},
        format="json",
    )
    assert response.status_code == 200
    summary = response.data["fuel_summary"]
    assert summary["total_refueling_spend_usd"] == "0.00"
    assert summary["economic_fuel_cost_usd"] == money(D(str(summary["gallons_consumed"])) * 4)
    assert response.data["meta"]["price_basis"] == "illustrative_test_fixture"
    assert response.data["warnings"][0].startswith("ILLUSTRATIVE")


@pytest.mark.django_db
def test_invalid_responses_are_not_cached(prepared_db, monkeypatch):
    mock = Mock(return_value=httpx.Response(200, json={"features": []}))
    monkeypatch.setattr("httpx.request", mock)
    for _ in range(2):
        response = APIClient().post(URL, BODY, format="json")
        assert response.status_code == 502 and not response.data["meta"]["route_cache_hit"]
    assert mock.call_count == 2


def test_repeated_route_passes_reject_ambiguous_marker():
    route = {
        "geometry": {
            "type": "LineString",
            "coordinates": [[-100, 40], [-99, 40], [-98, 41], [-100, 40], [-99, 40]],
        },
        "distance_meters": 500_000,
    }
    diagnostics = {}
    result = project_stations(
        route, [SimpleNamespace(opis_id="ambiguous", longitude=-99.5, latitude=40)], 5, diagnostics
    )
    assert result == [] and diagnostics["ambiguous_projection_rejections"] == 1


@pytest.mark.django_db
def test_missing_verification_id_requires_explicit_opt_in(prepared_db, tmp_path):
    entry = json.loads((settings.BASE_DIR / "data/reference/verified_stations.json").read_text())[0]
    entry["opis_id"] = "not-in-this-fixture"
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps([entry]))
    with pytest.raises(ValueError, match="not in"):
        import_verified(path)
    assert import_verified(path, skip_missing=True) == 0


@pytest.mark.django_db(transaction=True)
def test_concurrency_with_actual_database_cache(prepared_db, settings, monkeypatch):
    settings.CACHES = {
        "default": {
            "BACKEND": "routing.sqlite_cache.SQLiteDatabaseCache",
            "LOCATION": "phase2_concurrency_cache",
        }
    }
    call_command("createcachetable", stdout=StringIO())
    cache.clear()
    road = json.loads((settings.BASE_DIR / "fixtures/routes/chicago-dallas.json").read_text())
    entered, release = threading.Event(), threading.Event()

    def request(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return httpx.Response(
            200,
            json={
                "features": [
                    {
                        "geometry": road["geometry"],
                        "properties": {
                            "summary": {
                                "distance": road["distance_meters"],
                                "duration": road["duration_seconds"],
                            }
                        },
                    }
                ]
            },
        )

    mock = Mock(side_effect=request)
    monkeypatch.setattr("httpx.request", mock)

    def send():
        from django.db import connections

        try:
            r = APIClient().post(URL, BODY, format="json")
            return r.status_code, r.json()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=4) as pool:
        pending = [pool.submit(send) for _ in range(4)]
        assert entered.wait(5)
        release.set()
        results = [f.result(timeout=20) for f in pending]
    assert all(status == 200 for status, _ in results), results
    assert mock.call_count == 1
    assert sum(p["meta"]["directions_api_calls"] for _, p in results) == 1
    assert len({p["fuel_summary"]["total_refueling_spend_usd"] for _, p in results}) == 1


@pytest.mark.django_db
def test_five_real_recordings_and_honest_coverage(settings):
    settings.ROUTING_PROVIDER = "recorded"
    import_cities(settings.BASE_DIR / "data/reference/census_places.txt")
    import_fuel(settings.BASE_DIR / "fixtures/public_demo_prices.csv")
    import_verified(settings.BASE_DIR / "data/reference/verified_stations.json")
    from scripts.validate_matrix import PAIRS

    for start, finish in PAIRS:
        for mode in ("strict", "estimated"):
            r = APIClient().post(
                URL, {"start": start, "finish": finish, "location_mode": mode}, format="json"
            )
            p = r.json()
            route = p.get("route") or p["error"]["details"]["route"]
            assert route["recorded"] and len(route["geometry"]["coordinates"]) > 1000
            assert p["meta"]["directions_api_calls"] == p["meta"]["geocoding_api_calls"] == 0
            if start.startswith("Seattle"):
                assert r.status_code == 422 and p["error"]["code"] == "UNREACHABLE_FUEL_GAP"
                assert p["error"]["details"]["plan_available"] is False
            else:
                assert r.status_code == 200, p
                f = p["fuel_summary"]
                assert (
                    abs(50 + f["gallons_purchased"] - f["gallons_consumed"] - f["end_fuel_gallons"])
                    < 1e-8
                )


@pytest.mark.django_db
def test_separate_route_keys_and_per_request_work_times(prepared_db, mock_directions):
    client = APIClient()
    first = client.post(URL, BODY, format="json")
    assert first.status_code == 200 and first.data["meta"]["optimizer_duration_ms"] >= 0
    repeat = client.post(URL, BODY, format="json")
    assert repeat.data["meta"]["optimizer_duration_ms"] == 0
    assert repeat.data["meta"]["projection_duration_ms"] == 0
    assert repeat.data["meta"]["directions_request_duration_ms"] == 0
    assert (
        repeat.data["meta"]["projection_diagnostics"]
        == first.data["meta"]["projection_diagnostics"]
    )
    reversed_route = client.post(
        URL, {"start": "Dallas, TX", "finish": "Chicago, IL"}, format="json"
    )
    assert reversed_route.data["meta"]["directions_api_calls"] == 1
    assert not reversed_route.data["meta"]["route_cache_hit"]
    assert mock_directions.call_count == 2
