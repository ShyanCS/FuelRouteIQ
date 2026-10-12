import copy
import time
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.cache import cache

from api.accounting import fifo_valuation
from api.errors import PlanningError
from optimizer.baseline import simulate_baseline
from optimizer.engine import optimize
from optimizer.schemas import Candidate, FuelGap, Vehicle
from routing.cache import cache_key, increment_metric, request_lock
from routing.geocoding import resolve_location
from routing.provider import METERS_PER_MILE, get_provider, validate_route
from stations.importer import active_dataset, coverage
from stations.locate import project_stations
from stations.models import Station


def money(value):
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def plan_response(route, data, dataset, projected, timings=None):
    timings = timings if timings is not None else {}
    distance = Decimal(str(route["distance_meters"])) / Decimal(str(METERS_PER_MILE))
    vehicle = Vehicle(data["mpg"], data["range_miles"], data["initial_fuel_gallons"])
    candidates = [
        Candidate(s.opis_id, s.name, min(distance, max(Decimal(0), Decimal(str(mile)))), s.price)
        for s, mile, _ in projected
    ]
    mode = data["location_mode"]
    geo_coverage = coverage(dataset) if dataset else {}
    route_payload = {**route, "distance_miles": float(distance)}
    started = time.perf_counter()
    try:
        plan = optimize(distance, candidates, vehicle)
    except FuelGap as exc:
        raise PlanningError(
            "UNREACHABLE_FUEL_GAP",
            "Insufficient eligible fueling coverage for this route and initial fuel; this is not proof that real stations do not exist.",
            422,
            {
                "from_mile": float(exc.start),
                "to_mile": float(exc.end),
                "available_range_miles": float(exc.available_range),
                "location_mode": mode,
                "location_coverage": geo_coverage,
                "candidate_count": len(candidates),
                "geo_qualification": "Only verified station points are eligible."
                if mode == "strict"
                else "City positions do not prove highway access.",
                "route": route_payload,
                "suggested_action": "Try location_mode=estimated for a visibly qualified city-based estimate; feasibility is not guaranteed."
                if mode == "strict"
                else "Eligible snapshot-priced locations leave a fuel gap. Supply reviewed enrichment; no invented stops or prices will be used.",
                "eligible_location_quality": dict(
                    Counter(s.location_precision for s, _, _ in projected)
                ),
                "plan_available": False,
            },
        ) from exc
    finally:
        timings["optimizer_duration_ms"] = round((time.perf_counter() - started) * 1000, 3)
    details = {s.opis_id: (s, lateral) for s, _, lateral in projected}

    def render_stops(purchases):
        rendered = []
        for p in purchases:
            s, lateral = details[p.station.station_id]
            rendered.append(
                {
                    "station_id": s.opis_id,
                    "station_name": s.name,
                    "city": s.city,
                    "state": s.state,
                    "address": s.address,
                    "price_per_gallon_usd": str(s.price),
                    "price_min_usd": str(s.price_min),
                    "price_max_usd": str(s.price_max),
                    "price_conflict": s.price_conflict,
                    "source_row_count": s.source_row_count,
                    "mile_marker": float(p.station.mile),
                    "gallons_purchased": float(p.gallons),
                    "purchase_cost_usd": money(p.cost),
                    "purchase_cost_unrounded_usd": str(p.cost),
                    "fuel_before_purchase_gallons": float(p.before),
                    "fuel_after_purchase_gallons": float(p.after),
                    "coordinates": [s.longitude, s.latitude],
                    "location_precision": s.location_precision,
                    "location_source": s.source,
                    "match_confidence": s.match_confidence,
                    "verified_at": s.verified_at.isoformat() if s.verified_at else None,
                    "source_address_context_conflict": bool(
                        s.verification.get("source_address_context_conflict")
                    ),
                    "coordinate_review_notes": s.verification.get("review_notes", ""),
                    "distance_from_route_miles": lateral,
                    "detour_miles": None,
                    "decision_explanation": p.explanation,
                }
            )
        return rendered

    started = time.perf_counter()
    try:
        baseline = simulate_baseline(distance, candidates, vehicle)
        baseline_status = "feasible_same_model"
        savings = baseline.spend - plan.spend
        baseline_payload = {
            "status": baseline_status,
            "policy": "nearest 80% of range, fill capped by destination need; ignores prices",
            "spend_usd": money(baseline.spend),
            "fuel_stops": render_stops(baseline.purchases),
        }
        savings_usd = money(savings)
        savings_percent = float(savings / baseline.spend * 100) if baseline.spend else None
    except FuelGap:
        baseline, baseline_status, savings_usd, savings_percent = None, "infeasible", None, None
        baseline_payload = {
            "status": baseline_status,
            "policy": "nearest 80% of range; ignores prices",
            "spend_usd": None,
            "fuel_stops": [],
        }
    finally:
        timings["baseline_duration_ms"] = round((time.perf_counter() - started) * 1000, 3)
    price_basis = dataset.price_basis if dataset else "unavailable"
    warnings = [
        "Fuel prices are undated assessment snapshots, not live pump prices."
        if price_basis == "assessment_snapshot"
        else "Prices are explicitly illustrative test values; no real pump-price or assessment-price claim applies.",
        "Optimal purchase spend is conditional on the fixed route, eligible candidates, divisible fuel and zero modeled detour. Road access, actual detour mileage and opening hours are unverified.",
        "En-route spend excludes initially owned fuel. $0 purchases does not mean zero consumption or zero economic cost.",
    ]
    if mode == "estimated":
        warnings.append(
            "ESTIMATED: city points may be far from the station. This is a conditional illustration, not a navigable fueling plan or a global optimum."
        )
    if route.get("recorded"):
        warnings.append(
            "RECORDED ROAD ROUTE: replay of a real OSRM response; no live directions request occurred. ORS integration requires a key."
        )
    if price_basis == "illustrative_test_fixture":
        warnings.insert(
            0,
            "ILLUSTRATIVE TEST PRICES: these deliberately labelled fixture values are not assessment observations or current pump prices. Import the supplied assessment CSV for an assessment-price plan.",
        )
    if any(s.price_conflict for s, _, _ in projected):
        warnings.append(
            "Eligible stations include conflicting observed prices; each chosen price is an actual observation closest to the source-row median."
        )
    initial_value = data.get("initial_fuel_cost_usd")
    valuation = fifo_valuation(plan, vehicle.initial, initial_value)
    for field in ("economic_fuel_cost_usd", "remaining_fuel_value_usd"):
        valuation[field] = money(valuation[field]) if valuation[field] is not None else None
    timeline = [{"mile_marker": 0, "fuel_gallons": float(vehicle.initial), "event": "start"}]
    for p in plan.purchases:
        timeline.extend(
            [
                {
                    "mile_marker": float(p.station.mile),
                    "fuel_gallons": float(p.before),
                    "event": "before_refuel",
                },
                {
                    "mile_marker": float(p.station.mile),
                    "fuel_gallons": float(p.after),
                    "event": "after_refuel",
                },
            ]
        )
    timeline.append(
        {
            "mile_marker": float(distance),
            "fuel_gallons": float(plan.end_fuel),
            "event": "destination",
        }
    )
    return {
        "route": route_payload,
        "vehicle": {
            "mpg": float(vehicle.mpg),
            "range_miles": float(vehicle.range_miles),
            "tank_capacity_gallons": float(vehicle.capacity),
            "initial_fuel_gallons": float(vehicle.initial),
        },
        "fuel_stops": render_stops(plan.purchases),
        "fuel_summary": {
            **valuation,
            "route_miles": float(distance),
            "gallons_consumed": float(plan.consumed),
            "gallons_purchased": float(plan.bought),
            "total_refueling_spend_usd": money(plan.spend),
            "total_refueling_spend_unrounded_usd": str(plan.spend),
            "initial_fuel_value_usd": money(initial_value) if initial_value is not None else None,
            "total_acquired_fuel_value_usd": money(initial_value + plan.spend)
            if initial_value is not None
            else None,
            "end_fuel_gallons": float(plan.end_fuel),
            "baseline_status": baseline_status,
            "baseline_spend_usd": money(baseline.spend) if baseline else None,
            "savings_usd": savings_usd,
            "savings_percent": savings_percent,
        },
        "total_fuel_cost_usd": money(plan.spend),
        "cost_basis": {
            "kind": "en_route_cash_purchases",
            "initial_owned_fuel_included": False,
            "initial_owned_fuel_value_known": initial_value is not None,
            "savings_comparison": "en_route_cash_purchases; identical initial volume and candidate quality for both policies",
            "price_basis": price_basis,
            "rounding": "USD half-up to cents after summing exact costs; displayed stop cents may differ from rounded total",
        },
        "baseline": baseline_payload,
        "fuel_timeline": timeline,
        "warnings": warnings,
        "meta": {
            "location_mode": mode,
            "location_coverage": geo_coverage,
            "candidate_count": len(candidates),
            "candidate_location_quality": dict(
                Counter(s.location_precision for s, _, _ in projected)
            ),
            "corridor_threshold_miles": settings.CORRIDOR_MILES,
            "dataset_revision": str(dataset.revision) if dataset else None,
            "price_basis": price_basis,
            "optimality_scope": "fixed_route_eligible_verified_candidates_zero_detour_model"
            if mode == "strict"
            else "conditional_estimate_city_positions_zero_detour_model",
        },
    }


