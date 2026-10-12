# Production deployment report

12 October 2026. **Public HTTPS deployment pending the required Render workspace selection.** No successful public URL, hosted request or deployment benchmark is claimed yet.

## Infrastructure prepared and executed

- Render connector is authenticated. Exactly one workspace was returned: My Workspace, shyan@cvs.du.ac.in, `tea-d28g9gruibrs73asrec0`. The tool explicitly requires user-confirmed workspace selection; the confirmation request is pending. No paid resource is selected.
- Dedicated Neon PostgreSQL 16 project `rough-rice-16106009`, name `fuelroute-iq`, in `aws-us-east-1`, under the connected console-managed **free** organization. Minimum/maximum compute 0.25 CU. Connection strings and a random production Django secret are in ignored `.env.production`; no values are printed or published.
- Actual Django migrations, cache table, 32,071 places and 31 reviewed/public illustrative sites have been loaded. No original assessment prices were uploaded. A custom suspension interval was rejected by the free account, so enforced defaults were retained.
- `render.yaml` / `scripts/render_build.sh` / `scripts/render_start.sh`: free Python web service, Python 3.12.10, versioned/compressed static assets, direct-URL migrations, transactional idempotent public seed, one Gunicorn worker/four threads bound to the platform PORT, 90-second worker timeout and health route `/api/v1/health/`.

## Security and verification

DEBUG=false fails startup without a strong private secret and durable PostgreSQL. HTTPS redirect, HSTS, secure cookies, trusted proxy and exact Render hostname are configured. No admin accounts or client-side ORS keys exist. Route bodies are capped at 16 KB; input and provider responses are validated. No CORS allow-all policy is introduced. Public optimization is limited to 30/minute per client and 500/day service-wide using the persistent shared cache and a process lock. Health remains outside that quota.

Production `manage.py check --deploy`: zero issues. Static collection succeeds. Existing provider requests have 5-second connect / 20-second HTTP timeouts and no retries or hidden fallback. Error responses are structured; unexpected failures log a correlation ID without client traceback.

Public HTTP/Newman/browser/restart evidence is **UNVERIFIED until a real service URL exists**. Local database checks and recorded roads do not substitute for it. Successful ORS is also UNVERIFIED because the real key remains absent.

## Free-plan limitations and operations

