# Data sources and redistribution boundaries

Endpoint correction: the San Francisco populated-place reference is from [GeoNames record 5391959](https://www.geonames.org/5391959/san-francisco.html), WGS84 37.77493, -122.41942, under [CC BY 4.0](https://www.geonames.org/about.html). Attribution: GeoNames / Unxos GmbH. A single factual coordinate record and its source/review note are bundled in `endpoint_overrides.json`. It replaces the offshore Census point only for endpoint routing/locality validation; Census station approximations remain unchanged. It is still an approximate city location, never a surveyed address or pump. No station or fuel price was added by this correction.

| Asset | Origin | Review package treatment |
|---|---|---|
| Full assessment CSV and original 12-row excerpt | Supplied private assessment material; sharing rights unspecified | Excluded from Git and `REVIEW_PACKAGE.zip`. Preserved locally. Import the evaluator's supplied file for assessment-price results. |
| `fixtures/public_*_prices.csv` | Original hand-authored numeric test values | CC0 illustrative fixtures. They are never described as assessment observations or current fuel prices; manifests propagate `illustrative_test_fixture` into API warnings and UI. |
| Station identities and selected coordinate facts | Individually cited public official operator pages | Small factual records only, with URLs, retrieval hashes and review notes. No operator HTML, marketing prose, logos, live fuel prices, or bulk proprietary location database is included. No license grant to operator content is asserted. |
| Census places | US Census 2026 Places Gazetteer | Public federal data; full original text with source/checksum manifest. Internal city points are approximate, never exact pump positions. |
| Natural Earth state outlines | Natural Earth public-domain data | Bundled with source/checksum manifest, used only as coarse basemap context. [Terms](https://www.naturalearthdata.com/about/terms-of-use/). |
| Recorded road geometry | Five actual OSRM responses generated from OpenStreetMap data | GeoJSON, source URLs, meter/time summaries, capture timestamps and hashes are included. OSM-derived data attributed under [ODbL](https://www.openstreetmap.org/copyright); database derivatives are offered under that license. No fabricated straight-line substitutes. |
| Leaflet 1.9.4 | Upstream release | Vendored BSD-2-Clause license retained with JS/CSS/image assets. |

The illustrative prices exist solely to keep unit tests and an independent demonstration runnable without redistributing private price material. Dollar results generated from them are illustrations of the implemented model. The assessment matrix in the reports uses the actual supplied assessment CSV and is labelled separately. Do not mix these datasets or treat illustrative savings as real savings.

Reviewed station facts currently cover 31 sites. Twenty-five additions came from an explicitly selected, bounded review of 27 corridor candidates; 26 public fact records were retrieved. One current brand mismatch was rejected and one unavailable page remained unresolved. The public operator robot policy advertised a sitemap and contained no blanket disallow when checked. This is not authorization for an unrestricted location crawl. The reproducible lookup utility takes a finite selection list and never harvests live prices.

One accepted site, Flying J #1096 Cocoa, has a source exit-number discrepancy (assessment description 201, current operator 202). The operator brand, numbered site, locality/state and highway agree; the API preserves the original address and explicitly reports the conflict. Site verification is not an entrance survey, routed detour proof, opening-hour check, or evidence of current price availability.
