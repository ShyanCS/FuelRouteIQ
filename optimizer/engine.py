from decimal import Decimal

from optimizer.schemas import ZERO, Candidate, FuelGap, Plan, Purchase, Vehicle


def prepare(distance: Decimal, stations: list[Candidate], vehicle: Vehicle) -> list[Candidate]:
    vehicle.validate()
    if not distance.is_finite() or distance < ZERO:
        raise ValueError("Distance must be finite and nonnegative")
    for s in stations:
        if (
            not s.mile.is_finite()
            or not ZERO <= s.mile <= distance
            or not s.price.is_finite()
            or s.price <= ZERO
        ):
            raise ValueError("Invalid station position or price")
    # Co-located opportunities are interchangeable in the mathematical model.
    unique: dict[Decimal, Candidate] = {}
    for s in sorted(stations, key=lambda s: (s.mile, s.price, s.station_id)):
        if s.mile < distance:
            unique.setdefault(s.mile, s)
    return list(unique.values())


def optimize(distance: Decimal, stations: list[Candidate], vehicle: Vehicle | None = None) -> Plan:
    """Fixed ordered route, divisible fuel, positive prices, zero modeled detour.

    Exchange argument: purchases before a reachable cheaper opportunity can be
    postponed to it; with no cheaper opportunity, buying earlier (up to capacity)
    cannot increase cost. A monotonic stack finds the next strictly cheaper node
    in O(n); destination is a virtual zero-price node. Sorting costs O(n log n).
    """
    vehicle = vehicle or Vehicle()
    nodes = prepare(distance, stations, vehicle)
    next_cheaper: list[int | None] = [None] * len(nodes)
    stack: list[int] = []
    for i in range(len(nodes) - 1, -1, -1):
        while stack and nodes[stack[-1]].price >= nodes[i].price:
            stack.pop()
        next_cheaper[i] = stack[-1] if stack else None
        stack.append(i)
    fuel, position = vehicle.initial, ZERO
    purchases: list[Purchase] = []
    for i, station in enumerate(nodes):
        travel = (station.mile - position) / vehicle.mpg
        if travel > fuel:
            raise FuelGap(position, station.mile, fuel * vehicle.mpg)
        fuel -= travel
        position = station.mile
        cheaper = next_cheaper[i]
        target = distance
        reason = "reach the destination without buying excess fuel"
        if cheaper is not None and nodes[cheaper].mile - position <= vehicle.range_miles:
            target = nodes[cheaper].mile
            reason = f"reach cheaper station {nodes[cheaper].name} at ${nodes[cheaper].price}/gal"
        if target - position > vehicle.range_miles:
            desired = vehicle.capacity
            reason = "fill the tank because no strictly cheaper station or destination is reachable on a full tank"
        else:
            desired = (target - position) / vehicle.mpg
        amount = max(ZERO, desired - fuel)
        if amount > ZERO:
            purchases.append(
                Purchase(
                    station,
                    amount,
                    fuel,
                    fuel + amount,
                    f"Buy {amount:.3f} gallons (display rounded) at ${station.price}/gal to {reason}.",
                )
            )
            fuel += amount
    remaining = (distance - position) / vehicle.mpg
    if remaining > fuel:
        raise FuelGap(position, distance, fuel * vehicle.mpg)
    return Plan(tuple(purchases), distance / vehicle.mpg, fuel - remaining)
