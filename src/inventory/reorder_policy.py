"""(s, S) and (R, Q) replenishment policies simulated over stochastic demand.

Lost-sales convention: demand that cannot be met from on-hand stock is lost
(not back-ordered). Lead time is a whole number of periods; an order placed in
period t arrives at the start of period t + lead_time.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PolicyResult:
    """Service and inventory metrics from a policy simulation."""

    fill_rate: float
    avg_on_hand: float
    n_orders: int
    total_demand: float
    satisfied_demand: float


def _run(
    demand: np.ndarray,
    lead_time: int,
    initial_inventory: float,
    decide_order,
) -> PolicyResult:
    """Shared simulation loop; ``decide_order`` maps inventory position to an order qty."""
    n = int(demand.size)
    pipeline = np.zeros(n + lead_time + 2)
    on_hand = float(initial_inventory)
    total_demand = 0.0
    satisfied = 0.0
    on_hand_sum = 0.0
    n_orders = 0

    for t in range(n):
        on_hand += float(pipeline[t])
        period_demand = float(demand[t])
        total_demand += period_demand
        sold = min(on_hand, period_demand)
        satisfied += sold
        on_hand -= sold

        inventory_position = on_hand + float(pipeline[t + 1 :].sum())
        order_qty = decide_order(inventory_position)
        if order_qty > 0:
            pipeline[t + lead_time] += order_qty
            n_orders += 1

        on_hand_sum += on_hand

    fill_rate = satisfied / total_demand if total_demand > 0 else 1.0
    return PolicyResult(
        fill_rate=fill_rate,
        avg_on_hand=on_hand_sum / n,
        n_orders=n_orders,
        total_demand=total_demand,
        satisfied_demand=satisfied,
    )


def simulate_ss_policy(
    demand: np.ndarray,
    reorder_level: float,
    order_up_to: float,
    lead_time: int,
    initial_inventory: float | None = None,
) -> PolicyResult:
    """(s, S): when inventory position drops to ``s``, order up to ``S``."""

    def decide(position: float) -> float:
        return order_up_to - position if position <= reorder_level else 0.0

    initial = order_up_to if initial_inventory is None else initial_inventory
    return _run(np.asarray(demand, dtype=float), int(lead_time), initial, decide)


def simulate_rq_policy(
    demand: np.ndarray,
    reorder_level: float,
    order_quantity: float,
    lead_time: int,
    initial_inventory: float | None = None,
) -> PolicyResult:
    """(R, Q): when inventory position drops to ``R``, order a multiple of ``Q``."""

    def decide(position: float) -> float:
        if position > reorder_level:
            return 0.0
        batches = int(np.ceil((reorder_level - position) / order_quantity)) + 1
        return batches * order_quantity

    initial = reorder_level + order_quantity if initial_inventory is None else initial_inventory
    return _run(np.asarray(demand, dtype=float), int(lead_time), initial, decide)
