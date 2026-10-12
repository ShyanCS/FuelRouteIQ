"""Bounded, resumable lookups of selected operator coordinate facts, never prices.

This consumes an explicit station/city-page list, not a web crawl. Exported facts
require reviewer approval of identity/locality/road matches before enrichment.
Only compact factual metadata is stored; HTML and site prose are not bundled.
"""

import argparse
import hashlib
import json
import re
import time
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

ROOT = Path(__file__).resolve().parent.parent


class FactsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.links, self.heading = [], [], []
        self.hidden = self.in_heading = 0
        self.current_link = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style", "noscript"):
            self.hidden += 1
        if tag == "h1":
            self.in_heading += 1
        if tag == "a":
            self.current_link = [attrs.get("href", ""), []]

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.hidden = max(0, self.hidden - 1)
        if tag == "h1":
            self.in_heading = max(0, self.in_heading - 1)
        if tag == "a" and self.current_link is not None:
            self.links.append((self.current_link[0], " ".join(self.current_link[1])))
            self.current_link = None

    def handle_data(self, data):
        if self.hidden:
            return
        text = " ".join(data.split())
        if text:
            self.parts.append(text)
            if self.in_heading:
                self.heading.append(text)
            if self.current_link is not None:
                self.current_link[1].append(text)


def fetch(client, url):
    response = client.get(url)
    response.raise_for_status()
    parser = FactsParser()
    parser.feed(response.text)
    return response, parser


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("selection", type=Path)
    args = parser.parse_args()
    folder = ROOT / "data/reference/operator_facts"
    folder.mkdir(parents=True, exist_ok=True)
    selections = json.loads(args.selection.read_text(encoding="utf-8"))
    with httpx.Client(
        timeout=httpx.Timeout(20, connect=5),
        follow_redirects=True,
        headers={
            "User-Agent": "FuelRouteIQ assessment coordinate review (bounded public factual lookups)"
        },
    ) as client:
        city_cache = {}
        for selected in selections:
            path = folder / (selected["opis_id"] + ".json")
            if path.exists():
                print("Preserved facts", selected["opis_id"])
                continue
            city_url = selected["city_url"]
            if urlparse(city_url).hostname != "locations.pilotflyingj.com":
                raise ValueError("Only explicitly selected official operator pages supported")
            if city_url not in city_cache:
                try:
                    city_cache[city_url] = fetch(client, city_url)
                except httpx.HTTPError:
                    print(
                        "UNRESOLVED official city page unavailable", selected["opis_id"], city_url
                    )
                    continue
            _, city_parser = city_cache[city_url]
            number = selected["store_number"]
            pattern = re.compile(r"#\s*" + re.escape(str(number)) + r"\b")
            matches = [
                urljoin(city_url, href)
                for href, label in city_parser.links
                if pattern.search(label)
                and href.count("/") >= 4
                and urlparse(urljoin(city_url, href)).hostname == "locations.pilotflyingj.com"
            ]
            if not matches:
                print("UNRESOLVED no matching official detail link", selected["opis_id"], number)
                continue
            try:
                response, detail = fetch(client, matches[0])
            except httpx.HTTPError:
                print("UNRESOLVED official detail page unavailable", selected["opis_id"])
                continue
            text = " ".join(detail.parts)
            coordinates = re.search(
                r"Interstate\s*:(.{0,240}?)Coordinates\s*:\s*([-0-9.]+)\s*,\s*([-0-9.]+)", text
            )
            title = " ".join(detail.heading)
            if not coordinates or not pattern.search(title):
                print("UNRESOLVED missing coordinate or identity facts", selected["opis_id"])
                continue
            facts = {
                "opis_id": selected["opis_id"],
                "station_name": title,
                "city": selected["city"],
                "state": selected["state"],
                "latitude": float(coordinates[2]),
                "longitude": float(coordinates[3]),
                "road_context": coordinates[1].strip(),
                "source": str(response.url),
                "source_city": urlparse(str(response.url)).path.split("/")[3].replace("-", " "),
                "verified_at": datetime.now(UTC).isoformat(),
                "source_response_sha256": hashlib.sha256(response.content).hexdigest(),
                "retrieval_method": "bounded selected operator page; coordinate/name/road facts only, no prices",
                "review_notes": "Pending reviewer validation of source identity, city/state and road context.",
            }
            path.write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(facts))
            time.sleep(0.3)


if __name__ == "__main__":
    main()
