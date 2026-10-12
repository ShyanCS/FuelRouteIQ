/* Leaflet map and SVG timeline render exactly the latest API response. */
"use strict";
const $ = (id) => document.getElementById(id);
const money = (value) => value == null ? "Unavailable" : `$${Number(value).toFixed(2)}`;
const number = (value, digits = 1) => Number(value).toLocaleString("en-US", {maximumFractionDigits: digits});
const priceLabel = (basis) => basis === "illustrative_test_fixture" ? "illustrative prices" : basis === "assessment_snapshot" ? "assessment prices" : "prices unavailable";
const map = L.map("map", {scrollWheelZoom: false}).setView([38.2, -93.2], 4);
map.attributionControl.addAttribution('<a href="https://www.naturalearthdata.com/">Natural Earth</a> · road geometry © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors');
fetch("/static/demo/us-states.geojson").then(r => r.json()).then(data => {
  L.geoJSON(data, {style: {color:"#c3cfc3",weight:1,fillColor:"#f1f4ee",fillOpacity:0.95},onEachFeature:(feature,layer) => {
    layer.bindTooltip(textElement("span", "", feature.properties.postal || feature.properties.name), {permanent:true,direction:"center",className:"state-label",interactive:false});
  }}).addTo(map).bringToBack();
}).catch(() => $("tile-status").textContent="State basemap unavailable; route geometry still shown");
let streetLayer = null;
$("street-tiles").addEventListener("click",() => {
  if (streetLayer) {map.removeLayer(streetLayer);streetLayer=null;$("tile-status").textContent="Local state basemap";return;}
  streetLayer = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {maxZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).addTo(map);
  streetLayer.on("tileerror",() => {if(streetLayer){map.removeLayer(streetLayer);streetLayer=null;}$("tile-status").textContent="Street tiles blocked or unavailable; local state basemap retained";});
  $("tile-status").textContent="Online street tiles";
});
const layers = L.featureGroup().addTo(map);
let latestResult = null;
let generation = 0;
let activeRequest = null;

