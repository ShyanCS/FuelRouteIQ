import os

import pytest

from routing.provider import CallCounts, ORSProvider


@pytest.mark.live
@pytest.mark.django_db
def test_opt_in_live_ors(settings, monkeypatch):
    if os.getenv("RUN_LIVE_TESTS") != "1" or not os.getenv("ORS_API_KEY"):
        pytest.skip("Set RUN_LIVE_TESTS=1 and ORS_API_KEY to make exactly one live request")
    import httpx
    from httpx import Client

    settings.ORS_API_KEY = os.environ["ORS_API_KEY"]

    def live_request(method, url, **kwargs):
        with Client() as client:
            return client.request(method, url, **kwargs)

    monkeypatch.setattr(httpx, "request", live_request)
    counts = CallCounts()
    route = ORSProvider().directions([-87.63, 41.88], [-87.91, 43.03], counts)
    assert route["geometry"]["type"] == "LineString" and route["distance_meters"] > 100_000
    assert counts.directions == 1 and counts.geocoding == 0
