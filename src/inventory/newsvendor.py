"""The newsvendor: single-period stocking under uncertain demand.

The optimal stock is the *critical-ratio quantile* of the demand distribution,
not its mean. When a stockout costs more than a leftover, that quantile sits
above the mean, and stocking to the mean leaves a computable amount on the table.
"""

from __future__ import annotations

from dataclasses import dataclass

from scipy import stats


def critical_ratio(underage_cost: float, overage_cost: float) -> float:
    """Optimal stocking quantile = underage / (underage + overage)."""
    if underage_cost < 0 or overage_cost < 0:
        raise ValueError("costs must be non-negative")
    total = underage_cost + overage_cost
    if total == 0:
        raise ValueError("at least one of underage/overage cost must be positive")
    return underage_cost / total


def optimal_quantity(underage_cost: float, overage_cost: float, mean: float, std: float) -> float:
    """Optimal order quantity for normally distributed demand."""
    ratio = critical_ratio(underage_cost, overage_cost)
    return float(stats.norm.ppf(ratio, loc=mean, scale=std))


def stock_to_mean(mean: float) -> float:
    """The intuitive baseline: order expected demand."""
    return float(mean)


def expected_cost(
    quantity: float, underage_cost: float, overage_cost: float, mean: float, std: float
) -> float:
    """Expected overage + underage cost at ``quantity`` for normal demand."""
    dist = stats.norm(loc=mean, scale=std)
    overage = overage_cost * dist.expect(lambda d: max(quantity - d, 0.0))
    underage = underage_cost * dist.expect(lambda d: max(d - quantity, 0.0))
    return float(overage + underage)


@dataclass(frozen=True)
class NewsvendorSolution:
    """Optimal stocking decision and the gap versus stocking to the mean."""

    critical_ratio: float
    optimal_quantity: float
    optimal_cost: float
    mean_quantity: float
    mean_cost: float
    cost_gap: float  # money left on the table by stocking to the mean


def solve_newsvendor(
    underage_cost: float, overage_cost: float, mean: float, std: float
) -> NewsvendorSolution:
    """Solve the newsvendor and quantify the cost of the stock-to-mean guess."""
    ratio = critical_ratio(underage_cost, overage_cost)
    q_opt = optimal_quantity(underage_cost, overage_cost, mean, std)
    q_mean = stock_to_mean(mean)
    cost_opt = expected_cost(q_opt, underage_cost, overage_cost, mean, std)
    cost_mean = expected_cost(q_mean, underage_cost, overage_cost, mean, std)
    return NewsvendorSolution(
        critical_ratio=ratio,
        optimal_quantity=q_opt,
        optimal_cost=cost_opt,
        mean_quantity=q_mean,
        mean_cost=cost_mean,
        cost_gap=cost_mean - cost_opt,
    )
