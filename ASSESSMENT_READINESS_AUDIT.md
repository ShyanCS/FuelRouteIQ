# FuelRoute IQ — assessment readiness audit

Historical Phase 2 evidence. Final production/publication status and later fixes are authoritative in FINAL_SUBMISSION_AUDIT.md, FINAL_IMPLEMENTATION_REPORT.md and PRODUCTION_DEPLOYMENT_REPORT.md.
Updated Phase 2, 12 October 2026. PASS means demonstrated; PARTIAL means implemented with material limits; FAIL identifies a known unavailable scenario; UNVERIFIED means required external execution/input is missing. Ready for independent source review; final submission readiness is PARTIAL.

| Requirement | Status | Evidence / limit |
|---|---|---|
| Preserve/inspect project, specification and source data | PASS | Originals preserved; brief filename alias, complete pipeline review and remediation plan. |
| Compatible pinned Django and maintained layout | PASS | Django 6.1.2 / DRF 3.18.3, lockfile, startup/migration/dependency checks. |
| Structured US location inputs | PASS | Local Census lookup; state abbreviations/full names/trailing USA; foreign, unknown, ambiguous and malformed inputs rejected. |
| Real road geometry from a free API | PASS for recordings | Five actual OSRM responses with provenance; no fabricated route lines or disguised live counts. |
| Current live ORS/Pelias implementation | PASS for contract/mocks | Official HeiGIT prefixes, headers, parsing, quotas, timeouts, keys and cache regressions. |
| Successful live provider integration / ORS-vs-OSRM comparison | UNVERIFIED | No genuine key. Invalid-sentinel authorization rejection is not successful routing. |
| 500-mile range, 10 MPG, 50-gallon default inventory | PASS | Unchanged; bounds, accounting and exactly-range tests. |
| True minimum purchase spend | PASS within model | Greedy proof; 200 original plus 200 fractional independent oracle comparisons. Fixed route/candidates, zero modeled detour only. |
| Tank balance, destination, equal prices and infeasibility | PASS | Automated conservation/bounds, reachable cheaper and gap cases. |
| Decimal prices/money, observed median-nearest import | PASS | No fabricated averages/latest price; range/conflict/count/raw evidence retained, cents rounded only for display. |
| Initial value versus consumption/purchases/cash/economic cost | PASS | FIFO fields only when valued; $0 short-trip cash with positive consumption and known-value economic asset checks. |
| Baseline savings comparable and non-fabricated | PASS | Identical initial inventory/candidates; separate feasible full-fill simulation and unavailable comparison handling. |
| Original exact CSV audit | PASS locally | 8,151 rows, 620 Canadian, 6,626 US IDs, 597 overall conflicts; package skips this test without private input. |
| Reviewed station sources | PASS for 31 points | 25 additions, rejected mismatch/unavailable source, explicit confidence/provenance and exit conflict. |
| Nationwide verified fueling coverage | PARTIAL | Only 31 exact sites; 5,983 city points and 612 unresolved on full source. No national verification claim. |
| Strict/estimated usability and honest partial roads | PASS | Strict default, clear mode help/retry/banner, useful 422 road/coverage diagnostics and no invented stops. |
| Previously unseen US routes | PARTIAL | Live adapter/broad local names supported; fuel feasibility depends on snapshot-priced candidate coverage. |
| Seattle–San Francisco recorded fueling plan | FAIL for source coverage | Both modes leave a >500-mile priced gap. No California I-5 source identities; no fabricated price/stop workaround. |
| Metric/geodesic projection and monotonic progress | PASS within approximation | Indexed prefilter, Shapely/Geod, 5-mile corridor, repeated-pass rejection and diagnostics. |
| Routed detour/access/hours/current grade/reserve | PARTIAL | Outside guarantee and disclosed. Site point is not an entrance survey; model may arrive with zero fuel. |
| One directions call / zero repeat calls | PASS in executable adapter tests | Vehicle/mode/revision/base/reverse/TTL/error cases. Successful live behavior remains key-dependent. |
| Separate geocoding, timeouts and truthful counters | PASS locally/mocked | Known cities zero geocoding, conservative cached address contract, no retries/redirects/hidden live fallback. |
| Concurrent local requests | PASS for one process | Four calls with actual DatabaseCache, one mocked provider request, consistent plans. Distributed guarantee PARTIAL. |
| Actual latency/work measurement | PASS for recorded local scenarios | Real SQLite/APIClient/Newman measurements with separate phases; no mocked-only or live-latency claim. |
| Leaflet geometry, quality pins and fuel timeline | PASS | Exact JSON, two green/four amber pins, paired x-coordinate jumps and offline basemap; browser inspected. |
| Clear UI accounting / no stale error results | PASS | Inventory/value ledger, cancellation/generation and cleared long/short/estimated/coverage/foreign states. |
| Reproduction without private workspace | PASS | Public illustrative inputs, real road/geodata/facts, relative source paths, isolated installation/database/tests. |
| Credentials/private data excluded from review ZIP | PASS | Allowlist, private hashes/token/assignment checks; no env, credentials, databases, caches, venvs or Git. |
| README/API/Postman/setup/source notes | PASS | Updated paths, modes, price/cost basis, 11 requests, platform scripts and licensing boundaries. |
| Automated engineering checks | PASS | 295 passed / 1 valid-key skip, 94.92% coverage; checks/migrations/pip/Ruff/mypy/JS syntax. |
| Postman runtime | PASS | 11 actual local requests / 74 assertions / zero failures; GUI itself UNVERIFIED. |
| Fresh Windows package setup | PASS | New lockfile environment and extracted source; private CSV absent; package logs identify expected skips. |
| Linux/macOS setup and remote CI | UNVERIFIED | Prepared scripts/workflow; execution host Windows; no approved push. |
| Under-five-minute Loom preparation | PASS for guide | Actual figures/provider and illustrative labels specified; recording/publication UNVERIFIED. |
| GitHub/Loom submission | UNVERIFIED | User approval and valid-key evidence still required; nothing pushed/deployed/published. |

The highest remaining risks are successful live provider validation and priced-station geographic coverage. Mocks, illustrative prices or moved geometry cannot turn these into PASS. Detailed root-cause/fix evidence is in FINAL_TECHNICAL_AUDIT.md; per-road/call/coverage data is in ROUTING_AND_COVERAGE_REPORT.md. REVIEW_PACKAGE.zip is for independent code review, with its manifest and isolated-check evidence.
