import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from stations.importer import import_fuel


class Command(BaseCommand):
    help = "Audit and import source CSV, retaining all raw rows. Does not geocode online."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reuse",
            action="store_true",
            help="Reuse an identical active dataset without changing its revision or enrichment",
        )
        parser.add_argument(
            "path",
            nargs="?",
            default=str(settings.BASE_DIR / "data/raw/fuel-prices-for-be-assessment.csv"),
        )

    def handle(self, *args, **options):
        try:
            dataset = import_fuel(options["path"], reuse=options["reuse"])
        except (ValueError, OSError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(dataset.report, indent=2))
