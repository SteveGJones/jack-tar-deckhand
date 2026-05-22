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


from src.creative_vision.cascade import detect_plateau  # noqa: E402


def _scores(entity=80, spatial=80, style=80, quality=80, composition=80):
    return {
        "entity_fidelity": entity,
        "spatial_fidelity": spatial,
        "style_fidelity": style,
        "quality": quality,
        "composition": composition,
    }


def test_plateau_false_with_improvement():
    history = [_scores(entity=60), _scores(entity=72)]
    assert detect_plateau(history) is False


def test_plateau_true_when_no_axis_improves_by_5():
    history = [_scores(entity=60, spatial=60), _scores(entity=62, spatial=63), _scores(entity=63, spatial=64)]
    # max delta is 3 on any axis — under 5-point threshold
    assert detect_plateau(history) is True


def test_plateau_false_with_only_one_prior_iteration():
    # Need at least 2 priors to compute a window — return False
    assert detect_plateau([_scores()]) is False


def test_plateau_true_when_scores_degrade():
    history = [_scores(entity=80, spatial=80), _scores(entity=78, spatial=78), _scores(entity=77, spatial=79)]
    # No 5-point improvement on any axis across 2 iterations
    assert detect_plateau(history) is True


def test_plateau_false_when_any_axis_improves_by_5_plus():
    history = [_scores(entity=70), _scores(entity=70), _scores(entity=76)]
    assert detect_plateau(history) is False
