import uuid

from django.db import models


class Dataset(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    source_name = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64)
    revision = models.UUIDField(default=uuid.uuid4)
    report = models.JSONField(default=dict)
    price_basis = models.CharField(
        max_length=32,
        default="assessment_snapshot",
        choices=[
            ("assessment_snapshot", "Assessment snapshots"),
            ("illustrative_test_fixture", "Illustrative test prices"),
        ],
    )


class SourceRow(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    row_number = models.PositiveIntegerField()
    raw = models.JSONField()
    rejection_reason = models.CharField(max_length=255, blank=True)


class City(models.Model):
    geoid = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=160)
    key = models.CharField(max_length=160)
    state = models.CharField(max_length=2)
    latitude = models.FloatField()
    longitude = models.FloatField()
    source = models.URLField(max_length=500)

    class Meta:
        indexes = [models.Index(fields=["key", "state"])]


class Station(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    opis_id = models.CharField(max_length=40)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=160)
    state = models.CharField(max_length=2)
    price = models.DecimalField(max_digits=18, decimal_places=10)
    price_min = models.DecimalField(max_digits=18, decimal_places=10)
    price_max = models.DecimalField(max_digits=18, decimal_places=10)
    price_conflict = models.BooleanField(default=False)
    identity_conflict = models.BooleanField(default=False)
    source_row_count = models.PositiveIntegerField()
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    location_precision = models.CharField(max_length=24, default="unresolved")
    source = models.URLField(max_length=500, blank=True)
    match_confidence = models.CharField(max_length=80, default="unresolved")
    verified_at = models.DateTimeField(null=True)
    verification = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["dataset", "opis_id"], name="station_dataset_identity")
        ]
        indexes = [
            models.Index(fields=["dataset", "location_precision"]),
            models.Index(fields=["dataset", "latitude", "longitude"]),
        ]
