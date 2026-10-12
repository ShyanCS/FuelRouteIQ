import json
import math
import re

from django.conf import settings
from django.core.cache import cache
from pyproj import Geod

from api.errors import PlanningError
from routing.cache import cache_key, request_lock
from routing.provider import request_json
from stations.models import City
from stations.normalization import CANADIAN_STATES, STATE_NAMES, US_STATES, city_key, clean


def city_reference(city):
    """Endpoint-only reviewed corrections; never change station approximations."""
    entries = json.loads(
        (settings.BASE_DIR / "data/reference/endpoint_overrides.json").read_text(encoding="utf-8")
    )
    for entry in entries:
        if (
            city.geoid == entry["census_geoid"]
            and city.key == city_key(entry["city"])
            and city.state == entry["state"]
        ):
            return entry["coordinates"], entry["source"], entry["reason"]
    return (
        [city.longitude, city.latitude],
        city.source,
        "Census representative city point; not an exact departure or arrival address.",
    )


def resolve_location(value, counts):
    normalized = clean(value)
    parts = [clean(p) for p in normalized.split(",")]
    if parts[-1].casefold() in {"us", "usa", "united states", "united states of america"}:
        parts.pop()
    if len(parts) < 2:
        raise PlanningError(
            "LOCATION_FORMAT",
            "Use a US city and state code, e.g. Chicago, IL; precise addresses also require a state code.",
            400,
        )
    state = STATE_NAMES.get(parts[-1].casefold(), parts[-1].upper())
    if state in CANADIAN_STATES or state not in US_STATES:
        raise PlanningError(
            "LOCATION_OUTSIDE_US",
            "Only the 50 US states and DC are supported; finish the location with a two-letter US state code.",
            422,
        )
    if len(parts) == 2:
        matches = list(City.objects.filter(key=city_key(parts[0]), state=state)[:2])
        if len(matches) > 1:
            raise PlanningError(
                "AMBIGUOUS_LOCATION",
                "Multiple Census places match this city/state; use a precise address.",
                422,
            )
        if matches:
            c = matches[0]
            coordinates, source, note = city_reference(c)
            return {
                "coordinates": coordinates,
                "label": f"{c.name}, {state}",
                "precision": "approximate_city",
                "source": source,
                "representative_point_note": note,
                "cache_hit": False,
                "local_index": True,
            }
    # Unsupported named cities do not silently become geocoder guesses. Precise
    # address requests require a street number and a uniquely known US locality.
    if len(parts) < 3 or not re.search(r"\d", parts[0]):
        raise PlanningError(
            "LOCATION_NOT_FOUND",
            "City/state not found in the local Census index. Try a supported city or a street address, city, state.",
            422,
        )
    cities = list(City.objects.filter(key=city_key(parts[-2]), state=state)[:2])
    if len(cities) != 1:
        raise PlanningError(
            "LOCATION_NOT_FOUND",
            "Precise address must specify a uniquely supported US city/state.",
            422,
        )
    key = cache_key(
        "geocode-v2",
        {
            "query": normalized.casefold(),
            "provider_url": settings.ORS_GEOCODING_BASE_URL,
            "locality": [cities[0].geoid, *city_reference(cities[0])[0]],
        },
    )
    with request_lock(key):
        existing = cache.get(key)
        if existing:
            return {**existing, "cache_hit": True}
        if not settings.ORS_API_KEY:
            raise PlanningError(
                "GEOCODING_NOT_CONFIGURED",
                "ORS_API_KEY is required for precise address lookup; city/state endpoints work locally.",
                503,
            )
        data = request_json(
            "GET",
            settings.ORS_GEOCODING_BASE_URL + "/search",
            counts,
            "geocoding",
            headers={"Authorization": settings.ORS_API_KEY},
            params={"text": normalized, "boundary.country": "US", "size": 2},
        )
        try:
            features = data["features"]
            if len(features) != 1:
                raise PlanningError(
                    "AMBIGUOUS_LOCATION", "Address did not resolve uniquely; refine the input.", 422
                )
            properties = features[0]["properties"]
            if (
                properties.get("country_a") not in ("USA", "US")
                or properties.get("region_a") != state
            ):
                raise PlanningError(
                    "LOCATION_OUTSIDE_US", "Provider match is outside the requested US state.", 422
                )
            confidence = properties.get("confidence", 0)
            if (
                not isinstance(confidence, (int, float))
                or isinstance(confidence, bool)
                or not math.isfinite(confidence)
                or not 0.8 <= confidence <= 1
                or properties.get("layer")
                not in (
                    "address",
                    "venue",
                )
            ):
                raise PlanningError(
                    "UNCERTAIN_ADDRESS",
                    "Provider returned a low-confidence or non-address match.",
                    422,
                )
            coords = features[0]["geometry"]["coordinates"][:2]
            locality = city_reference(cities[0])[0]
            if (
                len(coords) != 2
                or not all(math.isfinite(float(v)) for v in coords)
                or not -180 <= coords[0] <= 180
                or not -90 <= coords[1] <= 90
                or Geod(ellps="WGS84").inv(*locality, *coords)[2] > 50_000
            ):
                raise PlanningError(
                    "UNCERTAIN_ADDRESS",
                    "Provider match is inconsistent with the supplied US locality.",
                    422,
                )
            result = {
                "coordinates": coords,
                "label": properties.get("label", normalized),
                "precision": "provider_address",
                "source": "https://openrouteservice.org/services/",
                "cache_hit": False,
                "local_index": False,
            }
        except (KeyError, TypeError, IndexError, ValueError) as exc:
            raise PlanningError(
                "INVALID_PROVIDER_RESPONSE", "Invalid geocoding response.", 502
            ) from exc
        cache.set(key, result, settings.GEOCODE_CACHE_TTL_SECONDS)
        return result
