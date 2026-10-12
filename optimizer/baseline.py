from decimal import Decimal

from optimizer.engine import prepare
from optimizer.schemas import ZERO, Candidate, FuelGap, Plan, Purchase, Vehicle


def simulate_baseline(distance: Decimal, stations: list[Candidate], vehicle: Vehicle) -> Plan:
    """Stop nearest 80% of range among currently reachable forward stations.

    Ignore prices; fill up, capped by fuel needed to finish. With unique ordered
    opportunities this preserves feasibility; genuine coverage gaps still fail.
    """
    nodes = prepare(distance, stations, vehicle)
    position, fuel = ZERO, vehicle.initial
    purchases: list[Purchase] = []
    used: set[str] = set()
    while (distance - position) / vehicle.mpg > fuel:
        reachable = [
            s
            for s in nodes
            if s.station_id not in used and position <= s.mile <= position + fuel * vehicle.mpg
        ]
        if not reachable:
            next_mile = min((s.mile for s in nodes if s.mile > position), default=distance)
            raise FuelGap(position, next_mile, fuel * vehicle.mpg)
        target = position + vehicle.range_miles * Decimal("0.8")
        station = min(reachable, key=lambda s: (abs(s.mile - target), -s.mile, s.station_id))
        fuel -= (station.mile - position) / vehicle.mpg
        position = station.mile
        amount = max(ZERO, min(vehicle.capacity, (distance - position) / vehicle.mpg) - fuel)
        if amount:
            purchases.append(
                Purchase(
                    station,
                    amount,
                    fuel,
                    fuel + amount,
                    "Baseline: stop nearest 80% of driving range; fill up, capped by fuel needed to finish.",
                )
            )
            fuel += amount
        used.add(station.station_id)
    return Plan(
        tuple(purchases), distance / vehicle.mpg, fuel - (distance - position) / vehicle.mpg
    )