def run_planning(data, counts, metadata):
    started = time.perf_counter()
    start = resolve_location(data["start"], counts)
    finish = resolve_location(data["finish"], counts)
    provider = get_provider()
    metadata["endpoint_resolution_duration_ms"] = round((time.perf_counter() - started) * 1000, 3)
    metadata.update(
        {"projection_duration_ms": 0, "optimizer_duration_ms": 0, "baseline_duration_ms": 0}
    )
    key = cache_key(
        "route-v2",
        {
            "start": start["coordinates"],
            "finish": finish["coordinates"],
            "provider": provider.cache_identity,
            "options": {"instructions": False},
        },
    )
    metadata["endpoints"] = {"start": start, "finish": finish}
    t = time.perf_counter()
    with request_lock(key):
        route = cache.get(key)
        metadata["route_cache_hit"] = route is not None
        increment_metric("route_hits" if route is not None else "route_misses")
        if route is None:
            if start["coordinates"] == finish["coordinates"]:
                route = {
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [start["coordinates"], finish["coordinates"]],
                    },
                    "distance_meters": 0,
                    "duration_seconds": 0,
                    "provider": "identical_endpoints",
                    "recorded": False,
                }
            else:
                route = provider.directions(start["coordinates"], finish["coordinates"], counts)
            route = validate_route(route)
            cache.set(key, route, settings.ROUTE_CACHE_TTL_SECONDS)
    metadata["routing_duration_ms"] = round((time.perf_counter() - t) * 1000, 3)
    dataset = active_dataset()
    plan_key = cache_key(
        "plan-v2",
        {
            "route": key,
            "route_content": cache_key("content", route),
            "dataset": str(dataset.revision) if dataset else None,
            "mode": data["location_mode"],
            "vehicle": {k: v for k, v in data.items() if k not in ("start", "finish")},
            "corridor": settings.CORRIDOR_MILES,
            "selection_policy": "metric_projection_near_tie_rejection_v2",
        },
    )
    with request_lock(plan_key):
        result = cache.get(plan_key)
        metadata["optimization_cache_hit"] = result is not None
        if result is None:
            selected = (
                Station.objects.filter(
                    dataset=dataset, latitude__isnull=False, identity_conflict=False
                )
                if dataset
                else Station.objects.none()
            )
            if data["location_mode"] == "strict":
                selected = selected.filter(location_precision="verified_station")
            t = time.perf_counter()
            projection_diagnostics = {}
            projected = project_stations(
                route, selected, settings.CORRIDOR_MILES, projection_diagnostics
            )
            metadata["projection_diagnostics"] = projection_diagnostics
            metadata["projection_duration_ms"] = round((time.perf_counter() - t) * 1000, 3)
            result = plan_response(route, data, dataset, projected, metadata)
            result["meta"]["projection_diagnostics"] = projection_diagnostics
            cache.set(plan_key, result, settings.OPTIMIZATION_CACHE_TTL_SECONDS)
    result = copy.deepcopy(result)
    result["meta"].update(metadata)
    return result
