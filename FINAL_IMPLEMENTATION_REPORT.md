# Final implementation report

12 October 2026. See `FINAL_SUBMISSION_AUDIT.md` for current external gates; historical Phase 2 reports are retained as evidence, not current publication status.

## Architecture and production changes

The existing Django 6.1.2 / DRF application is preserved. Validation resolves US city endpoints from a checksummed Census index, optionally caches a Pelias address match, independently caches road geometry, projects eligible station sites, executes the Decimal greedy optimizer and baseline, values initial inventory and returns map-ready JSON. Leaflet renders this response directly, including same-mile before/after fuel jumps.

Final production work added pinned Gunicorn 26.2.0, WhiteNoise 6.12.0, dj-database-url 3.1.2 and psycopg 3.3.6; durable PostgreSQL configuration with SSL in connection strings, direct migrations and pooled application connections; fail-fast production secret/database requirements; HTTPS redirect/HSTS, secure cookies, exact allowed hosts/trusted origins and no cross-origin browser access; console error logging; one four-thread worker for in-process request coalescing; route quotas (30/minute per client, 500/day global); meaningful readiness failure before seed; reproducible build/start scripts and free Render configuration.

`seed_demo` transactionally imports public checksummed illustrative prices and reviewed sites. Repeated identical seed preserves rows, dataset revision and enrichment; it refuses to overwrite an assessment dataset. `import_fuel --reuse` is an optional idempotent assessment import; normal imports retain separate raw audits. Leaflet's missing optional source-map reference was removed so production manifest collection succeeds; its copyright/license is preserved.

## Actual validation

- Full local suite: **302 passed, 1 skipped**, 225.21 seconds. Skip: genuine-key ORS. Backend statement coverage: **95.21% (895/940)**. `artifacts/public/final-tests.txt`, `final-coverage.json`.
- Focused production/API regression run: **33 passed**. Covers seed idempotency/protection, checksum-based active reuse, unavailable readiness, per-client/global quotas, fail-fast production requirements and existing API behavior. Initial regression failures were corrected and rerun; failed attempts are not counted as passes.
- Django checks and migration drift, Ruff lint/format, strict optimizer mypy, pip consistency and JS syntax pass. `check --deploy` reports zero issues with production settings. `collectstatic` succeeds after fixing the missing optional Leaflet map reference.
- Dedicated free PostgreSQL database: actual migrations, shared cache creation, 32,071 Census places and public 31-site seed succeeded. Later deployment/external/CI evidence is in the production report and final audit.

## Data and proof scope

The original supplied CSV remains private and supported: 8,151 observations, 6,626 US identities; 31 reviewed sites, 5,983 city approximations and 612 unresolved on that imported dataset. Raw rows, conflicting observed prices and source quality remain auditable. Public deployment uses **31 hand-authored illustrative prices**, never the assessment prices; source attribution/checksums and CC0 fixture designation are bundled. Broad approximate coverage belongs to the full assessment import, not the small public fixture.

Default range 500 miles, MPG 10, capacity 50 gallons and initial full tank are unchanged. Fuel conservation and tank bounds hold; zero-fuel arrival is allowed by the model. Cash purchases exclude initially owned fuel. Unknown initial value yields unavailable economic consumption value; known initial value enables FIFO consumption/remaining-asset accounting. Baseline savings use identical initial fuel and candidates.

The next-strictly-cheaper greedy algorithm minimizes purchase spend on a **fixed route, ordered eligible candidates, fixed prices, divisible purchases and zero modeled detours**. Independent DP oracle tests are preserved; no global route cost or operational navigation guarantee is claimed. Five recorded OSRM roads are real, checksummed and attributed. Strict mode uses reviewed sites; estimated mode visibly qualifies city positions. Seattle–San Francisco has an honest priced-coverage gap. Nationwide strict coverage, detours, entrances, hours and live prices remain limited.

## External and user-controlled gates

