# FuelRoute IQ — Codex implementation brief

**Project:** Backend Django Engineer take-home assessment  
**Goal:** Implement a fast, understandable, tested US road-trip fuel-planning API with a trustworthy interactive demo and precise documentation of its limitations.  
**Status:** Approved implementation specification, NOT evidence that the code has been implemented.

## 1. Assessment contract (must pass before adding extras)

Build a Django API accepting US start and finish locations. Compute a road route using a free routing API. Use the supplied `fuel-prices-for-be-assessment.csv` to recommend cost-effective refueling locations respecting a maximum driving range of **500 miles** and efficiency of **10 MPG**. Return a map-renderable route, refueling stops and estimated total fuel expenditure. Optimize response speed and minimize external routing calls (one directions call per new route; zero for a cache hit). Deliver GitHub repository and <5-minute Loom walkthrough showing Postman and code.

The provided CSV is authoritative for fuel *prices*, not geospatial coordinates or live availability. No scraping live prices or assuming all stations are geocoded.

## 2. Real CSV audit — do not ignore

CSV columns: `OPIS Truckstop ID`, `Truckstop Name`, `Address`, `City`, `State`, `Rack ID`, `Retail Price`.

Verified on supplied file:
- 8,151 data records; 7,531 rows have a US state code, and 620 use Canadian province/territory codes.
- 6,738 distinct OPIS IDs; 6,626 distinct OPIS IDs within US rows.
- 597 OPIS IDs are associated with conflicting fuel prices.
- 4,617 rows contain the word `EXIT` in `Address`.
- The file contains **no latitude or longitude** and **no timestamp**. Do not infer which conflicting price is 'latest'.

Keep raw source rows for auditability, normalize whitespace, validate `Decimal` prices (reject ≤0, NaN, Infinity), filter to 50 US states + DC for selection, dedupe at identity level while retaining price range and source-row count. For a reproducible default, choose **one observed price closest to the median** (not a fabricated average) and mark `price_conflict=true` when conflicting observations exist. Include min/max price observations for transparency. Document that prices are snapshots and may not reflect current pump pricing.

## 3. Critical geo-trust policy

Do not present city centroids as exact station coordinates. A substantial fraction of source addresses resemble highway exit descriptions (`I-44, EXIT 283 & US-69`), which conventional street geocoders may misinterpret.

Build a station-enrichment import path that accepts **verified** station-level coordinates from a separate, documented source with provenance and validation (matching station name, locality/state, road context where feasible). Keep fields `location_precision: verified_station | approximate_city | unresolved`, `source`, `match_confidence`, and `verified_at` where applicable. Use a US Census Gazetteer / other permissibly licensed US placename dataset to give city-level approximate positions *only* as a fallback; label these explicitly and never treat them as exact road-access points. A city center can help with candidate discovery/visualization but is not proof of station access.

**Mode separation:**
- `strict` (default for claims of optimality): only verified_station candidates may be used to claim an actionable fueling plan; if coverage insufficient, return a structured infeasibility/coverage response, not invented stops.
- `estimated` (clearly labeled demo / approximation): allow city-centroid candidates, disclose coordinate quality and potential highway detour, and label results as estimated/conditional. Never claim global optimality or navigable station coordinates. Avoid calling this mode verified or production-safe.

For the take-home, deliver a small demonstrably verified reference corridor if reasonably achievable and honest graceful fallback elsewhere. Do not claim national verified coverage without supplying and auditing the station-coordinate source. Show coordinate coverage statistics in import report and API warnings.

For route projection: use Shapely LineString and a suitably local projected CRS or carefully geodesic method (not raw degrees as miles) to calculate approximate mile markers and distance from route; sort stations by projected distance along route. Reject candidates beyond documented corridor threshold. Require monotonic progress and a feasible 500-mile travel gap between fueling opportunities; detours are not measured as exact routed distances unless explicitly requested from a routing service.

