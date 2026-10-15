"""Persist notebook outputs: figures as PNG, inputs and results as JSON.

Every notebook writes its figures to ``outputs/figures/`` and its textual and
numerical inputs and results to ``outputs/data/`` through these helpers, so the
artefacts are regenerated deterministically.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import numpy as np
from matplotlib.figure import Figure

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
FIGURE_DIR = OUTPUT_DIR / "figures"
DATA_DIR = OUTPUT_DIR / "data"


def _to_jsonable(obj: Any) -> Any:
    """Recursively convert numpy types, arrays, and dataclasses to JSON-native values."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {key: _to_jsonable(value) for key, value in dataclasses.asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(key): _to_jsonable(value) for key, value in obj.items()}
    if isinstance(obj, list | tuple):
        return [_to_jsonable(value) for value in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    return obj


def save_figure(fig: Figure, name: str, *, dpi: int = 150) -> Path:
    """Save a matplotlib figure as ``outputs/figures/<name>.png``."""
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURE_DIR / f"{name}.png"
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    return path


def save_json(data: Any, name: str) -> Path:
    """Save inputs/results as pretty-printed ``outputs/data/<name>.json``."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{name}.json"
    path.write_text(json.dumps(_to_jsonable(data), indent=2))
    return path
