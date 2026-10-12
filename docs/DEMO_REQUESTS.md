# Live hosted Postman demonstration

Import `postman/FuelRouteIQ.postman_collection.json` and `postman/FuelRouteIQ.hosted.postman_environment.json`. `base_url` is `https://fuelroute-iq.onrender.com`. POST JSON to `{{base_url}}/api/v1/routes/optimize/`. No client ORS key is needed.

### Long strict and repeat

```json
{"start":"Chicago, IL","finish":"Dallas, TX","location_mode":"strict","initial_fuel_gallons":50}
```

Observed public live result: 964.798887 miles, two stops (7466, 64679), 96.479889 gallons consumed, 46.479889 bought, $139.44 cash, $147.01 baseline, $7.57 savings, zero end fuel. The dataset is illustrative. Repeat: route cache true, directions/geocoding zero. Cache misses can occur after TTL/data revisions; use actual metadata rather than asserting every first request is cold.

### Changed fuel / estimated qualification

```json
{"start":"Chicago, IL","finish":"Dallas, TX","location_mode":"estimated","initial_fuel_gallons":45}
```

Road cache is shared. The current public fixture has reviewed points only; estimated mode does not invent extra sites. The full assessment import adds city approximations with explicit qualifications.

### Short valued inventory

```json
{"start":"Chicago, IL","finish":"Milwaukee, WI","initial_fuel_gallons":50,"initial_fuel_cost_usd":"200.00"}
```

Observed road 98.005709 miles; consumption 9.800571 gallons, purchased zero, cash $0.00, economic consumed value $39.20 and remaining asset $160.80. `initial_fuel_cost_usd` is the total owned inventory value, not a per-gallon price. Without it economic value is null.

### Other live cases

```json
{"start":"New York, NY","finish":"Miami, FL"}
```

```json
{"start":"Los Angeles, CA","finish":"Denver, CO"}
```

```json
{"start":"Seattle, WA","finish":"San Francisco, CA"}
```

Current public strict results: New York–Miami 1291.234006 miles/four stops/$238.91; LA–Denver 1036.823078/three/$166.45. Seattle returns 422 `UNREACHABLE_FUEL_GAP`, its actual 815.658243-mile road and diagnostic mile gap. Road/price revisions may alter results. Previously unseen Austin–Houston returned a real 168.877505-mile road, no purchase, and 16.887751 gallons consumed.

Inspect road GeoJSON/provider/license, stop coordinate quality/source and before/after quantities; fuel conservation and baseline; `cost_basis.price_basis`; dataset revision; separate outbound calls; timeline pairs at equal mile markers. City endpoints use local representative points; precise `233 S Wacker Dr, Chicago, IL` uses separately cached Pelias.

Foreign finish `Toronto, ON` → 422; excess initial fuel 51 → 400; malformed JSON → 400. Public throttles → 429/Retry-After. Provider failures are structured, never silently replaced with recorded geometry. Avoid quota/load demonstrations while filming; the bounded recorded and mocked tests cover those paths.