## 4. Routing and location inputs

Recommended stack: Python >=3.12; Django **6.1.2** (verified current on 2026-10-12); compatible Django REST Framework >=3.18; SQLite; Requests or HTTPX; Shapely; pytest. Verify resolution/compatibility during installation and pin actual tested versions in lockfile.

- Public API accepts named US endpoints: e.g. `{"start": "Chicago, IL", "finish": "Dallas, TX"}`; optionally support coordinate pairs validated as US by geospatial boundary checking, not just bounding box.
- For common US city/state inputs, first resolve endpoints from a local location index (Census Gazetteer or other explicitly sourced database): **0 geocoding API calls**.
- For unsupported precise addresses, use one geocoding request per endpoint only when required, cache results, verify country=US. These are geocoding calls, not directions calls, but report and document both counts honestly.
- Call OpenRouteService **POST `/v2/directions/driving-car/geojson`** once per uncached route; return its road-following LineString with distance and duration, not a straight line. ORS requires a free API key; keep key in `.env`, never commit secrets. ORS public directions limit is 6,000 km per request, so return a helpful error when exceeded rather than fabricating a journey.
- Cache route geometry/distance keyed on normalized endpoint coordinates + provider/profile/options; include TTL and dataset/import version where appropriate. **Optimization result cache and route geometry cache must be independent** so changing vehicle/fuel settings need not request another route.
- Clean timeouts, retry/backoff only for safe transient errors and within call budget, provider exception handling, and deterministic fixture-backed test mode with no external requests.

## 5. Fuel model — define accounting precisely

`range_miles=500`, `mpg=10`, derived `tank_capacity_gal=50`.

Input may include `initial_fuel_gallons` (default 50.0, configurable 0–50). Default full tank means the driver starts with 50 gallons already owned. Keep `initial_fuel_cost_usd` optional if the user knows the fuel's purchase price; never invent it. Report separately:

- `route_miles`
- `fuel_consumed_gallons = route_miles / 10`
- `fuel_purchased_gallons = sum(purchases at stops)`
- `total_refueling_spend_usd = sum(purchase_gallons * station_price)` (money paid during this route; excludes initial tank)
- `initial_fuel_value_usd` if supplied, otherwise null
- `total_acquired_fuel_value_usd` only if starting fuel valuation known, otherwise null
- `remaining_fuel_at_destination_gallons`

**Important:** a short route with initial full tank may legitimately have $0 in *en-route cash purchases*. This is NOT the same as zero fuel consumed or zero economic cost. Explain that clearly in response and README. If the assessment evaluator expects a single numeric `total_fuel_cost_usd`, include it with an unambiguous cost-basis object and state exactly what it includes. Do not fabricate a monetary cost for initially owned fuel when price is unknown.

## 6. True purchase optimization, not just cheap-stop selection

Treat route as fixed and stations sorted by mile marker. In the idealized **no-detour** model, with divisible fuel purchases, fixed prices, 50-gallon capacity, and no minimum-purchase constraints, use and document a provably correct greedy optimizer:

1. At the current station, search forward to the next *strictly cheaper* reachable station within a full tank's 500-mile driving range. Also treat the destination as a terminal node requiring no more purchases (virtual cheaper endpoint), when reachable.
2. If there is a cheaper reachable station, purchase only enough fuel to reach it after using remaining tank fuel. Otherwise purchase enough to fill the tank, but never buy more than needed to finish if the destination is already reachable.
3. Respect tank capacity, never use negative fuel or quantities, maintain precise distances (avoid rounding fuel balances during decisions), and always include initial-fuel state.
4. Verify that no gap between reachable fueling opportunities violates the range; if impossible, return `UNREACHABLE_FUEL_GAP`, including relevant mile range and geo-coverage qualification.
5. Station-location uncertainty, drivable detours, opening hours, and price freshness are explicitly outside the optimizer's formal optimality guarantee. Never call a city-centroid estimated solution globally optimal.

