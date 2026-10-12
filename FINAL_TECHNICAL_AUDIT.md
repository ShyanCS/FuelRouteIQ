# FuelRoute IQ — final technical audit

Historical Phase 2 evidence. Final production/publication status and later fixes are authoritative in FINAL_SUBMISSION_AUDIT.md, FINAL_IMPLEMENTATION_REPORT.md and PRODUCTION_DEPLOYMENT_REPORT.md.
Phase 2 local review, 12 October 2026. **Ready for independent source-code review. Final live submission readiness is PARTIAL.** No commit, push, deployment, account creation or publication was performed.

## Material findings and remediation

| Issue / root cause | Files and correction | Status / evidence |
|---|---|---|
| Deprecated ORS host and old geocoding path | `routing/provider.py`, `geocoding.py`, settings and `.env.example`: current HeiGIT routing prefix and Pelias `/v1/search`; configurable bases, raw Authorization key, no redirects/retries | PASS for contract/mocks; valid-key success UNVERIFIED. [Official migration](https://ask.openrouteservice.org/t/deprecating-api-openrouteservice-org-in-favour-of-api-heigit-org/7912). |
| Daily quota failures incorrectly classified as bad credentials | Provider distinguishes daily 403 quota exhaustion from authentication, returns 429 for quota, 503 for invalid key | PASS, targeted quota/auth tests. [Official FAQ](https://giscience.github.io/openrouteservice/frequently-asked-questions#when-and-how-does-my-quota-reset). |
| Routing error codes were over-broad: missing 2009, treating unknown/incompatible parameters as distance limits | Current routing-code classification includes no-route/point/limit errors; invalid adapter options remain provider failures | PASS, regression verifies 2009 versus 2012. [Official error codes](https://giscience.github.io/openrouteservice/api-reference/error-codes). |
| Numeric summary validation cast measurements but returned raw values | Reject strings/booleans/non-finite values and return canonical numeric meter/second summaries | PASS, malformed summary and geometry tests; failures not cached. |
| Cache identity omitted provider deployment base and recording integrity | Versioned routing identity includes base/profile/options; recordings include manifest fingerprint and are checked against hashes at load | PASS, base-change, reverse-route, expiry, invalid-response and recording integrity tests. |
| No executable concurrency evidence; database-cache counters use read/modify/write | Process-local metric lock; actual DatabaseCache test with four simultaneous requests | PASS for this local single-process deployment: one provider call, consistent results. Multi-process stampede/counter guarantees remain PARTIAL. |
| Six sites and two road recordings were insufficient for independent scenarios | Preserved originals; appended three actual OSRM recordings and 25 reviewed operator records | PASS for expanded reference coverage: 31 sites, five actual roads. Nationwide verified coverage remains PARTIAL. |
| Operator identity/road discrepancies can hide bad enrichment | Bounded selection review rejected current ONE9/old Flying J mismatch; unavailable page unresolved; Cocoa exit discrepancy disclosed in stop JSON | PASS, reviewed provenance and `operator_review_summary.json`; no guessed sites or new pump prices. |
| Enrichment repeatedly read all raw observations per station | Alias index loaded once; missing evidence IDs fail explicitly unless compact-fixture skip is deliberately selected | PASS, command and missing-ID regression; source rows remain auditable. |
| Nearest-segment exact ties alone did not conservatively handle repeated route visits | Metric near-tie rejection within 25 m; indexed geographic prefilter; persistent projection diagnostics | PASS, repeated-pass regression and actual matrix. This remains approximate projection, not routed access proof. |
| Cash purchases could be mistaken for economic consumption value | Backward-compatible spend fields plus FIFO consumption/remaining-asset valuation when initial value is supplied | PASS. Short route: $0 cash, 9.502642 gallons consumed; with supplied $200 initial value, $38.01 consumed value and $161.99 remaining asset. Unknown initial value remains null. |
| Baseline docstring claimed it could be infeasible while the optimizer succeeded under this full-fill model | Corrected explanation; original oracle cases also check baseline feasibility/conservation and spend >= optimum | PASS. No heuristic replaces the greedy optimizer. |
| Integer-only oracle did not demonstrate fractional inventories | Added one independent 200-case half-gallon/scaled-MPG oracle test, preserving the original 200 generated tests | PASS. No optimizer defect was found in these or the separate 10,000 finite-marker audit. No default reserve/range assumptions changed. |
| UI could retain an old result on network/JSON failure or mismatched async completions | Clear-state helper, immutable submitted labels, request generation/abort guard, bounded client wait, explicit mode help and retry | PASS for long/short/estimated/coverage/foreign browser states; old figures and timeline clear on failures. |
| Broader estimated mode and supported examples were obscure | Five example buttons, prominent scope/banner, initial inventory/value and consumption-value ledger | PASS, actual browser JSON comparison and marker/timeline inspection. |
| Original demo excerpt had uncertain redistribution rights | Preserve privately, ignore/exclude original CSV/excerpt; source-independent CC0 illustrative fixtures with checksum manifests and API/UI price-basis flags | PASS for package reproducibility/safety. Illustrative prices are deliberately test inputs, never real/assessment observations. |
| Historical dataset report lacked the new price-basis field, leading to wrong evidence-folder classification | Stats derives price basis from the model; capture labels/folders now follow actual dataset basis | PASS; original assessment evidence is local-only, public demonstration evidence is labelled separately. |
| Locale-dependent earlier text edits left README mojibake and stale six-site/two-route descriptions | Explicit UTF-8 updates and current instructions/reports | PASS, current README and portable package paths. |
| ZIP scanner confused a blank key with the following line and scanned environment access expressions as literals | Horizontal whitespace anchors, explicit environment expressions, allowlisted source trees, private-file hashes and token scan | PASS, archive safety/integrity scan. Initial archive/install attempts failed and were rerun; no failed attempt is counted as successful verification. |
| Requested brief filename did not exist | Added `IMPLEMENTATION_BRIEF.md` as a pointer; original approved brief preserved unchanged | PASS, no specification replacement. |

## Real validation results

- Main workspace full suite: **295 passed, 1 skipped** in **204.38 s**. The skip is valid-key ORS. Coverage **94.92%** over API/routing/stations/optimizer, 841/886 statements. Evidence: `artifacts/phase2-pytest-results.txt`, `phase2-coverage.json`.
- Targeted Phase 2 run: **13 passed** before the final cache/timing regression was added. The final full run includes all 14 substantive new tests. Test counts were not padded by extra seed parametrization.
- Newman/Postman runtime: **11 actual loopback HTTP requests, 74 assertions, zero failures**. Includes additional roads, honest Seattle gap, initial valuation, changed fuel and cached mode reuse. Evidence: `artifacts/public/postman-summary.json`; Postman desktop GUI operation itself remains UNVERIFIED.
- Django checks and migration drift, dependency checks, Ruff lint/format, strict optimizer mypy and JS syntax checks pass. A fresh pinned environment and extracted checkout passed migrations/imports and five-pair smoke checks. The extracted suite passed **294 tests with 2 explicit skips** (private CSV and genuine ORS key absent) in **82.05 s**. Evidence: `artifacts/public/package-smoke.json` and `package-tests.txt`.
- Browser: actual private-CSV $145.60 matched rendered cash spend, two reviewed pins matched JSON coordinates, purchase pre/post chart points have identical x positions, estimated mode shows four amber pins and conditional warnings, known-value short trip matches FIFO JSON, coverage and foreign errors clear the plan.
- Real provider evidence is limited to **two invalid-sentinel gateway rejections**: one directions attempt and one geocoding attempt. No successful credentialed ORS journey, live corridor comparison or live routing latency is claimed.

## Original assessment gates still at risk

| Gate | Status | What remains |
|---|---|---|
| Correct minimum purchase cost on a fixed route/candidates | PASS | Proof assumptions and oracle evidence preserved; no global route/operational-cost claim. |
| Arbitrary US route geometry via free live provider | UNVERIFIED | Genuine HeiGIT key, five-pair live matrix, repeat/fuel/mode cache checks and recorded-vs-live eligibility comparison. |
| Feasible fuel plans for previously unseen US routes | PARTIAL | Strict coverage is 31 reviewed sites, not national. Estimated mode has 5,983 city points on the full CSV but may fail or be geographically conditional. |
| Seattle–San Francisco using supplied prices | FAIL for this recorded road | No feasible priced-candidate chain in either mode; actual road returned with precise coverage gap. This is not proof that real stations do not exist. |
| Real detour/access, opening hours, current prices, reserve margin | PARTIAL | Outside the approved idealized guarantee and visibly disclosed; zero modeled arrival fuel can require extra real-world fuel. |
| Portable source-review package without private data | PASS | Run with illustrative fixtures or import the evaluator's assessment file; never conflate their dollar results. |
| Linux/macOS install and remote GitHub CI execution | UNVERIFIED | Scripts/workflow supplied; execution host is Windows and no push authorized. |
| GitHub/Loom submission | UNVERIFIED | Obtain approval to push/publish, perform GUI walkthrough, record the prepared <=5-minute sequence. |

The application is defensible for independent source review with these limits. A final hiring submission should add valid-key ORS evidence and explicitly explain geographic/price coverage rather than presenting the five recorded roads as national live validation.

Extracted public-package HTTP verification also passed all 74 assertions across 11 requests. A controlled real network failure cleared the prior cost, markers and timeline; the review server was then restored. Public UI and JSON both identify illustrative test prices.
