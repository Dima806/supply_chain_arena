"""Capacitated facility location (MILP).

Choose which candidate sites to open (binary, with fixed costs) and how to assign
demand to open sites (subject to capacity), minimizing fixed + transportation cost.
Verified against brute force at small size, contrasted with the nearest-site
heuristic, and mined for capacity shadow prices (which site to expand next).
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pulp

from src.solvers import Backend, solve


@dataclass(frozen=True)
class FacilitySolution:
    """Which sites open, how demand is assigned, and the cost breakdown."""

    opened: tuple[int, ...]
    assignment: np.ndarray  # [n_sites, n_customers] units shipped
    total_cost: float
    fixed_cost: float
    transport_cost: float
    status: str


def _as_arrays(
    fixed_costs: object, capacities: object, demands: object, transport_costs: object
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.asarray(fixed_costs, dtype=float),
        np.asarray(capacities, dtype=float),
        np.asarray(demands, dtype=float),
        np.asarray(transport_costs, dtype=float),
    )


def solve_facility_location(
    fixed_costs: object,
    capacities: object,
    demands: object,
    transport_costs: object,
    backend: Backend = Backend.CBC,
) -> FacilitySolution:
    """Solve the capacitated facility-location MILP to exact optimality."""
    fixed, cap, dem, cost = _as_arrays(fixed_costs, capacities, demands, transport_costs)
    n_sites = int(fixed.size)
    n_customers = int(dem.size)

    prob = pulp.LpProblem("facility_location", pulp.LpMinimize)
    y = [pulp.LpVariable(f"open_{i}", cat="Binary") for i in range(n_sites)]
    x = [
        [pulp.LpVariable(f"ship_{i}_{j}", lowBound=0) for j in range(n_customers)]
        for i in range(n_sites)
    ]

    prob += pulp.lpSum(float(fixed[i]) * y[i] for i in range(n_sites)) + pulp.lpSum(
        float(cost[i, j]) * x[i][j] for i in range(n_sites) for j in range(n_customers)
    )
    for j in range(n_customers):
        prob += pulp.lpSum(x[i][j] for i in range(n_sites)) == float(dem[j])
    for i in range(n_sites):
        prob += pulp.lpSum(x[i][j] for j in range(n_customers)) <= float(cap[i]) * y[i]

    result = solve(prob, backend)
    opened = tuple(i for i in range(n_sites) if (pulp.value(y[i]) or 0.0) > 0.5)
    assignment = np.array(
        [[float(pulp.value(x[i][j]) or 0.0) for j in range(n_customers)] for i in range(n_sites)]
    )
    transport = float(np.sum(assignment * cost))
    fixed_total = float(sum(float(fixed[i]) for i in opened))
    total = result.objective if result.objective is not None else fixed_total + transport
    return FacilitySolution(
        opened, assignment, float(total), fixed_total, transport, result.status
    )


def _min_transport_cost(cap: np.ndarray, dem: np.ndarray, cost: np.ndarray) -> float:
    """Minimum transportation cost to serve ``dem`` from fixed sites with ``cap``."""
    if float(cap.sum()) + 1e-9 < float(dem.sum()):
        return float("inf")
    n_sites = int(cap.size)
    n_customers = int(dem.size)
    prob = pulp.LpProblem("transport", pulp.LpMinimize)
    x = [
        [pulp.LpVariable(f"t_{i}_{j}", lowBound=0) for j in range(n_customers)]
        for i in range(n_sites)
    ]
    prob += pulp.lpSum(
        float(cost[i, j]) * x[i][j] for i in range(n_sites) for j in range(n_customers)
    )
    for j in range(n_customers):
        prob += pulp.lpSum(x[i][j] for i in range(n_sites)) == float(dem[j])
    for i in range(n_sites):
        prob += pulp.lpSum(x[i][j] for j in range(n_customers)) <= float(cap[i])
    result = solve(prob)
    if result.status != "Optimal" or result.objective is None:
        return float("inf")
    return float(result.objective)


def brute_force_facility_location(
    fixed_costs: object, capacities: object, demands: object, transport_costs: object
) -> tuple[tuple[int, ...], float]:
    """Enumerate every subset of sites to open; return the cheapest (sites, cost)."""
    fixed, cap, dem, cost = _as_arrays(fixed_costs, capacities, demands, transport_costs)
    n_sites = int(fixed.size)
    best_cost = float("inf")
    best_opened: tuple[int, ...] = ()
    for size in range(1, n_sites + 1):
        for subset in combinations(range(n_sites), size):
            idx = list(subset)
            transport = _min_transport_cost(cap[idx], dem, cost[idx, :])
            if not np.isfinite(transport):
                continue
            total = float(sum(float(fixed[i]) for i in subset)) + transport
            if total < best_cost:
                best_cost = total
                best_opened = subset
    return best_opened, best_cost


def nearest_site_cost(
    fixed_costs: object, capacities: object, demands: object, transport_costs: object
) -> float:
    """Cost of the intuitive baseline: serve each customer from its cheapest site,
    overflowing to the next cheapest when capacity runs out."""
    fixed, cap, dem, cost = _as_arrays(fixed_costs, capacities, demands, transport_costs)
    n_sites = int(fixed.size)
    n_customers = int(dem.size)
    remaining = cap.copy()
    assignment = np.zeros((n_sites, n_customers))
    for j in range(n_customers):
        need = float(dem[j])
        for i in np.argsort(cost[:, j]):
            if need <= 1e-12:
                break
            take = min(need, float(remaining[i]))
            assignment[i, j] += take
            remaining[i] -= take
            need -= take
    opened = tuple(i for i in range(n_sites) if assignment[i].sum() > 1e-9)
    transport = float(np.sum(assignment * cost))
    fixed_total = float(sum(float(fixed[i]) for i in opened))
    return fixed_total + transport


def capacity_shadow_prices(
    fixed_costs: object,
    capacities: object,
    demands: object,
    transport_costs: object,
    backend: Backend = Backend.CBC,
) -> dict[int, float]:
    """Marginal value of one more unit of capacity at each open site.

    Fixes the MILP's open/close decision, re-solves the resulting LP, and reads the
    dual of each capacity constraint. A large value flags the site to expand next.
    """
    fixed, cap, dem, cost = _as_arrays(fixed_costs, capacities, demands, transport_costs)
    opened = solve_facility_location(
        fixed_costs, capacities, demands, transport_costs, backend
    ).opened
    n_customers = int(dem.size)

    prob = pulp.LpProblem("facility_lp", pulp.LpMinimize)
    x = {
        (i, j): pulp.LpVariable(f"x_{i}_{j}", lowBound=0)
        for i in opened
        for j in range(n_customers)
    }
    prob += pulp.lpSum(float(cost[i, j]) * x[i, j] for i in opened for j in range(n_customers))
    for j in range(n_customers):
        prob += pulp.lpSum(x[i, j] for i in opened) == float(dem[j])
    cap_constraints = {}
    for i in opened:
        constraint = pulp.lpSum(x[i, j] for j in range(n_customers)) <= float(cap[i])
        prob += constraint
        cap_constraints[i] = constraint

    solve(prob, backend)
    prices: dict[int, float] = {}
    for i in opened:
        dual = cap_constraints[i].pi
        prices[i] = abs(float(dual)) if dual is not None else 0.0
    return prices
