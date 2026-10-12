import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
success_checks = [
    "pm.test('HTTP 200', () => pm.response.to.have.status(200));",
    "const r = pm.response.json();",
    "pm.test('Road GeoJSON', () => { pm.expect(r.route.geometry.type).to.eql('LineString'); pm.expect(r.route.geometry.coordinates.length).to.be.above(2); });",
    "pm.test('Conservation of fuel', () => pm.expect(Math.abs(r.vehicle.initial_fuel_gallons + r.fuel_summary.gallons_purchased - r.fuel_summary.gallons_consumed - r.fuel_summary.end_fuel_gallons)).to.be.below(1e-8));",
    "pm.test('Owned fuel valuation not invented', () => pm.expect(r.fuel_summary.initial_fuel_value_usd).to.eql(null));",
    "pm.test('No endpoint geocoding for known cities', () => pm.expect(r.meta.geocoding_api_calls).to.eql(0));",
    "pm.test('Directions budget', () => pm.expect(r.meta.directions_api_calls).to.be.at.most(1));",
    "pm.test('Tank bounds', () => r.fuel_stops.forEach(s => { pm.expect(s.fuel_before_purchase_gallons).to.be.at.least(0); pm.expect(s.fuel_after_purchase_gallons).to.be.at.most(r.vehicle.tank_capacity_gallons + 1e-8); }));",
]


def request(name, body, checks):
    return {
        "name": name,
        "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
                "mode": "raw",
                "raw": json.dumps(body, indent=2),
                "options": {"raw": {"language": "json"}},
            },
            "url": "{{base_url}}/api/v1/routes/optimize/",
        },
        "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": checks}}],
    }