Use Decimal money values (round for display only), preserve enough precision for gallons and projection; only round final reported USD to cents. Test the greedy solver against a small brute-force/dynamic-programming oracle with integer-gallon fixtures, random short cases, edge cases (0-mile, exactly 500 miles, two identical-price stations, zero purchases, inaccessible cheaper station, high initial fuel, station at start, station at end). Confirm fuel never drops below zero and never exceeds 50 gal.

## 7. Savings intelligence and explanations

Return a human-readable justification for each purchase: "buy X gallons at $Y/gal to reach cheaper station Z" or "fill here because no cheaper reachable fuel remains". Do not claim savings until a real feasible baseline has been simulated **with the same initial fuel and candidate locations**.

Implement a simple documented baseline (e.g. next reachable station near a 350–400-mile stopping policy, then fill as needed) as a separate simulated policy. If baseline is infeasible or dataset is too uncertain, report `baseline_status` rather than fabricated savings. Report baseline spend, optimized spend, absolute/percentage savings only if both valid under same accounting and location-quality mode.

## 8. API contract and demo

`POST /api/v1/routes/optimize/`

Example body:
```json
{
  "start": "Chicago, IL",
  "finish": "Dallas, TX",
  "location_mode": "estimated",
  "initial_fuel_gallons": 50
}
```

Minimum response shape (names may be refined, but semantics must not change):
```json
{
  "route": {"distance_miles": 0, "duration_seconds": 0, "geometry": {"type": "LineString", "coordinates": []}},
  "vehicle": {"mpg": 10, "range_miles": 500, "tank_capacity_gallons": 50, "initial_fuel_gallons": 50},
  "fuel_stops": [
    {
      "station_id": "...", "station_name": "...", "price_per_gallon_usd": "3.249",
      "mile_marker": 0, "gallons_purchased": 0, "purchase_cost_usd": "0.00",
      "fuel_before_purchase_gallons": 0, "fuel_after_purchase_gallons": 0,
      "coordinates": [-95.0, 35.0], "location_precision": "approximate_city",
      "decision_explanation": "..."
    }
  ],
  "fuel_summary": {
    "gallons_consumed": 0, "gallons_purchased": 0,
    "total_refueling_spend_usd": "0.00", "end_fuel_gallons": 0,
    "baseline_spend_usd": null, "savings_usd": null, "savings_percent": null
  },
  "warnings": [],
  "meta": {"directions_api_calls": 1, "geocoding_api_calls": 0, "route_cache_hit": false, "location_mode": "estimated", "location_coverage": {}}
}
```

Example body is illustrative; zero values are placeholders, never emit fake zero route geometry in real successful responses.

Appropriate HTTP status codes: 400 for malformed inputs; 422 for locations outside US / no feasible verified fueling plan; 429 for provider quota/rate limiting where applicable; 502/503 for routing provider failures. Structured `error.code`, `error.message`, and details, no tracebacks to clients. Add `/api/v1/health/` and optional `/api/v1/stats/` for dataset and cache metrics.

Build a *small* Leaflet page (not a large SPA) displaying route GeoJSON, station pins (different visual for verified vs approximate), summary metrics, comparison, and a fuel-level timeline. Timeline must faithfully represent discontinuous purchase jumps with paired pre-/post-refuel points at identical mile markers. Label estimated coordinates and source caveats visibly. Map tiles/attribution follow provider terms.

## 9. Maintainable project layout

Use Django app(s) and clearly isolated modules: `api/serializers.py`, `api/views.py`, `routing/provider.py`, `routing/geocoding.py`, `routing/cache.py`, `stations/importer.py`, `stations/locate.py`, `stations/models.py`, `optimizer/engine.py`, `optimizer/baseline.py`, `optimizer/schemas.py`, `demo/` HTML/template/assets, `tests/` unit/integration tests, `fixtures/` deterministic mock routes, `scripts/` import/verification reports, `postman/` collection. Actual layout may vary if cohesive and consistently structured.