[Render's current free documentation](https://render.com/docs/free): web instances sleep after 15 idle minutes and may take about a minute to wake; 750 free workspace instance-hours/month; ephemeral filesystem, no free persistent disk. Free Render PostgreSQL expires after 30 days, so this deployment uses dedicated Neon storage. Render can suspend unusually high outbound traffic. Bandwidth/build usage can incur overages when a payment method is present: keep a $0 spending limit/account suspension policy; no overage or paid upgrade is authorized.

[Neon's 2 October 2026 update](https://neon.com/blog/neon-free-plan-1-gb-per-project) raises free storage to 1 GB/project; some account/API records still show the conservative 512 MB cap. Free compute is 100 CU-hours/project/month, ten branches and six-hour restore history. Account-enforced idle suspension and transfer quotas apply; monitor the console. There is no paid-plan uptime guarantee. The bundled illustrative dataset is small and rebuildable; do not upgrade plans without approval.

Deploy the reviewed main branch. Configure private DATABASE_URL (pooled, SSL), DATABASE_URL_UNPOOLED (direct, SSL), DJANGO_SECRET_KEY and DEBUG=false through hosting secrets. Render supplies its public hostname. Start in explicitly recorded mode when no key exists; set genuine ORS_API_KEY and ROUTING_PROVIDER=ors only for deliberate live validation. Secret changes require redeploy. Failed provider routes are never cached as successful or silently replaced with recordings.

On redeploy the start script runs migrations/cache creation and skips identical seed work; station data/cache remain in PostgreSQL. New public fixture or verified-evidence revisions update the plan identity. An assessment database is protected from replacement by `seed_demo`; use separate private deployment/import configuration if assessment-price publication is explicitly authorized.

## Final endpoint audit correction

The original Seattle–San Francisco recording is retired: Census's offshore San Francisco point snapped 29,953 m onto Point Reyes Lighthouse Road, so the historical 835.41-mile result is not a valid San Francisco city-route demonstration. The old file is preserved byte-for-byte with a retirement manifest. A single sourced GeoNames populated-place reference (CC BY 4.0, attributed) now corrects this endpoint only; station approximations and original Census records are unchanged. One additional real OSRM request produced a corrected **808.901515-mile** road with **12,369 points** and a **2.502-metre destination snap**. Both fuel modes still return an honest gap. Active route manifest: five pairs; six road files retained including the retired one.

Every new API road is now rejected before caching if its first/last coordinate lies over 1 km from the requested endpoint. This is a conservative proximity guard, not proof of highway/station access. The route-cache namespace was advanced so previously unchecked cached geometry cannot bypass it. Endpoint source and representative-point qualification are returned in metadata. Precise-address locality checks use the reviewed endpoint reference when present. Other political/place representative points can still be unsuitable: such routes return a useful error requiring a precise address, rather than quietly accepting distant snapping.

## Publication and independent evidence

The sanitized main branch is published at https://github.com/ShyanCS/FuelRouteIQ. First CI discovered a missing PostgreSQL OPTIONS dictionary for URLs without query parameters; the fix uses setdefault and enforces production TLS, with an executable regression. Ubuntu CI on `12d948933d78ebf0c02a7b0880a1408e382b5ee3` then passed: **302 passed, 2 skipped in 32.44 s**, plus system/deploy/static/migration/pip/lint/format/type checks and **74 Newman assertions across 11 actual loopback HTTP requests**. This is CI evidence, not hosted HTTPS or authenticated ORS proof. [Run](https://github.com/ShyanCS/FuelRouteIQ/actions/runs/38231909027). Later endpoint changes have a separate final verification gate.

A fresh public clone and new environment installed its lockfile, migrated/seeding 32,071 places and 31 public reviewed sites, and returned expected statuses for all five pairs/modes. Unseen Austin→Austin is a valid zero-distance 200; Austin→Houston returns the honest recorded-provider unavailable error until live routing is configured. Browser checks compare API/UI cost $138.44, two actual stop pins, paired fuel jumps, short-trip cash/consumption, estimated disclosure and cleared failure states. Desktop/mobile layouts were inspected; mobile document width equals its client width. These are local-clone checks, not production browser evidence.

The dependency advisory scan checked all **36 pinned packages, no skips, no known vulnerabilities**. This is a point-in-time advisory check, not a security guarantee. Private files/real credentials are excluded by publication/archive allowlists and Git ignore. Git attributes preserve checksummed source/recording bytes on Windows and Linux clones.

Actual local APIClient over the remote PostgreSQL database passed nine cases and route reuse. First response **13,199.616 ms**, repeat **8,394.158 ms**; these include cross-region database round trips from the local machine and are not a hosted latency claim. Pure algorithm/network phase fields are separately recorded. The hosted app/database are intended for nearby regions, but no unmeasured improvement is claimed. Repeated real database seed retained revision `e38195aa-0f88-439f-ae25-9e602ed0991c` and all 31 reviewed sites. Artifacts: `artifacts/public/production-checks.json`, `production-source-review.json` and `production-dependency-audit.json`.

Final endpoint-corrected publication/CI is verified on code commit **e7905f473fe6011f11e9b14cb8b0132e18cd7eb4**. [Successful Ubuntu run](https://github.com/ShyanCS/FuelRouteIQ/actions/runs/38234341812): **305 passed, 2 explicit skips in 27.46 s**, plus **74/74 Newman assertions across 11 real loopback HTTP requests**, production static/security/migration, dependency, lint/format and type checks. Skips: private assessment CSV and genuine ORS key. The independent public clone fast-forwarded to that commit and confirmed the corrected Seattle road/provenance/snap distances and honest 422 coverage gap. Later documentation-only commits preserve this code evidence. Public HTTPS, hosted Postman/browser/restart tests and successful authenticated ORS remain UNVERIFIED; Loom is unrecorded.
