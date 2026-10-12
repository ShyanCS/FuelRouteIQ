import hashlib
import json
import math
import time
from dataclasses import dataclass

import httpx
from django.conf import settings

from api.errors import PlanningError
from routing.cache import increment_metric

METERS_PER_MILE = 1609.344


@dataclass
class CallCounts:
    directions: int = 0
    geocoding: int = 0
    recorded_reads: int = 0
    directions_request_duration_ms: float = 0.0
    geocoding_request_duration_ms: float = 0.0


def request_json(method, url, counts, kind, **kwargs):
    # Deliberately no automatic retries: the one-call directions budget wins.
    setattr(counts, kind, getattr(counts, kind) + 1)
    increment_metric(kind + "_calls")
    started = time.perf_counter()
    try:
        response = httpx.request(
            method, url, timeout=httpx.Timeout(20, connect=5), follow_redirects=False, **kwargs
        )
    except httpx.TimeoutException as exc:
        raise PlanningError(
            "PROVIDER_TIMEOUT",
            "Routing/location provider timed out; retry this request later.",
            503,
        ) from exc
    except httpx.RequestError as exc:
        raise PlanningError(
            "PROVIDER_UNAVAILABLE", "Routing/location provider could not be reached.", 503
        ) from exc
    finally:
        field = kind + "_request_duration_ms"
        setattr(counts, field, getattr(counts, field) + (time.perf_counter() - started) * 1000)
    if response.status_code == 429:
        raise PlanningError("PROVIDER_RATE_LIMIT", "Provider quota or rate limit reached.", 429)
    if response.status_code == 403:
        # HeiGIT documents 403 for daily quota exhaustion, not just bad keys.
        try:
            payload = response.json()
            error = payload.get("error", "") if isinstance(payload, dict) else ""
            message = error.get("message", "") if isinstance(error, dict) else str(error)
        except ValueError:
            message = ""
        if "quota" in message.casefold() or response.headers.get("x-ratelimit-remaining") == "0":
            raise PlanningError("PROVIDER_RATE_LIMIT", "Provider daily quota is exhausted.", 429)
    if response.status_code in (401, 403):
        raise PlanningError(
            "PROVIDER_AUTH_ERROR",
            "Provider credential is missing, invalid, or not authorized.",
            503,
        )
    if response.status_code >= 500:
        raise PlanningError("PROVIDER_FAILURE", "Provider returned a server error.", 502)
    if 300 <= response.status_code < 400:
        raise PlanningError(
            "PROVIDER_REDIRECT",
            "Provider endpoint redirected; verify the configured API base URL.",
            502,
        )
    try:
        data = response.json()
    except ValueError as exc:
        raise PlanningError(
            "INVALID_PROVIDER_RESPONSE", "Provider did not return valid JSON.", 502
        ) from exc
    if response.status_code >= 400:
        error = data.get("error") if isinstance(data, dict) else None
        code = error.get("code") if isinstance(error, dict) else None
        if code in (2004, 2009, 2010, 2013, 2014, 2015, 2016, 2017):
            raise PlanningError(
                "ROUTE_LIMIT_OR_UNAVAILABLE",
                "Route exceeds provider restrictions or could not be found (ORS maximum 6,000 km).",
                422,
            )
        raise PlanningError(
            "PROVIDER_REJECTED_REQUEST", "Provider rejected the validated route request.", 502
        )
    return data


