"""Build an allowlisted portable review ZIP; never include private source prices.

Only selected source directories/files and explicit sanitized evidence are
eligible. Scan every text file for credential-looking assignments and reject
private datasets, environment files, databases, caches, Git and unsafe paths.
"""

import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROOT_FILES = {
    "manage.py",
    "README.md",
    "IMPLEMENTATION_BRIEF.md",
    "FuelRoute_IQ_Codex_Implementation_Brief.md",
    "IMPLEMENTATION_REPORT.md",
    "ASSESSMENT_READINESS_AUDIT.md",
    "FINAL_TECHNICAL_AUDIT.md",
    "ROUTING_AND_COVERAGE_REPORT.md",
    "requirements.txt",
    "requirements.lock",
    "pyproject.toml",
    ".gitignore",
    ".gitattributes",
    ".env.example",
    "DATA_SOURCES_AND_LICENSES.md",
    "render.yaml",
    "FINAL_SUBMISSION_AUDIT.md",
    "PRODUCTION_DEPLOYMENT_REPORT.md",
    "FINAL_IMPLEMENTATION_REPORT.md",
    "FINAL_LOOM_SCRIPT.md",
    "SUBMISSION_LINKS.md",
}
DIRECTORIES = {
    "api",
    "fuelroute",
    "routing",
    "optimizer",
    "stations",
    "tests",
    "scripts",
    "demo",
    "docs",
    "postman",
    ".github",
}
ALLOWED_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".csv",
    ".geojson",
    ".js",
    ".css",
    ".html",
    ".png",
    ".yml",
    ".yaml",
    ".toml",
    ".ps1",
    ".sh",
}
ARTIFACTS = {
    "artifacts/phase2-pytest-results.txt",
    "artifacts/phase2-regression-tests.txt",
    "artifacts/phase2-checks.json",
    "artifacts/provider-gateway-probes.json",
    "artifacts/public/postman-summary.json",
    "artifacts/public/recorded-illustrative-matrix.json",
    "artifacts/public/package-smoke.json",
    "artifacts/public/package-postman-summary.json",
    "artifacts/public/package-postman-results.txt",
    "artifacts/public/package-tests.txt",
    "artifacts/public/browser-checks.json",
    "artifacts/public/public-review-demo.png",
    "artifacts/public/final-tests.txt",
    "artifacts/public/final-coverage.json",
    "artifacts/public/production-checks.json",
    "artifacts/public/production-http.json",
    "artifacts/public/production-postman-summary.json",
    "artifacts/public/production-browser.json",
    "artifacts/public/production-demo.png",
    "artifacts/public/production-dependency-audit.json",
    "artifacts/public/final-review-local.png",
    "artifacts/public/production-source-review.json",
    "artifacts/public/production-corridor-comparison.json",
    "artifacts/public/production-provider-errors.json",
    "artifacts/public/production-live-response.json",
    "artifacts/public/production-redeploy.json",
    "artifacts/public/production-throttle.json",
    "artifacts/public/production-first-probe.json",
    "artifacts/public/production-final-verification.json",
    "artifacts/public/production-concurrency.json",
}


def eligible(path):
    if not path.resolve().is_relative_to(ROOT):
        return False
    relative = path.relative_to(ROOT)
    parts, name = relative.parts, relative.name
    if any(
        part
        in {
            "__pycache__",
            ".git",
            ".pytest_cache",
            ".pytest-tmp",
            ".ruff_cache",
            ".mypy_cache",
            "private",
        }
        or part.startswith(".venv")
        for part in parts
    ):
        return False
    if name.startswith(".env") and name != ".env.example":
        return False
    if name.endswith((".sqlite3", ".pyc", ".zip")) or name in {
        "demo_fuel.csv",
        "fuel-prices-for-be-assessment.csv",
    }:
        return False
    if len(parts) == 1:
        return name in ROOT_FILES
    if relative.as_posix() in ARTIFACTS:
        return True
    if parts[0] == "data":
        return parts[1] == "reference" and path.suffix in {".json", ".txt"}
    if parts[0] == "fixtures":
        return parts[1] == "routes" or name.startswith("public_")
    return parts[0] in DIRECTORIES and (path.suffix in ALLOWED_SUFFIXES or name == "LICENSE")


def main():
    archive_path = ROOT / "FINAL_REVIEW_PACKAGE.zip"
    # Start inside allowed trees; never traverse virtual environments/databases.
    candidates = {ROOT / name for name in ROOT_FILES}
    candidates.update(ROOT / name for name in ARTIFACTS)
    for directory in DIRECTORIES | {"data/reference", "fixtures/routes"}:
        folder = ROOT / directory
        if folder.exists():
            candidates.update(p for p in folder.rglob("*") if p.is_file())
    candidates.update((ROOT / "fixtures").glob("public_*"))
    items = sorted(p for p in candidates if p.is_file() and eligible(p))
    manifest = []
    private_hashes = {
        hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [ROOT / "fuel-prices-for-be-assessment.csv", ROOT / "fixtures/demo_fuel.csv"]
        if p.exists()
    }
    for path in items:
        relative = path.relative_to(ROOT).as_posix()
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest in private_hashes:
            raise ValueError("Private dataset content found in allowed paths")
        if path.suffix != ".png":
            text = content.decode("utf-8-sig")
            if re.search(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", text):
                raise ValueError(f"Token-shaped secret in {relative}")
            for match in re.finditer(
                r"^[ \t]*(?:ORS_API_KEY|API_KEY|ACCESS_TOKEN|PASSWORD)[ \t]*=[ \t]*([^\r\n]*)",
                text,
                re.M,
            ):
                value = match[1].strip().strip("\"'")
                if value.startswith(("os.getenv(", "os.environ[")):
                    continue
                if value and not any(
                    placeholder in value.lower()
                    for placeholder in ("your_", "test", "example", "invalid")
                ):
                    raise ValueError(f"Potential credential assignment in {relative}")
        manifest.append({"path": relative, "bytes": len(content), "sha256": digest})
    metadata = {
        "files": manifest,
        "file_count": len(manifest),
        "price_data": "Only explicitly illustrative hand-authored fixtures; private full CSV and original excerpt excluded",
        "excluded": [
            ".env",
            "API credentials",
            "virtual environments",
            "Git",
            "databases",
            "caches",
            "private source prices",
        ],
        "runtime_paths": "Source resolves paths relative to project files, not the original Windows workspace",
    }
    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in items:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr("REVIEW_MANIFEST.json", json.dumps(metadata, indent=2) + "\n")
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP integrity check failed")
        for entry in archive.infolist():
            if entry.filename.startswith("/") or ".." in Path(entry.filename).parts:
                raise ValueError("Unsafe archive member path")
    report = {
        "path": "FINAL_REVIEW_PACKAGE.zip",
        "bytes": archive_path.stat().st_size,
        "sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "file_count": len(items),
        "zip_integrity": "passed",
        "credential_and_private_data_scan": "passed",
    }
    (ROOT / "artifacts/review-package-manifest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
