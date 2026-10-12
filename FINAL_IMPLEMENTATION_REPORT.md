# Final implementation report

Final phase, 13 October 2026. Current executed gates and counts are in `FINAL_SUBMISSION_AUDIT.md` and `artifacts/public/production-final-verification.json`. The actual application and source are public; live authenticated routing and the supplied private CSV importer are verified independently.

## Request flow and architecture

Django 6.1.2 / DRF validate a bounded JSON body and vehicle/location options. Census resolves unambiguous US city/state endpoints; a separately cached Pelias adapter resolves precise addresses. A provider/version/ordered-coordinate road key coalesces local concurrent misses and obtains one real GeoJSON road. Geometry and endpoint snap validation occur before caching. Indexed projection discovers eligible priced stations along this geometry. A distinct revision/vehicle/mode/geometry plan cache stores Decimal greedy purchases, baseline simulation, FIFO inventory accounting, explanations and a correctly paired fuel timeline. Leaflet uses this actual JSON for every metric and marker.

`stations` holds immutable raw import audits, deduplicated active identities, coverage and reviewed enrichment; `routing` holds provider/geocoder/cache/projection; `optimizer` is framework-independent typed math; `api` validates/coordinates/serializes; `demo` is a small dependency-light interface. SQLite remains local; production station/cache storage is TLS PostgreSQL. Gunicorn/WhiteNoise supply production process/static serving. All dependency versions are pinned.

## Final fixes

- Current HeiGIT endpoints/authentication and actual directions/Pelias responses verified with the securely configured genuine key. Real short/long, fuel/mode cache reuse, invalid authentication, forced real-network deadline and unsupported route failures checked; no silent fallback or automatic retry.
- San Francisco's offshore Census point had incorrectly snapped to Point Reyes in an old recording. Preserve/retire that file; use a sourced GeoNames endpoint reference, new actual road recording, and reject endpoints snapping over 1 km before road caching. Station approximations and original Census observations remain unchanged.
- Production PostgreSQL URLs without query options no longer fail initialization; required TLS and connection bounds are regression-tested. Deployment is actually public, secrets server-side, with database-aware HTTP health and idempotent public seed.
- Added aggregate minute throttle alongside client/day policies to protect shared vendor quota; synchronized updates within the deliberately single threaded worker. Public health is not throttled.
- An intermittent full-suite SQLite cache read/write race was reproduced as SQLITE_LOCKED. Local `SQLiteDatabaseCache` serializes only cache SQL using one reentrant lock; production PostgreSQL keeps the standard backend. Existing simultaneous-request assertions are preserved. Cross-process locking is outside this local guarantee.
- API road output and Leaflet attribution now expose current ORS CC BY-SA 4.0 terms even for cached geometry. Corrected stale live-provider badge; DOM text nodes escape user endpoint labels.
- Coverage errors expose price basis/revision/quality in metadata; no-dataset no-purchase plans honestly report unavailable price data. Plan namespace advanced independently of route cache to prevent stale schema/warnings.
- Public Postman environment, pinned Newman, fresh-clone setup, privacy allowlists, deployment scripts and under-five-minute video materials finalized. No API key or private assessment CSV is published.

## Data and finance

Original assessment file: 8,151 rows, 7,531 US/620 Canadian rows; 6,626 deduplicated US identities, 487 US conflicting-price identities, 597 overall, and 4,617 highway-exit descriptions. Positive finite observed Decimal prices only. The deterministic selected observed price is closest to the weighted source-row median, lower tie; no date/freshness is invented. Raw rows, hashes, conflicts and identity mismatches remain auditable. Full import coverage: 31 reviewed sites, 5,983 city approximations, 612 unresolved. Public demo: 31 reviewed sites and 31 independently authored illustrative prices; estimated mode does not manufacture broader priced coverage.

Default range 500 miles, efficiency 10 MPG, derived capacity 50 gallons, initially full tank. Conservation is exact in the calculation model; negative fuel/capacity breaches are rejected; zero arrival fuel is permitted. Initial fuel is an owned asset. Cash purchases and consumed fuel are distinct. Unknown initial value yields null economic consumption cost; known value enables FIFO consumption and remaining asset valuation. Savings compare identical initial volume and candidates, use unrounded spend and report percent only when baseline spending is positive. Final money rounding is half-up; exact costs remain available.

## Mathematical scope and geography

Greedy next-strictly-cheaper reachable selection minimizes expenditure for a fixed ordered route/candidate set, fixed prices, divisible purchases, capacity constraints and zero modeled detours. Destination is virtually free; initial inventory and equal-price/co-located candidates are handled consistently. A monotonic stack plus sorting is O(n log n). Independent DP oracle checks both optimal expenditure and infeasibility with integer and fractional cases. No change to default reserve or range was made. External review's 12,000 additional comparisons are reported as external review evidence, not counted as this phase's executed test suite.

Metric route STRtree projection and geodesic progress/lateral distances implement candidate discovery; projection near-ties/repeated visits are conservatively rejected. A five-mile lateral threshold is not an access route. Strict reviewed coordinates are individually cited operator site facts, not certified pump entrances. Estimated city positions qualify proximity, access, detours and savings. Road/vehicle profile is driving-car, not HGV restriction planning. Price freshness, hours, real detours, truck access, reserve and route-choice optimality remain outside scope.

## Validation and remaining submission actions

The final audit distinguishes full local tests (private CSV + genuine one-call integration), public CI (two explicit absent-private/opt-in skips), recorded roads, mocked error coverage, actual live five-pair matrix and external HTTPS/browser/Postman. Sanitized artifacts accompany source; private matrix with assessment prices remains local. Dependency advisory scan: 36 packages, zero known vulnerabilities, zero skips, point-in-time only. Linux CI and independent public clone verify installation/seed/migrations; PostgreSQL redeploy verifies persistence.

Public Chicagoâ€“Dallas live result: 964.798887 miles, 2 stops, 96.479889 gallons consumed, 46.479889 purchased, $139.44 cash, $147.01 baseline, $7.57 savings. Private CSV on the same live corridor gives different observed-price choices and totals; the public fixture is not substituted for assessment evidence. Seattleâ€“San Francisco has real geometry but no feasible priced plan. Geographic coverage is the material functional limitation. Loom requires the user's microphone/login/recording; deadline receipt timestamp is unknown; employer submission is not performed.
