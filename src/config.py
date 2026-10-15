"""Typed configuration loaded from ``config/settings.yaml`` via pydantic-settings.

Read parameters from here rather than hardcoding seeds, sizes, or cost ratios in
notebooks and ``src/``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"


class StationaryDemand(BaseModel):
    mean: float
    std: float


class SeasonalDemand(BaseModel):
    mean: float
    amplitude: float
    period: int
    noise_std: float


class IntermittentDemand(BaseModel):
    demand_prob: float
    demand_mean: float
    demand_std: float


class DemandConfig(BaseModel):
    stationary: StationaryDemand
    seasonal: SeasonalDemand
    intermittent: IntermittentDemand


class NewsvendorConfig(BaseModel):
    underage_cost: float
    overage_cost: float
    demand_mean: float
    demand_std: float


class EOQConfig(BaseModel):
    demand_rate: float
    order_cost: float
    holding_cost: float


class SafetyStockConfig(BaseModel):
    service_level: float
    lead_time: float
    review_period: float
    flat_weeks: float


class FacilityLocationConfig(BaseModel):
    n_sites: int
    n_customers: int


class BullwhipConfig(BaseModel):
    n_stages: int
    n_periods: int
    forecast_window: int
    lead_time: int


class Settings(BaseSettings):
    """Root configuration. Nested dicts in the YAML coerce into the models above."""

    model_config = SettingsConfigDict(env_prefix="SCA_", extra="forbid")

    seed: int
    demand: DemandConfig
    newsvendor: NewsvendorConfig
    eoq: EOQConfig
    safety_stock: SafetyStockConfig
    facility_location: FacilityLocationConfig
    bullwhip: BullwhipConfig


def load_settings(path: Path | None = None) -> Settings:
    """Load and validate settings from a YAML file (defaults to ``CONFIG_PATH``)."""
    config_path = path or CONFIG_PATH
    data: dict[str, Any] = yaml.safe_load(config_path.read_text())
    return Settings(**data)


SETTINGS = load_settings()
