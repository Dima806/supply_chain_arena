"""Newsvendor: critical ratio matches the closed form; optimum beats stock-to-mean."""

from __future__ import annotations

import pytest
from scipy import stats

from src.inventory.newsvendor import (
    critical_ratio,
    optimal_quantity,
    solve_newsvendor,
    stock_to_mean,
)


def test_critical_ratio_matches_formula():
    assert critical_ratio(3.0, 1.0) == pytest.approx(0.75)


def test_optimal_quantity_is_the_critical_ratio_quantile():
    mean, std = 100.0, 25.0
    optimum = optimal_quantity(3.0, 1.0, mean, std)
    assert optimum == pytest.approx(stats.norm.ppf(0.75, loc=mean, scale=std))


def test_symmetric_costs_stock_to_the_mean():
    mean = 100.0
    assert optimal_quantity(1.0, 1.0, mean, 25.0) == pytest.approx(mean)
    assert stock_to_mean(mean) == pytest.approx(mean)


def test_expensive_stockout_pushes_the_optimum_above_the_mean():
    sol = solve_newsvendor(3.0, 1.0, 100.0, 25.0)
    assert sol.optimal_quantity > sol.mean_quantity
    assert sol.optimal_cost <= sol.mean_cost
    assert sol.cost_gap >= 0.0


def test_gap_grows_with_cost_asymmetry():
    mild = solve_newsvendor(1.5, 1.0, 100.0, 25.0).cost_gap
    severe = solve_newsvendor(5.0, 1.0, 100.0, 25.0).cost_gap
    assert severe > mild


def test_gap_grows_with_demand_uncertainty():
    tight = solve_newsvendor(3.0, 1.0, 100.0, 10.0).cost_gap
    wide = solve_newsvendor(3.0, 1.0, 100.0, 40.0).cost_gap
    assert wide > tight
