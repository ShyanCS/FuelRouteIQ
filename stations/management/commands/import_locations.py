from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from stations.enrichment import import_verified
from stations.importer import import_cities


class Command(BaseCommand):
    help = "Import checksummed Census places or human-reviewed station evidence"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cities", nargs="?", const=str(settings.BASE_DIR / "data/reference/census_places.txt")
        )
        parser.add_argument("--verified", type=Path)
        parser.add_argument(
            "--skip-missing",
            action="store_true",
            help="Explicitly ignore evidence IDs absent from a deliberately compact price fixture",
        )

    def handle(self, *args, **options):
        if bool(options["cities"]) == bool(options["verified"]):
            raise CommandError("Specify exactly one of --cities or --verified")
        try:
            count = (
                import_cities(options["cities"])
                if options["cities"]
                else import_verified(options["verified"], skip_missing=options["skip_missing"])
            )
        except (ValueError, OSError, KeyError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(f"Imported {count} locations")