def validate_route(route):
    try:
        geometry = route["geometry"]
        points = geometry["coordinates"]

        def number(value):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("Provider measurements must be JSON numbers")
            return float(value)

        distance, duration = number(route["distance_meters"]), number(route["duration_seconds"])
        if geometry["type"] != "LineString" or len(points) < 2:
            raise ValueError("LineString required")
        if not all(
            len(p) >= 2
            and all(math.isfinite(number(v)) for v in p[:2])
            and -180 <= p[0] <= 180
            and -90 <= p[1] <= 90
            for p in points
        ):
            raise ValueError("Invalid coordinate")
        if (
            not math.isfinite(distance)
            or not math.isfinite(duration)
            or distance < 0
            or duration < 0
        ):
            raise ValueError("Invalid summary")
        if distance == 0 and any(p[:2] != points[0][:2] for p in points):
            raise ValueError("Nonzero geometry with zero route distance")
        if distance > 0 and all(p[:2] == points[0][:2] for p in points):
            raise ValueError("Positive distance with degenerate geometry")
        if distance > 6_000_000:
            raise PlanningError(
                "ROUTE_TOO_LONG", "Road distance exceeds the public ORS 6,000 km limit.", 422
            )
        return {**route, "distance_meters": distance, "duration_seconds": duration}
    except (KeyError, ValueError, TypeError, IndexError) as exc:
        raise PlanningError(
            "INVALID_PROVIDER_RESPONSE", "Provider route geometry or summary is invalid.", 502
        ) from exc


class ORSProvider:
    name = "ors"
    profile = "driving-car"
    version = "heigit-v2-contract-2"

    @property
    def cache_identity(self):
        return {
            "provider": self.name,
            "profile": self.profile,
            "version": self.version,
            "base_url": settings.ORS_API_BASE_URL,
        }

    def directions(self, start, finish, counts):
        if not settings.ORS_API_KEY:
            raise PlanningError(
                "ROUTING_NOT_CONFIGURED",
                "Set ORS_API_KEY for live routing, or ROUTING_PROVIDER=recorded for the documented demo routes.",
                503,
            )
        data = request_json(
            "POST",
            settings.ORS_API_BASE_URL + "/v2/directions/driving-car/geojson",
            counts,
            "directions",
            headers={"Authorization": settings.ORS_API_KEY, "Accept": "application/geo+json"},
            json={"coordinates": [start, finish], "instructions": False},
        )
        try:
            feature = data["features"][0]
            summary = feature["properties"]["summary"]
            return validate_route(
                {
                    "geometry": feature["geometry"],
                    "distance_meters": summary["distance"],
                    "duration_seconds": summary["duration"],
                    "provider": self.name,
                    "profile": self.profile,
                    "recorded": False,
                    "attribution": "openrouteservice | OpenStreetMap contributors",
                }
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise PlanningError(
                "INVALID_PROVIDER_RESPONSE", "Provider response lacks a route summary.", 502
            ) from exc


class RecordedProvider:
    name = "recorded-osrm"
    profile = "driving-car"
    version = "recording-v2"

    @property
    def cache_identity(self):
        manifest = settings.BASE_DIR / "fixtures/routes/manifest.json"
        return {
            "provider": self.name,
            "profile": self.profile,
            "version": self.version,
            "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest()
            if manifest.exists()
            else None,
        }

    def directions(self, start, finish, counts):
        manifest = settings.BASE_DIR / "fixtures/routes/manifest.json"
        entries = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else []
        for entry in entries:
            if start == entry["start"] and finish == entry["finish"]:
                content = (manifest.parent / entry["file"]).read_bytes()
                if hashlib.sha256(content).hexdigest() != entry["sha256"]:
                    raise PlanningError(
                        "RECORDING_INTEGRITY_ERROR",
                        "Recorded route checksum does not match its source manifest.",
                        503,
                    )
                counts.recorded_reads += 1
                return validate_route(json.loads(content))
        raise PlanningError(
            "RECORDED_ROUTE_UNAVAILABLE",
            "This pair is not in the recorded route manifest. Configure a HeiGIT API key and ROUTING_PROVIDER=ors for arbitrary US routes.",
            422,
        )


def get_provider():
    if settings.ROUTING_PROVIDER == "ors":
        return ORSProvider()
    if settings.ROUTING_PROVIDER == "recorded":
        return RecordedProvider()
    raise PlanningError("ROUTING_NOT_CONFIGURED", "Unknown routing provider configuration.", 503)
