# Final employer submission audit

12 October 2026. **Engineering source ready for independent review; complete live submission readiness remains PARTIAL.** Only demonstrated gates are PASS. Deployment, CI and publication entries are updated with actual evidence after execution.

| Original employer requirement | Status | Evidence and limitation |
|---|---|---|
| Django API takes US start/finish | PASS locally | Validated city/state and conservative address lookup; foreign/malformed/ambiguous inputs have structured errors. Hosted execution pending. |
| Map of road route and optimal fuel locations | PASS within model / PARTIAL overall | Five real OSRM recordings, exact-response Leaflet markers; conditional fixed-route optimizer. Small reviewed coverage and no modeled access/detours. |
| Vehicle maximum range 500 miles, 10 MPG | PASS | Capacity derived as 50 gallons; independent oracle, boundaries, conservation and infeasible gaps. |
| Money spent at supplied fuel prices | PASS for private assessment mode | Original CSV audit/import and actual local assessment requests tested. Public demonstration deliberately uses labelled illustrative prices; no private file/prices uploaded. |
| Free map/routing API | PASS for recorded free roads; live UNVERIFIED | Actual attributed OSRM roads; current HeiGIT adapter/contract/mocks. Genuine authenticated key still needed. |
| Quick responses, few external requests | PASS executable cache tests / live UNVERIFIED | One mocked directions miss, zero repeats/fuel/mode changes; recorded reads separately counted, separate geocoding and phase timings. Hosted/live timing pending. |
| Latest stable Django | PASS at verification | Django 6.1.2, Python 3.12.10; pinned dependencies installed and checked. |
| GitHub source code | PASS | Sanitized designated main published, independently cloned; actual Ubuntu CI passed. Later endpoint fix receives a final CI run. |
| <=5-minute Loom showing API and code | PARTIAL | Updated natural 4:30 script, precise shot list and Postman requests. Human microphone/login/actual recording required; no link invented. |
| Submit within three days | UNVERIFIED / user-controlled | Receipt timestamp unavailable; no employer submission performed. |

## Final engineering evidence

- Full local automated suite: **302 passed, 1 skipped**, 225.21 seconds; **95.21%** statement coverage (895/940). Skip is genuinely credential-dependent ORS. Focused production/API regressions: 33 passed.
- Django system/migration checks, production deployment checks, pip consistency, Ruff lint/format, strict optimizer mypy and JS syntax pass. Static collection and real PostgreSQL migrations/32,071-place/public-site seeding passed.
- Historical Phase 2 local Newman: 74 assertions across 11 actual HTTP requests; fresh safe package: 294 passed / two explicit input-dependent skips. These are local historical results, not hosted evidence.
- Security: secret/database fail-fast production settings; HTTPS/header controls; conservative public quotas; one threaded worker; no admin credentials, open CORS or client-side provider key. Private assessment CSV, old excerpt, .env files, databases/caches and environments remain excluded.

## Remaining critical gates

1. Genuine HeiGIT key via local .env or hosting secret: authenticated short/long directions/Pelias, cache repeat and live corridor eligibility comparison.
2. Confirm the connected Render workspace so the authorized free web service can be created; verify actual HTTPS homepage/assets/health/API, Newman, desktop/mobile browser and restart persistence.
3. Publication and final endpoint CI are PASS; no remaining code/CI blocker is known.
4. Record and inspect the <=5-minute Loom, add its real share URL, then the user submits to the employer.

Nationwide strict coverage is PARTIAL (31 reviewed sites). Full assessment estimated mode has 5,983 city points and 612 unresolved sites, with conditional proximity/savings; the public fixture has only 31 reviewed sites. Seattle–San Francisco fails priced coverage honestly. No station/price/route is invented to guarantee success.

## Final endpoint audit correction

The original Seattle–San Francisco recording is retired: Census's offshore San Francisco point snapped 29,953 m onto Point Reyes Lighthouse Road, so the historical 835.41-mile result is not a valid San Francisco city-route demonstration. The old file is preserved byte-for-byte with a retirement manifest. A single sourced GeoNames populated-place reference (CC BY 4.0, attributed) now corrects this endpoint only; station approximations and original Census records are unchanged. One additional real OSRM request produced a corrected **808.901515-mile** road with **12,369 points** and a **2.502-metre destination snap**. Both fuel modes still return an honest gap. Active route manifest: five pairs; six road files retained including the retired one.

