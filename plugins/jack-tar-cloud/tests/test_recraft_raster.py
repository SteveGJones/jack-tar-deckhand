"""Tests for Recraft V4 raster provider — cost helpers, dual-path generation,
4K via Creative Upscale chain."""
import os
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.generate_cloud_image import (
    estimate_recraft_cost,
    ProviderResolutionUnsupportedError,
)


def test_recraft_cost_1k_standard():
    assert estimate_recraft_cost(tier='standard', resolution='1K') == 0.04


def test_recraft_cost_2k_pro():
    assert estimate_recraft_cost(tier='pro', resolution='2K') == 0.25


def test_recraft_cost_4k_chain():
    """4K = generate at 2K Pro ($0.25) + Creative Upscale (~$0.25) = $0.50."""
    assert estimate_recraft_cost(tier='pro', resolution='4K') == 0.50


def test_recraft_cost_standard_rejects_4k():
    """Standard tier doesn't support 4K — caller is expected to upgrade tier."""
    with pytest.raises(ValueError, match='standard.*4K'):
        estimate_recraft_cost(tier='standard', resolution='4K')


def test_recraft_cost_unknown_tier():
    with pytest.raises(ValueError, match='Unknown'):
        estimate_recraft_cost(tier='ultra', resolution='1K')


def test_recraft_upscale_cost_override_via_env(monkeypatch):
    """RECRAFT_UPSCALE_COST_USD env var overrides the assumed parity price.

    Used to hot-fix the 4K chain cost if the upscale price isn't the assumed
    $0.25. See spike report for context."""
    monkeypatch.setenv('RECRAFT_UPSCALE_COST_USD', '0.30')
    cost_4k = estimate_recraft_cost(tier='pro', resolution='4K')
    assert cost_4k == 0.55  # 0.25 (2K) + 0.30 (override upscale)
