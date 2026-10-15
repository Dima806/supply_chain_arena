"""Safety stock: the buffer tied to demand variability, lead time, and service level.

A flat "N weeks of stock" rule over-protects stable items and under-protects
volatile ones. The service-level formula ties the buffer to the demand standard
deviation instead, which is exactly the forecast-error quantity the audience
already knows.
"""

from __future__ import annotations

import numpy as np
from scipy import stats


def z_score(service_level: float) -> float:
    """Standard-normal quantile for a target (cycle) service level."""
    if not 0.0 < service_level < 1.0:
        raise ValueError("service_level must be in (0, 1)")
    return float(stats.norm.ppf(service_level))


def safety_stock(
    sigma_demand: float,
    lead_time: float,
    service_level: float,
    review_period: float = 0.0,
) -> float:
    """Service-level safety stock = z * sigma * sqrt(lead_time + review_period)."""
    if sigma_demand < 0:
        raise ValueError("sigma_demand must be non-negative")
    if lead_time < 0 or review_period < 0:
        raise ValueError("lead_time and review_period must be non-negative")
    return float(z_score(service_level) * sigma_demand * np.sqrt(lead_time + review_period))


def reorder_point(mean_demand: float, lead_time: float, safety: float) -> float:
    """Reorder point = expected lead-time demand + safety stock."""
    return float(mean_demand * lead_time + safety)


def flat_safety_stock(mean_demand: float, weeks: float) -> float:
    """The naive baseline: a flat number of weeks of average demand, for every item."""
    return float(mean_demand * weeks)
