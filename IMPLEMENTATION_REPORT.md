# FuelRoute IQ — implementation report

Historical Phase 2 evidence. Final production/publication status and later fixes are authoritative in FINAL_SUBMISSION_AUDIT.md, FINAL_IMPLEMENTATION_REPORT.md and PRODUCTION_DEPLOYMENT_REPORT.md.
Updated Phase 2, 12 October 2026. Ready for independent source review; final live submission readiness is PARTIAL. No public commit/push, deployment or publication occurred. The original CSV, approved brief, two initial road recordings and six original site records are preserved. Intended origin: https://github.com/ShyanCS/FuelRouteIQ.

## Architecture and actual improvements

The HTTP pipeline validates inputs, resolves common US endpoints from Census places, optionally uses cached Pelias address lookup, obtains/version-caches one road geometry, selects candidates by coordinate quality, projects them in metric/geodesic units, runs the greedy optimizer and separate baseline, values inventory and serializes the response. The Leaflet page uses that JSON directly.

| Module | Responsibility |
|---|---|
| fuelroute/ | Django/SQLite configuration, URLs, WSGI and persistent cache |
| api/ | Request contract, structured failures, accounting, FIFO consumption/asset value and work/call metadata |
| routing/ | Current HeiGIT ORS/Pelias adapters, checked recordings, independent caches and bounded requests |
| stations/ | Raw source audit, median-nearest observed prices, Census fallback, reviewed enrichment and indexed projection |
| optimizer/ | Typed domain, next-cheaper greedy purchases and deterministic full-fill baseline |
| demo/ | Five journeys, mode disclosure/retry, initial-value ledger, correct markers/fuel jumps and local basemap |
| tests/scripts/postman | Independent oracle, regressions, matrix evidence, safe packaging and setup |

Django 6.1.2, DRF 3.18.3 and all transitive/test dependencies remain pinned in requirements.lock. Python 3.12.10 was used locally.

Phase 2 corrected deprecated provider paths, daily-quota/auth classification, routing error codes and numeric normalization. Provider base/recording fingerprint now participates in cache identity. Redirects and retries remain disabled. Process-local cache metrics are serialized; four concurrent requests against actual DatabaseCache are tested. Projection has an indexed prefilter and conservative near-tie repeated-pass rejection. Enrichment loads source aliases once and requires explicit compact-fixture missing-ID handling.

The original greedy engine remains intact. Its 200 original independent DP cases now also check baseline feasibility/conservation and minimum comparison. One additional test checks 200 fractional-unit instances against the independent oracle; no extra seed-parametrized counts were added. Default range 500 miles, MPG 10, capacity 50 gallons and full initial tank are unchanged.

Cash purchases are separate from consumption and owned-fuel value. FIFO economic consumption/remaining-asset fields are only available when initial inventory is valued (or none exists). The UI exposes this distinction, uses immutable submitted labels, cancels superseded requests and clears stale values on failures.

## Source audit and coverage

Source SHA256: c704371f141ded9c54df6c32d488a0ba2ceb589f88c936c967daa5330e0cd241. Actual supplied CSV: 8,151 rows; 7,531 US / 620 Canadian; 6,738 overall IDs / 6,626 US IDs; 597 overall price conflicts / 487 US; 4,617 EXIT descriptions. No coordinates or timestamp. All raw rows are retained, invalid values rejected, and selected prices remain observed median-nearest values with range/conflict/count transparency.

Geographic coverage on the full dataset: 31 reviewed operator site points, 5,983 approximate Census city points, 612 unresolved. Census places: 32,071 US/DC records. Twenty-five site additions came from 27 selected corridor candidates: 26 fact records retrieved, one current brand mismatch rejected, one unavailable page unresolved. URLs, timestamps, retrieval hashes, review notes and a disclosed Cocoa exit discrepancy are retained. Site verification is not proof of pump entrance, access, detour, opening hours or current price availability.

## Actual assessment-price response evidence

These rows use the supplied private CSV and real recorded OSRM roads. Runtime external directions/geocoding calls are zero; replay reads and route cache hits are disclosed separately. Three additional recordings were acquired in Phase 2; original files are unchanged.

