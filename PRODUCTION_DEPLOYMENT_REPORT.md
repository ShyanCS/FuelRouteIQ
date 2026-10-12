# Production deployment report

Final phase, 13 October 2026 local time. The service is **externally reachable and functionally verified**, not merely marked deployed by its dashboard. Public data is illustrative; private assessment prices are not hosted.

| Resource | Actual configuration |
|---|---|
| Application | https://fuelroute-iq.onrender.com/ |
| API | POST https://fuelroute-iq.onrender.com/api/v1/routes/optimize/ |
| Health | https://fuelroute-iq.onrender.com/api/v1/health/ |
| Render | `fuelroute-iq`, `srv-db6gqadg1s2s7396m3r0`, My Workspace, Virginia, free web instance |
| Source | https://github.com/ShyanCS/FuelRouteIQ, main, automatic deploy on commit |
| Runtime | Python 3.12.10, pinned Gunicorn, one worker/four threads, port supplied by Render |
| Build/start | `sh scripts/render_build.sh` / `sh scripts/render_start.sh` |
| PostgreSQL | Dedicated Neon project `rough-rice-16106009`, database `fuelroute`, PostgreSQL 16, AWS us-east-1, free plan |
| Connections | TLS required; pooled app connection, direct schema/seed connection, 10s connect deadline |
| Readiness | Render HTTP health path `/api/v1/health/`, configured and confirmed through connector |
| Seed | 32,071 Census places; 31 reviewed sites with illustrative prices, idempotent checksum-based import |

Private DJANGO_SECRET_KEY, ORS_API_KEY, DATABASE_URL and DATABASE_URL_UNPOOLED are in service secrets, never browser code or source. DEBUG=false; exact Render hostname; HTTPS redirect/HSTS; nosniff/DENY/referrer headers; secure cookie settings; no admin credentials or permissive CORS. Body limit 16 KB. Directions/geocoding have 5s connect/20s read/write deadlines, no automatic retries. Errors are structured and cannot silently become recorded routes.

## Executed validation

- HTTPS homepage, health and all referenced static CSS/JS returned 200 with valid TLS/security headers.
- Fifteen external API cases cover long/repeat/changed fuel/estimated, valued short, three more corridors, unseen Austinâ€“Houston, foreign/invalid JSON, precise address/repeat and unsupported long route/repeat. Assertions check fuel conservation, tank bounds, exact cash aggregate and paired timeline. Artifact `artifacts/public/production-http.json` records each response and call counts.
- Actual hosted Postman/Newman: 11 HTTPS requests, 74 assertions, zero failures; `production-postman-summary.json`. This is independent of CI loopback/mock evidence.
- Genuine ORS/Pelias and failure checks are separately documented in `ROUTING_AND_COVERAGE_REPORT.md`; the configured key actually succeeded.
- Redeployment after health-path configuration (`dep-db6iaqgm7kps73e0gefg`) retained dataset revision `07029b0d-e6da-4346-b8e7-983839eb34d3`, station data and route geometry cache: subsequent Chicagoâ€“Dallas made zero directions/geocoding calls. `production-redeploy.json`. Optimization TTL expiry can legitimately recompute the plan.
- Public browser, final code redeploy, concurrency/throttle and final CI evidence are recorded in `artifacts/public/production-final-verification.json` as those gates complete. Historical source-review/local browser evidence is explicitly distinguished.
- Application error logs inspected through Render contained no entries at the initial validation checkpoint; that is a bounded observation, not a promise that future logs stay empty.

Initial live cold road-cache request: 2,597.073 ms external end-to-end, 1,839.753 ms server pipeline, 1,090.625 ms provider, 488.413 ms projection, 0.107 ms greedy. Immediate warm repeat 473.236 ms end-to-end/107.235 ms pipeline, zero outbound calls. `production-first-probe.json` preserves historical observed tool output; the validator does not manufacture these measurements on later runs. Cold here means a route-cache miss, not Render waking from sleep. Other actual per-case timings appear in the HTTPS/Newman artifacts.

## Persistence and operation

Station rows and all cache tables reside in durable PostgreSQL, not ephemeral hosted SQLite. Startup runs migrations/cache-table creation and idempotent seed before Gunicorn. Identical seed preserves the dataset revision; changed public input/enrichment changes plan identity. `seed_demo` refuses to replace an assessment import. Git line-ending normalization changed the evidence hash on the first Linux seed; the documented production revision then remained stable on redeploy. Checked-in source/route bytes use explicit Git attributes for reproducible checksums.

To reproduce: connect this main branch to a free Render web service; use the build/start commands above; set private environment secrets and ROUTING_PROVIDER=ors; set health path. `render.yaml` documents the same web configuration. Provision a separate free PostgreSQL database with pooled/direct TLS URLs. Never switch to paid resources without approval. Do not expose assessment CSV/results until its publication permission is resolved.

For updates, push reviewed main; auto-deploy installs the lockfile, collects manifest static files and reruns safe startup migration/seed. Inspect deployment/log status, then rerun bounded HTTPS/Newman checks. A failed release can be rolled back to an existing tested Render deploy; no Git history reset is required. Do not print secret settings or clear the shared route cache while demonstrating. One worker is deliberate: process-local route locks and quota updates share synchronization. Multiple workers require distributed atomic coordination before scaling.

## Free-tier and provider limits

[Render free-plan documentation](https://render.com/docs/free): idle web instances spin down after 15 minutes and may take about a minute to wake; 750 instance-hours/month are shared across the workspace, which also contains unrelated services. Ephemeral filesystem and no free persistent disk; dedicated Neon avoids Render free PostgreSQL's 30-day expiration. Outbound/bandwidth/build quotas apply. No paid instance/upgrade/purchase was selected or authorized; monitor account caps and suspend rather than approve overages.

[Neon free-plan update](https://neon.com/blog/neon-free-plan-1-gb-per-project): published storage 1 GB/project and 100 CU-hours/project/month; some account API records remain conservatively capped at 512 MB. Account-enforced idle/suspension and transfer limits apply; the small demo fits. No custom idle-suspension setting or uptime guarantee is claimed.

[Current HeiGIT Standard plan](https://account.heigit.org/info/plans): 0â‚¬, directions 2,000/day and 40/minute; geocoding 3,000/day and 100/minute. These are published plan limits, not verified account usage. Public app limits are stricter: 30/min/client, 30/min/service, 500/day/service. Calls to browser map tiles are separate and never folded into directions/geocoding counts. No quota exhaustion was forced to test vendor rate errors.

The hosting free tier and finite price/location coverage are appropriate demonstration constraints, not a nationwide operational fueling service or production SLA. Actual Loom remains unrecorded.