Authenticated ORS short/long routing, Pelias success and live-versus-recorded corridor comparison require a genuine key configured securely. Public hosting requires the connected Render workspace confirmation. No Loom recording/link exists; the refreshed 4:30 script/shot list and requests are ready for human microphone recording. Exact current publication/deployment status is recorded separately; none of these gates is inferred from mocks.

## Final endpoint audit correction

The original Seattle–San Francisco recording is retired: Census's offshore San Francisco point snapped 29,953 m onto Point Reyes Lighthouse Road, so the historical 835.41-mile result is not a valid San Francisco city-route demonstration. The old file is preserved byte-for-byte with a retirement manifest. A single sourced GeoNames populated-place reference (CC BY 4.0, attributed) now corrects this endpoint only; station approximations and original Census records are unchanged. One additional real OSRM request produced a corrected **808.901515-mile** road with **12,369 points** and a **2.502-metre destination snap**. Both fuel modes still return an honest gap. Active route manifest: five pairs; six road files retained including the retired one.

Every new API road is now rejected before caching if its first/last coordinate lies over 1 km from the requested endpoint. This is a conservative proximity guard, not proof of highway/station access. The route-cache namespace was advanced so previously unchecked cached geometry cannot bypass it. Endpoint source and representative-point qualification are returned in metadata. Precise-address locality checks use the reviewed endpoint reference when present. Other political/place representative points can still be unsuitable: such routes return a useful error requiring a precise address, rather than quietly accepting distant snapping.

## Publication and independent evidence

The sanitized main branch is published at https://github.com/ShyanCS/FuelRouteIQ. First CI discovered a missing PostgreSQL OPTIONS dictionary for URLs without query parameters; the fix uses setdefault and enforces production TLS, with an executable regression. Ubuntu CI on `12d948933d78ebf0c02a7b0880a1408e382b5ee3` then passed: **302 passed, 2 skipped in 32.44 s**, plus system/deploy/static/migration/pip/lint/format/type checks and **74 Newman assertions across 11 actual loopback HTTP requests**. This is CI evidence, not hosted HTTPS or authenticated ORS proof. [Run](https://github.com/ShyanCS/FuelRouteIQ/actions/runs/38231909027). Later endpoint changes have a separate final verification gate.

A fresh public clone and new environment installed its lockfile, migrated/seeding 32,071 places and 31 public reviewed sites, and returned expected statuses for all five pairs/modes. Unseen Austin→Austin is a valid zero-distance 200; Austin→Houston returns the honest recorded-provider unavailable error until live routing is configured. Browser checks compare API/UI cost $138.44, two actual stop pins, paired fuel jumps, short-trip cash/consumption, estimated disclosure and cleared failure states. Desktop/mobile layouts were inspected; mobile document width equals its client width. These are local-clone checks, not production browser evidence.

The dependency advisory scan checked all **36 pinned packages, no skips, no known vulnerabilities**. This is a point-in-time advisory check, not a security guarantee. Private files/real credentials are excluded by publication/archive allowlists and Git ignore. Git attributes preserve checksummed source/recording bytes on Windows and Linux clones.

Actual local APIClient over the remote PostgreSQL database passed nine cases and route reuse. First response **13,199.616 ms**, repeat **8,394.158 ms**; these include cross-region database round trips from the local machine and are not a hosted latency claim. Pure algorithm/network phase fields are separately recorded. The hosted app/database are intended for nearby regions, but no unmeasured improvement is claimed. Repeated real database seed retained revision `e38195aa-0f88-439f-ae25-9e602ed0991c` and all 31 reviewed sites. Artifacts: `artifacts/public/production-checks.json`, `production-source-review.json` and `production-dependency-audit.json`.

Final endpoint-corrected local suite: **306 passed, 1 skipped in 228.23 s**, **95.30%** backend statement coverage (913/958). The sole local skip requires a genuine ORS key. No mock or recording is claimed as successful authenticated ORS. Full evidence is in `artifacts/public/final-tests.txt` and `final-coverage.json`.
