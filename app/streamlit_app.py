"""supply_chain_arena — interactive explorer.

Four tools, each backed by the same models the notebooks use:
newsvendor explorer, safety-stock calculator, facility-location map, bullwhip
simulator. Run with ``make run``.
"""

from __future__ import annotations

import numpy as np
import streamlit as st

from src.evaluation.cost_of_the_guess import safety_stock_inventory_gap
from src.inventory.newsvendor import solve_newsvendor
from src.inventory.safety_stock import safety_stock
from src.network.facility_location import (
    capacity_shadow_prices,
    nearest_site_cost,
    solve_facility_location,
)
from src.simulation.bullwhip import simulate_bullwhip
from src.simulation.demand import stationary_demand

st.set_page_config(page_title="supply_chain_arena", layout="wide")


def newsvendor_explorer() -> None:
    st.header("Newsvendor explorer")
    st.caption("The optimal stock is a quantile of demand, not its mean.")
    col1, col2 = st.columns(2)
    with col1:
        underage = st.slider("Stockout (underage) cost", 1.0, 10.0, 3.0, 0.5)
        overage = st.slider("Leftover (overage) cost", 1.0, 10.0, 1.0, 0.5)
    with col2:
        mean = st.slider("Mean demand", 10.0, 300.0, 100.0, 10.0)
        std = st.slider("Demand std dev", 1.0, 100.0, 25.0, 1.0)

    sol = solve_newsvendor(underage, overage, mean, std)
    st.metric("Critical ratio", f"{sol.critical_ratio:.3f}")
    left, right = st.columns(2)
    left.metric("Optimal order quantity", f"{sol.optimal_quantity:.1f}")
    right.metric("Stock-to-mean quantity", f"{sol.mean_quantity:.1f}")
    st.metric(
        "Cost left on the table by stocking to the mean",
        f"{sol.cost_gap:.2f}",
        delta=f"{sol.cost_gap / sol.mean_cost:.1%} of the guess's cost",
    )


def safety_stock_calculator() -> None:
    st.header("Safety-stock calculator")
    st.caption("A flat rule misplaces the buffer; the distribution puts it where the risk is.")
    lead_time = st.slider("Lead time (periods)", 1.0, 12.0, 4.0, 1.0)
    service_level = st.slider("Target service level", 0.80, 0.999, 0.95, 0.005)
    mean = st.slider("Mean demand per product", 10.0, 300.0, 100.0, 10.0)
    flat_weeks = st.slider("Flat rule: weeks of stock", 0.5, 6.0, 2.0, 0.5)

    sigmas = np.array([5.0, 8.0, 12.0, 20.0, 35.0, 50.0])
    buffers = [safety_stock(float(s), lead_time, service_level) for s in sigmas]
    comparison = safety_stock_inventory_gap(sigmas, mean, lead_time, service_level, flat_weeks)

    st.bar_chart({"distribution-based safety stock": buffers})
    col1, col2, col3 = st.columns(3)
    col1.metric("Distribution-based total", f"{comparison.distribution_total:.0f}")
    col2.metric("Flat-rule total", f"{comparison.flat_total:.0f}")
    col3.metric("Inventory saved", f"{comparison.inventory_saved:.0f}")


def facility_location_map() -> None:
    st.header("Facility-location map")
    st.caption("Open the cost-optimal set of sites, not the nearest one to each customer.")
    n_sites = st.slider("Candidate sites", 3, 6, 5)
    n_customers = st.slider("Customers", 4, 10, 8)
    seed = st.number_input("Random seed", min_value=0, value=7, step=1)

    rng = np.random.default_rng(int(seed))
    fixed = rng.uniform(80.0, 150.0, n_sites)
    capacities = rng.uniform(120.0, 220.0, n_sites)
    demands = rng.uniform(20.0, 60.0, n_customers)
    capacities = capacities * (demands.sum() / capacities.sum()) * 1.6
    transport = rng.uniform(1.0, 10.0, (n_sites, n_customers))

    sol = solve_facility_location(fixed, capacities, demands, transport)
    naive = nearest_site_cost(fixed, capacities, demands, transport)
    prices = capacity_shadow_prices(fixed, capacities, demands, transport)

    col1, col2 = st.columns(2)
    col1.metric("Optimal total cost", f"{sol.total_cost:.0f}")
    col2.metric("Nearest-site cost", f"{naive:.0f}", delta=f"{naive - sol.total_cost:.0f} wasted")
    st.write("**Open sites:**", ", ".join(str(i) for i in sol.opened) or "none")
    st.write("**Capacity shadow prices** (which site to expand next):")
    st.json({f"site {i}": round(price, 3) for i, price in prices.items()})


def bullwhip_simulator() -> None:
    st.header("Bullwhip simulator")
    st.caption("A small signal at the customer end amplifies into wild swings upstream.")
    n_stages = st.slider("Stages in the chain", 2, 6, 4)
    forecast_window = st.slider("Forecast window", 2, 15, 5)
    lead_time = st.slider("Lead time", 1, 6, 2)

    demand = stationary_demand(200, 100.0, 20.0, seed=0)
    result = simulate_bullwhip(demand, n_stages, forecast_window, lead_time, warmup=20)

    series = {"customer demand": demand}
    for stage, orders in enumerate(result.orders_by_stage):
        series[f"stage {stage + 1} orders"] = orders
    st.line_chart(series)
    st.write("**Order-variance amplification vs the customer:**")
    labels = ["customer", *[f"stage {i + 1}" for i in range(n_stages)]]
    st.json({label: round(a, 2) for label, a in zip(labels, result.amplification, strict=True)})


TOOLS = {
    "Newsvendor explorer": newsvendor_explorer,
    "Safety-stock calculator": safety_stock_calculator,
    "Facility-location map": facility_location_map,
    "Bullwhip simulator": bullwhip_simulator,
}


def main() -> None:
    st.title("Your supply chain is an optimization model")
    choice = st.sidebar.radio("Tool", list(TOOLS))
    TOOLS[choice]()


if __name__ == "__main__":
    main()
