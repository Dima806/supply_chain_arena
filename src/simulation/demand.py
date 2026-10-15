"""Synthetic, seeded demand generators with known structure.

Demand is clipped at zero. Seeds make every stream reproducible so the newsvendor
and safety-stock optima stay analytically checkable.
"""

from __future__ import annotations

import numpy as np


def stationary_demand(n: int, mean: float, std: float, seed: int = 0) -> np.ndarray:
    """Independent normal demand with a constant mean."""
    rng = np.random.default_rng(seed)
    return np.maximum(rng.normal(mean, std, size=n), 0.0)


def seasonal_demand(
    n: int, mean: float, amplitude: float, period: int, noise_std: float, seed: int = 0
) -> np.ndarray:
    """Sinusoidal seasonality around a mean, plus normal noise."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    base = mean + amplitude * np.sin(2.0 * np.pi * t / period)
    return np.maximum(base + rng.normal(0.0, noise_std, size=n), 0.0)


def intermittent_demand(
    n: int, demand_prob: float, demand_mean: float, demand_std: float, seed: int = 0
) -> np.ndarray:
    """Sparse demand: a sale occurs with probability ``demand_prob``, else zero."""
    rng = np.random.default_rng(seed)
    occurs = rng.random(n) < demand_prob
    sizes = np.maximum(rng.normal(demand_mean, demand_std, size=n), 0.0)
    return np.where(occurs, sizes, 0.0)
