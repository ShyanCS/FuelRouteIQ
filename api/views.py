import json
import time

import django
from django.conf import settings
from django.core.cache import cache
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response

from api.errors import PlanningError
from api.serializers import OptimizeRequestSerializer
from api.service import run_planning
from api.throttles import RouteClientThrottle, RouteGlobalThrottle
from routing.provider import CallCounts
from stations.importer import active_dataset, coverage
from stations.models import City


@api_view(["POST"])
@throttle_classes([RouteClientThrottle, RouteGlobalThrottle])
def optimize_route(request):
    started = time.perf_counter()
    # Enforce Django's body-size guard before DRF's streaming JSON parser.
    if len(request.body) > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
        raise PlanningError("REQUEST_TOO_LARGE", "JSON body exceeds the 16 KB request limit.", 400)
    serializer = OptimizeRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    counts, metadata = CallCounts(), {}
    try:
        result = run_planning(serializer.validated_data, counts, metadata)
    except PlanningError as exc:
        result = exc.payload
        result["meta"] = metadata
        status = exc.status_code
    else:
        status = 200
    result["meta"].update(
        {
            "directions_api_calls": counts.directions,
            "geocoding_api_calls": counts.geocoding,
            "recorded_route_reads": counts.recorded_reads,
            "directions_request_duration_ms": round(counts.directions_request_duration_ms, 3),
            "geocoding_request_duration_ms": round(counts.geocoding_request_duration_ms, 3),
            "request_duration_ms": round((time.perf_counter() - started) * 1000, 3),
        }
    )
    return Response(result, status=status)


@api_view(["GET"])
def health(request):
    dataset = active_dataset()
    places = City.objects.count()
    ready = dataset is not None and places > 0
    return Response(
        {
            "status": "ok" if ready else "not_ready",
            "django_version": django.get_version(),
            "routing_provider": settings.ROUTING_PROVIDER,
            "live_routing_configured": bool(settings.ORS_API_KEY),
            "fuel_dataset_loaded": dataset is not None,
            "local_places": places,
            "price_basis": dataset.price_basis if dataset else "unavailable",
            "recorded_route_count": len(
                json.loads(
                    (settings.BASE_DIR / "fixtures/routes/manifest.json").read_text(
                        encoding="utf-8"
                    )
                )
            ),
        },
        status=200 if ready else 503,
    )


@api_view(["GET"])
def stats(request):
    dataset = active_dataset()
    return Response(
        {
            "dataset": {**dataset.report, "price_basis": dataset.price_basis} if dataset else None,
            "dataset_revision": str(dataset.revision) if dataset else None,
            "location_coverage": coverage(dataset) if dataset else {},
            "local_places": City.objects.count(),
            "cache_metrics": {
                k: cache.get("metric:" + k, 0)
                for k in ("directions_calls", "geocoding_calls", "route_hits", "route_misses")
            },
            "metrics_scope": "local database cache lifetime; not provider account quota",
        }
    )
