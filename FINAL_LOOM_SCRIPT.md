# Final Loom script — target 4 minutes 30 seconds

Stage directions in brackets are not spoken. Read current API numbers before recording. Approximately 500 spoken words; leave time for interactions and natural pauses.

## 0:00–0:20

“This is FuelRoute IQ, my Django backend assessment. It takes US start and finish locations, returns a real road route, and calculates where and how much fuel to buy. The default 500-mile range and ten miles per gallon give a fifty-gallon tank.”

## 0:20–1:05

[Run Chicago–Dallas and click a stop marker.]

“Here is the public HTTPS application using authenticated OpenRouteService. Everything on the map and fuel timeline comes from the Django API. This journey is about 965 miles, with two reviewed station sites. The current public dataset gives $139.44 in purchases and $7.57 savings against the independently simulated baseline.

The prices are prominently labelled illustrative. The original employer CSV is supported and tested through the audited importer, but stays private because its redistribution rights are unspecified. These are reviewed site coordinates, not a claim that highway access or detours have been routed.”

## 1:05–1:55

[Send the long strict request in Postman; expand stop and fuel-summary JSON.]

“This is the actual hosted API. It returns the road geometry, distance and duration, vehicle assumptions, station sources, prices, quantities, and fuel before and after each purchase. It consumes about 96.48 gallons and buys 46.48, starting with fifty gallons already owned. The remaining fuel is zero, which the model explicitly allows. Exact unrounded costs are included; displayed dollars are rounded only at the reporting boundary.

The baseline uses the same starting fuel and candidates, so its $147.01 purchases give a comparable savings figure. This is a snapshot and model comparison, not a guaranteed pump-price discount.”

## 1:55–2:20

[Repeat and then set initial fuel to 45.]

“The repeat reports a route cache hit and zero new directions calls. Changing fuel keeps that geometry and recalculates purchases. The captured cold request made one directions call. Geocoding is counted separately; city and state endpoints resolve from the local index.”

## 2:20–2:45

[Send the short known-value request.]

“Milwaukee consumes about 9.80 gallons but buys no fuel with a full tank. Zero cash spending does not mean free consumption. Supplying a two-hundred-dollar initial inventory value enables FIFO economic consumption and remaining-asset accounting; without that value those estimates remain unavailable.”

## 2:45–3:35

[Show the service, provider, optimizer and oracle files.]

“Django validation, routing, station projection and optimization are separate modules. The provider has bounded timeouts, structured failures and no concealed replay fallback. The greedy algorithm buys enough to reach a cheaper reachable opportunity; otherwise it fills, capped by destination need. Decimal arithmetic maintains the fuel ledger.

An independent dynamic-programming oracle checks cost and infeasibility. The optimum is for a fixed route, eligible stations, divisible purchases and zero modelled detours. It does not optimize every possible road or promise operational access.”

## 3:35–4:10

[Show the final audit and current counts; inspect estimated warning or Seattle gap.]

“The audit separates deterministic, recorded, genuinely live and deployed evidence. [Read the current local test and hosted Postman counts.] CI also checks reproducible setup. Estimated mode visibly qualifies city positions. National strict coverage remains limited: Seattle to San Francisco returns its actual road with a priced-station gap, without inventing a stop. The public limiter protects provider quota.”

## 4:10–4:30

“The repository includes migrations, a pinned setup, provenance, free deployment configuration, the Postman collection and verification artifacts. The README links to the live app and explains the assumptions. Thank you.”

No Loom recording or URL exists until the human recording is completed and inspected.
