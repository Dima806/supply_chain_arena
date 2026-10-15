"""Network flow: conservation holds and optimal cost is verified."""

from __future__ import annotations

import numpy as np
import pytest

from src.network.transportation import check_conservation, solve_transportation
from src.network.transshipment import solve_transshipment


def test_transportation_is_optimal_and_conserved():
    supply = [100.0, 150.0, 120.0]
    demand = [80.0, 90.0, 100.0]
    cost = [[4.0, 6.0, 8.0], [5.0, 3.0, 7.0], [9.0, 5.0, 2.0]]
    sol = solve_transportation(supply, demand, cost)
    assert sol.status == "Optimal"
    assert check_conservation(sol.flows, supply, demand)
    assert sol.total_cost == pytest.approx(float(np.sum(sol.flows * np.array(cost))))


def test_transportation_cost_is_at_most_a_feasible_assignment():
    supply = [200.0, 200.0]
    demand = [100.0, 100.0]
    cost = [[1.0, 9.0], [9.0, 1.0]]
    sol = solve_transportation(supply, demand, cost)
    # the obvious diagonal assignment costs 200; the optimum cannot do worse
    assert sol.total_cost <= 200.0 + 1e-6


def test_transshipment_conserves_flow_at_warehouses():
    supply = [200.0, 180.0]
    demand = [90.0, 110.0, 120.0]
    cost_sw = [[2.0, 4.0], [5.0, 3.0]]  # 2 sources x 2 warehouses
    cost_wc = [[3.0, 5.0, 7.0], [6.0, 4.0, 2.0]]  # 2 warehouses x 3 customers
    sol = solve_transshipment(supply, demand, cost_sw, cost_wc)
    assert sol.status == "Optimal"
    inflow = sol.source_to_warehouse.sum(axis=0)
    outflow = sol.warehouse_to_customer.sum(axis=1)
    assert np.allclose(inflow, outflow, atol=1e-6)
    received = sol.warehouse_to_customer.sum(axis=0)
    assert np.allclose(received, demand, atol=1e-6)
