"""(s, S) and (R, Q) policy simulations behave sensibly over stochastic demand."""

from __future__ import annotations

from src.inventory.reorder_policy import simulate_rq_policy, simulate_ss_policy
from src.simulation.demand import stationary_demand


def test_ss_policy_metrics_are_valid():
    demand = stationary_demand(300, 50.0, 10.0, seed=3)
    result = simulate_ss_policy(demand, reorder_level=120.0, order_up_to=260.0, lead_time=2)
    assert 0.0 <= result.fill_rate <= 1.0
    assert result.n_orders > 0
    assert result.avg_on_hand > 0.0


def test_higher_order_up_to_does_not_hurt_fill_rate():
    demand = stationary_demand(300, 50.0, 15.0, seed=4)
    low = simulate_ss_policy(demand, 120.0, 180.0, 2).fill_rate
    high = simulate_ss_policy(demand, 120.0, 320.0, 2).fill_rate
    assert high >= low


def test_rq_policy_orders_in_batches():
    demand = stationary_demand(300, 50.0, 10.0, seed=5)
    result = simulate_rq_policy(demand, reorder_level=120.0, order_quantity=100.0, lead_time=2)
    assert 0.0 <= result.fill_rate <= 1.0
    assert result.n_orders > 0
