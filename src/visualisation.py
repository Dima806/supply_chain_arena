"""Shared matplotlib helpers for the notebooks and the Streamlit app.

Kept deliberately small: figures are assembled here, parameters and model calls
stay in the notebooks.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def plot_cost_gap(x: np.ndarray, gaps: np.ndarray, *, xlabel: str, title: str):
    """Line plot of the cost-of-the-guess against a swept parameter."""
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(x, gaps, marker="o")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("expected cost left on the table")
    ax.set_title(title)
    ax.grid(visible=True, alpha=0.3)
    return fig


def plot_safety_stock_comparison(sigmas: np.ndarray, distribution: np.ndarray, flat: float):
    """Bar chart contrasting distribution-based safety stock with a flat rule."""
    fig, ax = plt.subplots(figsize=(6, 4))
    index = np.arange(len(sigmas))
    ax.bar(index, distribution, label="distribution-based")
    ax.axhline(flat, color="crimson", linestyle="--", label="flat rule")
    ax.set_xlabel("product (increasing demand volatility)")
    ax.set_ylabel("safety stock")
    ax.set_title("Flat rules misplace the buffer")
    ax.legend()
    return fig


def plot_bullwhip(orders_by_stage: list[np.ndarray], customer_demand: np.ndarray):
    """Overlay order series from the customer up through the chain."""
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(customer_demand, label="customer demand", linewidth=2, color="black")
    for stage, orders in enumerate(orders_by_stage):
        ax.plot(orders, label=f"stage {stage + 1} orders", alpha=0.7)
    ax.set_xlabel("period")
    ax.set_ylabel("units")
    ax.set_title("Order swings amplify upstream")
    ax.legend()
    return fig
