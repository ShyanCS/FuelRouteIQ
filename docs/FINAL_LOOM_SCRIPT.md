# Final spoken walkthrough — target 4:30

## 0:00–0:25 — introduction

“This is FuelRoute IQ, my Django backend assessment. It accepts US starting and finishing locations, returns a road route, and calculates where and how much fuel to buy. The assessment defaults are a 500-mile range and 10 miles per gallon, which gives a 50-gallon tank.”

## 0:25–1:15 — hosted application

“Here is the hosted Django application. I’m running Chicago to Dallas. The map, station markers, costs and fuel timeline all come from the API response. Green pins are individually reviewed operator station sites. The public demo uses clearly labelled illustrative prices; the original employer CSV is supported through the audited import command and is kept private.

The provider badge tells us whether this request uses live ORS or a recorded OSRM road. [Read the badge and describe the actual mode.] Recorded roads are real road geometries, but replay makes no external directions call. There is no automatic fallback that disguises a provider failure.”

## 1:15–2:10 — Postman and accounting

“In Postman I’m sending the same JSON to the hosted optimization endpoint. The response contains the route geometry, mileage, vehicle assumptions, selected stations, their source and prices, exact purchase quantities and fuel before and after each purchase.

The total here is [read total_refueling_spend_usd] in cash purchases, with [read gallons_consumed] gallons consumed and [read gallons_purchased] purchased. The vehicle starts with 50 gallons already owned. For the short Milwaukee route, purchases can be zero while consumption is positive. If the starting fuel’s value is unknown, its economic consumption cost remains unavailable. Savings compare a separately simulated price-blind baseline with the same starting fuel and candidates.”

## 2:10–2:40 — caching

“I repeat the long request. The metadata shows a route cache hit and zero new directions calls. Changing initial fuel or station mode keeps the same geometry cache; prices and vehicle assumptions belong in the separate optimization cache. Endpoint geocoding is counted separately. Common city and state inputs resolve from the local Census index.”

## 2:40–3:30 — architecture and algorithm

“The request flows through validation, endpoint resolution, the routing adapter, candidate projection and the optimizer. These are separate modules with deterministic offline tests. The routing adapter has bounded timeouts and structured authentication, quota and malformed-response errors.

The greedy optimizer buys only enough to reach the next cheaper reachable station; otherwise it fills the tank, capped by destination need. Decimal arithmetic keeps fuel and money consistent. An independent dynamic-programming oracle checks its answers. The proof applies to a fixed route and eligible stations with divisible purchases and zero modeled detours; it does not claim a global minimum driving cost.”

## 3:30–4:15 — evidence and honest limits

“The final audit records the actual test, coverage, CI and hosted Postman results. [Show and read the current verified results, including skips.] Station prices are not live pump prices. A reviewed site coordinate is not proof of an entrance, opening hours or a routed detour. Estimated mode prominently qualifies city positions. Coverage gaps return the real route with an explanation, rather than invented stops. Seattle to San Francisco is one such limitation with the current priced dataset.

[If authenticated ORS remains unverified: ‘Successful authenticated ORS validation still needs a genuine configured key; the hosted replay demo and mocked adapter tests do not prove it.’]”

## 4:15–4:30 — close

“The repository includes migrations, reproducible setup, data provenance, production configuration and this Postman collection. The README and final audit explain what is verified and what remains limited. Thank you.”

Bracketed instructions are stage directions, not words to read. Do not insert a live-provider, CI, deployment or test claim unless the current audit supports it. Record and inspect the actual video before adding a Loom link.
