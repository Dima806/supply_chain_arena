# CLAUDE.md — supply_chain_arena

Guidance for Claude Code (and any contributor) working in this repository.

---

## 1. What this project is

A hands-on tour of the optimization models that run the physical economy, built to prove a single thesis:

> **Core supply-chain decisions are exact optimization problems, not spreadsheet judgment calls.**

Where to put warehouses, which site serves each customer, how much stock to hold, and when to reorder each have a *provably cheapest* answer. The intuitive rules people actually use — stock to the forecast, flat "two weeks of safety stock" everywhere, assign each customer to the nearest site — are systematically wrong, and the gap is a fixed, computable amount of money.

Format: a GitHub repo with **6 Jupyter notebooks**, a **`src/` library**, and a **lightweight Streamlit app**, all runnable inside a **2-CPU / 8 GB GitHub Codespace with no GPU**.

Audience: data scientists who forecast demand but have never optimized the decisions the forecast feeds. The forecast is the *input*; the decision it feeds is the *value*. This repo is the resume-gap closer for operations research / supply chain.

**Current status:** the `src/` library, the 27-test suite, the Streamlit app, and all six notebooks are implemented. `make ci` (sync + lint + test) and `make notebooks` both pass green.

### The showpiece claim (newsvendor)

Stock a product for a season when demand is uncertain, each unsold unit is a write-off, each short unit is a lost sale. Intuition says stock to expected demand. The newsvendor optimum is a **quantile** of the demand distribution set by the **critical ratio** `underage / (underage + overage)`. If a stockout costs 3× a leftover, the optimum is the 75th percentile, not the 50th. Stocking to the mean leaves computable profit on the table every season, and the gap grows with both demand uncertainty and cost asymmetry.

---

## 2. Non-negotiable invariants

These are the things that make the project's promise true. Do not violate them.

- **Every optimum is verified**, never asserted by eye:
  - Newsvendor & safety-stock optima → checked against their **closed-form** formulas.
  - Facility-location MILP → checked against **brute force** at small test sizes.
  - Network flow → **flow conservation** holds and optimal cost is verified.
  - Bullwhip → order-variance **amplification upstream is asserted** in a test.
- **Solvers are 100% open-source. No commercial solver, no license, no activation.** Only `pulp` (CBC), `highspy` (HiGHS, MIT), and `ortools`. Every result must reproduce on a bare Codespace, and CI runs the full set.
- **All data is synthetic and seeded** with known structure, so the optimal cost and the cost-of-the-guess are both computable. No external data, no downloads.
- **Everything solves instantly on 2 CPUs.** Networks are tens of sites/customers; simulations are lightweight; each notebook runs in **< 5 minutes**.
- **Demand is a distribution, not a point.** Any decision that consumes a forecast consumes its spread (σ), not just its mean.
- **The cost-of-the-guess is always measured**, not just the optimum. Optimal vs. stock-to-mean, vs. flat safety stock, vs. nearest-site — each contrast is quantified.

---

## 3. Stack & environment

- **Python 3.11+** (uv currently resolves the venv to 3.14; every dependency has wheels). Package manager is **`uv`** — never `pip`, never a bare `python`/`pytest`; always `uv run ...`.
- **No GPU.** Constraint target: 2 CPU / 8 GB.
- Core deps: `pulp` (+CBC), `highspy` (HiGHS), `ortools`, `scipy`, `numpy`, `pandas`, `matplotlib`, `plotly`, `streamlit`, `pydantic`, `pydantic-settings`, `pyyaml`. **`pulp` is pinned `<3`**: PuLP 4.x is a breaking API rewrite (no `PULP_CBC_CMD`, new `LpVariable`); the classic LP/MILP API lives in the 2.x line.
- Dev deps: `pytest`, `ruff`, `ty`, `jupyter`, `ipykernel`, `nbconvert`, `nbclient`.
- Lint/format: **ruff** (line length 99, `E501` ignored; rule set `E,F,W,I,UP,N,B,A,SIM,PTH`). Type check: **ty** (over `src/`).
- Config lives in `config/settings.yaml` (network sizes, cost ratios, lead times, service levels, seeds) and is loaded through `src/config.py` using **pydantic-settings**. Read parameters from config — do not hardcode seeds, sizes, or cost ratios in notebooks or `src/`.

