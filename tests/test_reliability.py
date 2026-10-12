import json
from decimal import Decimal as D
from io import StringIO
from unittest.mock import Mock

import httpx
import pytest
from django.conf import settings
from django.core.management import call_command
from rest_framework.test import APIClient

from api.errors import PlanningError
from optimizer.engine import optimize
from optimizer.schemas import Candidate, Vehicle
from routing.provider import CallCounts, ORSProvider, request_json, validate_route
from tests.test_api import BODY, URL


@pytest.mark.parametrize("bad", [D(-1), D("Infinity"), D("NaN")])
def test_bad_core_distance(bad):
    with pytest.raises(ValueError):
        optimize(bad, [])


@pytest.mark.parametrize("mile,price", [("-1", "3"), ("501", "3"), ("1", "0"), ("1", "NaN")])
def test_bad_core_station(mile, price):
    with pytest.raises(ValueError):
        optimize(D(500), [Candidate("test", "synthetic test station", D(mile), D(price))])


@pytest.mark.parametrize("mpg", ["3", "7", "3.333", "19.125"])
def test_fractional_efficiency_conserves_fuel(mpg):
    v = Vehicle(mpg=D(mpg), range_miles=D(500), initial=D(0))
    stations = [
        Candidate("a", "synthetic test A", D(0), D("3.123456789")),
        Candidate("b", "synthetic test B", D(400), D("2.123456789")),
    ]
    plan = optimize(D(850), stations, v)
    assert abs(plan.bought - plan.consumed - plan.end_fuel) < D("1e-20")
    assert all(p.before >= 0 and p.after <= v.capacity for p in plan.purchases)


@pytest.mark.parametrize(
    "distance,points",
    [
        (1, [[-90, 35], [-90, 35]]),
        (0, [[-90, 35], [-90, 36]]),
        (1, [[-90, 95], [-90, 35]]),
        (float("nan"), [[-90, 35], [-90, 36]]),
    ],
)
def test_invalid_provider_geometry(distance, points):
    with pytest.raises(PlanningError) as error:
        validate_route(
            {
                "geometry": {"type": "LineString", "coordinates": points},
                "distance_meters": distance,
                "duration_seconds": 1,
            }
        )
    assert error.value.status_code == 502


def test_route_too_long():
    with pytest.raises(PlanningError) as error:
        validate_route(
            {
                "geometry": {"type": "LineString", "coordinates": [[-90, 35], [-90, 36]]},
                "distance_meters": 6_000_001,
                "duration_seconds": 1,
            }
        )
    assert error.value.status_code == 422


@pytest.mark.django_db
@pytest.mark.parametrize(
    "response,code",
    [
        (httpx.Response(200, text="not-json"), "INVALID_PROVIDER_RESPONSE"),
        (httpx.Response(400, json={"error": "bad"}), "PROVIDER_REJECTED_REQUEST"),
        (httpx.Response(400, json={"error": {"code": 2004}}), "ROUTE_LIMIT_OR_UNAVAILABLE"),
    ],
)
def test_non_json_and_variant_provider_errors(monkeypatch, response, code):
    monkeypatch.setattr("httpx.request", Mock(return_value=response))
    counts = CallCounts()
    with pytest.raises(PlanningError) as error:
        request_json("POST", "https://example.invalid", counts, "directions")
    assert error.value.payload["error"]["code"] == code
    assert counts.directions == 1


@pytest.mark.django_db
def test_connection_failure(monkeypatch):
    monkeypatch.setattr(
        "httpx.request", Mock(side_effect=httpx.ConnectError("synthetic offline error"))
    )
    with pytest.raises(PlanningError) as error:
        ORSProvider().directions([-90, 35], [-90, 36], CallCounts())
    assert error.value.status_code == 503


@pytest.mark.django_db
def test_dataset_enrichment_invalidates_plan_only(prepared_db, mock_directions):
    client = APIClient()
    assert client.post(URL, BODY, format="json").status_code == 200
    prepared_db.refresh_from_db()
    import uuid

    prepared_db.revision = uuid.uuid4()
    prepared_db.save()
    response = client.post(URL, BODY, format="json")
    assert response.status_code == 200
    assert response.data["meta"]["route_cache_hit"]
    assert not response.data["meta"]["optimization_cache_hit"]
    assert mock_directions.call_count == 1


@pytest.mark.django_db
def test_management_commands_reproducible():
    output = StringIO()
    call_command("import_locations", "--cities", stdout=output)
    call_command(
        "import_fuel", str(settings.BASE_DIR / "fixtures/public_unit_prices.csv"), stdout=output
    )
    call_command(
        "import_locations",
        "--verified",
        str(settings.BASE_DIR / "data/reference/verified_stations.json"),
        skip_missing=True,
        stdout=output,
    )
    assert "Imported 6 locations" in output.getvalue()
    assert '"source_rows": 12' in output.getvalue()


@pytest.mark.django_db
def test_zero_initial_fuel_value_rejected(prepared_db):
    response = APIClient().post(
        URL, {**BODY, "initial_fuel_gallons": 0, "initial_fuel_cost_usd": 5}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_missing_key_is_honest_and_does_not_make_calls(prepared_db, settings):
    settings.ORS_API_KEY = ""
    response = APIClient().post(URL, BODY, format="json")
    assert response.status_code == 503
    assert response.data["meta"]["directions_api_calls"] == 0


@pytest.mark.django_db
def test_route_cache_expiration_key_reloads_provider(prepared_db, mock_directions, settings):
    settings.ROUTE_CACHE_TTL_SECONDS = 0
    client = APIClient()
    assert client.post(URL, BODY, format="json").status_code == 200
    # A zero TTL expires geometry immediately; the plan has its independent TTL.
    response = client.post(URL, BODY, format="json")
    assert response.status_code == 200 and response.data["meta"]["directions_api_calls"] == 1
    assert mock_directions.call_count == 2


def test_recording_integrity():
    import hashlib

    folder = settings.BASE_DIR / "fixtures/routes"
    for entry in json.loads((folder / "manifest.json").read_text()):
        content = (folder / entry["file"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == entry["sha256"]
        route = json.loads(content)
        assert route["source_url"].startswith("https://router.project-osrm.org/route/v1/driving/")
        assert route["recorded_at"] and route["source_response_sha256"]


@pytest.mark.django_db
def test_unexpected_failure_does_not_expose_traceback_or_secret(prepared_db, monkeypatch):
    monkeypatch.setattr(
        "api.views.run_planning", Mock(side_effect=RuntimeError("synthetic-private-detail"))
    )
    response = APIClient().post(URL, BODY, format="json")
    assert response.status_code == 500 and response.data["error"]["code"] == "INTERNAL_ERROR"
    assert response.data["error"]["details"]["request_id"]
    assert (
        b"Traceback" not in response.content and b"synthetic-private-detail" not in response.content
    )


@pytest.mark.django_db
def test_oversized_json_has_structured_error(prepared_db):
    response = APIClient().post(
        URL, json.dumps({**BODY, "extra": "x" * 17000}), content_type="application/json"
    )
    assert response.status_code == 400 and response.data["error"]["code"] == "REQUEST_TOO_LARGE"
