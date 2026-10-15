"""Economic order quantity: the ordering-cost vs holding-cost trade-off."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def economic_order_quantity(demand_rate: float, order_cost: float, holding_cost: float) -> float:
    """EOQ = sqrt(2 * D * K / h)."""
    if demand_rate <= 0 or order_cost <= 0 or holding_cost <= 0:
        raise ValueError("demand_rate, order_cost and holding_cost must be positive")
    return float(np.sqrt(2.0 * demand_rate * order_cost / holding_cost))


def total_cost(
    quantity: float, demand_rate: float, order_cost: float, holding_cost: float
) -> float:
    """Average ordering + holding cost per period for order size ``quantity``."""
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    ordering = demand_rate / quantity * order_cost
    holding = quantity / 2.0 * holding_cost
    return float(ordering + holding)


@dataclass(frozen=True)
class EOQSolution:
    """Optimal order size and the cost/cadence it implies."""

    order_quantity: float
    total_cost: float
    orders_per_period: float
    cycle_length: float


def solve_eoq(demand_rate: float, order_cost: float, holding_cost: float) -> EOQSolution:
    """Solve for the EOQ and its associated cost and ordering cadence."""
    quantity = economic_order_quantity(demand_rate, order_cost, holding_cost)
    return EOQSolution(
        order_quantity=quantity,
        total_cost=total_cost(quantity, demand_rate, order_cost, holding_cost),
        orders_per_period=demand_rate / quantity,
        cycle_length=quantity / demand_rate,
    )
