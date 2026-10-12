# Routing and coverage report

Final phase, 13 October 2026. Genuine authenticated routing is now **PASS**. Geometry is independently projected for each actual provider; recorded/mock success is not substituted for live evidence.

## Current verified contract

- Directions: **POST https://api.heigit.org/openrouteservice/v2/directions/driving-car/geojson**.
- Geocoding: **GET https://api.heigit.org/pelias/v1/search**.
- Private raw Authorization header, server-side only. Longitude/latitude coordinate order; GeoJSON summary distance/duration parsed and validated.
- [Official migration notice](https://ask.openrouteservice.org/t/deprecating-api-openrouteservice-org-in-favour-of-api-heigit-org/7912), [directions reference](https://giscience.github.io/openrouteservice/api-reference/endpoints/directions/), [public restrictions](https://openrouteservice.org/restrictions/).
- Published Standard free plan: directions 2,000/day, 40/min; geocoding 3,000/day, 100/min, [current plan page](https://account.heigit.org/info/plans). These are not reported remaining account quota.
- 6,000 km public road limit; actual Key West–Prudhoe Bay fails 422 on both tries, one directions attempt each, demonstrating failures are not valid cached roads.
- HTTP connect 5s, read/write 20s; no retries or concealed recorded fallback. Actual invalid sentinel auth gave 503 PROVIDER_AUTH_ERROR; valid-key retry on the same uncached pair succeeded with one call. Actual 1ms forced transport deadline gave 503 PROVIDER_TIMEOUT; natural 20s outage is not claimed. Vendor 429/5xx/malformed cases remain deterministic mock evidence; quotas were not exhausted deliberately.

Current [HeiGIT terms](https://account.heigit.org/info/tos): ORS results CC BY-SA 4.0, attribution **© openrouteservice by HeiGIT | Data from OpenStreetMap**. API and UI expose it. Pelias underlying OSM/OpenAddresses/GeoNames/Who's On First provenance is documented. No private CSV price redistribution is inferred from map-data licenses.

## Live calls and corridor evidence

A controlled private-assessment five-pair matrix acquired five real roads once, then reused them across strict/estimated/fuel/repeat changes. All five geometries succeeded; Seattle could not be fueled from eligible priced data. `artifacts/private/live-ors-matrix.json` remains local because it contains assessment prices. An earlier short probe and the opt-in one-call live test are additional real attempts, not included in the five-call matrix total. Provider error probes count separately.

Actual public Chicago–Dallas cold: one directions/zero geocoding; warm and fuel/mode changes zero/zero. Common city inputs resolve locally. Precise Willis Tower address → Milwaukee acquired one Pelias/one directions, then zero/zero on repeat. Browser tiles are separate. Meta counts outbound attempts, not inferred provider account usage.

Recorded OSRM Chicago–Dallas: **961.473868 miles / 9,539 points**; live ORS: **964.798887 / 5,351**. Projection recomputed independently yields the same six reviewed IDs (7466, 60373, 63596, 10077, 64679, 63794), with altered route mile markers. Public illustrative optimum selected 7466/64679; private assessment-price optimum selected 63596/10077, with $146.68 purchases and $15.63 baseline savings on this live corridor. Private totals are aggregate verification, not public per-station price redistribution. No road geometry was altered. `production-corridor-comparison.json` contains coordinate/mile eligibility evidence without assessment prices.

## Actual public HTTPS scenarios — strict mode

All road geometries below were returned by genuine ORS; prices are illustrative. Success rows use reviewed sites only; no purchased fuel is invented for missing plans.

| Case | HTTP | Road miles | Stops | Gallons consumed | Gallons purchased | Cash / failure |
|---|---|---|---|---|---|---|
| long | 200 | 964.798887 | 2 | 96.479889 | 46.479889 | $139.44 |
| short | 200 | 98.005709 | 0 | 9.800571 | 0.000000 | $0.00 |
| new-york-miami | 200 | 1291.234006 | 4 | 129.123401 | 79.123401 | $238.91 |
| la-denver | 200 | 1036.823078 | 3 | 103.682308 | 53.682308 | $166.45 |
| seattle-sf | 422 | 815.658243 | unavailable | unavailable | unavailable | UNREACHABLE_FUEL_GAP |
| unseen-austin-houston | 200 | 168.877505 | 0 | 16.887751 | 0.000000 | $0.00 |

Per-case request, geometry-point count, quality, call counts, cache status and duration are recorded in `artifacts/public/production-http.json`. A cached acquisition reports zero new calls, not zero calls when originally obtained. Both strict and estimated modes are tested; public estimated mode uses the same 31 reviewed-site prices and may not improve feasibility. The full private CSV adds approximate candidates; Seattle still has a gap in both modes. Failed optimization includes real road geometry/coverage; consumption/purchase/cost fields for a nonexistent plan remain unavailable.

## Data coverage and limitations

| Data scope | Reviewed sites | Approximate city identities | Unresolved identities |
|---|---|---|---|
| Original assessment import, 6,626 US identities | 31 | 5,983 | 612 |
| Public 31-row illustrative fixture | 31 | 0 | 0 |

Price source: original 8,151 rows, 7,531 US/620 non-US, no latitude/longitude or timestamps. Price conflicts and identity collisions remain auditable. Reviewed facts cite official operator pages with dates/identity/road context; no proprietary bulk database is claimed. Census points are federal representative locality points, not fuel pumps. A GeoNames CC BY 4.0 reference corrects San Francisco's endpoint only; offshore historical recording is retired and preserved.

Strict coverage is **PARTIAL nationally**. Short unseen US routes within initial range can succeed without priced candidates; long unfamiliar corridors may fail. Estimated mode expands full-CSV candidates while explicitly qualifying proximity, road access, detours and savings. It is not navigation advice or proof of an operational station. 5-mile lateral distance and route mile projection are not routed detour mileage. Zero reserve/zero detours, driving-car profile, constant undated prices and fixed eligible route are the optimization assumptions.

## Observed performance

Initial actual external cold/warm long: **2,597.073 / 473.236 ms**. Cold server pipeline 1,839.753 ms, directions 1,090.625 ms, candidate projection 488.413 ms, greedy 0.107 ms. Historical exact sample in production-first-probe.json; subsequent runs have their own measured timings. These are not mocked estimates, service-spin-up measurements or an SLA. Local APIClient over remote PostgreSQL and recorded fixtures have distinct labelled artifacts and are not used for hosted performance claims.