function textElement(tag, className, text) {
  const element = document.createElement(tag); element.className = className; element.textContent = text; return element;
}
function drawRoute(route, labels = null) {
  if (!route?.geometry?.coordinates?.length) return;
  map.attributionControl.removeAttribution('© <a href="https://openrouteservice.org/">openrouteservice by HeiGIT</a> · <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>');
  if (route.provider === "ors") map.attributionControl.addAttribution('© <a href="https://openrouteservice.org/">openrouteservice by HeiGIT</a> · <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>');
  L.geoJSON(route.geometry, {style: {color: "#177d68", weight: 4, opacity: 0.9}}).addTo(layers);
  const points = route.geometry.coordinates;
  for (const [point,label] of [[points[0],labels?.start || $("start").value],[points[points.length-1],labels?.finish || $("finish").value]]) {
    L.circleMarker([point[1],point[0]], {radius:5,color:"#172b36",weight:2,fillColor:"white",fillOpacity:1}).bindTooltip(textElement("span", "", label),{permanent:true,direction:"right",className:"endpoint-label"}).addTo(layers);
  }
  map.fitBounds(layers.getBounds(), {padding: [35, 35], maxZoom: 12});
}
function timeline(points, distance, capacity) {
  const svg = $("timeline"); svg.replaceChildren();
  const ns = "http://www.w3.org/2000/svg";
  const add = (name, attrs, text) => {const node = document.createElementNS(ns, name); Object.entries(attrs).forEach(([k,v]) => node.setAttribute(k, v)); if(text !== undefined) node.textContent = text; svg.appendChild(node); return node;};
  const x = (mile) => 52 + (distance ? mile / distance : 0) * 716;
  const y = (fuel) => 140 - fuel / capacity * 112;
  for (const fraction of [0, 0.5, 1]) {
    const fuel = capacity * fraction;
    add("line", {x1:52, x2:768, y1:y(fuel), y2:y(fuel), class:"chart-grid"});
    add("text", {x:43, y:y(fuel)+4, "text-anchor":"end", class:"chart-label"}, `${number(fuel)} gal`);
    add("text", {x:x(distance*fraction), y:163, "text-anchor":"middle", class:"chart-label"}, `${number(distance*fraction,0)} mi`);
  }
  add("polyline", {points:points.map(p => `${x(p.mile_marker)},${y(p.fuel_gallons)}`).join(" "), fill:"none", stroke:"#177d68", "stroke-width":3, "stroke-linejoin":"round"});
  points.filter(p => p.event === "after_refuel").forEach((p,i) => {
    add("circle", {cx:x(p.mile_marker),cy:y(p.fuel_gallons),r:4,fill:"#177d68",stroke:"white","stroke-width":2});
    add("text", {x:x(p.mile_marker), y:Math.max(15,y(p.fuel_gallons)-9), "text-anchor":"middle", class:"chart-label"}, `Stop ${i+1}`);
  });
}
function render(result, submitted) {
  latestResult = result;
  const route = result.route, fuel = result.fuel_summary, meta = result.meta;
  $("journey").textContent = `${submitted.start} → ${submitted.finish}`;
  $("distance").textContent = number(route.distance_miles,0);
  $("spend").textContent = money(fuel.total_refueling_spend_usd);
  $("savings").textContent = money(fuel.savings_usd);
  $("baseline").textContent = fuel.baseline_status === "infeasible" ? "Baseline policy could not finish" : `Baseline ${money(fuel.baseline_spend_usd)}${fuel.savings_percent == null ? "" : ` · ${number(fuel.savings_percent)}% savings`}`;
  $("consumed").textContent = `${number(fuel.gallons_consumed)} gal`;
  $("purchased").textContent = `${number(fuel.gallons_purchased)} gal purchased during journey`;
  $("end-fuel").textContent = `${number(fuel.end_fuel_gallons)} gal at destination`;
  const routeLabel = route.provider === "identical_endpoints" ? "Same location; no directions needed" : route.recorded ? "Recorded road geometry" : "Live ORS road route";
  $("provider-badge").textContent = `${routeLabel} · ${priceLabel(meta.price_basis)}`;
  $("status").textContent = `${routeLabel} · ${meta.location_mode === "estimated" ? "Conditional city estimate" : "Verified station points; zero-detour model"} · ${number(route.duration_seconds/3600)} hours driving`;
  $("initial-volume").textContent = `${number(result.vehicle.initial_fuel_gallons)} gal`;
  $("initial-worth").textContent = fuel.initial_fuel_value_usd == null ? "Unknown" : money(fuel.initial_fuel_value_usd);
  $("economic-cost").textContent = fuel.economic_fuel_cost_usd == null ? "Unavailable · initial value unknown" : money(fuel.economic_fuel_cost_usd);
  const illustrative = meta.price_basis === "illustrative_test_fixture";
  $("quality-banner").className = `quality-banner${illustrative ? " illustrative" : meta.location_mode === "estimated" ? " estimated" : ""}`;
  $("quality-banner").textContent = `${illustrative ? "ILLUSTRATIVE TEST PRICES · " : meta.price_basis === "assessment_snapshot" ? "Assessment price snapshots · " : "Price dataset unavailable · "}${meta.location_mode === "estimated" ? "ESTIMATED CITY POSITIONS: highway access, detours and savings are conditional. " : "Reviewed station sites; access and detours unmeasured. "}This minimizes cash purchases only for the fixed route and eligible candidates.`;
  layers.clearLayers(); drawRoute(route, submitted);
  $("stops").replaceChildren(); $("stop-count").textContent = result.fuel_stops.length;
  if (!result.fuel_stops.length) $("stops").appendChild(textElement("li","placeholder","Starting fuel covers the trip. Fuel is still consumed; its initial monetary value is unknown unless supplied."));
  result.fuel_stops.forEach((stop, i) => {
    const approximate = stop.location_precision !== "verified_station";
    const item = document.createElement("li"), top = textElement("div","stop-top","");
    top.appendChild(textElement("span","stop-number",i+1));
    const title = document.createElement("div"); title.appendChild(textElement("div","stop-title",stop.station_name)); title.appendChild(textElement("div","stop-locality",`${stop.city}, ${stop.state} · mile ${number(stop.mile_marker,0)}`)); top.appendChild(title); item.appendChild(top);
    const buy = textElement("div","stop-buy",""); buy.appendChild(textElement("span","",`${number(stop.gallons_purchased)} gal × ${money(stop.price_per_gallon_usd)}`)); buy.appendChild(textElement("span","",money(stop.purchase_cost_usd))); item.appendChild(buy);
    item.appendChild(textElement("div",`precision${approximate ? " approximate" : ""}`,approximate ? "● Approximate city point · station access unverified" : "● Reviewed station site · detour unmeasured"));
    item.appendChild(textElement("p","stop-explanation",stop.decision_explanation));
    item.appendChild(textElement("p","stop-locality",`Fuel ${number(stop.fuel_before_purchase_gallons)} → ${number(stop.fuel_after_purchase_gallons)} gal${stop.price_conflict ? ` · Price observations ${money(stop.price_min_usd)}–${money(stop.price_max_usd)}` : ""}`));
    const source = textElement("a","stop-source","Coordinate source ↗");
    try {const url = new URL(stop.location_source); if (url.protocol === "https:") {source.href = url.href; source.target = "_blank"; source.rel = "noopener noreferrer"; item.appendChild(source);}} catch {}
    $("stops").appendChild(item);
    const popup = document.createElement("div"); popup.appendChild(textElement("strong","",stop.station_name)); popup.appendChild(textElement("p","",`${number(stop.gallons_purchased)} gal · ${money(stop.purchase_cost_usd)} · ${approximate ? "approximate city" : "verified site"}`));
    L.marker([stop.coordinates[1],stop.coordinates[0]], {icon:L.divIcon({className:`fuel-marker${approximate ? " approximate" : ""}`,html:String(i+1),iconSize:[28,28],iconAnchor:[14,14]})}).bindPopup(popup).addTo(layers);
  });
  timeline(result.fuel_timeline,route.distance_miles,result.vehicle.tank_capacity_gallons);
  $("warnings").replaceChildren(...result.warnings.map(w => textElement("li","",w)));
  $("request-meta").textContent = `Directions calls: ${meta.directions_api_calls} · Geocoding calls: ${meta.geocoding_api_calls} · Route cache: ${meta.route_cache_hit ? "hit" : "miss"} · Plan cache: ${meta.optimization_cache_hit ? "hit" : "miss"} · API: ${number(meta.request_duration_ms)} ms · Candidates: ${meta.candidate_count} · ${JSON.stringify(meta.location_coverage)}`;
  $("raw").textContent = JSON.stringify(result,null,2);
}
function clearResults(message = "No current plan. Submit the locations above.") {
  latestResult = null; layers.clearLayers();
  ["distance","spend","savings","consumed","stop-count","initial-volume"].forEach(id => $(id).textContent = "—");
  $("initial-worth").textContent="Unknown";$("economic-cost").textContent="Unavailable";
  $("baseline").textContent="Comparison unavailable";$("purchased").textContent="No purchase plan";$("end-fuel").textContent="No feasible plan";
  $("stops").replaceChildren(textElement("li","placeholder",message));$("timeline").replaceChildren();
  $("warnings").replaceChildren(textElement("li","",message));$("request-meta").textContent="";
  $("raw").textContent=message;$("retry-estimated").hidden=true;
}
$("planner").addEventListener("submit",async event => {
  event.preventDefault(); activeRequest?.abort();
  const thisRequest = ++generation;
  activeRequest = new AbortController();
  const submitted = {start:$("start").value,finish:$("finish").value,location_mode:$("mode").value,initial_fuel_gallons:Number($("fuel").value)};
  if ($("initial-value").value !== "") submitted.initial_fuel_cost_usd=$("initial-value").value;
  clearResults("Calculating a new plan…");$("error").hidden=true;
  $("journey").textContent=`${submitted.start} → ${submitted.finish}`;
  $("submit").disabled=true;$("submit").firstChild.textContent="Calculating… ";
  $("status").textContent="Resolving endpoints and calculating the fuel plan…";
  const controller = activeRequest;
  const timeout = setTimeout(() => controller.abort(),80000);
  try {
    const response = await fetch("/api/v1/routes/optimize/", {method:"POST",headers:{"Content-Type":"application/json"},signal:controller.signal,body:JSON.stringify(submitted)});
    const result = await response.json();
    if(thisRequest !== generation)return;
    if(!response.ok){
      clearResults("No feasible plan for these inputs.");$("raw").textContent=JSON.stringify(result,null,2);
      $("request-meta").textContent=JSON.stringify(result.meta || {});
      const route=result.error?.details?.route;
      if(route){drawRoute(route,submitted);$("distance").textContent=number(route.distance_miles,0);}
      $("retry-estimated").hidden=!(result.error?.code === "UNREACHABLE_FUEL_GAP" && submitted.location_mode === "strict");
      $("quality-banner").textContent="Route geometry may be available, but no feasible fueling plan was returned. Broader estimated coverage is conditional and may also fail.";
      throw new Error(`${result.error?.code || response.status}: ${result.error?.message || "Request failed"}`);
    }
    render(result,submitted);
  }catch(error){
    if(thisRequest !== generation)return;
    if(error.name === "AbortError")clearResults("Request cancelled or timed out. Submit again when ready.");
    else if(!$("raw").textContent.startsWith("{"))clearResults("The network or response failed. Previous results have been cleared.");
    $("error").textContent=error.name === "AbortError" ? "Request cancelled or timed out." : error.message;
    $("error").hidden=false;$("status").textContent="This request needs attention. No earlier plan is being shown.";
  }finally{
    clearTimeout(timeout);
    if(thisRequest === generation){activeRequest=null;$("submit").disabled=false;$("submit").firstChild.textContent="Find my fuel plan ";}
  }
});
$("mode").addEventListener("change",() => {
  $("mode-help").textContent=$("mode").value === "estimated" ? "Estimated mode allows city approximations. Station proximity, highway access, detours and savings are conditional." : "Strict uses reviewed station sites only. Sparse coverage may prevent a plan; estimated mode is available with explicit uncertainty.";
});
$("retry-estimated").addEventListener("click",() => {$("mode").value="estimated";$("mode").dispatchEvent(new Event("change"));$("planner").requestSubmit();});
document.querySelectorAll(".example").forEach(button => button.addEventListener("click",() => {$("start").value=button.dataset.start;$("finish").value=button.dataset.city;$("planner").requestSubmit();}));
fetch("/api/v1/health/").then(r=>r.json()).then(data=>{const prices = priceLabel(data.price_basis); $("provider-badge").textContent=data.routing_provider === "recorded" ? `${data.recorded_route_count} recorded roads · ${prices}` : `${data.live_routing_configured ? "HeiGIT configured" : "HeiGIT key needed"} · ${prices}`;}).catch(()=>$("provider-badge").textContent="API unavailable");
window.fuelRouteState=()=>latestResult;