def main():
    long = {"start": "Chicago, IL", "finish": "Dallas, TX", "location_mode": "strict"}
    items = [
        request(
            "1. Long strict journey",
            long,
            success_checks
            + [
                "pm.test('Multiple real purchases', () => pm.expect(r.fuel_stops.length).to.be.at.least(2));",
                "pm.test('Verified coordinates only', () => r.fuel_stops.forEach(s => pm.expect(s.location_precision).to.eql('verified_station')));",
                "pm.test('Recorded calls disclosed or live budget', () => { if (r.route.recorded) pm.expect(r.meta.directions_api_calls).to.eql(0); else if (!r.meta.route_cache_hit) pm.expect(r.meta.directions_api_calls).to.eql(1); });",
            ],
        ),
        request(
            "2. Short journey, owned fuel",
            {**long, "finish": "Milwaukee, WI"},
            success_checks
            + [
                "pm.test('No purchases, positive consumption', () => { pm.expect(r.fuel_summary.total_refueling_spend_usd).to.eql('0.00'); pm.expect(r.fuel_summary.gallons_consumed).to.be.above(0); });"
            ],
        ),
        request(
            "3. Repeat long, route cache hit",
            long,
            success_checks
            + [
                "pm.test('Zero repeated directions calls', () => pm.expect(r.meta.directions_api_calls).to.eql(0));",
                "pm.test('Route and plan cache hit', () => { pm.expect(r.meta.route_cache_hit).to.eql(true); pm.expect(r.meta.optimization_cache_hit).to.eql(true); });",
            ],
        ),
        request(
            "4. Estimated mode, warning visible",
            {**long, "location_mode": "estimated"},
            success_checks
            + [
                "pm.test('Estimated qualification', () => pm.expect(r.warnings.some(w => w.includes('ESTIMATED'))).to.eql(true));",
                "pm.test('Route reused across modes', () => pm.expect(r.meta.directions_api_calls).to.eql(0));",
            ],
        ),
        request(
            "5. Reject foreign location",
            {**long, "finish": "Toronto, ON"},
            [
                "pm.test('HTTP 422', () => pm.response.to.have.status(422));",
                "pm.test('Foreign error', () => pm.expect(pm.response.json().error.code).to.eql('LOCATION_OUTSIDE_US'));",
            ],
        ),
        request(
            "6. Reject excess initial fuel",
            {**long, "initial_fuel_gallons": 51},
            [
                "pm.test('HTTP 400', () => pm.response.to.have.status(400));",
                "pm.test('Validation error', () => pm.expect(pm.response.json().error.code).to.eql('INVALID_INPUT'));",
            ],
        ),
    ]
    for name, body in [
        (
            "7. New York to Miami, estimated",
            {"start": "New York, NY", "finish": "Miami, FL", "location_mode": "estimated"},
        ),
        (
            "8. Los Angeles to Denver, estimated",
            {"start": "Los Angeles, CA", "finish": "Denver, CO", "location_mode": "estimated"},
        ),
    ]:
        items.append(
            request(
                name,
                body,
                success_checks
                + [
                    "pm.test('Estimated scope disclosed', () => pm.expect(r.meta.location_mode).to.eql('estimated'));",
                    "pm.test('Positive purchases on long route', () => pm.expect(r.fuel_summary.gallons_purchased).to.be.above(0));",
                ],
            )
        )
    items.append(
        request(
            "9. Seattle to San Francisco, honest coverage diagnostics",
            {"start": "Seattle, WA", "finish": "San Francisco, CA", "location_mode": "estimated"},
            [
                "const r = pm.response.json();",
                "pm.test('Real road geometry available', () => { const route=r.route || r.error.details.route; pm.expect(route.geometry.type).to.eql('LineString'); pm.expect(route.geometry.coordinates.length).to.be.above(1000); });",
                "pm.test('Recorded dataset gap is explicit', () => { const route=r.route || r.error.details.route; if(route.recorded){pm.response.to.have.status(422);pm.expect(r.error.code).to.eql('UNREACHABLE_FUEL_GAP');pm.expect(r.error.details.plan_available).to.eql(false);}else{pm.expect([200,422]).to.include(pm.response.code);} });",
                "pm.test('Call counts visible', () => {pm.expect(r.meta.directions_api_calls).to.be.at.most(1);pm.expect(r.meta.geocoding_api_calls).to.eql(0);});",
            ],
        )
    )
    items.append(
        request(
            "10. Short route with known initial inventory value",
            {"start": "Chicago, IL", "finish": "Milwaukee, WI", "initial_fuel_cost_usd": "200.00"},
            [
                "pm.test('HTTP 200', () => pm.response.to.have.status(200));",
                "const r=pm.response.json();",
                "pm.test('Cash purchase remains zero', () => pm.expect(r.fuel_summary.total_refueling_spend_usd).to.eql('0.00'));",
                "pm.test('Owned inventory has supplied value', () => pm.expect(r.fuel_summary.initial_fuel_value_usd).to.eql('200.00'));",
                "pm.test('Positive consumption value, remaining asset', () => {pm.expect(Number(r.fuel_summary.economic_fuel_cost_usd)).to.be.above(0);pm.expect(Number(r.fuel_summary.remaining_fuel_value_usd)).to.be.above(0);});",
                "pm.test('Same geometry cached across valuation', () => {pm.expect(r.meta.route_cache_hit).to.eql(true);pm.expect(r.meta.directions_api_calls).to.eql(0);});",
            ],
        )
    )
    items.append(
        request(
            "11. Changed starting volume reuses road geometry",
            {**long, "initial_fuel_gallons": 45},
            success_checks
            + [
                "pm.test('Fuel change makes no directions request', () => {pm.expect(r.meta.directions_api_calls).to.eql(0);pm.expect(r.meta.route_cache_hit).to.eql(true);});"
            ],
        )
    )
    collection = {
        "info": {
            "name": "FuelRoute IQ · Assessment verification",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": "Run in order. Works with documented recorded routes or ORS. Inspect cache-miss status after clearing local cache. Recorded routes never claim live directions calls.",
        },
        "variable": [{"key": "base_url", "value": "http://127.0.0.1:8000"}],
        "item": items,
    }
    folder = ROOT / "postman"
    folder.mkdir(exist_ok=True)
    (folder / "FuelRouteIQ.postman_collection.json").write_text(
        json.dumps(collection, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
