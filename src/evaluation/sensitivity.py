"""Sensitivity analysis: capacity shadow prices and cost-vs-parameter sweeps."""

from __future__ import annotations

import numpy as np

from src.inventory.newsvendor import solve_newsvendor
from src.network.facility_location import capacity_shadow_prices


def newsvendor_cost_ratio_sweep(
    cost_ratios: object, overage_cost: float, mean: float, std: float
) -> tuple[np.ndarray, np.ndarray]:
    """Cost gap vs the stockout/leftover cost ratio (underage = ratio * overage)."""
    ratios = np.asarray(cost_ratios, dtype=float)
    gaps = np.array(
        [
            solve_newsvendor(float(r) * overage_cost, overage_cost, mean, std).cost_gap
            for r in ratios
        ]
    )
    return ratios, gaps


def newsvendor_uncertainty_sweep(
    stds: object, underage_cost: float, overage_cost: float, mean: float
) -> tuple[np.ndarray, np.ndarray]:
    """Cost gap vs demand uncertainty (the demand standard deviation)."""
    sigmas = np.asarray(stds, dtype=float)
    gaps = np.array(
        [solve_newsvendor(underage_cost, overage_cost, mean, float(s)).cost_gap for s in sigmas]
    )
    return sigmas, gaps


def capacity_sensitivity(
    fixed_costs: object, capacities: object, demands: object, transport_costs: object
) -> dict[int, float]:
    """Capacity shadow prices per open facility: which site to expand next."""
    return capacity_shadow_prices(fixed_costs, capacities, demands, transport_costs)
