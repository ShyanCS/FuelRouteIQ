"""Controlled HeiGIT validation with redacted output and no secret persistence.

Default: one explicitly invalid credential request per endpoint to verify gateway
rejection, NOT successful routing. --live requires a configured genuine key and
makes the five matrix directions requests once; repeats/fuel changes use cache.
"""

import argparse
import json
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fuelroute.settings")
django.setup()

from django.conf import settings  # noqa: E402
from django.test import override_settings  # noqa: E402

from api.errors import PlanningError  # noqa: E402
from routing.provider import CallCounts, ORSProvider, request_json  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.live:
        if not settings.ORS_API_KEY:
            raise SystemExit(
                "Live validation blocked: configure a genuine ORS_API_KEY locally. No key is invented."
            )
        from scripts.validate_matrix import capture_matrix

        with override_settings(ROUTING_PROVIDER="ors"):
            capture_matrix("live-ors")
        return
    results = []
    with override_settings(ORS_API_KEY="deliberately-invalid-fuelroute-validation-key"):
        for kind in ("directions", "geocoding"):
            counts = CallCounts()
            try:
                if kind == "directions":
                    ORSProvider().directions([-87.63, 41.88], [-87.91, 43.03], counts)
                else:
                    request_json(
                        "GET",
                        settings.ORS_GEOCODING_BASE_URL + "/search",
                        counts,
                        "geocoding",
                        headers={"Authorization": settings.ORS_API_KEY},
                        params={"text": "Chicago, IL", "boundary.country": "US", "size": 1},
                    )
                result = {
                    "endpoint": kind,
                    "status": "unexpected_acceptance_of_invalid_key",
                    "successful_live_routing_verified": False,
                }
            except PlanningError as exc:
                result = {
                    "endpoint": kind,
                    "application_status": exc.status_code,
                    "error_code": exc.payload["error"]["code"],
                    "status": "gateway_rejection_or_network_failure",
                    "successful_live_routing_verified": False,
                }
            result.update(
                {
                    "directions_calls": counts.directions,
                    "geocoding_calls": counts.geocoding,
                    "directions_request_duration_ms": counts.directions_request_duration_ms,
                    "geocoding_request_duration_ms": counts.geocoding_request_duration_ms,
                }
            )
            results.append(result)
    path = settings.BASE_DIR / "artifacts/provider-gateway-probes.json"
    path.write_text(
        json.dumps(
            {
                "scope": "Real HTTP with a deliberately invalid non-secret sentinel; not a valid-key integration test",
                "configured_key_present": bool(settings.ORS_API_KEY),
                "results": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
