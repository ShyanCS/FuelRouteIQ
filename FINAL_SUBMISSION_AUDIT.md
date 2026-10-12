# Final submission audit

13 October 2026 local time. Authoritative original employer requirements are evaluated below. PASS means demonstrated behavior within its disclosed assumptions, not a nationwide navigation guarantee. This audit replaces stale absent-key/unpublished claims.

| Employer requirement | Status | Actual evidence / residual risk |
|---|---|---|
| API accepts start/finish within USA | PASS | Local Census/Pelias validation; genuine hosted US requests and foreign/invalid rejection. Only supported unambiguous US formats, 50 states/DC |
| Return route map and cost-effective fuel stops | PARTIAL | Actual hosted Leaflet/ORS geometry and fixed-route purchase optimum. Four demo corridors feasible; limited 31-site public prices mean some unseen long routes fail transparently |
| Maximum 500-mile range/multiple fuel ups | PASS | Derived 50-gallon tank at 10 MPG, exact gap/capacity tests, DP oracle; live long routes show multiple feasible stops; zero arrival allowed |
| Total money spent at 10 MPG | PASS | Actual prices selected from active dataset, Decimal costs, explicit cash/owned-fuel accounting, hosted conservation assertions |
| Use supplied fuel-price file | PASS locally / PARTIAL public | Real 8,151-row import/raw audit and real-price live matrix tested locally. Public fixture is illustrative and prominently labelled; original CSV excluded pending redistribution permission |
| Free map/routing API selected | PASS | Genuine free HeiGIT directions/Pelias plus attributed Leaflet/map data. Provider license/limits documented |
| Latest stable Django | PASS | Django 6.1.2 checked against official release, tested Python/DRF pins; real public health/lockfile |
| Return quickly | PASS, scoped | Measured live road-cache cold 2,597 ms / warm 473 ms; phases independently timed. Free sleep/wake is not an SLA |
| Minimize external routing calls, ideally one | PASS | Actual cold one directions/zero geocoding; warm/fuel/mode zero directions; precise address geocoding counted separately; failures not cached |
| Loom ≤5 minutes with API and code | PARTIAL | Updated 4:30 spoken script/shot list/hosted requests ready. No recording/link exists; human microphone/account required |
| Share GitHub source | PASS | Public repository independently cloned; exact current CI code/run recorded in production-final-verification.json |
| Submit within three days | UNVERIFIED | Receipt timestamp not supplied. Employer submission remains user-controlled and is not performed |

## Executed verification

- Final full local suite: **308 passed, zero skipped, zero failures in 99.17s**, including private CSV audit and genuine opt-in ORS. Statement coverage **95.22% (937/984)**. Raw successful summary/coverage in artifacts/public/final-tests.txt and final-coverage.json.
- Earlier restricted-network run: 307 passed/one live DNS failure. Network-enabled run exposed one SQLite cache concurrency failure; genuine ORS passed. Local cache SQL synchronization fixed it. Those failures are disclosed in production-final-verification.json; no failed or skipped test is counted as successful.
- Django checks, migration drift, Ruff lint/format, strict optimizer mypy and pip consistency passed; production check --deploy zero issues. 36-package dependency advisory scan: zero known vulnerabilities/zero skips, point-in-time only.
- Five genuine ORS roads acquired in the private assessment matrix. Actual authenticated Pelias address, invalid-key rejection/recovery, forced network deadline and unsupported-distance repeated failure tested. Unforced vendor rate-limit/5xx/malformed behavior remains mocked, not fabricated live evidence.
- Actual public HTTPS validator: fifteen cases; real homepage/static/health and consistency/cache/foreign/failure handling. Actual hosted Newman: **11 requests/74 assertions/zero failures**. Final code CI on **cf101b4f80ee9e45e6b010a3d94920f179a4d666** passed **306 tests/two explicit skips in 24.86s**, plus **74 loopback Newman assertions**, [run](https://github.com/ShyanCS/FuelRouteIQ/actions/runs/38292091673). CI skips private-source absence and the unconfigured opt-in live test; local full verification executed both. CI loopback is never mislabeled as hosted evidence.
- Fresh public clone/new environment installed pins, migrated/cached/seeded 32,071 places and 31 sites without private CSV; five pairs in both modes gave eight 200/two honest 422. Linux CI independently runs setup/checks/recorded HTTP collection. The final public clone passed 36 API/production regressions in 15.03s on cf101b4.
- Actual PostgreSQL/route cache survived Render health-path redeploy. Public price revision remained 07029b0d-e6da-4346-b8e7-983839eb34d3; next long route made zero directions calls.

- Deployed browser checks passed long/short/estimated/gap states; UI cash/savings agree with JSON, both markers agree with independent Web-Mercator projection within 0.76 pixels, and before/after timeline jumps use identical mileage. Stale costs/pins/timeline clear on failure. No browser console errors. Desktop automation passed; the tool viewport override failed to apply, disclosed as unverified automation. The user separately ran the phone journey and confirmed “Phone layout works”; mobile PASS is manual evidence.
- Four simultaneous public requests acquired one new directions route and identical results. Application throttle returned 429/Retry-After after 29 bounded empty-body requests, adding zero provider calls; health stayed 200.

## Honest readiness decision

The source and working public application are suitable for independent review. Nationwide reviewed-price coverage remains partial; Seattle–San Francisco has a real road but no feasible priced plan. Prices are undated snapshots or expressly illustrative. Model detours/reserve are zero; entrances, operational access, HGV restrictions and hours are unverified. Greedy optimality covers a fixed route/candidate set, not all possible drives.

No private price data, real secrets, paid resources or employer submission are authorized/exposed. A public assessment-price dataset requires resolved permission; the local importer and private original matrix already demonstrate assessment support. The final employer-facing submission still needs the actual under-five-minute Loom recording (the user explicitly chose to handle it) and user-controlled submission/deadline confirmation. Final current machine-verifiable gates are in artifacts/public/production-final-verification.json.
