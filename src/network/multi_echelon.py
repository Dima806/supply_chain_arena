"""Multi-echelon stock positioning and the risk-pooling result.

Holding safety stock at every store requires more total inventory than pooling it
at an upstream node, because independent demands aggregate with less proportional
variability (the square-root-of-the-sum-of-squares beats the sum).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.inventory.safety_stock import z_score


@dataclass(frozen=True)
class PoolingResult:
    """Total safety stock decentralized vs centralized, and the inventory saved."""

    decentralized: float
    centralized: float
    savings: float
    pooling_factor: float


def decentralized_safety_stock(sigmas: object, lead_time: float, service_level: float) -> float:
    """Safety stock held separately at each node: z * sqrt(L) * sum(sigma_i)."""
    sigma = np.asarray(sigmas, dtype=float)
    return float(z_score(service_level) * np.sqrt(lead_time) * sigma.sum())


def centralized_safety_stock(sigmas: object, lead_time: float, service_level: float) -> float:
    """Safety stock pooled at one node: z * sqrt(L) * sqrt(sum(sigma_i^2))."""
    sigma = np.asarray(sigmas, dtype=float)
    return float(z_score(service_level) * np.sqrt(lead_time) * np.sqrt(np.sum(sigma**2)))


def pooling_factor(sigmas: object) -> float:
    """Ratio of pooled to summed standard deviation; 1 for a single node, else < 1."""
    sigma = np.asarray(sigmas, dtype=float)
    denominator = float(sigma.sum())
    if denominator == 0.0:
        return 1.0
    return float(np.sqrt(np.sum(sigma**2)) / denominator)


def compare_pooling(sigmas: object, lead_time: float, service_level: float) -> PoolingResult:
    """Quantify the inventory saved by pooling safety stock upstream."""
    decentralized = decentralized_safety_stock(sigmas, lead_time, service_level)
    centralized = centralized_safety_stock(sigmas, lead_time, service_level)
    return PoolingResult(
        decentralized=decentralized,
        centralized=centralized,
        savings=decentralized - centralized,
        pooling_factor=pooling_factor(sigmas),
    )
