"""The single place that knows about solver APIs.

All backends are open-source: CBC (bundled with PuLP) and HiGHS (via highspy).
Network models build a ``pulp.LpProblem`` and hand it here; they do not import
solver packages directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import pulp


class Backend(StrEnum):
    """Available open-source solver backends."""

    CBC = "cbc"
    HIGHS = "highs"


@dataclass(frozen=True)
class SolveResult:
    """Outcome of a solve: status string and objective value (``None`` if unsolved)."""

    status: str
    objective: float | None


def _make_solver(backend: Backend, *, msg: bool) -> Any:
    if backend is Backend.HIGHS:
        try:
            return pulp.HiGHS(msg=msg)
        except Exception:  # noqa: BLE001 - fall back to the always-present CBC
            return pulp.PULP_CBC_CMD(msg=msg)
    return pulp.PULP_CBC_CMD(msg=msg)


def solve(problem: Any, backend: Backend = Backend.CBC, *, msg: bool = False) -> SolveResult:
    """Solve a PuLP problem in place and return its status and objective value."""
    solver = _make_solver(backend, msg=msg)
    problem.solve(solver)
    status = pulp.LpStatus[problem.status]
    objective = pulp.value(problem.objective)
    return SolveResult(status=status, objective=None if objective is None else float(objective))
