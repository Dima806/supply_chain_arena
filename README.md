# supply_chain_arena

**Your supply chain is a spreadsheet full of guesses. It should be an optimization model.**

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Solvers](https://img.shields.io/badge/solvers-open--source-success)
![License](https://img.shields.io/badge/license-Apache--2.0-green)

A hands-on tour of the optimization models that run the physical economy — built on CPU
with open solvers, sized to run inside a **2-CPU / 8 GB GitHub Codespace** with no GPU.

The core supply-chain decisions — where to put warehouses, which site serves each
customer, how much stock to hold, when to reorder — are **exact optimization problems,
not spreadsheet judgment calls**. Opening the wrong facility or holding the wrong safety
stock costs a fixed, computable amount of money. And the classic newsvendor formula
shows why the intuitive "stock to meet average demand" rule is *provably* wrong whenever
a stockout costs something different from a leftover — which it always does.

The forecast is the **input**; the decision it feeds is the **value**. This project
connects the forecasting a data scientist already knows to the optimization models that
turn a forecast into a plan.

---

## What's inside

- **6 Jupyter notebooks** that build up from a single stocking decision to a whole chain.
- **A typed `src/` library** of inventory, network, simulation, and evaluation models.
- **A Streamlit app** with four interactive tools.
- **Regenerated artefacts**: every figure as a PNG and every input/result as JSON.
- **27 tests** that verify each optimum against a closed form or brute force.

Every solver is open-source — `pulp` (CBC), `highspy` (HiGHS), `ortools` — so every
result reproduces on a bare Codespace with no license or activation.

---

## Headline results

Numbers below are produced by the notebooks on the seeded instances in
`config/settings.yaml` and saved under `outputs/data/`.

| Decision | Intuitive guess | Optimization | Result |
|---|---|---|---|
| **Newsvendor** — season stocking | stock to the mean | critical-ratio quantile | optimum is the **75th percentile**, ~17 units above the mean |
| **Safety stock** — the buffer | flat "2 weeks" everywhere | service-level formula from σ | **772 fewer units** at matched service (error < 0.2%) |
| **Facility location** — where to build | nearest-site assignment | capacitated MILP | **matches brute force exactly**; ~1,138 (~9%) cheaper than nearest-site |
| **Network flow** — how to route | manual lanes | transportation / transshipment LP | exact optimal flows, conservation verified |
| **Risk pooling** — where to hold stock | a buffer at every store | pool upstream | pooling factor **0.42**: 428 → 179 units at equal service |
| **Bullwhip** — coordinating the chain | optimize locally | take a global view | customer variance amplifies to **95×** by the 4th stage |

---

## Quickstart

Requires [`uv`](https://docs.astral.sh/uv/). Everything else is handled by the Makefile.

```bash
make setup        # install uv if missing, sync deps, register the Jupyter kernel
make test         # run the 27 tests
make ci           # sync + lint (ruff + ty) + test — what CI runs
make notebooks    # execute all 6 notebooks in place (< 5 min each)
make run          # launch the Streamlit app on :8501
make lab          # launch JupyterLab on :8888
```

Run `make help` to see every target.

---

## The notebooks

Each runs in seconds and writes its figures to `outputs/figures/` and its inputs,
results, and takeaways to `outputs/data/`.

| # | Notebook | What it shows |
|---|----------|---------------|
| 01 | [The Newsvendor](notebooks/01_the_newsvendor.ipynb) | The optimal single-period stock is the critical-ratio quantile of demand, not the mean; the gap grows with cost asymmetry and uncertainty. |
| 02 | [Safety Stock](notebooks/02_safety_stock.ipynb) | The buffer is a function of forecast error (σ), lead time, and service level — a simulation confirms the achieved service level, and distribution-based beats a flat rule. |
| 03 | [Facility Location](notebooks/03_facility_location.ipynb) | The capacitated facility-location MILP, verified against brute force, contrasted with nearest-site, and mined for capacity shadow prices (which site to expand). |
| 04 | [Network Flow](notebooks/04_network_flow.ipynb) | The transportation LP and its transshipment extension through warehouses; conservation verified, shadow prices read as the marginal value of capacity. |
| 05 | [Multi-Echelon](notebooks/05_multi_echelon.ipynb) | Risk pooling: consolidating safety stock upstream protects the network with less total inventory, because pooled demand is proportionally less variable. |
| 06 | [Bullwhip & Decisions](notebooks/06_bullwhip_and_decisions.ipynb) | Local order reactions amplify demand variance upstream; closes with the decision framework for the whole chain. |

---

## The Streamlit app

`make run` opens four tools, each backed by the same models the notebooks use:

1. **Newsvendor explorer** — set the costs and demand and watch the optimal quantile and
   the gap versus stock-to-mean update live.
2. **Safety-stock calculator** — set volatility, lead time, and service level and see the
   buffer per product against a flat rule.
3. **Facility-location map** — generate candidate sites and customers, solve, and see who
   opens, who they serve, and the capacity shadow prices.
4. **Bullwhip simulator** — change the chain's lead time and forecast window and watch the
   order swings amplify upstream.

---

## Repository layout

```
config/settings.yaml   Seeds, network sizes, cost ratios, lead times, service levels
src/
  config.py            Typed settings (pydantic-settings)
  inventory/           newsvendor · eoq · safety_stock · reorder_policy
  network/             facility_location (MILP) · transportation · transshipment · multi_echelon
  solvers/backends.py  The single solver seam (CBC / HiGHS)
  simulation/          demand generators · bullwhip
  evaluation/          cost_of_the_guess · service_level · sensitivity
  visualisation.py     Shared plotting helpers
  outputs.py           save_figure() -> PNG, save_json() -> JSON
app/streamlit_app.py   The four interactive tools
notebooks/             01–06
tests/                 One suite per model family
outputs/figures/       Generated PNGs      outputs/data/  Generated JSON
```

All data is synthetic, generated with known structure and seeded, so every scenario has
a computable optimal cost and a computable cost-of-the-guess. No external data, no
downloads.

---

## Related projects

This is part of a series of hands-on, CPU-only data-science projects. The ones most
relevant here:

- **[optimization_101](https://github.com/Dima806/optimization_101)** — the LP/MILP
  foundation this project applies to supply chains.
- **[threshold_lab](https://github.com/Dima806/threshold_lab)** — asymmetric costs decide
  the optimal action; the newsvendor is the same logic applied to inventory.
- **[forecasting_arena](https://github.com/Dima806/forecasting_arena)** — produces the
  demand forecasts that inventory optimization consumes.
- **[prediction_intervals_arena](https://github.com/Dima806/prediction_intervals_arena)**
  — the demand *distribution*, not the point forecast, is what inventory decisions need.
- **[timeseries_101](https://github.com/Dima806/timeseries_101)** — the properties of the
  time-ordered demand data these models sit on top of.
- **[bandits_101](https://github.com/Dima806/bandits_101)** — decision-making under
  uncertainty from the online-learning side.

---

## References

- Arrow, Harris & Marschak (1951). *Optimal Inventory Policy.* Econometrica. (newsvendor)
- Chopra & Meindl (2019). *Supply Chain Management: Strategy, Planning, and Operation.*
- Daskin (2013). *Network and Discrete Location: Models, Algorithms, and Applications.*
- Lee, Padmanabhan & Whang (1997). *The Bullwhip Effect in Supply Chains.* Sloan Mgmt Rev.
- Silver, Pyke & Thomas (2016). *Inventory and Production Management in Supply Chains.*

---

## License

[Apache-2.0](LICENSE).
