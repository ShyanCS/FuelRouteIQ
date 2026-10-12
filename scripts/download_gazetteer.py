"""One explicit Census download; preserve source checksum and original archive."""

import hashlib
import io
import json
import zipfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2026_Gazetteer/2026_Gaz_place_national.zip"


def main():
    folder = ROOT / "data" / "reference"
    folder.mkdir(parents=True, exist_ok=True)
    response = httpx.get(URL, timeout=60, follow_redirects=True)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = [n for n in archive.namelist() if n.endswith(".txt")]
        if len(names) != 1:
            raise ValueError("Unexpected Census archive contents")
        content = archive.read(names[0])
    (folder / "census_places.txt").write_bytes(content)
    metadata = {
        "url": URL,
        "archive_sha256": hashlib.sha256(response.content).hexdigest(),
        "text_sha256": hashlib.sha256(content).hexdigest(),
        "archive_member": names[0],
        "license": "US Census federal government data; public domain",
        "precision": "Census internal point, approximate city only; never a station coordinate",
    }
    (folder / "census_source.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
