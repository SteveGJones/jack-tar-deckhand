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
    TIER_TO_PROVIDER_MODEL_RESOLUTION,
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
    # Issue #113 AC6: reconciled with cloud module 2026-05-24.
    # Google Nano Banana Pro 2K is priced same as Pro 1K ($0.134),
    # not $0.193 as the prior cascade table claimed.
    assert TIER_COSTS["pro_2k"] == 0.134
    assert TIER_COSTS["pro_4k"] == 0.240
    assert TIER_COSTS["recraft_standard_1k"] == 0.04
    assert TIER_COSTS["recraft_pro_2k"] == 0.25
    assert TIER_COSTS["recraft_pro_4k"] == 0.50


def test_tier_to_provider_model_resolution_covers_all_ladder_tiers():
    """Every tier in either ladder must have a (provider, model, resolution)
    tuple. ``mlx_edit`` (issue #143) is the one deliberate exception — it is
    NOT a ladder rung (it's a $0 tier-orthogonal edit action), so it is
    excluded from this ladder-coverage check but still present in the
    mapping (see the dedicated mlx_edit tests below)."""
    all_tiers = set(LADDER_DEFAULT) | set(LADDER_RECRAFT)
    assert set(TIER_TO_PROVIDER_MODEL_RESOLUTION) - {"mlx_edit"} == all_tiers


def test_tier_to_provider_model_resolution_ollama_is_local():
    """ollama is the local free tier — no cloud (provider, model, resolution)."""
    assert TIER_TO_PROVIDER_MODEL_RESOLUTION["ollama"] == (None, None, None)


def test_tier_to_provider_model_resolution_google_tiers():
    """All flash_* and pro_* tiers route through Google's two image models."""
    assert TIER_TO_PROVIDER_MODEL_RESOLUTION["flash_1k"] == (
        "google", "gemini-3.1-flash-image", "1K"
    )
    assert TIER_TO_PROVIDER_MODEL_RESOLUTION["flash_2k"] == (
        "google", "gemini-3.1-flash-image", "2K"
    )
    assert TIER_TO_PROVIDER_MODEL_RESOLUTION["flash_4k"] == (
        "google", "gemini-3.1-flash-image", "4K"
    )
    assert TIER_TO_PROVIDER_MODEL_RESOLUTION["pro_1k"] == (
        "google", "gemini-3-pro-image", "1K"
    )
    assert TIER_TO_PROVIDER_MODEL_RESOLUTION["pro_2k"] == (
        "google", "gemini-3-pro-image", "2K"
    )
    assert TIER_TO_PROVIDER_MODEL_RESOLUTION["pro_4k"] == (
        "google", "gemini-3-pro-image", "4K"
    )


def test_tier_to_provider_model_resolution_recraft_tiers():
    """Recraft tiers route to recraft-v4-standard / recraft-v4-pro."""
    assert TIER_TO_PROVIDER_MODEL_RESOLUTION["recraft_standard_1k"] == (
        "recraft", "recraft-v4-standard", "1K"
    )
    assert TIER_TO_PROVIDER_MODEL_RESOLUTION["recraft_pro_2k"] == (
        "recraft", "recraft-v4-pro", "2K"
    )
    assert TIER_TO_PROVIDER_MODEL_RESOLUTION["recraft_pro_4k"] == (
        "recraft", "recraft-v4-pro", "4K"
    )


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


from src.creative_vision.cascade import can_afford, next_tier  # noqa: E402


def test_can_afford_when_budget_covers_next_render():
    assert can_afford(remaining_budget_usd=0.50, tier="flash_2k") is True


def test_can_afford_false_when_budget_short():
    assert can_afford(remaining_budget_usd=0.10, tier="flash_2k") is False


def test_can_afford_ollama_always_true():
    assert can_afford(remaining_budget_usd=0.0, tier="ollama") is True


def test_next_tier_default_ladder():
    assert next_tier("flash_1k", LADDER_DEFAULT) == "flash_2k"


def test_next_tier_top_of_ladder_returns_none():
    assert next_tier("pro_4k", LADDER_DEFAULT) is None


def test_next_tier_clamped_by_allowed_ceiling():
    assert next_tier("flash_1k", LADDER_DEFAULT, allowed_ceiling="flash_4k") == "flash_2k"
    # At the ceiling, no further escalation
    assert next_tier("flash_4k", LADDER_DEFAULT, allowed_ceiling="flash_4k") is None


# --- mlx_edit — $0, tier-orthogonal action (issue #143, F-10) --------------


def test_mlx_edit_present_in_tier_to_provider_model_resolution():
    assert TIER_TO_PROVIDER_MODEL_RESOLUTION["mlx_edit"] == (None, None, None)


def test_mlx_edit_cost_is_zero():
    assert TIER_COSTS["mlx_edit"] == 0.0


def test_mlx_edit_never_returned_by_next_tier():
    """mlx_edit appears in NO ladder, so it can never be a next_tier
    candidate on either ladder, and it is not itself a valid 'current'
    tier to advance from."""
    assert next_tier("mlx_edit", LADDER_DEFAULT) is None
    assert next_tier("mlx_edit", LADDER_RECRAFT) is None
    assert "mlx_edit" not in LADDER_DEFAULT
    assert "mlx_edit" not in LADDER_RECRAFT


def test_can_afford_mlx_edit_always_true():
    assert can_afford(remaining_budget_usd=0.0, tier="mlx_edit") is True
