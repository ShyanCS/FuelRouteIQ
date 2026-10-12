import os
import subprocess
import sys
from io import StringIO

import pytest
from django.conf import settings
from django.core.management import call_command
from rest_framework.test import APIClient

from api.throttles import RouteClientThrottle, RouteGlobalMinuteThrottle, RouteGlobalThrottle
from stations.importer import import_fuel
from stations.models import Dataset, SourceRow

pytestmark = pytest.mark.django_db


def test_repeat_seed_preserves_revision_raw_rows_and_enrichment():
    output = StringIO()
    call_command("seed_demo", stdout=output)
    dataset = Dataset.objects.get()
    first_revision = dataset.revision
    assert dataset.station_set.filter(location_precision="verified_station").count() == 31
    assert SourceRow.objects.count() == 31
    call_command("seed_demo", stdout=output)
    dataset.refresh_from_db()
    assert Dataset.objects.count() == 1 and SourceRow.objects.count() == 31
    assert dataset.revision == first_revision
    assert dataset.station_set.filter(location_precision="verified_station").count() == 31


def test_seed_refuses_to_replace_assessment_data(prepared_db):
    prepared_db.price_basis = "assessment_snapshot"
    prepared_db.save()
    with pytest.raises(Exception, match="Refusing to replace"):
        call_command("seed_demo", stdout=StringIO())
    assert Dataset.objects.count() == 1


def test_reuse_only_identical_active_data(prepared_db):
    prepared_db.refresh_from_db()
    reused = import_fuel(settings.BASE_DIR / "fixtures/public_unit_prices.csv", reuse=True)
    assert reused.id == prepared_db.id and reused.revision == prepared_db.revision
    changed = import_fuel(settings.BASE_DIR / "fixtures/public_demo_prices.csv", reuse=True)
    assert changed.id != reused.id and changed.revision != reused.revision


def test_not_ready_health_does_not_report_success():
    response = APIClient().get("/api/v1/health/")
    assert response.status_code == 503 and response.data["status"] == "not_ready"
    assert not response.data["fuel_dataset_loaded"]


def test_public_throttling_protects_malformed_requests(settings, monkeypatch):
    settings.PUBLIC_API_THROTTLING = True
    monkeypatch.setattr(
        RouteClientThrottle,
        "THROTTLE_RATES",
        {"route_client": "2/minute", "route_global_minute": "30/minute", "route_global": "500/day"},
    )
    client = APIClient()
    for _ in range(2):
        assert client.post("/api/v1/routes/optimize/", {}, format="json").status_code == 400
    limited = client.post("/api/v1/routes/optimize/", {}, format="json")
    assert limited.status_code == 429 and int(limited["Retry-After"]) > 0
    # Health probes remain usable after the route quota is exhausted.
    assert client.get("/api/v1/health/").status_code == 503


def test_global_quota_spans_clients(settings, monkeypatch):
    settings.PUBLIC_API_THROTTLING = True
    monkeypatch.setattr(
        RouteGlobalThrottle,
        "THROTTLE_RATES",
        {"route_global": "2/day", "route_global_minute": "30/minute"},
    )
    client = APIClient()
    for ip in ("192.0.2.1", "192.0.2.2"):
        assert (
            client.post("/api/v1/routes/optimize/", {}, format="json", REMOTE_ADDR=ip).status_code
            == 400
        )
    assert (
        client.post(
            "/api/v1/routes/optimize/", {}, format="json", REMOTE_ADDR="192.0.2.3"
        ).status_code
        == 429
    )


def test_production_requires_secret_and_durable_database():
    env = {**os.environ, "DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": "", "DATABASE_URL": ""}
    cmd = [sys.executable, "-c", "import fuelroute.settings"]
    missing_secret = subprocess.run(
        cmd, cwd=settings.BASE_DIR, env=env, capture_output=True, text=True
    )
    assert missing_secret.returncode != 0 and "private DJANGO_SECRET_KEY" in missing_secret.stderr
    env["DJANGO_SECRET_KEY"] = "test-only-long-secret-" * 4
    missing_db = subprocess.run(cmd, cwd=settings.BASE_DIR, env=env, capture_output=True, text=True)
    assert missing_db.returncode != 0 and "durable PostgreSQL" in missing_db.stderr


def test_global_minute_quota_recovers_without_resetting_daily_quota(settings, monkeypatch):
    settings.PUBLIC_API_THROTTLING = True
    monkeypatch.setattr(
        RouteGlobalMinuteThrottle, "THROTTLE_RATES", {"route_global_minute": "2/minute"}
    )
    clock = [1700000000.0]
    monkeypatch.setattr(RouteGlobalMinuteThrottle, "timer", lambda self: clock[0])
    client = APIClient()
    for ip in ("192.0.2.11", "192.0.2.12"):
        assert (
            client.post("/api/v1/routes/optimize/", {}, format="json", REMOTE_ADDR=ip).status_code
            == 400
        )
    limited = client.post("/api/v1/routes/optimize/", {}, format="json", REMOTE_ADDR="192.0.2.13")
    assert limited.status_code == 429 and 0 < int(limited["Retry-After"]) <= 60
    clock[0] += 61
    assert (
        client.post(
            "/api/v1/routes/optimize/", {}, format="json", REMOTE_ADDR="192.0.2.14"
        ).status_code
        == 400
    )


def test_plain_postgres_url_gets_options_and_production_ssl():
    env = {
        **os.environ,
        "DJANGO_DEBUG": "false",
        "DJANGO_SECRET_KEY": "test-only-long-secret-" * 4,
        "DATABASE_URL": "postgresql://test:test@localhost/test",
    }
    cmd = [
        sys.executable,
        "-c",
        "import fuelroute.settings as s; assert s.DATABASES['default']['OPTIONS']['connect_timeout']==10; assert s.DATABASES['default']['OPTIONS']['sslmode']=='require'",
    ]
    result = subprocess.run(cmd, cwd=settings.BASE_DIR, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    env["DATABASE_URL"] += "?sslmode=disable"
    rejected = subprocess.run(cmd, cwd=settings.BASE_DIR, env=env, capture_output=True, text=True)
    assert rejected.returncode != 0 and "requires SSL" in rejected.stderr
