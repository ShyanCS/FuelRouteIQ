from decimal import Decimal
from unittest.mock import Mock

import httpx
import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from routing.geocoding import resolve_location
from routing.provider import CallCounts
from stations.models import Dataset, Station

pytestmark = pytest.mark.django_db
URL = "/api/v1/routes/optimize/"
BODY = {"start": "Chicago, IL", "finish": "Dallas, TX"}


def post(body):
    return APIClient().post(URL, body, format="json")


def test_live_adapter_cache_and_vehicle_changes(prepared_db, mock_directions):
    first = post(BODY)
    assert first.status_code == 200, first.data
    assert first.data["meta"]["directions_api_calls"] == 1
    assert first.data["meta"]["geocoding_api_calls"] == 0
    assert first.data["route"]["license"] == "CC-BY-SA-4.0"
    assert "HeiGIT" in first.data["route"]["attribution"]
    assert not first.data["meta"]["route_cache_hit"]
    assert len(first.data["fuel_stops"]) >= 2
    assert all(s["location_precision"] == "verified_station" for s in first.data["fuel_stops"])
    second = post(BODY)
    assert second.status_code == 200
    assert second.data["meta"]["directions_api_calls"] == 0
    assert second.data["meta"]["route_cache_hit"] and second.data["meta"]["optimization_cache_hit"]
    changed = post({**BODY, "initial_fuel_gallons": 45, "initial_fuel_cost_usd": "100.00"})
    assert changed.status_code == 200
    assert (
        changed.data["meta"]["route_cache_hit"]
        and not changed.data["meta"]["optimization_cache_hit"]
    )
    summary = changed.data["fuel_summary"]
    assert float(summary["gallons_purchased"]) + 45 - summary["gallons_consumed"] == pytest.approx(
        summary["end_fuel_gallons"]
    )
    assert summary["initial_fuel_value_usd"] == "100.00"
    assert (
        Decimal(summary["total_acquired_fuel_value_usd"])
        == Decimal(summary["total_refueling_spend_usd"]) + 100
    )
    assert mock_directions.call_count == 1
    call = mock_directions.call_args
    assert call.args[0] == "POST" and call.args[1].endswith("/v2/directions/driving-car/geojson")


def test_recorded_real_geometry_long_short_and_timeline(prepared_db, settings):
    settings.ROUTING_PROVIDER = "recorded"
    long = post(BODY)
    assert long.status_code == 200, long.data
    assert (
        long.data["route"]["recorded"] and len(long.data["route"]["geometry"]["coordinates"]) > 9000
    )
    assert long.data["meta"]["directions_api_calls"] == 0
    assert long.data["meta"]["recorded_route_reads"] == 1
    for before, after in zip(
        long.data["fuel_timeline"][1:-1:2], long.data["fuel_timeline"][2:-1:2], strict=True
    ):
        assert before["mile_marker"] == after["mile_marker"]
        assert after["fuel_gallons"] > before["fuel_gallons"]
    short = post({"start": "Chicago, IL", "finish": "Milwaukee, WI"})
    assert short.status_code == 200
    assert short.data["fuel_summary"]["total_refueling_spend_usd"] == "0.00"
    assert short.data["fuel_summary"]["gallons_consumed"] > 0
    assert short.data["fuel_summary"]["initial_fuel_value_usd"] is None
    assert short.data["fuel_summary"]["total_acquired_fuel_value_usd"] is None
    Dataset.objects.all().delete()
    no_prices = post({"start": "Chicago, IL", "finish": "Milwaukee, WI"})
    assert no_prices.status_code == 200
    assert no_prices.data["meta"]["price_basis"] == "unavailable"
    assert no_prices.data["fuel_summary"]["total_refueling_spend_usd"] == "0.00"
    assert "No fuel-price dataset" in no_prices.data["warnings"][0]


def test_strict_coverage_gap_estimated_mode(prepared_db, mock_directions):
    Station.objects.all().update(location_precision="approximate_city")
    strict = post(BODY)
    assert strict.status_code == 422
    assert strict.data["error"]["code"] == "UNREACHABLE_FUEL_GAP"
    assert strict.data["error"]["details"]["candidate_count"] == 0
    estimated = post({**BODY, "location_mode": "estimated"})
    assert estimated.status_code == 200
    assert estimated.data["meta"]["directions_api_calls"] == 0
    assert "conditional_estimate" in estimated.data["meta"]["optimality_scope"]
    assert any("ESTIMATED" in w for w in estimated.data["warnings"])


