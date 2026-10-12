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
