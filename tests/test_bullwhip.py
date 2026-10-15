"""Bullwhip: order variance amplifies as it propagates upstream."""

from __future__ import annotations

from src.simulation.bullwhip import simulate_bullwhip
from src.simulation.demand import stationary_demand


def test_order_variance_amplifies_upstream():
    demand = stationary_demand(400, 100.0, 20.0, seed=11)
    result = simulate_bullwhip(demand, n_stages=4, forecast_window=5, lead_time=2, warmup=40)
    assert result.amplification[0] == 1.0  # customer is the reference
    # every stage upstream of the customer carries more order variance
    assert all(a > 1.0 for a in result.amplification[1:])
    # amplification compounds moving up the chain
    assert result.amplification[-1] > result.amplification[1]


def test_top_stage_swings_more_than_the_customer():
    demand = stationary_demand(400, 100.0, 20.0, seed=12)
    result = simulate_bullwhip(demand, n_stages=3, forecast_window=5, lead_time=2, warmup=40)
    assert result.variances[-1] > result.variances[0]
