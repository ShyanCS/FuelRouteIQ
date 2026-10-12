# Loom shot list — target 4:30, maximum 5:00

Prepare three tabs: live application, hosted Postman collection, GitHub source/audit. Avoid Render environment screens and secret files. Pre-wake the free service. Use the actual response figures at recording time.

| Time | Screen interaction |
|---|---|
| 0:00–0:20 | Live homepage; introduce Django, 500-mile range, 10 MPG. |
| 0:20–1:05 | Click Chicago–Dallas, strict mode, Optimize. Show live-provider and illustrative-price badges, real road, two station pins, cash/consumption/savings and fuel jumps. Click one pin to show gallons and reviewed source. |
| 1:05–1:55 | Postman: select hosted environment, send Long strict request. Expand route/provider, fuel_stops, fuel_summary, cost_basis and meta. |
| 1:55–2:20 | Repeat identical request; show route_cache_hit and directions_api_calls=0. Change initial fuel to 45; same route cache, recalculated purchases. |
| 2:20–2:45 | Send short known-value request; distinguish zero cash, positive consumption and valued initial inventory. |
| 2:45–3:35 | GitHub: api/service.py → routing/provider.py → optimizer/engine.py → tests/test_optimizer.py. Explain fixed-route greedy and independent DP. |
| 3:35–4:10 | Audit: actual local/CI/Newman counts, genuine provider evidence. Return UI: estimated qualification and/or Seattle useful gap. State limited coverage and no routed detours. |
| 4:10–4:30 | README links/setup/Postman; close and stop recording. |

After recording: watch it, confirm no secrets, check under five minutes, copy the real Loom share URL and add it to README/SUBMISSION_LINKS. Do not submit to the employer automatically.
