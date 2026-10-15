"""Risk pooling: centralizing safety stock cuts total inventory at equal service."""

from __future__ import annotations

import pytest

from src.network.multi_echelon import compare_pooling


def test_pooling_reduces_total_safety_stock():
    sigmas = [20.0, 25.0, 30.0, 15.0, 22.0]
    result = compare_pooling(sigmas, lead_time=4.0, service_level=0.95)
    assert result.centralized < result.decentralized
    assert result.savings > 0.0
    assert 0.0 < result.pooling_factor < 1.0


def test_single_node_has_no_pooling_benefit():
    result = compare_pooling([30.0], lead_time=4.0, service_level=0.95)
    assert result.centralized == pytest.approx(result.decentralized)
    assert result.pooling_factor == pytest.approx(1.0)
