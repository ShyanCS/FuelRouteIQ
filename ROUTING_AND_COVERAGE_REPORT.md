# Routing and coverage report

Historical Phase 2 evidence. Final production/publication status and later fixes are authoritative in FINAL_SUBMISSION_AUDIT.md, FINAL_IMPLEMENTATION_REPORT.md and PRODUCTION_DEPLOYMENT_REPORT.md.
Phase 2, 12 October 2026. Full assessment-price results and public illustrative results are separate. Nothing has been deployed or published.

## Current provider contract

| Operation | Current default |
|---|---|
| Road directions | `POST https://api.heigit.org/openrouteservice/v2/directions/driving-car/geojson` |
| Address lookup | `GET https://api.heigit.org/pelias/v1/search` |
| Authentication | Private personal key in server-side `Authorization` header; no browser key |
| Limits/timeouts | Public 6,000 km route limit; 5 s connect / 20 s read/write; no redirect, retry or hidden fallback |

The [official migration notice](https://ask.openrouteservice.org/t/deprecating-api-openrouteservice-org-in-favour-of-api-heigit-org/7912) specifies the new prefixes. GeoJSON summary parsing and longitude/latitude order follow the [current directions documentation](https://giscience.github.io/openrouteservice/api-reference/endpoints/directions/). The [official FAQ](https://giscience.github.io/openrouteservice/frequently-asked-questions#when-and-how-does-my-quota-reset) identifies daily quota 403 and minutely 429 responses; the adapter distinguishes quota from authentication errors. Account quotas are read from the dashboard, not fabricated from application counters.

No genuine key is configured. Two controlled real HTTP probes used a deliberate invalid, non-secret sentinel. Both returned the adapter's `PROVIDER_AUTH_ERROR`: **one directions attempt, one geocoding attempt**. This proves reachable gateway rejection at the new paths, not successful authorization, routing or geocoding. Details/timings are in `artifacts/provider-gateway-probes.json`.

Valid-key ORS, live short/long roads and ORS-versus-OSRM geometry/eligibility comparison remain **UNVERIFIED**. Configure the key in local `.env` and run `python -m scripts.validate_provider --live`; this requests five new geometries once each and reuses them for mode/volume/repetition checks. Each response is projected independently; no station or geometry is moved to force feasibility.

## Coordinate and price coverage

The full private CSV contains 8,151 source rows, 7,531 US rows, 620 Canadian rows and 6,626 deduped US identities. Conflicting IDs: 597 overall / 487 US. Every original row remains available locally for audit.

| Precision | Full assessment dataset |
|---|---:|
| Reviewed operator station site | 31 |
| Approximate Census city point | 5,983 |
| Unresolved | 612 |

Review expanded six sites to 31: 27 explicitly selected corridor candidates, 26 factual page records retrieved, 25 accepted additions. One brand mismatch was rejected and one unavailable page unresolved. Source URLs, retrieval hashes, timestamps, locality/road checks and review notes are included. Cocoa #1096 has a disclosed source exit discrepancy; its store identity/site point is established separately. No live price was harvested.

The public demo contains 31 reviewed sites with **illustrative test prices**, not the private source prices. Import the evaluator's supplied CSV for assessment-price plans and the broader city fallback. Public test fixtures do not assert national fuel-price availability.

## Five representative roads — actual assessment-price API results

All road geometries below are actual recorded OSRM responses. Three were obtained in Phase 2; the original two recordings were preserved byte-for-byte. These rows have **zero runtime external directions calls and zero endpoint geocoding calls**; a cold recorded pair reads one fixture, mode changes/repeats read none. Geometry availability is independent of fueling feasibility.

| Pair / mode | Road miles | Candidate quality / count | Stops | Required/consumed gallons | Purchased gallons | Cash spend | Result |
|---|---:|---|---:|---:|---:|---:|---|
| Chicago–Dallas strict | 961.473868 | reviewed / 6 | 2 | 96.147387 | 46.147387 | $145.60 | PASS |
| Chicago–Dallas estimated | 961.473868 | mixed eligible / 160; chosen pins approximate | 4 | 96.147387 | 46.147387 | $134.57 | PASS, conditional |
| Chicago–Milwaukee strict | 95.026421 | reviewed / 0 needed | 0 | 9.502642 | 0 | $0.00 | PASS; initial value unknown |
| Chicago–Milwaukee estimated | 95.026421 | eligible / 35; no purchases | 0 | 9.502642 | 0 | $0.00 | PASS |
| New York–Miami strict | 1280.053363 | reviewed / 11 | 3 | 128.005336 | 78.005336 | $271.58 | PASS |
| New York–Miami estimated | 1280.053363 | mixed eligible / 191 | 4 | 128.005336 | 78.005336 | $226.72 | PASS, conditional |
| Los Angeles–Denver strict | 1036.833144 | reviewed / 8 | 2 | 103.683314 | 53.683314 | $197.46 | PASS |
| Los Angeles–Denver estimated | 1036.833144 | mixed eligible / 41 | 3 | 103.683314 | 53.683314 | $176.04 | PASS, conditional |
| Seattle–San Francisco strict | 835.414057 | reviewed / 3 | unavailable | 83.541406 required | unavailable | unavailable | 422 `UNREACHABLE_FUEL_GAP` |
| Seattle–San Francisco estimated | 835.414057 | eligible / 22 | unavailable | 83.541406 required | unavailable | unavailable | 422 `UNREACHABLE_FUEL_GAP` |

The final two rows give fuel required to complete the proposed road, not actual fuel consumed on a successfully feasible journey. Purchased quantity, expenditure and savings are unavailable; no zero-cost or invented stop plan is substituted.

The supplied file has only 16 California rows / eight identities, none on California I-5, and sparse Oregon coverage. The strict final fueling opportunity projects around mile 212.216; estimated around 259.448; destination is mile 835.414, leaving a greater-than-500-mile priced-candidate gap. Current geometry therefore cannot be planned using this source at the allowed range. Improving coordinate accuracy cannot create missing source prices.

Coordinate counts: Chicago–Dallas 9,539; Chicago–Milwaukee 1,893; New York–Miami 15,530; Los Angeles–Denver 12,706; Seattle–San Francisco 14,074. Source/capture/hash/summary/waypoint provenance remains in `fixtures/routes/`. OSRM acquisition counts across both phases: five explicit requests, of which three in Phase 2. Runtime replay is never reported as a live call.

## Cache and latency evidence

The full matrix makes five cold recorded reads and shares road geometry between strict and estimated modes. Repeating Chicago–Dallas, changing initial fuel to 45 gallons, and changing mode each make zero directions calls. Separate executable ORS transport tests validate 1→0 call counts, provider-base/reverse-route key separation, dataset-revision plan invalidation, expired route reload and no failure caching. Actual DatabaseCache concurrency yields one mocked provider request across four consistent concurrent API results; successful live coalescing remains key-dependent.

Measured local processing uses actual SQLite/APIClient responses and real recorded road shapes, not only mocks. Latest raw cold/warm, projection, greedy and baseline timing values are in the local assessment matrix and the public illustrative matrix. Network durations are separately zero for replay. The 11-request Newman run averaged 669 ms in a concurrent local verification run; this includes payload serialization/errors and is not an ORS network-latency claim. Pure greedy execution in representative full-CSV cases was sub-millisecond. Exact numerical timings vary with background tests and are not service-level guarantees.

## Model limits

The default driver starts with 50 gallons already owned, capacity 50, MPG 10 and range 500. Minimum purchase spend applies to fixed route and eligible ordered nodes, constant selected snapshot prices, divisible purchases and zero modeled detours. Economic FIFO consumption value is unavailable when starting inventory is unvalued. Baseline uses identical initial inventory/candidates and compares cash purchases. No global route-cost, national station coverage, navigable pump entrance, live-price, opening-hours or reserve-fuel guarantee is made.

Strict is conservative; estimated accepts government city points with prominent conditional labels. Every request recomputes or uses versioned cached eligibility for that actual road. Successful ORS geometry must be evaluated before claiming that these OSRM corridor results transfer to it.

## Final endpoint audit correction

The original Seattle–San Francisco recording is retired: Census's offshore San Francisco point snapped 29,953 m onto Point Reyes Lighthouse Road, so the historical 835.41-mile result is not a valid San Francisco city-route demonstration. The old file is preserved byte-for-byte with a retirement manifest. A single sourced GeoNames populated-place reference (CC BY 4.0, attributed) now corrects this endpoint only; station approximations and original Census records are unchanged. One additional real OSRM request produced a corrected **808.901515-mile** road with **12,369 points** and a **2.502-metre destination snap**. Both fuel modes still return an honest gap. Active route manifest: five pairs; six road files retained including the retired one.

Every new API road is now rejected before caching if its first/last coordinate lies over 1 km from the requested endpoint. This is a conservative proximity guard, not proof of highway/station access. The route-cache namespace was advanced so previously unchecked cached geometry cannot bypass it. Endpoint source and representative-point qualification are returned in metadata. Precise-address locality checks use the reviewed endpoint reference when present. Other political/place representative points can still be unsuitable: such routes return a useful error requiring a precise address, rather than quietly accepting distant snapping.
