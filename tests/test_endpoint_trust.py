import json

import pytest
from django.conf import settings
from rest_framework.test import APIClient

from api.errors import PlanningError
from routing.geocoding import resolve_location
from routing.geometry import validate_endpoint_snaps
from routing.provider import CallCounts
from stations.models import City
from stations.normalization import city_key

pytestmark = pytest.mark.django_db


def test_offshore_census_endpoint_uses_attributed_city_reference():
    City.objects.create(
        geoid="0667000",
        name="San Francisco city",
        key=city_key("San Francisco"),
        state="CA",
        latitude=37.727239,
        longitude=-123.032229,
        source="https://www.census.gov/",
    )
    counts = CallCounts()
    result = resolve_location("San Francisco, CA", counts)
    assert result["coordinates"] == [-122.41942, 37.77493]
    assert result["precision"] == "approximate_city" and "geonames.org/5391959" in result["source"]
    assert counts.geocoding == 0
    assert "not a precise address or station" in result["representative_point_note"]
    city = City.objects.get()
    assert city.longitude == -123.032229  # Original Census/station fallback is preserved.


def test_historical_offshore_recording_rejected_corrected_road_valid():
    old = json.loads((settings.BASE_DIR / "fixtures/routes/seattle-san-francisco.json").read_text())
    with pytest.raises(PlanningError) as exc:
        validate_endpoint_snaps(old, [-122.351538, 47.619335], [-123.032229, 37.727239])
    assert exc.value.payload["error"]["code"] == "ENDPOINT_SNAP_TOO_FAR"
    corrected = json.loads(
        (
            settings.BASE_DIR / "fixtures/routes/seattle-san-francisco-reviewed-endpoint.json"
        ).read_text()
    )
    checked = validate_endpoint_snaps(corrected, [-122.351538, 47.619335], [-122.41942, 37.77493])
    assert max(checked["endpoint_snap_distances_meters"]) < 1000
    assert old["geometry"] != corrected["geometry"]


def test_bad_snapped_provider_response_is_not_cached(prepared_db, mock_directions):
    from unittest.mock import Mock

    import httpx

    wrong = Mock(
        return_value=httpx.Response(
            200,
            json={
                "features": [
                    {
                        "geometry": {"type": "LineString", "coordinates": [[-90, 35], [-90, 36]]},
                        "properties": {"summary": {"distance": 100000, "duration": 3600}},
                    }
                ]
            },
        )
    )
    # A valid-shaped road hundreds of miles from the inputs must still fail.
    import unittest.mock

    with unittest.mock.patch("httpx.request", wrong):
        client = APIClient()
        for _ in range(2):
            r = client.post(
                "/api/v1/routes/optimize/",
                {"start": "Chicago, IL", "finish": "Dallas, TX"},
                format="json",
            )
            assert r.status_code == 422 and r.data["error"]["code"] == "ENDPOINT_SNAP_TOO_FAR"
        assert wrong.call_count == 2
