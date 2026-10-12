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
