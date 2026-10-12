import random
from decimal import Decimal as D

import pytest

from optimizer.baseline import simulate_baseline
from optimizer.engine import optimize
from optimizer.schemas import Candidate, FuelGap, Vehicle


def nodes(*values):
    return [
        Candidate(str(i), f"station {i}", D(str(m)), D(str(p))) for i, (m, p) in enumerate(values)
    ]


def oracle(distance, stations, capacity, initial):
    """Independent integer-gallon DP enumerates every allowed purchase at every node.

    Distances are gallons at MPG=1; integer prices imply an integral optimum for
    these inventory-flow instances. No use of greedy engine or its helpers.
    """
    costs = {initial: D(0)}
    last = 0
    for position, price in sorted(stations) + [(distance, None)]:
        delta = position - last
        arrivals = {f - delta: cost for f, cost in costs.items() if f >= delta}
        if not arrivals:
            return None
        if price is None:
            return min(arrivals.values())
        costs = {}
        for fuel, cost in arrivals.items():
            for purchase in range(capacity - fuel + 1):
                after = fuel + purchase
                candidate = cost + purchase * D(price)
                costs[after] = min(costs.get(after, D("Infinity")), candidate)
        last = position
    raise AssertionError("destination missing")


@pytest.mark.parametrize("seed", range(200))
def test_greedy_matches_independent_dp(seed):
    rng = random.Random(seed)
    capacity = rng.randint(2, 12)
    distance = rng.randint(0, 45)
    initial = rng.randint(0, capacity)
    stations = sorted(
        (p, rng.randint(1, 9))
        for p in rng.sample(range(distance + 1), min(rng.randint(0, 8), distance + 1))
    )
    expected = oracle(distance, stations, capacity, initial)
    vehicle = Vehicle(D(1), D(capacity), D(initial))
    if expected is None:
        with pytest.raises(FuelGap):
            optimize(D(distance), nodes(*stations), vehicle)
    else:
        plan = optimize(D(distance), nodes(*stations), vehicle)
        assert plan.spend == expected
        assert plan.bought + D(initial) - plan.consumed == plan.end_fuel
        assert 0 <= plan.end_fuel <= capacity
        assert all(0 <= p.before <= p.after <= capacity and p.gallons > 0 for p in plan.purchases)
        baseline = simulate_baseline(D(distance), nodes(*stations), vehicle)
        assert baseline.spend >= plan.spend
        assert baseline.bought + D(initial) - baseline.consumed == baseline.end_fuel


@pytest.mark.parametrize("miles,remaining", [(0, 50), (100, 40), (500, 0)])
def test_no_purchase_short_and_exact_range(miles, remaining):
    plan = optimize(D(miles), [])
    assert plan.spend == 0 and plan.consumed == D(miles) / 10
    assert plan.end_fuel == remaining


def test_two_stops_accounting_and_decimal_prices():
    plan = optimize(D(1200), nodes((400, "3.12345678"), (850, "3.5")))
    assert [p.gallons for p in plan.purchases] == [D(40), D(30)]
    assert plan.bought == 70 and plan.end_fuel == 0 and plan.consumed == 120
    assert plan.spend == D("229.93827120")


def test_reachable_cheaper_station_only_buys_needed():
    plan = optimize(D(700), nodes((0, 5), (200, 4), (400, 2)), Vehicle(initial=D(0)))
    assert [p.gallons for p in plan.purchases] == [20, 20, 30]


def test_inaccessible_cheaper_does_not_underfill():
    plan = optimize(D(1000), nodes((0, 4), (400, 5), (600, 1)), Vehicle(initial=D(0)))
    assert plan.purchases[0].gallons == 50


def test_equal_prices_and_colocated_candidates():
    plan = optimize(D(1000), nodes((0, 4), (0, 2), (500, 2), (1000, 1)), Vehicle(initial=D(0)))
    assert [p.station.price for p in plan.purchases] == [2, 2]
    assert plan.spend == 200


@pytest.mark.parametrize("stations,initial", [([], 50), ([(501, 1)], 50), ([(100, 1)], 0)])
def test_unreachable(stations, initial):
    with pytest.raises(FuelGap):
        optimize(D(1000), nodes(*stations), Vehicle(initial=D(initial)))


def test_initial_owned_fuel_is_used_first():
    plan = optimize(D(700), nodes((0, 1), (300, 2)), Vehicle(initial=D(50)))
    assert plan.purchases[0].station.mile == 300
    assert plan.bought == 20


def test_baseline_detects_infeasible_gap():
    vehicle = Vehicle(D(1), D(10), D(10))
    stations = nodes((7, 5), (20, 2))
    with pytest.raises(FuelGap):
        simulate_baseline(D(25), stations, vehicle)


@pytest.mark.parametrize(
    "vehicle", [Vehicle(mpg=D(0)), Vehicle(initial=D(51)), Vehicle(initial=D("NaN"))]
)
def test_invalid_vehicle(vehicle):
    with pytest.raises(ValueError):
        optimize(D(5), [], vehicle)
