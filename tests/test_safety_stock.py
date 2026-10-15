"""Safety stock: achieved service level matches target; distribution beats flat."""

from __future__ import annotations

import pytest

from src.evaluation.cost_of_the_guess import safety_stock_inventory_gap
from src.evaluation.service_level import simulate_cycle_service_level
from src.inventory.safety_stock import safety_stock


@pytest.mark.parametrize("target", [0.90, 0.95, 0.99])
def test_achieved_service_level_matches_target(target: float):
    achieved = simulate_cycle_service_level(100.0, 25.0, 4.0, target, n_cycles=200_000, seed=1)
    assert achieved == pytest.approx(target, abs=0.01)


def test_volatile_item_needs_more_safety_stock():
    stable = safety_stock(5.0, 4.0, 0.95)
    volatile = safety_stock(40.0, 4.0, 0.95)
    assert volatile > stable


def test_distribution_based_holds_less_than_a_flat_rule():
    sigmas = [5.0, 8.0, 10.0, 12.0, 40.0]
    comparison = safety_stock_inventory_gap(
        sigmas, mean_demand=100.0, lead_time=4.0, service_level=0.95, flat_weeks=2.0
    )
    assert comparison.distribution_total < comparison.flat_total
    assert comparison.inventory_saved > 0.0
