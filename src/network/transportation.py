"""Transportation LP: ship from sources to sinks at minimum cost.

Supply is capped per source, demand must be met per sink, and the shadow prices
on those constraints are the marginal value of capacity at each node.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pulp

from src.solvers import Backend, solve


@dataclass(frozen=True)
class TransportationSolution:
    """Optimal flows, total cost, and shadow prices on supply and demand."""

    flows: np.ndarray  # [n_sources, n_sinks]
    total_cost: float
    supply_prices: np.ndarray
    demand_prices: np.ndarray
    status: str


def _dual(constraint: object) -> float:
    pi = getattr(constraint, "pi", None)
    return float(pi) if pi is not None else 0.0


def solve_transportation(
    supply: object, demand: object, cost: object, backend: Backend = Backend.CBC
) -> TransportationSolution:
    """Solve the minimum-cost transportation LP (total supply must cover demand)."""
    sup = np.asarray(supply, dtype=float)
    dem = np.asarray(demand, dtype=float)
    unit_cost = np.asarray(cost, dtype=float)
    n_sources = int(sup.size)
    n_sinks = int(dem.size)

    prob = pulp.LpProblem("transportation", pulp.LpMinimize)
    x = [
        [pulp.LpVariable(f"x_{i}_{j}", lowBound=0) for j in range(n_sinks)]
        for i in range(n_sources)
    ]
    prob += pulp.lpSum(
        float(unit_cost[i, j]) * x[i][j] for i in range(n_sources) for j in range(n_sinks)
    )

    supply_cons = []
    for i in range(n_sources):
        constraint = pulp.lpSum(x[i][j] for j in range(n_sinks)) <= float(sup[i])
        prob += constraint
        supply_cons.append(constraint)

    demand_cons = []
    for j in range(n_sinks):
        constraint = pulp.lpSum(x[i][j] for i in range(n_sources)) >= float(dem[j])
        prob += constraint
        demand_cons.append(constraint)

    result = solve(prob, backend)
    flows = np.array(
        [[float(pulp.value(x[i][j]) or 0.0) for j in range(n_sinks)] for i in range(n_sources)]
    )
    total = result.objective if result.objective is not None else float(np.sum(flows * unit_cost))
    return TransportationSolution(
        flows=flows,
        total_cost=float(total),
        supply_prices=np.array([_dual(c) for c in supply_cons]),
        demand_prices=np.array([_dual(c) for c in demand_cons]),
        status=result.status,
    )


def check_conservation(
    flows: np.ndarray, supply: object, demand: object, tol: float = 1e-6
) -> bool:
    """Demand met exactly and no source ships beyond its supply."""
    sup = np.asarray(supply, dtype=float)
    dem = np.asarray(demand, dtype=float)
    shipped_out = flows.sum(axis=1)
    received = flows.sum(axis=0)
    supply_ok = bool(np.all(shipped_out <= sup + tol))
    demand_ok = bool(np.all(np.abs(received - dem) <= tol))
    return supply_ok and demand_ok
