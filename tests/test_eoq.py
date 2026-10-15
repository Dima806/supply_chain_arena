"""EOQ matches its closed form and minimizes total cost."""

from __future__ import annotations

import numpy as np
import pytest

from src.inventory.eoq import economic_order_quantity, solve_eoq, total_cost


def test_eoq_matches_closed_form():
    assert economic_order_quantity(1000.0, 50.0, 2.0) == pytest.approx(
        np.sqrt(2.0 * 1000.0 * 50.0 / 2.0)
    )


def test_eoq_minimizes_total_cost():
    demand_rate, order_cost, holding_cost = 1000.0, 50.0, 2.0
    q_star = economic_order_quantity(demand_rate, order_cost, holding_cost)
    best = total_cost(q_star, demand_rate, order_cost, holding_cost)
    for factor in (0.5, 0.75, 1.25, 2.0):
        assert total_cost(q_star * factor, demand_rate, order_cost, holding_cost) >= best - 1e-9


def test_eoq_balances_ordering_and_holding_cost():
    sol = solve_eoq(1000.0, 50.0, 2.0)
    ordering = 1000.0 / sol.order_quantity * 50.0
    holding = sol.order_quantity / 2.0 * 2.0
    assert ordering == pytest.approx(holding)
