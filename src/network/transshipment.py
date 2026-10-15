"""Multi-echelon transshipment: sources -> warehouses -> customers at minimum cost.

Flow is conserved at each intermediate warehouse (inflow equals outflow), the
backbone of multi-stage network design.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pulp

from src.solvers import Backend, solve


@dataclass(frozen=True)
class TransshipmentSolution:
    """Optimal flows on both echelons and the total cost."""

    source_to_warehouse: np.ndarray  # [n_sources, n_warehouses]
    warehouse_to_customer: np.ndarray  # [n_warehouses, n_customers]
    total_cost: float
    status: str


def solve_transshipment(
    supply: object,
    demand: object,
    cost_source_warehouse: object,
    cost_warehouse_customer: object,
    warehouse_capacity: object | None = None,
    backend: Backend = Backend.CBC,
) -> TransshipmentSolution:
    """Solve the two-echelon minimum-cost flow with conservation at warehouses."""
    sup = np.asarray(supply, dtype=float)
    dem = np.asarray(demand, dtype=float)
    cost_sw = np.asarray(cost_source_warehouse, dtype=float)  # [S, W]
    cost_wc = np.asarray(cost_warehouse_customer, dtype=float)  # [W, C]
    n_sources, n_warehouses = cost_sw.shape
    n_customers = int(dem.size)

    prob = pulp.LpProblem("transshipment", pulp.LpMinimize)
    f_sw = [
        [pulp.LpVariable(f"sw_{s}_{w}", lowBound=0) for w in range(n_warehouses)]
        for s in range(n_sources)
    ]
    f_wc = [
        [pulp.LpVariable(f"wc_{w}_{c}", lowBound=0) for c in range(n_customers)]
        for w in range(n_warehouses)
    ]

    prob += pulp.lpSum(
        float(cost_sw[s, w]) * f_sw[s][w] for s in range(n_sources) for w in range(n_warehouses)
    ) + pulp.lpSum(
        float(cost_wc[w, c]) * f_wc[w][c] for w in range(n_warehouses) for c in range(n_customers)
    )

    for s in range(n_sources):
        prob += pulp.lpSum(f_sw[s][w] for w in range(n_warehouses)) <= float(sup[s])
    for c in range(n_customers):
        prob += pulp.lpSum(f_wc[w][c] for w in range(n_warehouses)) >= float(dem[c])
    for w in range(n_warehouses):
        inflow = pulp.lpSum(f_sw[s][w] for s in range(n_sources))
        outflow = pulp.lpSum(f_wc[w][c] for c in range(n_customers))
        prob += inflow == outflow
        if warehouse_capacity is not None:
            cap = np.asarray(warehouse_capacity, dtype=float)
            prob += inflow <= float(cap[w])

    result = solve(prob, backend)
    sw = np.array(
        [
            [float(pulp.value(f_sw[s][w]) or 0.0) for w in range(n_warehouses)]
            for s in range(n_sources)
        ]
    )
    wc = np.array(
        [
            [float(pulp.value(f_wc[w][c]) or 0.0) for c in range(n_customers)]
            for w in range(n_warehouses)
        ]
    )
    total = result.objective
    if total is None:
        total = float(np.sum(sw * cost_sw) + np.sum(wc * cost_wc))
    return TransshipmentSolution(sw, wc, float(total), result.status)
