"""Tests for the creative_vision cascade module (tier ladder, plateau, budget)."""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.cascade import (  # noqa: E402
    DEFAULT_BUDGET_USD,
    DEFAULT_ITERATION_CAPS,
    LADDER_DEFAULT,
    LADDER_RECRAFT,
    TIER_COSTS,
    ladder_for,
)


def test_ladder_for_default_brand_fidelity():
    assert ladder_for("none") == LADDER_DEFAULT
    assert ladder_for("approximate") == LADDER_DEFAULT


def test_ladder_for_exact_brand_fidelity_returns_recraft():
    assert ladder_for("exact") == LADDER_RECRAFT


def test_ladder_default_order_matches_spec():
    assert LADDER_DEFAULT == [
        "ollama", "flash_1k", "flash_2k", "flash_4k",
        "pro_1k", "pro_2k", "pro_4k",
    ]


def test_ladder_recraft_order_matches_spec():
    assert LADDER_RECRAFT == [
        "ollama", "recraft_standard_1k", "recraft_pro_2k", "recraft_pro_4k",
    ]


def test_tier_costs_match_spec():
    assert TIER_COSTS["ollama"] == 0.0
    assert TIER_COSTS["flash_1k"] == 0.067
    assert TIER_COSTS["flash_2k"] == 0.101
    assert TIER_COSTS["flash_4k"] == 0.151
    assert TIER_COSTS["pro_1k"] == 0.134
    assert TIER_COSTS["pro_2k"] == 0.193
    assert TIER_COSTS["pro_4k"] == 0.240
    assert TIER_COSTS["recraft_standard_1k"] == 0.04
    assert TIER_COSTS["recraft_pro_2k"] == 0.25
    assert TIER_COSTS["recraft_pro_4k"] == 0.50


def test_default_iteration_caps_match_spec():
    assert DEFAULT_ITERATION_CAPS == {
        "ollama": 5,
        "flash_1k": 3, "flash_2k": 3, "flash_4k": 3,
        "pro_1k": 2, "pro_2k": 2, "pro_4k": 1,
        "recraft_standard_1k": 3, "recraft_pro_2k": 2, "recraft_pro_4k": 1,
    }


def test_default_budget_matches_spec():
    assert DEFAULT_BUDGET_USD == 1.00