| Pair/mode | Road miles | Stops | Consumed/required gal | Bought gal | Cash spend |
|---|---:|---:|---:|---:|---:|
| Chicago–Dallas strict | 961.473868 | 2 | 96.147387 | 46.147387 | $145.60 |
| Chicago–Dallas estimated | 961.473868 | 4 | 96.147387 | 46.147387 | $134.57, conditional |
| Chicago–Milwaukee strict | 95.026421 | 0 | 9.502642 | 0 | $0.00 |
| New York–Miami strict / estimated | 1280.053363 | 3 / 4 | 128.005336 | 78.005336 | $271.58 / $226.72 |
| Los Angeles–Denver strict / estimated | 1036.833144 | 2 / 3 | 103.683314 | 53.683314 | $197.46 / $176.04 |
| Seattle–San Francisco, both | 835.414057 | unavailable | 83.541406 required | unavailable | 422 coverage gap |

Strict Chicago–Dallas still buys about 1.949273 gallons at Pilot #442 Hayti and 44.198114 at Flying J #607 West Memphis. Spend $145.60, baseline $150.09, savings $4.49. Conservation: initial 50 + bought 46.147387 − consumed 96.147387 = end 0 under the no-detour model. For the short trip, supplied initial value $200 gives $38.01 consumed economic value / $161.99 remaining asset while cash stays $0. Unknown initial value remains null.

Local full-price evidence: artifacts/private/recorded-assessment-matrix.json. Public package evidence uses explicitly illustrative test prices and has a separate label; its dollar results are not these assessment figures.

## Real validation

- Full workspace: 295 passed, 1 skipped in 204.38 s; 94.92% backend statement coverage (841/886). The skip is valid-key ORS. Logs: artifacts/phase2-pytest-results.txt and phase2-coverage.json.
- Newman/Postman runtime: 11 actual local HTTP requests, 74 assertions, no failures. Includes the five roads, honest gap, valuation and cached fuel/mode changes. Sanitized artifact: artifacts/public/postman-summary.json. Desktop Postman GUI itself remains unverified.
- Django startup/migration consistency, pip dependency check, Ruff lint/format, strict optimizer mypy and JS syntax checks passed.
- A new isolated environment installed the ZIP lockfile and imported Django 6.1.2. Extracted-source migrations/imports/five-road smoke passed; full suite: 294 passed / 2 expected skips in 82.05 s. Private CSV/excerpt were absent. Evidence: artifacts/public/package-smoke.json and package-tests.txt.
- Browser compares actual JSON against $145.60 cash, two reviewed markers and paired same-mile fuel jumps; estimated mode gives four amber pins and conditional warning; known-value short trip and coverage/foreign failure clearing were checked.
- Two real invalid-sentinel HeiGIT requests reached authorization rejection: one directions and one geocoding attempt. Successful valid-key routing/geocoding, live latency and corridor comparison remain UNVERIFIED.

Actual recorded timings separate request wall processing, endpoint resolution, projection, greedy/baseline and provider request time. Raw values are in the matrix artifacts; greedy work was sub-millisecond in representative cases. Zero replay network time is not an ORS latency claim.

## Run and review

Use scripts/setup.ps1 with the supplied full dataset, then .venv/Scripts/python.exe manage.py runserver. Without private source material use scripts/setup.ps1 -Demo, or sh scripts/setup.sh --demo. The local reviewed API is on http://127.0.0.1:8001/. Source resolves paths relative to the checkout, not an absolute Windows workspace.

REVIEW_PACKAGE.zip includes source, tests, migrations, lockfile, five real road recordings, public geodata, reviewed facts and labelled illustrative price fixtures. The original full CSV and 12-row excerpt are preserved privately and excluded. Import the evaluator's file for assessment-price results. See DATA_SOURCES_AND_LICENSES.md.

Remaining risks: missing genuine HeiGIT key, small exact coverage, inherent recorded I-5 price gap, undated/unspecified-grade source prices, unmeasured detours/access/hours and no reserve, per-process rather than distributed coalescing, unexecuted Linux/remote CI/Postman GUI/Loom submission. Detailed statuses: FINAL_TECHNICAL_AUDIT.md and ROUTING_AND_COVERAGE_REPORT.md.

Extracted public-package HTTP verification also passed all 74 assertions across 11 requests. A controlled real network failure cleared the prior cost, markers and timeline; the review server was then restored. Public UI and JSON both identify illustrative test prices.
