"""Idempotent, public-only deployment seed; no network or private paths."""

import hashlib
import json

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from stations.enrichment import import_verified
from stations.importer import active_dataset, import_fuel
from stations.models import City


class Command(BaseCommand):
    help = "Seed checksummed public illustrative prices and reviewed locations; preserve private assessment datasets"

    @transaction.atomic
    def handle(self, *args, **options):
        root = settings.BASE_DIR
        dataset = active_dataset()
        if dataset and dataset.price_basis != "illustrative_test_fixture":
            raise CommandError(
                "Refusing to replace a private assessment dataset with public demo data"
            )
        if not City.objects.exists():
            call_command("import_locations", cities=str(root / "data/reference/census_places.txt"))
        dataset = import_fuel(root / "fixtures/public_demo_prices.csv", reuse=True)
        path = root / "data/reference/verified_stations.json"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if dataset.report.get("verified_evidence_sha256") != digest:
            import_verified(path)
            dataset.refresh_from_db()
            dataset.report["verified_evidence_sha256"] = digest
            dataset.save(update_fields=["report"])
        self.stdout.write(
            json.dumps(
                {
                    "dataset_revision": str(dataset.revision),
                    "price_basis": dataset.price_basis,
                    "location_coverage": dataset.report["location_coverage"],
                }
            )
        )
