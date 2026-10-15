"""Service-level measurement: fill rate, stockout probability, and simulation checks."""

from __future__ import annotations

import numpy as np

from src.inventory.safety_stock import reorder_point, safety_stock


def fill_rate(demand: object, supplied: object) -> float:
    """Fraction of demand met from stock."""
    dem = np.asarray(demand, dtype=float)
    sup = np.asarray(supplied, dtype=float)
    total = float(dem.sum())
    if total == 0.0:
        return 1.0
    return float(np.minimum(sup, dem).sum() / total)


def cycle_service_level(lead_time_demand: object, order_up_to_level: float) -> float:
    """Probability that lead-time demand is covered by the stocking level."""
    ltd = np.asarray(lead_time_demand, dtype=float)
    return float(np.mean(ltd <= order_up_to_level))


def stockout_probability(lead_time_demand: object, order_up_to_level: float) -> float:
    """Probability of a stockout during a replenishment cycle."""
    return 1.0 - cycle_service_level(lead_time_demand, order_up_to_level)


def simulate_cycle_service_level(
    mean_demand: float,
    sigma_demand: float,
    lead_time: float,
    service_level: float,
    n_cycles: int = 100_000,
    seed: int = 0,
) -> float:
    """Simulate achieved cycle service level for a safety-stock-based reorder point.

    Confirms the service-level formula: the achieved rate should match the target.
    """
    rng = np.random.default_rng(seed)
    buffer = safety_stock(sigma_demand, lead_time, service_level)
    rop = reorder_point(mean_demand, lead_time, buffer)
    lead_time_demand = rng.normal(
        mean_demand * lead_time, sigma_demand * np.sqrt(lead_time), size=n_cycles
    )
    return float(np.mean(lead_time_demand <= rop))
