"""Bullwhip simulation: local order reactions amplify demand variance upstream.

Each stage forecasts with a moving average and orders up to a base-stock level.
Order = demand + change in base stock, so variability grows as orders propagate
upstream, even though the only exogenous signal is steady customer demand.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def order_up_to_orders(
    incoming_demand: np.ndarray, forecast_window: int, lead_time: int
) -> np.ndarray:
    """Orders a single stage places when it faces ``incoming_demand``."""
    demand = np.asarray(incoming_demand, dtype=float)
    n = int(demand.size)
    orders = np.zeros(n)
    previous_base = float(demand[0]) * (lead_time + 1) if n > 0 else 0.0
    for t in range(n):
        start = max(0, t - forecast_window + 1)
        forecast = float(demand[start : t + 1].mean())
        base_stock = forecast * (lead_time + 1)
        order = float(demand[t]) + (base_stock - previous_base)
        orders[t] = max(order, 0.0)
        previous_base = base_stock
    return orders


@dataclass(frozen=True)
class BullwhipResult:
    """Per-stage order series and the variance amplification versus the customer."""

    orders_by_stage: list[np.ndarray]  # stage 0 is closest to the customer
    variances: list[float]  # [customer, stage0, stage1, ...]
    amplification: list[float]  # variance / customer-demand variance


def simulate_bullwhip(
    customer_demand: np.ndarray,
    n_stages: int,
    forecast_window: int,
    lead_time: int,
    warmup: int = 20,
) -> BullwhipResult:
    """Propagate customer demand up a chain and measure order-variance amplification."""
    demand = np.asarray(customer_demand, dtype=float)
    orders_by_stage: list[np.ndarray] = []
    downstream = demand
    for _ in range(n_stages):
        orders = order_up_to_orders(downstream, forecast_window, lead_time)
        orders_by_stage.append(orders)
        downstream = orders

    base_var = float(demand[warmup:].var())
    variances = [base_var] + [float(stage[warmup:].var()) for stage in orders_by_stage]
    amplification = [v / base_var if base_var > 0 else 1.0 for v in variances]
    return BullwhipResult(orders_by_stage, variances, amplification)