Builds on the shared Dima806 series — [optimization_101](https://github.com/Dima806/optimization_101) (the LP/MILP foundation), [threshold_lab](https://github.com/Dima806/threshold_lab) (asymmetric-cost logic, the same principle as the newsvendor), [forecasting_arena](https://github.com/Dima806/forecasting_arena) (the demand forecasts this project consumes), and [prediction_intervals_arena](https://github.com/Dima806/prediction_intervals_arena) (the demand distribution inventory decisions actually need). The README's *Related projects* section has the full list.

---

## 4. Repository structure

```
config/settings.yaml          Network sizes, cost ratios, lead times, service levels, seeds
src/
  config.py                   pydantic-settings loader for settings.yaml
  inventory/
    newsvendor.py             Critical-ratio quantile, expected cost, vs stock-to-mean
    eoq.py                    Economic order quantity (the reorder-quantity classic)
    safety_stock.py           Service-level safety stock from demand sigma and lead time
    reorder_policy.py         (s, S) and (R, Q) policies simulated
  network/
    facility_location.py      Capacitated facility location (MILP)
    transportation.py         Transportation LP (plants -> warehouses -> customers)
    transshipment.py          Multi-echelon flow with intermediate nodes
    multi_echelon.py          Stock positioning across echelons (risk pooling)
  solvers/
    backends.py               PuLP/CBC, HiGHS (highspy), OR-Tools — all open-source
  simulation/
    demand.py                 Demand generators (stationary, seasonal, intermittent)
    bullwhip.py               Beer-game order amplification across a chain
  evaluation/
    cost_of_the_guess.py      Optimal vs intuitive (stock-to-mean, flat safety stock, nearest-site)
    service_level.py          Fill rate, stockout probability achieved
    sensitivity.py            Shadow prices on capacity; cost vs cost-ratio and uncertainty
  visualisation.py            Shared plotting helpers
  outputs.py                  save_figure() -> PNG, save_json() -> JSON (numpy/dataclass aware)
app/streamlit_app.py          Newsvendor explorer, safety-stock calc, facility map, bullwhip sim
notebooks/01..06              See section 5
tests/                        One test file per model family; verifies the invariants above
outputs/figures/             Generated PNG figures (do not hand-edit)
outputs/data/                Generated JSON — every notebook's inputs, results, and takeaways
```

### Layering rules

- `src/solvers/backends.py` is the single place that knows about solver APIs. Network models call into it; they should not import `pulp`/`highspy`/`ortools` scattered around.
- `src/evaluation/` compares optimal vs. intuitive — it imports from `inventory/` and `network/`, never the reverse.
- `src/simulation/demand.py` produces demand distributions; `inventory/` and `evaluation/` consume them.
- Notebooks and the Streamlit app are **thin**: they import from `src/`, set parameters, and visualize. Model logic lives in `src/`, not in cells.

---

## 5. The six notebooks (build-up order)

The narrative builds strictly in this order; each notebook runs < 5 min.

1. **`01_the_newsvendor.ipynb`** — the showpiece. Stock-to-mean baseline → critical-ratio optimum (a quantile above the mean when stockouts cost more). Compute both expected costs, show the gap, sweep cost ratio and uncertainty and watch it grow. Same asymmetric-cost logic as `threshold_lab`.
2. **`02_safety_stock.ipynb`** — from forecast error to inventory buffer. Service-level formula ties the buffer to demand σ, lead time, target fill rate. Flat "N weeks" over-protects stable items and under-protects volatile ones; distribution-based safety stock holds **less total inventory at higher service**. Bridges to `forecasting_arena` / `prediction_intervals_arena`.
3. **`03_facility_location.ipynb`** — capacitated facility-location MILP: which sites to open (binary, fixed cost) + demand assignment (capacity). Solve exactly, verify vs brute force, contrast with nearest-site heuristic. Extract **capacity shadow prices** → which facility to expand.
4. **`04_network_flow.ipynb`** — transportation LP (sources → sinks, respecting supply/demand) + transshipment through intermediate warehouses. Conservation verified; shadow prices on supply/demand read as marginal value of capacity.
5. **`05_multi_echelon.ipynb`** — where to hold stock across supplier → DC → store. **Risk pooling**: centralizing safety stock upstream protects the network with less total inventory, because pooled demand is proportionally less variable.
6. **`06_bullwhip_and_decisions.ipynb`** — bullwhip simulation: small customer-end variability amplifies into violent upstream order swings; measure amplification stage by stage. Closes with the decision framework (newsvendor for single-period; EOQ/(s,S) for repeated; distribution-based safety stock always; facility MILP for network design; global over local view).

---

## 6. Commands (via Makefile)

Always use the Makefile targets; they wrap `uv run`.

| Command | What it does |
|---|---|
| `make setup` | First-time: install uv if missing, `uv sync --all-extras`, register Jupyter kernel |
| `make sync` | Sync deps (`uv sync --all-extras`) |
| `make lint` | `format` + `check` + `typecheck` |
| `make format` | `ruff format` over `src/ tests/ app/` |
| `make check` | `ruff check --fix` over `src/ tests/ app/` |
| `make typecheck` | `ty check src/` |
| `make test` | `uv run pytest` |
| `make test-cov` | pytest with coverage |
| `make notebooks` | Execute all notebooks (nbconvert, 300s timeout each) |
| `make run` | Streamlit app on port 8501 |
| `make lab` | JupyterLab on port 8888 |
| `make clean` / `make reset` | Clean caches / also remove `.venv` |
| `make ci` | `sync` + `lint` + `test` (what CI runs) |
| `make dev` | `lint` + `test` (fast local loop) |

**Definition of done for a change:** `make lint` and `make test` pass with zero errors, and if a notebook is touched, `make notebooks` completes it in < 5 min.

---

## 7. Conventions when writing code

- Put model logic in `src/`; keep notebooks and `app/` thin.
- State inventory conventions **explicitly** per model (lead-time demand, review period, units) and back them with a simulation test that confirms the achieved service level matches the target — the formula is validated, not taken on faith.
- Prefer closed-form where one exists (newsvendor, EOQ, safety stock); use a solver only where the problem is combinatorial (facility location, flows).
- Route all solver calls through `src/solvers/backends.py`; keep a model solvable by more than one open backend where practical.
- Seed everything from config; a fresh checkout must reproduce every number.
- Notebooks persist every artefact through `src/outputs.py`: figures via `save_figure()` to `outputs/figures/*.png`, and all textual/numerical inputs, results, and takeaways via `save_json()` to `outputs/data/*.json`. Don't hand-edit generated files.
- `make notebooks` executes notebooks in place (`--inplace`), so committed notebooks carry rendered outputs and no `*.nbconvert.ipynb` duplicates appear.
- Match surrounding style: ruff config is authoritative; line length 99.

---

## 8. Success criteria (what tests and notebooks must show)

- Newsvendor optimum matches the closed-form critical ratio (asserted); gap vs stock-to-mean quantified and growing with asymmetry/uncertainty.
- Safety-stock achieved service level matches target fill rate in simulation; distribution-based beats flat (lower inventory, equal-or-higher service).
- Facility MILP optimum matches brute force at test size (asserted); savings vs nearest-site quantified; capacity shadow prices extracted and interpreted.
- Network flow: conservation holds, optimal cost verified.
- Risk pooling: centralized stock cuts total inventory at equal service.
- Bullwhip: order variance amplifies upstream (asserted).
- All solvers open-source (verified); all notebooks < 5 min on 2 CPU.

---

## 9. Token rules

- **Caveman mode: ON.** Code-first; keep prose minimal in working exchanges. (A terse caveman skill lives at `.claude/skills/caveman.md`.)
- `/compact` at notebook boundaries.
- This document is the detailed reference; the working style stays lean.
