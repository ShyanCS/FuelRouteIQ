from decimal import Decimal

from rest_framework import serializers


class OptimizeRequestSerializer(serializers.Serializer):
    start = serializers.CharField(max_length=250, allow_blank=False)
    finish = serializers.CharField(max_length=250, allow_blank=False)
    location_mode = serializers.ChoiceField(choices=["strict", "estimated"], default="strict")
    mpg = serializers.DecimalField(
        max_digits=8,
        decimal_places=3,
        min_value=Decimal("1"),
        max_value=Decimal("100"),
        default=Decimal("10"),
    )
    range_miles = serializers.DecimalField(
        max_digits=8,
        decimal_places=3,
        min_value=Decimal("1"),
        max_value=Decimal("500"),
        default=Decimal("500"),
    )
    initial_fuel_gallons = serializers.DecimalField(
        max_digits=12, decimal_places=6, min_value=Decimal(0), required=False
    )
    initial_fuel_cost_usd = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal(0), required=False, allow_null=True
    )

    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError({k: "Unknown field" for k in sorted(unknown)})
        return super().to_internal_value(data)

    def validate(self, attrs):
        capacity = attrs["range_miles"] / attrs["mpg"]
        attrs.setdefault("initial_fuel_gallons", capacity)
        if attrs["initial_fuel_gallons"] > capacity:
            raise serializers.ValidationError(
                {"initial_fuel_gallons": "Initial fuel cannot exceed derived tank capacity."}
            )
        if attrs["initial_fuel_gallons"] == 0 and attrs.get("initial_fuel_cost_usd"):
            raise serializers.ValidationError(
                {"initial_fuel_cost_usd": "Cannot value a nonexistent starting fuel supply."}
            )
        return attrs
