# FuelRoute IQ

A Django road-trip fuel API with explainable, minimum-cost fuel purchases, explicit geographic uncertainty, and a small Leaflet interface. The assessment defaults are **500 miles range, 10 MPG, 50 gallons capacity, and an initially full tank**.

**Production preparation.** See [PRODUCTION_DEPLOYMENT_REPORT.md](PRODUCTION_DEPLOYMENT_REPORT.md) for the verified deployment status and [SUBMISSION_LINKS.md](SUBMISSION_LINKS.md) for published links. The `.env.example` selects a credential-free demo that replays five **real recorded OSRM road routes**. Live OpenRouteService (ORS) is implemented separately and requires a free API key. Recorded requests report **zero external directions calls**. Tests exercise ORS with mocked responses and independently validate optimization. See `IMPLEMENTATION_REPORT.md` and `ASSESSMENT_READINESS_AUDIT.md` for actual evidence and submission limitations.

## Run locally

Python **3.12+**. Tested dependency versions: Django **6.1.2**, Django REST Framework **3.18.3**, Shapely **2.2.0**, pyproj **3.8.0**; complete transitive/test dependency pins are in `requirements.lock`. Official release checks: [Django security release](https://www.djangoproject.com/weblog/2026/oct/06/security-releases/), [DRF compatibility](https://www.django-rest-framework.org/).

Windows PowerShell, in this repository:

```powershell
# Supplied full assessment CSV already exists at the workspace root:
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
.\.venv\Scripts\python.exe manage.py runserver
```

For a fresh clone without the private CSV, use `scripts/setup.ps1 -Demo`. It imports 31 explicitly illustrative price records for 31 reviewed station sites across the recorded corridors. These hand-authored test values are never represented as assessment observations or current pump prices. Import the evaluator's supplied CSV for assessment-price results.

Linux/macOS equivalent:

```sh
sh scripts/setup.sh --demo  # omit --demo when full source CSV is available
.venv/bin/python manage.py runserver
```

Open **http://127.0.0.1:8000/**. Try Chicago, IL → Dallas, TX (long) and Chicago, IL → Milwaukee, WI (short). Identical endpoints return a legitimate zero-length route locally. The first four recorded pairs have feasible fueling demonstrations. Seattle → San Francisco returns real route geometry with an honest priced-station coverage gap. Other endpoint pairs in recorded mode return `RECORDED_ROUTE_UNAVAILABLE`; configure live ORS for arbitrary US route geometry.

Manual setup (activate the virtual environment first):

```sh
python -m pip install -r requirements.lock
# Copy .env.example to .env if not already present.
python manage.py migrate
python manage.py createcachetable
python manage.py import_locations --cities
# Place the original supplied CSV in data/raw/fuel-prices-for-be-assessment.csv.
python manage.py import_fuel  # or: python manage.py import_fuel fixtures/public_demo_prices.csv
python manage.py import_locations --verified data/reference/verified_stations.json
python manage.py check
python manage.py runserver
```

The original workspace files remain intact. Full source CSV, `.env`, SQLite database, and virtual environments are ignored by Git. Reimport creates a new auditable dataset; reapply verified enrichment after any fuel reimport. All imported raw rows remain attached to their dataset. Imports are transactional.

## Live routing

Get a free personal key from [HeiGIT](https://account.heigit.org/), then set these values in your local `.env`:

```dotenv
ROUTING_PROVIDER=ors
ORS_API_KEY=your_private_key_here
ORS_API_BASE_URL=https://api.heigit.org/openrouteservice
ORS_GEOCODING_BASE_URL=https://api.heigit.org/pelias/v1
```

Restart the server. The current documented endpoint is **POST `https://api.heigit.org/openrouteservice/v2/directions/driving-car/geojson`**. It returns geometry, distance and duration for each uncached coordinate pair. Cached requests make zero directions requests. There are deliberately **no automatic retries**: honoring the single-call budget also prevents accidental quota bursts. Connection timeout is 5 seconds; HTTP read/write timeout is 20 seconds. Provider failures are structured, and failed routes are not cached. A different provider/route may have insufficient verified coverage even for the demo endpoints; this correctly returns a coverage gap.

[Public ORS directions restrictions](https://openrouteservice.org/restrictions/) include a **6,000 km route limit**. Account quotas depend on the current plan; confirm them in the ORS dashboard rather than treating a hardcoded request quota as permanent. No paid service is required. Response metadata counts attempted outbound directions and geocoding requests separately, including failed attempts. Provider account usage is not inferred from these application metrics.

Common `City, ST` endpoints resolve from the bundled **2026 US Census Places Gazetteer** with no online geocoding. Use two-letter state codes or full state names; an optional trailing USA is accepted. Only the 50 states and DC are supported. Ambiguous and unknown city names are rejected. Optional precise input `100 Main St, Chicago, IL` uses one HeiGIT Pelias `GET /pelias/v1/search` request when required, and a separate 30-day cache. Country/state, address layer, confidence and consistency with the known locality are checked. No station addresses are bulk geocoded. Coordinates as endpoint input are intentionally unsupported, avoiding a misleading bounding-box US check. Endpoints resolved as cities are Census internal points, not precise departure addresses.

## API

`POST /api/v1/routes/optimize/`, JSON:

```json
{"start":"Chicago, IL","finish":"Dallas, TX","location_mode":"strict","initial_fuel_gallons":50}
```

```powershell
$body = @{ start = 'Chicago, IL'; finish = 'Dallas, TX'; location_mode = 'strict' } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/routes/optimize/ -Method Post -ContentType application/json -Body $body
```

Optional fields:

| Field | Default / validation |
|---|---|
| `location_mode` | `strict`; alternatively `estimated` |
| `mpg` | 10; 1–100, up to 3 decimal places |
| `range_miles` | 500; 1–500, up to 3 decimal places |
| `initial_fuel_gallons` | derived capacity = range / MPG; 0–capacity, up to 6 decimal places |
| `initial_fuel_cost_usd` | null; known total purchase value of initially owned fuel, not a per-gallon price |

Unknown fields, malformed JSON, non-finite numbers, unsupported location formats and excess fuel are rejected. This assessment uses the default vehicle; optional settings always derive capacity from range/MPG and cannot extend the 500-mile maximum.

Responses include:

- `route`: true road LineString, distance miles/meters, duration, provider, recording provenance when applicable.
- `vehicle`, `fuel_stops`: exact model assumptions, selected observation prices and their ranges/conflicts, gallons, cost, pre/post fuel, source coordinates, precision/confidence, lateral distance and explanations. `detour_miles` is null because no routed detour was measured.
- `fuel_summary`: consumption, purchases, cash spend, end fuel, initial/acquired value, feasible-baseline spend and savings.
- `baseline`: separate deterministic policy and its purchases; unavailable comparisons are null.
- `fuel_timeline`: start, paired before/after purchases at identical mile markers, destination.
- `warnings`, `meta`: mode, coverage, dataset revision, conditional optimality scope, call counts, cache hits and measured request/routing/projection durations.

`GET /api/v1/health/` reports startup/dataset/provider configuration. `GET /api/v1/stats/` reports import audit, coordinate coverage, and cumulative counters from the local cache lifetime. Health is a process readiness summary, not a live provider connectivity probe. Public verification artifacts are in `artifacts/public/`; private assessment evidence stays local.

| Status | Meaning |
|---|---|
| 400 | malformed/unsupported input |
| 422 | foreign/unknown/ambiguous location, unavailable offline route, route limit, or `UNREACHABLE_FUEL_GAP` |
| 429 | provider quota/rate limit |
| 502 | malformed/failed provider response |
| 503 | missing key, provider timeout/auth/network failure |
| 500 | unexpected internal error, with a log-correlation request ID and no client traceback |

Errors have `error.code`, `error.message`, and `error.details`; no client traceback. Coverage errors explain the missing modeled mile range and eligible coordinate quality. Lack of dataset coverage is **not** proof of absence of real fuel stations.

## Fuel accounting and proof scope

`consumed = road_miles / MPG`; `purchased = sum(stop gallons)`; `initial + purchased - consumed = destination fuel`. Capacity is never exceeded; negative fuel is infeasible.

`total_refueling_spend_usd` and compatibility field `total_fuel_cost_usd` both mean **money spent buying fuel during this journey**. Initially owned fuel is excluded. A 95-mile trip with a full tank legitimately buys $0 while consuming about 9.5 gallons. Its economic fuel cost is unknown when the initial price is unknown. The supplied `initial_fuel_cost_usd` is reported as `initial_fuel_value_usd`; `total_acquired_fuel_value_usd` is initial value plus purchases only when initial valuation is supplied. Acquired value includes any remaining fuel; it is not allocated economic cost of consumption.

`economic_fuel_cost_usd` separately values consumed fuel using FIFO inventory accounting only when the initial inventory value is known (or no initial inventory exists). `remaining_fuel_value_usd` values the unconsumed asset. Both are null when owned starting fuel is unvalued. For the recorded short trip with 50 gallons valued at $200, cash purchases remain $0, consumption value is $38.01, and remaining value is $161.99. Savings still compare en-route cash purchases under identical starting fuel and candidate assumptions. The UI exposes all three distinctions and accepts an optional starting inventory value.

Internal distances/fuel/prices/costs use `Decimal`. Money is rounded half-up only for final USD display; exact aggregate and per-stop unrounded cost strings are included for audit. Summed displayed stop cents can differ from the correctly rounded aggregate. Numeric gallons/mile markers are serialized at float precision; decisions never use rounded display values.

The greedy optimizer considers all eligible stations in increasing route order. At each station buy enough to reach the next **strictly cheaper** full-tank-reachable station, or the destination; otherwise fill up. Initial fuel is used first. Co-located candidates collapse to the cheapest observation. A monotonic stack finds next cheaper nodes in O(n); sorting is O(n log n). Terminal destination is virtually free. If a cheaper opportunity exists, extra earlier fuel can be postponed without increasing spend. If none exists, buying at the current price up to capacity cannot cost more than later reachable purchases. This exchange argument establishes minimum spend **only for the fixed ordered candidates, constant snapshot prices, divisible purchases, and zero modeled detours**. It does not optimize route choice, real highway access, opening hours, fuel freshness or global station coverage.

`tests/test_optimizer.py` contains an independent integer-inventory dynamic program that enumerates every purchase amount at every node. Seeded generated instances compare both expenditure and infeasibility, alongside fractional-price and boundary tests. The baseline stops nearest 80% of the vehicle range among forward candidates reachable on currently owned fuel, ignores prices, and fills up capped by destination need. It uses the exact same initial fuel and candidates. Savings use unrounded policy costs; percentage is null when baseline spend is zero. A feasible full-fill baseline may yield zero savings; it is never presented as a guaranteed discount.

## Geographic trust and ingestion

The supplied price CSV contains **8,151 rows**, 7,531 US rows, 620 Canadian rows, 6,738 total distinct IDs, and 6,626 US IDs. There are **597 conflicting-price IDs overall**, **487 among US IDs**, and 4,617 highway-exit descriptions. The file has **no coordinates or timestamp**. Source SHA256 and full raw observations are retained. Positive finite Decimal prices are required. Repeated OPIS identities retain source-row count, min/max prices, price-conflict flag and identity conflict. The reproducible selected price is an **observed price closest to the median of all valid source observations**, with the lower observation winning a tie. Duplicates retain their observation weight; no observation is guessed to be newer.

The bundled checksummed Census file supplies 32,071 US/DC place records. Only an unambiguous normalized city/state match attaches an **approximate city internal point**. No fuzzy address match or invented confidence is used. Names with distinct duplicate matches and unmatched localities remain unresolved. Identical OPIS IDs across different localities are ineligible.

`data/reference/verified_stations.json` contains 31 individually reviewed official operator site records, expanded from the original six. Three along the recorded long route are Pilot #442 Hayti MO, Flying J #607 West Memphis AR, and Pilot #118 Benton AR. The original alternate-corridor references are preserved, and additions cover I-95, I-15/I-70 and portions of I-5 and I-57/I-30. Evidence contains station number/name, locality, highway context, URL, coordinates and review timestamp/notes. Enrichment validates matching source brand/number/locality/road context, finite coordinates near a known US locality, HTTPS provenance and non-future review timestamps. The importer is currently intentionally restricted to Pilot/Flying J numbered sites; other brands require extending the identity verifier. Reviewing an operator-published site point is not a surveyed pump/entrance or certification of road accessibility. These few location facts are cited individually; no proprietary bulk location dataset or site text is redistributed.

- **Strict (default)**: verified station points only; coverage failure returns 422. Even a successful strict plan has conditional no-detour optimality, not navigation certification.
- **Estimated**: verified and approximate city candidates; visible conditional/estimated labels, and no actionable/geospatial optimality claim.

Projection uses a Shapely STRtree over metric route segments, CONUS Albers projection (local azimuthal equidistant outside CONUS), geodesic cumulative segment distances and scaling to provider road distance. Off-route distances are measured geodesically to the projected route. Candidates farther than the configured **5-mile lateral corridor** are rejected. Mile markers are estimates; lateral distance is **not routed detour mileage**. Repeated-route ambiguities are rejected. Routes and stops are sorted for monotonic progress.

## Performance and caches

SQLite stores source/import data; Django database cache stores route, geocoding and optimization results independently. Route keys include ordered normalized endpoint coordinates, provider/profile/version/options; no fuel/price setting is part of this key. Plan keys include route content, dataset revision, vehicle, mode, cost basis and corridor settings. Reimport or verified enrichment invalidates plan identity without requesting another route. Cache TTLs default to **24h route / 30d geocoding / 1h plan**.

Bounded process-local lock stripes coalesce concurrent identical misses within one server process. Database cache shares results across processes but **cross-process simultaneous cold misses can each make a directions call**. Production uses one Gunicorn worker with four threads so coalescing and quota updates share locks. Scaling to multiple workers requires an atomic distributed limiter and coalescing design. A conservative indexed bounding prefilter reduces candidate work. Geometry construction is O(v), indexed candidate projection approximately O(n log v), optimizer O(n log n); first estimated plans are slower than warm cached plans. Metrics identify recorded reads separately; per-request metadata separates endpoint resolution, provider request time, projection, greedy optimization and baseline simulation. Cached requests report zero work for skipped phases. Run `python -m scripts.validate_matrix` for the five-pair matrix and timing evidence, or `python -m scripts.capture_evidence` for the original four example responses; it clears the local cache and performs 24 local API requests, with no live directions calls in recorded mode. Do not run it against ORS casually: it intentionally exercises distinct routes.

## Verification

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pip check
python -m ruff check .
python -m ruff format --check .
python -m mypy optimizer
python -m pytest --cov=api --cov=routing --cov=stations --cov=optimizer --cov-report=term-missing
python -m scripts.capture_evidence
```

The original greedy engine is preserved and cross-checked with both 200 original generated integer-inventory cases and 200 fractional-unit cases in one additional oracle test. Real database-cache concurrency is exercised separately.

All normal tests block HTTP calls; live tests are skipped unless both `RUN_LIVE_TESTS=1` and `ORS_API_KEY` are set. The opt-in live test makes exactly one ORS call. Mocked provider call counts validate 1→0 directions caching without disguising mocks as actual external service validation. CI uses labelled source-independent public test prices; the exact full-dataset audit test is skipped when the private supplied CSV is absent. Remote CI evidence is recorded in FINAL_SUBMISSION_AUDIT.md after publication.

Import `postman/FuelRouteIQ.postman_collection.json` into Postman. Run all 11 requests in order, including the five corridors, cache reuse, foreign input, known initial value and changed initial volume. A successful live key is still needed to validate ORS, and no mocked result is a substitute. It can also run using the free Newman/Postman CLI runtime. Clear cache using `python manage.py shell -c "from django.core.cache import cache; cache.clear()"` before a first-miss demonstration. The collection distinguishes recorded zero external calls from ORS calls. See `docs/LOOM_GUIDE.md` for a <=5-minute shot list.

## Sources and licenses

- Source price dataset: supplied for the assessment; sharing rights are unspecified. The full CSV and original 12-row excerpt are excluded from the review package. `fixtures/public_*` contain hand-authored, clearly labelled illustrative test values under CC0, never assessment prices. See `DATA_SOURCES_AND_LICENSES.md`.
- [2026 Census Gazetteer](https://www.census.gov/geographies/reference-files/2026/geo/gazetter-file.html): federal public data, source manifest and checksums bundled. These are internal representative points, not fuel stations. `scripts/download_gazetteer.py` refreshes it only when explicitly invoked.
- Thirty-one reviewed coordinate facts: individual official Pilot/Flying J pages cited in `verified_stations.json`; brand assets/site copy not included; no live prices read.
- [OSRM](https://project-osrm.org/docs/v5.24.0/api/) routes recorded with five explicit directions requests across both phases (three additional requests in Phase 2); original source URLs, UTC recording time, summary, waypoints and source-response hashes are preserved. OpenStreetMap-derived geometry is attributed under [ODbL](https://www.openstreetmap.org/copyright). `scripts/record_routes.py` is an explicit recording utility, never run by the server/tests.
- Leaflet 1.9.4 is vendored with its BSD-2-Clause license. A bundled public-domain Natural Earth state basemap works entirely locally, with source manifest/checksums in `data/reference/map_source.json`. It supplies visual context only and is never used for station positioning or US validation. Optional OpenStreetMap street tiles preserve attribution and normal browser caching; no bulk tile downloads. Street tiles need network access and may be blocked in embedded browsers; the local basemap remains available.
- Application code is original assessment work. No license grant is assumed for the private source files. Public optimization is quota-limited. Production requires DEBUG=false, a private secret and durable PostgreSQL; HTTPS headers and WhiteNoise serve the deployed application.

## Submission

Review `FINAL_TECHNICAL_AUDIT.md` and `ROUTING_AND_COVERAGE_REPORT.md`, configure and validate a genuine HeiGIT key, and record the Loom using real responses. The ZIP is a source-review artifact, not a claim of final live submission readiness. The intended remote is `https://github.com/ShyanCS/FuelRouteIQ`. Publication and free deployment are authorized in the final phase; only verified links and results are listed in SUBMISSION_LINKS.md. No employer submission is performed.

## Current migration and controlled live verification

The [official migration notice](https://ask.openrouteservice.org/t/deprecating-api-openrouteservice-org-in-favour-of-api-heigit-org/7912) specifies the HeiGIT routing and Pelias prefixes. The [official FAQ](https://giscience.github.io/openrouteservice/frequently-asked-questions#when-and-how-does-my-quota-reset) distinguishes daily 403 quota exhaustion from minutely 429 limits. The adapter maps quota exhaustion to 429 and key failures to 503, disables redirects and retries, and includes provider base URL in cache identity.

No genuine key is currently configured. Two real invalid-sentinel requests confirmed that the new directions and geocoder gateways reject invalid authorization; this does not validate successful routing. To complete valid-key checks, activate the environment and run:

```sh
# Set ORS_API_KEY in local .env. Do not put it in source or a command body.
python -m scripts.validate_provider --live
# Optional single-call live pytest: set RUN_LIVE_TESTS=1, then:
python -m pytest -m live
```

The live matrix requests five distinct geometries once each, then reuses them for mode/initial-fuel changes and repetitions. It records infeasible coverage honestly. ORS may choose different corridors from recorded OSRM; station eligibility is recomputed from each returned geometry. Actual live geometry and ORS-vs-OSRM corridor comparison remain unverified until a valid key is supplied.

## Review package

`REVIEW_PACKAGE.zip` contains the complete source, tests, migrations, lockfile, five recorded road fixtures, public mapping data, reviewed coordinate facts, illustrative price fixtures and sanitized evidence. It excludes `.env`, credentials, databases, cache files, Git internals, virtual environments and private assessment price files. An independent reviewer can extract it anywhere, use `scripts/setup.ps1 -Demo` or `sh scripts/setup.sh --demo`, and run the tests. The private full-dataset audit and valid-key test will be reported as skipped when their required inputs are absent.

## Production deployment

`render.yaml` declares one **free** Render Python web service. `scripts/render_build.sh` installs the lockfile and collects versioned static assets. `scripts/render_start.sh` applies migrations, creates the shared PostgreSQL cache table and idempotently seeds 31 public illustrative records before starting one Gunicorn worker with four threads. No ephemeral SQLite storage is used in production.

Set `DJANGO_DEBUG=false`, a privately generated `DJANGO_SECRET_KEY` of at least 50 characters, pooled PostgreSQL `DATABASE_URL` with SSL, direct `DATABASE_URL_UNPOOLED` for migrations, and `ROUTING_PROVIDER=recorded` or `ors`. Render supplies the allowed public hostname. For another host set `DJANGO_ALLOWED_HOSTS` explicitly. ORS keys stay in server-side secret settings. No cross-origin browser access is enabled; Postman and other HTTP clients work directly.

Public route requests are limited to 30/minute per client and 500/day across the service, including malformed/cached requests. Health probes do not consume this quota. These conservative assessment-demo limits protect the routing account; they are not the provider's contractual quota. One trusted Render proxy supplies the client address. Multi-worker scaling requires an atomic distributed rate limiter.

`seed_demo` refuses to overwrite an assessment dataset. Identical active prices and verified evidence preserve the dataset revision on restarts. A normal assessment import creates a new audit dataset; `import_fuel --reuse PATH` preserves an identical active import. Reapply verified enrichment to a new assessment dataset. The public service uses only hand-authored test prices. Privately import the original employer file for assessment-price results; publishing it or its station prices is not authorized.

A free Render instance can sleep after 15 minutes and take approximately a minute to wake. Its filesystem is ephemeral; durable station/cache data lives in the dedicated free Neon PostgreSQL project. Free quotas and account limitations can suspend availability; no uptime guarantee is claimed. See the deployment report for current sources, actual execution and restart evidence.

## Final endpoint audit correction

The original Seattle–San Francisco recording is retired: Census's offshore San Francisco point snapped 29,953 m onto Point Reyes Lighthouse Road, so the historical 835.41-mile result is not a valid San Francisco city-route demonstration. The old file is preserved byte-for-byte with a retirement manifest. A single sourced GeoNames populated-place reference (CC BY 4.0, attributed) now corrects this endpoint only; station approximations and original Census records are unchanged. One additional real OSRM request produced a corrected **808.901515-mile** road with **12,369 points** and a **2.502-metre destination snap**. Both fuel modes still return an honest gap. Active route manifest: five pairs; six road files retained including the retired one.

Every new API road is now rejected before caching if its first/last coordinate lies over 1 km from the requested endpoint. This is a conservative proximity guard, not proof of highway/station access. The route-cache namespace was advanced so previously unchecked cached geometry cannot bypass it. Endpoint source and representative-point qualification are returned in metadata. Precise-address locality checks use the reviewed endpoint reference when present. Other political/place representative points can still be unsuitable: such routes return a useful error requiring a precise address, rather than quietly accepting distant snapping.

Final endpoint-corrected local suite: **306 passed, 1 skipped in 228.23 s**, **95.30%** backend statement coverage (913/958). The sole local skip requires a genuine ORS key. No mock or recording is claimed as successful authenticated ORS. Full evidence is in `artifacts/public/final-tests.txt` and `final-coverage.json`.
