"""The cost of the guess: optimal decisions vs the intuitive baselines, in money."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.inventory.newsvendor import solve_newsvendor
from src.inventory.safety_stock import flat_safety_stock, safety_stock
from src.network.facility_location import nearest_site_cost, solve_facility_location


def newsvendor_cost_gap(
    underage_cost: float, overage_cost: float, mean: float, std: float
) -> float:
    """Expected cost that stocking to the mean leaves on the table per season."""
    return solve_newsvendor(underage_cost, overage_cost, mean, std).cost_gap


@dataclass(frozen=True)
class SafetyStockComparison:
    """Distribution-based vs flat safety stock across a range of products."""

    distribution_total: float
    flat_total: float
    inventory_saved: float


def safety_stock_inventory_gap(
    sigmas: object,
    mean_demand: float,
    lead_time: float,
    service_level: float,
    flat_weeks: float,
) -> SafetyStockComparison:
    """Total safety stock under a distribution-based rule vs a flat weeks-of-stock rule."""
    sigma = np.asarray(sigmas, dtype=float)
    distribution_total = float(
        sum(safety_stock(float(s), lead_time, service_level) for s in sigma)
    )
    flat_total = float(sigma.size * flat_safety_stock(mean_demand, flat_weeks))
    return SafetyStockComparison(
        distribution_total=distribution_total,
        flat_total=flat_total,
        inventory_saved=flat_total - distribution_total,
    )


def facility_savings(
    fixed_costs: object, capacities: object, demands: object, transport_costs: object
) -> float:
    """Money the nearest-site heuristic wastes versus the facility-location optimum."""
    optimal = solve_facility_location(fixed_costs, capacities, demands, transport_costs).total_cost
    naive = nearest_site_cost(fixed_costs, capacities, demands, transport_costs)
    return naive - optimal
