from dataclasses import dataclass
from decimal import Decimal

D = Decimal
ZERO = D(0)


@dataclass(frozen=True)
class Candidate:
    station_id: str
    name: str
    mile: Decimal
    price: Decimal


@dataclass(frozen=True)
class Vehicle:
    mpg: Decimal = D(10)
    range_miles: Decimal = D(500)
    initial: Decimal = D(50)

    @property
    def capacity(self) -> Decimal:
        return self.range_miles / self.mpg

    def validate(self) -> None:
        if not all(v.is_finite() for v in (self.mpg, self.range_miles, self.initial)):
            raise ValueError("Vehicle values must be finite")
        if (
            self.mpg <= ZERO
            or self.range_miles <= ZERO
            or not ZERO <= self.initial <= self.capacity
        ):
            raise ValueError("Invalid vehicle capacity or initial fuel")


@dataclass(frozen=True)
class Purchase:
    station: Candidate
    gallons: Decimal
    before: Decimal
    after: Decimal
    explanation: str

    @property
    def cost(self) -> Decimal:
        return self.gallons * self.station.price


@dataclass(frozen=True)
class Plan:
    purchases: tuple[Purchase, ...]
    consumed: Decimal
    end_fuel: Decimal

    @property
    def spend(self) -> Decimal:
        return sum((p.cost for p in self.purchases), ZERO)

    @property
    def bought(self) -> Decimal:
        return sum((p.gallons for p in self.purchases), ZERO)


class FuelGap(Exception):
    def __init__(self, start: Decimal, end: Decimal, available_range: Decimal):
        self.start, self.end, self.available_range = start, end, available_range
        super().__init__(
            f"Cannot travel from mile {start} to {end} with {available_range} miles available"
        )
