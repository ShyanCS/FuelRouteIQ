# Submission links

- GitHub: https://github.com/ShyanCS/FuelRouteIQ (published and independently cloned).
- Public application: **pending required Render workspace confirmation**.
- Public API: **pending public host**, path `/api/v1/routes/optimize/` (POST JSON).
- Health: **pending public host**, path `/api/v1/health/`.
- Postman: `postman/FuelRouteIQ.postman_collection.json`; set `base_url` to the verified host.
- Loom: **not recorded**. Use `docs/FINAL_LOOM_SCRIPT.md`, `docs/LOOM_SHOT_LIST.md` and `docs/DEMO_REQUESTS.md`.
- Review archive: `FINAL_REVIEW_PACKAGE.zip` (generated after final checks).

Employer-facing description: FuelRoute IQ is a Django API and interactive map that minimizes fuel purchases along a selected US road route using audited price inputs, precise fuel accounting, independent optimization checks and cached routing. It explains purchases and baseline savings while visibly qualifying station-location uncertainty. The public demonstration uses illustrative prices; the supplied assessment CSV is supported privately. Fixed-route, zero-detour and coverage limitations are disclosed.

Validated CI: https://github.com/ShyanCS/FuelRouteIQ/actions/runs/38231909027 (code commit 12d948933d78ebf0c02a7b0880a1408e382b5ee3; later endpoint correction has separate final CI evidence).
