"""Facility location: MILP optimum matches brute force and beats nearest-site."""

from __future__ import annotations

import numpy as np
import pytest

from src.network.facility_location import (
    brute_force_facility_location,
    capacity_shadow_prices,
    nearest_site_cost,
    solve_facility_location,
)


def _instance() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(7)
    n_sites, n_customers = 5, 7
    fixed = rng.uniform(80.0, 150.0, n_sites)
    capacities = rng.uniform(120.0, 220.0, n_sites)
    demands = rng.uniform(20.0, 60.0, n_customers)
    # scale capacity so the instance is comfortably feasible but no single site covers all
    capacities = capacities * (demands.sum() / capacities.sum()) * 1.5
    transport = rng.uniform(1.0, 10.0, (n_sites, n_customers))
    return fixed, capacities, demands, transport


def test_milp_optimum_matches_brute_force():
    fixed, capacities, demands, transport = _instance()
    sol = solve_facility_location(fixed, capacities, demands, transport)
    _, brute_cost = brute_force_facility_location(fixed, capacities, demands, transport)
    assert sol.status == "Optimal"
    assert sol.total_cost == pytest.approx(brute_cost, rel=1e-4)


def test_optimization_beats_nearest_site_heuristic():
    fixed, capacities, demands, transport = _instance()
    sol = solve_facility_location(fixed, capacities, demands, transport)
    naive = nearest_site_cost(fixed, capacities, demands, transport)
    assert naive >= sol.total_cost - 1e-6


def test_capacity_shadow_prices_extracted_for_open_sites():
    fixed, capacities, demands, transport = _instance()
    prices = capacity_shadow_prices(fixed, capacities, demands, transport)
    sol = solve_facility_location(fixed, capacities, demands, transport)
    assert set(prices) == set(sol.opened)
    assert all(price >= 0.0 for price in prices.values())