Every new API road is now rejected before caching if its first/last coordinate lies over 1 km from the requested endpoint. This is a conservative proximity guard, not proof of highway/station access. The route-cache namespace was advanced so previously unchecked cached geometry cannot bypass it. Endpoint source and representative-point qualification are returned in metadata. Precise-address locality checks use the reviewed endpoint reference when present. Other political/place representative points can still be unsuitable: such routes return a useful error requiring a precise address, rather than quietly accepting distant snapping.

## Publication and independent evidence

The sanitized main branch is published at https://github.com/ShyanCS/FuelRouteIQ. First CI discovered a missing PostgreSQL OPTIONS dictionary for URLs without query parameters; the fix uses setdefault and enforces production TLS, with an executable regression. Ubuntu CI on `12d948933d78ebf0c02a7b0880a1408e382b5ee3` then passed: **302 passed, 2 skipped in 32.44 s**, plus system/deploy/static/migration/pip/lint/format/type checks and **74 Newman assertions across 11 actual loopback HTTP requests**. This is CI evidence, not hosted HTTPS or authenticated ORS proof. [Run](https://github.com/ShyanCS/FuelRouteIQ/actions/runs/38231909027). Later endpoint changes have a separate final verification gate.

A fresh public clone and new environment installed its lockfile, migrated/seeding 32,071 places and 31 public reviewed sites, and returned expected statuses for all five pairs/modes. Unseen Austin→Austin is a valid zero-distance 200; Austin→Houston returns the honest recorded-provider unavailable error until live routing is configured. Browser checks compare API/UI cost $138.44, two actual stop pins, paired fuel jumps, short-trip cash/consumption, estimated disclosure and cleared failure states. Desktop/mobile layouts were inspected; mobile document width equals its client width. These are local-clone checks, not production browser evidence.

The dependency advisory scan checked all **36 pinned packages, no skips, no known vulnerabilities**. This is a point-in-time advisory check, not a security guarantee. Private files/real credentials are excluded by publication/archive allowlists and Git ignore. Git attributes preserve checksummed source/recording bytes on Windows and Linux clones.

Actual local APIClient over the remote PostgreSQL database passed nine cases and route reuse. First response **13,199.616 ms**, repeat **8,394.158 ms**; these include cross-region database round trips from the local machine and are not a hosted latency claim. Pure algorithm/network phase fields are separately recorded. The hosted app/database are intended for nearby regions, but no unmeasured improvement is claimed. Repeated real database seed retained revision `e38195aa-0f88-439f-ae25-9e602ed0991c` and all 31 reviewed sites. Artifacts: `artifacts/public/production-checks.json`, `production-source-review.json` and `production-dependency-audit.json`.

Final endpoint-corrected local suite: **306 passed, 1 skipped in 228.23 s**, **95.30%** backend statement coverage (913/958). The sole local skip requires a genuine ORS key. No mock or recording is claimed as successful authenticated ORS. Full evidence is in `artifacts/public/final-tests.txt` and `final-coverage.json`.

Final endpoint-corrected publication/CI is verified on code commit **e7905f473fe6011f11e9b14cb8b0132e18cd7eb4**. [Successful Ubuntu run](https://github.com/ShyanCS/FuelRouteIQ/actions/runs/38234341812): **305 passed, 2 explicit skips in 27.46 s**, plus **74/74 Newman assertions across 11 real loopback HTTP requests**, production static/security/migration, dependency, lint/format and type checks. Skips: private assessment CSV and genuine ORS key. The independent public clone fast-forwarded to that commit and confirmed the corrected Seattle road/provenance/snap distances and honest 422 coverage gap. Later documentation-only commits preserve this code evidence. Public HTTPS, hosted Postman/browser/restart tests and successful authenticated ORS remain UNVERIFIED; Loom is unrecorded.