@pytest.mark.parametrize(
    "body,status",
    [
        ({}, 400),
        ({**BODY, "initial_fuel_gallons": 51}, 400),
        ({**BODY, "initial_fuel_gallons": -1}, 400),
        ({**BODY, "mpg": "NaN"}, 400),
        ({**BODY, "range_miles": 501}, 400),
        ({**BODY, "location_mode": "fake"}, 400),
        ({**BODY, "unknown": True}, 400),
        ({**BODY, "finish": "Toronto, ON"}, 422),
        ({**BODY, "finish": "Paris, France"}, 422),
        ({**BODY, "finish": "Paris, TX"}, 422),
        ({**BODY, "finish": [-73, 45]}, 400),
    ],
)
def test_bad_inputs(prepared_db, body, status):
    response = post(body)
    assert response.status_code == status
    assert "error" in response.data


@pytest.mark.parametrize(
    "status,code,expected",
    [
        (429, "PROVIDER_RATE_LIMIT", 429),
        (500, "PROVIDER_FAILURE", 502),
        (401, "PROVIDER_AUTH_ERROR", 503),
        (400, "PROVIDER_REJECTED_REQUEST", 502),
    ],
)
def test_provider_errors(prepared_db, monkeypatch, status, code, expected):
    mock = Mock(return_value=httpx.Response(status, json={"error": {"code": 999}}))
    monkeypatch.setattr("httpx.request", mock)
    response = post(BODY)
    assert response.status_code == expected
    assert response.data["error"]["code"] == code
    assert response.data["meta"]["directions_api_calls"] == 1
    assert mock.call_count == 1


def test_timeout_no_retry_or_error_cache(prepared_db, monkeypatch):
    mock = Mock(side_effect=httpx.ReadTimeout("test timeout"))
    monkeypatch.setattr("httpx.request", mock)
    for _ in range(2):
        response = post(BODY)
        assert response.status_code == 503
        assert response.data["error"]["code"] == "PROVIDER_TIMEOUT"
        assert response.data["meta"]["directions_api_calls"] == 1
    assert mock.call_count == 2


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"features": []},
        {
            "features": [
                {
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {"summary": {"distance": 10, "duration": 1}},
                }
            ]
        },
    ],
)
def test_malformed_provider(prepared_db, monkeypatch, payload):
    monkeypatch.setattr("httpx.request", Mock(return_value=httpx.Response(200, json=payload)))
    response = post(BODY)
    assert (
        response.status_code == 502
        and response.data["error"]["code"] == "INVALID_PROVIDER_RESPONSE"
    )


def test_identical_endpoints_no_external_call(prepared_db):
    response = post({"start": "Chicago, IL", "finish": "Chicago, IL"})
    assert response.status_code == 200
    assert response.data["route"]["distance_miles"] == 0
    assert response.data["meta"]["directions_api_calls"] == 0


def test_address_geocoding_counts_cached_and_country_verified(prepared_db, monkeypatch):
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
    assert counts.geocoding == 1 and counts.directions == 0
    cached = resolve_location("100 Main St, Chicago, IL", counts)
    assert cached["cache_hit"] and counts.geocoding == 1
    cache.clear()
    mock.return_value = httpx.Response(
        200,
        json={
            "features": [
                {
                    "geometry": {"coordinates": [-79, 43]},
                    "properties": {"country_a": "CAN", "region_a": "ON"},
                }
            ]
        },
    )
    from api.errors import PlanningError

    with pytest.raises(PlanningError, match="outside"):
        resolve_location("100 Main St, Chicago, IL", CallCounts())


def test_health_stats_and_page(prepared_db):
    client = APIClient()
    assert client.get("/api/v1/health/").data["django_version"] == "6.1.2"
    assert client.get("/api/v1/stats/").data["location_coverage"]["verified_station"] == 6
    assert client.get("/").status_code == 200


def test_wrong_method_and_malformed_json(prepared_db):
    client = APIClient()
    assert client.get(URL).status_code == 405
    assert client.post(URL, "{broken", content_type="application/json").status_code == 400