Include `.env.example`, `README.md`, `requirements` / lockfile, migrations, data import management command, make/PowerShell run alternatives, optional Dockerfile, unit tests, formatter/linter checks, `.gitignore`, sample error and success responses, license/source notes, and reproducible verification commands. Do not commit the real API key. Read the supplied CSV from `data/raw/fuel-prices-for-be-assessment.csv` (ask operator to place the attached file there), and consider committing a compact deterministic fixture dataset if sharing the original file is not permitted.

## 10. Completion gates — stop only once demonstrated or explain blockers

- Django version is verified (`6.1.2` at task creation) and API starts cleanly from fresh environment after instructions.
- CSV importer reports exact source row counts, Canadian filtering, deduped US IDs, conflicting prices, location precision coverage.
- A nontrivial multi-stop long journey passes with actual road geometry; distances, fuel arithmetic, and cost accounting are internally consistent.
- One provider **directions** request on cache miss, zero on repeat; separate endpoint geocoder counts when needed.
- No bogus location confidence or invented detours. Strict/estimated results properly labeled.
- Optimizer oracle tests plus route geometry projection tests, multiple stop tests, short trip, no station coverage, malformed/foreign input, provider timeout, caching, baseline infeasibility, price conflicts.
- API responses validated in Postman using at least two distinct routes (long route and short route), then repeat first to demonstrate cache hit.
- Leaflet map and fuel-level timeline use exact API response, not hardcoded demo figures.
- Run `python manage.py check`, migrations, pytest, lint/type checks as configured. Record actual pass counts and known limitations; never claim tests that were not run.
- README provides architectural tradeoffs and complexity, environment variables, free routing provider quota/route limits, station-accuracy limitation, performance/call-count measurement and provider outage behavior.
- Prepare a <=5-minute Loom shot list covering Postman example, meaningful optimization, caching, the live map and key source files. Demonstrate real responses; do not pre-record invented numbers.

## 11. Prioritized Codex implementation sequence

**Phase A (core acceptance):** scaffold Django, import/normalize data, geocode start/finish, one-call routing adapter+cache, API validation, route geometry and basic fuel feasibility, tests.

**Phase B (differentiation):** verified/approximate location policy and station coverage report; provable optimizer and oracle tests; expenses & baseline; explanations; thorough edge case handling.

**Phase C (presentation):** Leaflet route and timeline, Postman collection, structured stats, reproducible setup, screenshots and 5-min walkthrough script, performance benchmark.

If time runs short, always ship a correct core API with documented uncertainty rather than a flashy but invalid nationwide optimizer.

## 12. Codex execution instructions

Act as a senior Django backend engineer and assessment reviewer. Work in the active repository. Before changes inspect existing project and CSV. Execute the phases above, implement actual code rather than writing a plan only, run real tests and report concrete evidence. Do not invent station geocodes, prices, speed measurements, successful HTTP responses, or test results. Do not push to GitHub, deploy services, or publish API keys without explicit approval. Once implementation and tests pass, provide a concise completion report detailing modified files, setup steps, coverage (verified vs estimated), known limitations, example command to run, exact test results, and what remains for GitHub/Loom submission.

### Primary reference links
- Django current release (Oct. 6, 2026): https://www.djangoproject.com/weblog/2026/oct/06/security-releases/
- Django REST Framework release compatibility: https://www.django-rest-framework.org/community/release-notes/
- ORS directions GeoJSON API: https://giscience.github.io/openrouteservice/api-reference/endpoints/directions/
- ORS distance limits: https://openrouteservice.org/restrictions/
- Census Gazetteer: https://www.census.gov/geographies/reference-files/2026/geo/gazetter-file.html
- Nominatim policy (do NOT systematically bulk geocode the supplied station CSV on public Nominatim): https://operations.osmfoundation.org/policies/nominatim/
