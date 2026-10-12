"""Economic consumption valuation is distinct from optimizing cash purchases."""

from decimal import Decimal, localcontext


def fifo_valuation(plan, initial_gallons, initial_value):
    if initial_value is None and initial_gallons > 0:
        return {
            "economic_fuel_cost_usd": None,
            "remaining_fuel_value_usd": None,
            "economic_cost_status": "unknown_initial_fuel_value",
            "valuation_method": "FIFO; unavailable when consumed initially owned fuel is unvalued",
        }
    with localcontext() as context:
        context.prec = 50
        initial_price = initial_value / initial_gallons if initial_gallons else Decimal(0)
        buckets = [(initial_gallons, initial_price)] + [
            (p.gallons, p.station.price) for p in plan.purchases
        ]
        to_consume, consumed_value, remaining_value = plan.consumed, Decimal(0), Decimal(0)
        for gallons, price in buckets:
            used = min(gallons, max(Decimal(0), to_consume))
            consumed_value += used * price
            remaining_value += (gallons - used) * price
            to_consume -= used
        return {
            "economic_fuel_cost_usd": consumed_value,
            "remaining_fuel_value_usd": remaining_value,
            "economic_cost_status": "known_fifo_inventory_valuation",
            "valuation_method": "FIFO using supplied initial inventory value and selected observed purchase prices",
        }
