# Hosted Postman requests

Import `postman/FuelRouteIQ.postman_collection.json`. Set `base_url` to the actual HTTPS homepage in `SUBMISSION_LINKS.md`, without a trailing slash. No client ORS credential is required or exposed. Send JSON to `{{base_url}}/api/v1/routes/optimize/`.

Long strict:
```json
{"start":"Chicago, IL","finish":"Dallas, TX","location_mode":"strict","initial_fuel_gallons":50}
```

Short inventory accounting:
```json
{"start":"Chicago, IL","finish":"Milwaukee, WI","initial_fuel_gallons":50,"initial_fuel_cost_usd":"200.00"}
```

Repeat the long body unchanged. Then reuse its geometry with:
```json
{"start":"Chicago, IL","finish":"Dallas, TX","location_mode":"estimated","initial_fuel_gallons":45}
```

Additional supported recorded pairs: New York, NY → Miami, FL and Los Angeles, CA → Denver, CO. Seattle, WA → San Francisco, CA returns real recorded road geometry with a structured `UNREACHABLE_FUEL_GAP` for the current priced data. An unseen city pair requires configured live routing; recorded mode returns `RECORDED_ROUTE_UNAVAILABLE` transparently.

Inspect `route.geometry`, `route.provider`, `route.recorded`, mileage/duration; `vehicle`; each stop’s coordinates, quality, price and before/after gallons; `fuel_summary` consumed/purchased/cash/owned value/economic value; `cost_basis.price_basis`; baseline and savings; warnings; `meta` direction/geocoder counts, cache status and measured durations. Pair before/after timeline events at the same mileage. Assert conservation and tank bounds using the collection, not a hardcoded historic dollar amount.

Foreign input: finish Toronto, ON → 422. Excess initial fuel 51 → 400. Invalid JSON → 400. Public quota exhaustion → 429 with Retry-After. A provider failure remains a structured error and is never silently replaced by replay.
