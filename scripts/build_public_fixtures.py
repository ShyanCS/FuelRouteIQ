"""Create labelled, source-independent PRICE TEST FIXTURES, not market data.

Locations/identities come from reviewed factual operator records. Deliberately
illustrative prices are hand-authored test values. Assessment prices are never
read by this script or copied into its output. Import manifests propagate the
illustrative designation to the API and UI.
"""

import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADERS = [
    "OPIS Truckstop ID",
    "Truckstop Name",
    "Address",
    "City",
    "State",
    "Rack ID",
    "Retail Price",
]


def write_fixture(filename, entries, extras=False):
    path = ROOT / "fixtures" / filename
    rows = []
    for i, entry in enumerate(entries):
        rows.append(
            {
                "OPIS Truckstop ID": entry["opis_id"],
                "Truckstop Name": entry["station_name"],
                "Address": entry["road_context"],
                "City": entry["city"],
                "State": entry["state"],
                "Rack ID": "ILLUSTRATIVE",
                "Retail Price": str(Decimal("3.00") + Decimal(i % 5) / Decimal(10)),
            }
        )
    if extras:
        rows.extend(
            [{**rows[0], "Retail Price": p} for p in ["3.10", "3.50", "3.30", "3.30", "3.50"]]
        )
        rows.append({**rows[5], "Retail Price": "4.50"})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "price_basis": "illustrative_test_fixture",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "license": "Original hand-authored test price values; CC0. Coordinate/identity facts have individually cited operator sources.",
        "purpose": "Reproducible inventory/cost algorithm demonstration only. These numbers are neither supplied assessment observations nor real or current pump prices.",
        "rows": len(rows),
        "identities": len(entries),
        "generation": "Fixed illustrative values 3.00 + (index mod 5)/10; unit fixture includes explicit conflict observations.",
    }
    path.with_suffix(".source.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(filename, manifest["rows"], manifest["identities"], manifest["price_basis"])


def main():
    entries = json.loads(
        (ROOT / "data/reference/verified_stations.json").read_text(encoding="utf-8")
    )
    write_fixture("public_unit_prices.csv", entries[:6], extras=True)
    write_fixture("public_demo_prices.csv", entries)


if __name__ == "__main__":
    main()
