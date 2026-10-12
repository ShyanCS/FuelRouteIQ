# FuelRoute IQ

A Django API and Leaflet map that minimizes fuel purchases along a selected US road route. It explains station choices, compares a separately simulated baseline, and makes price and location uncertainty visible.

**[Open the live application](https://fuelroute-iq.onrender.com/)** Â· [API](https://fuelroute-iq.onrender.com/api/v1/routes/optimize/) (POST) Â· [Health](https://fuelroute-iq.onrender.com/api/v1/health/) Â· [GitHub](https://github.com/ShyanCS/FuelRouteIQ)

The deployed application uses genuine authenticated HeiGIT/OpenRouteService directions. Its **31 reviewed station sites use explicitly illustrative prices**, not employer observations or live pump prices. The original supplied assessment CSV is fully supported through the import command, tested locally, and excluded from publication because its redistribution permission is unspecified. Nationwide strict fuel coverage is limited; a route can return real geometry with a useful 422 coverage diagnostic.

Try **Chicago â†’ Dallas**, **Chicago â†’ Milwaukee**, **New York â†’ Miami**, and **Los Angeles â†’ Denver**. Seattle â†’ San Francisco deliberately exposes a current priced-station coverage gap. Free hosting sleeps after inactivity; the initial wake can take about a minute.

## Quick API demonstration

```sh
curl -X POST https://fuelroute-iq.onrender.com/api/v1/routes/optimize/ \
  -H 'Content-Type: application/json' \
  -d '{"start":"Chicago, IL","finish":"Dallas, TX","location_mode":"strict"}'
```

Selected fields from the actual public live response (geometry and station detail omitted here):

```json
{
  "route": {"provider":"ors","recorded":false,"distance_miles":964.7988869999205},
  "vehicle": {"range_miles":500,"mpg":10,"tank_capacity_gallons":50,"initial_fuel_gallons":50},
  "fuel_summary": {
    "gallons_consumed":96.47988869999205,
    "gallons_purchased":46.479888699992046,
    "total_refueling_spend_usd":"139.44",
    "end_fuel_gallons":0,
    "baseline_spend_usd":"147.01",
    "savings_usd":"7.57",
    "economic_fuel_cost_usd":null
  },
  "cost_basis": {"kind":"en_route_cash_purchases","price_basis":"illustrative_test_fixture"}
}
```

These values describe one observed route and dataset, not guaranteed future prices/results. [Full public response](artifacts/public/production-live-response.json). Two purchases are feasible under the fixed-route, zero-detour model.

## Local installation

Python **3.12+**; tested Django **6.1.2**, DRF **3.18.3**, Shapely **2.2.0**, pyproj **3.8.0**. Complete tested pins are in `requirements.lock`. The current stable Django release and DRF compatibility were checked against [Django](https://www.djangoproject.com/weblog/2026/oct/06/security-releases/) and [DRF](https://www.django-rest-framework.org/).

Windows PowerShell:

```powershell
git clone https://github.com/ShyanCS/FuelRouteIQ.git
cd FuelRouteIQ
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1 -Demo
.\.venv\Scripts\python.exe manage.py runserver
```

Linux/macOS:

```sh
git clone https://github.com/ShyanCS/FuelRouteIQ.git
cd FuelRouteIQ
sh scripts/setup.sh --demo
.venv/bin/python manage.py runserver
```

Open http://127.0.0.1:8000/. Setup creates the environment, installs pins, migrates SQLite, creates the database cache, imports 32,071 Census places and 31 public reviewed sites. `.env.example` selects **recorded** mode, replaying five actual attributed OSRM roads without credentials. Other pairs return `RECORDED_ROUTE_UNAVAILABLE`; failures never silently switch providers. Production uses live ORS.

### Assessment data

Place the original CSV at `data/raw/fuel-prices-for-be-assessment.csv`, then use setup without `-Demo`/`--demo`, or in an activated environment:

```sh
python manage.py import_fuel data/raw/fuel-prices-for-be-assessment.csv
python manage.py import_locations --verified data/reference/verified_stations.json
```

Reapply enrichment after a new import. Raw rows, source hash and conflicts are retained. `import_fuel --reuse` reuses an identical active import; normal imports create separate audits. `seed_demo` is idempotent and refuses to replace an assessment dataset. The private file and original excerpt are not bundled. Assessment mode uses its real observed prices; public mode uses independently authored CC0 example values. Both are labelled in API/UI. Broad city-level station coverage belongs to the full CSV import, not the 31-row public demo.

### Live provider configuration

Create a free personal key at [HeiGIT](https://account.heigit.org/). Set these values securely in ignored `.env` or deployment secrets and restart:

```dotenv
ROUTING_PROVIDER=ors
ORS_API_KEY=your_private_key_here
ORS_API_BASE_URL=https://api.heigit.org/openrouteservice
ORS_GEOCODING_BASE_URL=https://api.heigit.org/pelias/v1
```

Directions use `POST /openrouteservice/v2/directions/driving-car/geojson`; precise addresses use `GET /pelias/v1/search`, with a private server-side Authorization header. Common `City, ST` or `City, State` inputs resolve locally. Address geocoding is separate and cached; no bulk station geocoding occurs. Coordinates as request inputs, ambiguous cities and non-US destinations are rejected. Only the 50 states/DC are supported. Endpoints are city representative points unless a precise address is supplied. The sourced San Francisco endpoint override and one-kilometre endpoint snap guard prevent a known offshore Census point from masquerading as a downtown road.

## API contract and accounting

`POST /api/v1/routes/optimize/` accepts required `start`, `finish` strings. Optional:

| Field | Default and constraints |
|---|---|
| `location_mode` | `strict` or `estimated`; default strict |
| `range_miles` | 500; positive, maximum 500 |
| `mpg` | 10; 1â€“100 |
| `initial_fuel_gallons` | derived capacity = range/MPG; 0â€“capacity |
| `initial_fuel_cost_usd` | null; total known value of initial inventory, not price/gallon |

The JSON contains road GeoJSON, distance/duration/provenance/license; vehicle assumptions; stops with coordinates, quality/source, prices, precise quantities, fuel before/after, unrounded costs and explanations; a separate baseline; savings; fuel timeline; warnings; dataset revision; cache status and separately counted directions/geocoding attempts. `detour_miles` remains null because access/detours were not routed.

`initial + purchased - consumed = remaining`; `consumed = miles/MPG`. The default full tank is **initially owned inventory**. Cash spending (`total_refueling_spend_usd`, compatible `total_fuel_cost_usd`) excludes it. Short trips can buy $0 while consuming fuel. Unknown initial value makes economic consumption value unavailable; a supplied initial value enables FIFO consumption and remaining-asset valuation. Savings compare cash purchases under identical initial fuel/candidates, using unrounded totals. USD is rounded half-up at final presentation boundaries; summed displayed stop cents can differ from the rounded aggregate.

Strict uses individually reviewed operator site points. Estimated additionally permits unambiguous Census city positions and prominently qualifies candidate proximity, access, detours and savings. A reviewed point is not a surveyed pump or entrance. The public fixture currently contains only reviewed sites, so estimated mode does not create new data there.

| HTTP | Meaning |
|---|---|
| 400 | invalid JSON/vehicle/format/unknown field |
| 422 | non-US/unknown location, excessive snap, unsupported road, or fueling gap |
| 429 | application throttle or provider quota, with structured error |
| 502 | malformed/failed provider response |
| 503 | unavailable key, authentication, timeout or network failure |
| 500 | unexpected error with correlation ID, no client traceback |

Fuel-gap responses include the actual route, mile-range gap and coordinate/price coverage diagnostics. No-data short routes honestly label their unavailable price dataset. `GET /api/v1/health/` is database-aware readiness, not an outbound provider probe. `GET /api/v1/stats/` exposes aggregate import/coverage/cache counters, never credentials. The API is intentionally public and stateless; there is no admin or cross-origin browser authorization surface.

## Architecture, optimizer and performance

Validation â†’ endpoint resolution â†’ independent road cache/provider â†’ geographic candidate projection â†’ Decimal greedy optimizer/baseline â†’ inventory valuation â†’ JSON/Leaflet. Django apps separate ingestion, routing, optimization and presentation.

At each station buy enough to reach the next **strictly cheaper reachable** opportunity, including the destination; otherwise fill to capacity, capped by remaining need. Co-located candidates collapse deterministically. A monotonic stack finds cheaper opportunities; sorting costs O(n log n). The exchange argument proves minimum purchase expenditure for a **fixed route, eligible ordered candidates, snapshot prices, divisible purchases and zero modeled detours**. Range/capacity are respected; zero-fuel arrival is allowed. No reserve, route-choice optimum, real entrance, truck restrictions, hours or fresh-price guarantee is claimed. Independent dynamic-programming oracle cases check expenditure and infeasibility with integer and fractional inventories.

Metric STRtree projection, geodesic mile markers and a five-mile lateral corridor filter station candidates; repeated-pass ambiguities are rejected. Lateral proximity is not routed detour mileage.

Durable database caches are separate: road 24h, endpoint geocoding 30d, plans 1h. Road keys include ordered coordinates/provider/profile/options, exclude fuel/price/mode. Plan keys include revision, geometry, policy, vehicle and mode. Invalid provider responses are not cached. One uncached city-pair directions call becomes zero on repeat or fuel/mode changes. One threaded Gunicorn worker coalesces simultaneous identical misses; scaling to multiple processes needs distributed atomic coordination.

Actual first external Chicagoâ€“Dallas route-cache miss: **2,597 ms**, one directions/zero geocoding; immediate warm repeat **473 ms**, zero/zero. Pure cold greedy processing **0.107 ms**, provider **1,091 ms**, projection **488 ms**. These are observed samples, not an SLA or free-host startup benchmark. [Evidence](artifacts/public/production-first-probe.json).

## Verification and Postman

The final local suite includes the private-source audit and genuine opt-in ORS test. Exact current counts/coverage and CI are in [FINAL_SUBMISSION_AUDIT.md](FINAL_SUBMISSION_AUDIT.md). Independent public clone setup, actual hosted HTTP/browser tests and PostgreSQL redeploy persistence are documented separately; mocked, recorded and live evidence are never conflated.

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pip check
python -m ruff check .
python -m ruff format --check .
python -m mypy optimizer
python -m pytest --cov=api --cov=routing --cov=stations --cov=optimizer
# Genuine key required; exactly one additional directions request:
RUN_LIVE_TESTS=1 python -m pytest tests/test_live.py
```

Import [Postman collection](postman/FuelRouteIQ.postman_collection.json) and [hosted environment](postman/FuelRouteIQ.hosted.postman_environment.json). Actual hosted Newman: **11 HTTPS requests, 74 assertions, zero failures**. CLI:

```sh
npx newman@6.2.3 run postman/FuelRouteIQ.postman_collection.json \
  -e postman/FuelRouteIQ.hosted.postman_environment.json
```

`scripts.validate_hosted` is a bounded fifteen-request live HTTPS verification script; it does not clear public caches. Normal tests forbid network, except explicitly opted-in live tests. CI skips the absent private CSV and live credential test, and executes the rest plus recorded loopback Newman.

## Deployment and submission

Free **Render web service + durable Neon PostgreSQL**; pinned Gunicorn/WhiteNoise, production-only secrets, DEBUG=false, HTTPS/HSTS, bounded timeouts, exact hostname and no client key. `render.yaml`, `scripts/render_build.sh` and `scripts/render_start.sh` reproduce deployment. Migrations/seeding run before startup; no private filesystem path is required. HTTP health path `/api/v1/health/` is configured. Public requests are bounded to 30/min/client, 30/min/service and 500/day/service to protect vendor quota. Free quotas, shared workspace hours and idle starts apply; no paid infrastructure was selected. See [PRODUCTION_DEPLOYMENT_REPORT.md](PRODUCTION_DEPLOYMENT_REPORT.md).

[Submission audit](FINAL_SUBMISSION_AUDIT.md) Â· [Implementation report](FINAL_IMPLEMENTATION_REPORT.md) Â· [Licenses/provenance](DATA_SOURCES_AND_LICENSES.md) Â· [Routing/coverage](ROUTING_AND_COVERAGE_REPORT.md) Â· [Submission links](SUBMISSION_LINKS.md)

**Loom is not yet recorded.** The natural [4:30 script](docs/FINAL_LOOM_SCRIPT.md), [shot list](docs/LOOM_SHOT_LIST.md) and [requests](docs/DEMO_REQUESTS.md) are ready for a human microphone recording. Inspect duration under five minutes before sharing; employer submission remains the user's action.

Source price sharing rights are unspecified; private CSV/excerpt, secrets, DBs, caches, environments and Git internals are excluded from `FINAL_REVIEW_PACKAGE.zip`. Public illustrative numeric fixtures are CC0. Census data is federal public data; GeoNames endpoint is CC BY 4.0; Natural Earth is public domain; Leaflet's BSD license is retained. ORS response geometry is attributed to **Â© openrouteservice by HeiGIT | Data from OpenStreetMap**, CC BY-SA 4.0; recorded OSRM/OSM provenance is separately attributed. These data licenses do not imply permissions to redistribute private assessment prices.
