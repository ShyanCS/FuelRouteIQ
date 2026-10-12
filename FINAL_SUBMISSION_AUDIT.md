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
| GitHub source code | Pending publication | Designated empty remote verified, sanitized source prepared; SHA/remote CI recorded after push. |
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
3. Verify pushed GitHub source and actual CI result; resolve any CI failure before claiming PASS.
4. Record and inspect the <=5-minute Loom, add its real share URL, then the user submits to the employer.

Nationwide strict coverage is PARTIAL (31 reviewed sites). Full assessment estimated mode has 5,983 city points and 612 unresolved sites, with conditional proximity/savings; the public fixture has only 31 reviewed sites. Seattle–San Francisco fails priced coverage honestly. No station/price/route is invented to guarantee success.
