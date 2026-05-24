"""Tests for the creative_vision per-slide cost estimator (#113 AC1)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.cost_estimator import (  # noqa: E402
    TYPICAL_GATE_BAND,
    estimate_creative_vision_slide_cost,
    format_spend_summary_markdown,
    summarise_creative_vision_spend,
)
from src.creative_vision.cascade import TIER_COSTS  # noqa: E402


# ---------------------------------------------------------------------------
# estimate_creative_vision_slide_cost
# ---------------------------------------------------------------------------


def test_estimate_slide_cost_ollama_ceiling_is_free():
    """When the cascade can't escalate beyond Ollama, the slide is free.

    A degenerate case for testing — production decks always allow at least
    Flash 1K — but the estimator must not crash or compute negative cost.
    """
    band = estimate_creative_vision_slide_cost(allowed_ceiling="ollama")
    assert band["min_cost_usd"] == 0.0
    assert band["max_cost_usd"] == 0.0
    assert band["typical_gates"] == TYPICAL_GATE_BAND
    assert band["allowed_ceiling"] == "ollama"


def test_estimate_slide_cost_flash_1k_ceiling():
    """flash_1k ceiling: min is one Flash 1K render ($0.067); max is
    5*Ollama + 3*Flash 1K = 3 * $0.067 = $0.201."""
    band = estimate_creative_vision_slide_cost(allowed_ceiling="flash_1k")
    assert band["min_cost_usd"] == 0.067
    assert band["max_cost_usd"] == pytest.approx(0.201, abs=0.001)
    assert band["cost_band_str"] == "$0.07 - $0.20"


def test_estimate_slide_cost_pro_4k_ceiling_matches_dogfood_envelope():
    """pro_4k ceiling: should span the $0.20-$1.50 dogfood envelope.

    min = $0.240 (single Pro 4K shot after free Ollama)
    max = sum of caps × costs all the way up the ladder.
    """
    band = estimate_creative_vision_slide_cost(allowed_ceiling="pro_4k")
    assert band["min_cost_usd"] == 0.240
    # max = 5*0 + 3*0.067 + 3*0.101 + 3*0.151 + 2*0.134 + 2*0.134 + 1*0.240
    expected_max = 3 * 0.067 + 3 * 0.101 + 3 * 0.151 + 2 * 0.134 + 2 * 0.134 + 1 * 0.240
    assert band["max_cost_usd"] == pytest.approx(round(expected_max, 3), abs=0.001)
    # Sanity: the max ceiling falls within the documented dogfood envelope upper-bound area
    assert 1.0 < band["max_cost_usd"] < 2.0


def test_estimate_slide_cost_recraft_ceiling_uses_recraft_ladder():
    """When brand_fidelity='exact', the Recraft ladder is used and Recraft
    ceilings become reachable.

    Recraft Pro 2K ceiling: min $0.25, max sums Recraft ladder up to 2K.
    """
    band = estimate_creative_vision_slide_cost(
        allowed_ceiling="recraft_pro_2k", brand_fidelity="exact"
    )
    assert band["min_cost_usd"] == 0.25
    # max = 5*0 + 3*0.04 + 2*0.25 = 0.62
    assert band["max_cost_usd"] == pytest.approx(0.62, abs=0.001)


def test_estimate_slide_cost_rejects_recraft_ceiling_on_default_ladder():
    """Asking for a Recraft ceiling under non-exact brand_fidelity is a
    config error — the recraft ladder is not reachable from the default
    ladder, so the function must raise rather than silently use 0."""
    with pytest.raises(ValueError, match="not reachable"):
        estimate_creative_vision_slide_cost(
            allowed_ceiling="recraft_pro_2k", brand_fidelity="none"
        )


def test_estimate_slide_cost_rejects_unknown_tier():
    """Unknown tiers are a config error, not a fallback case."""
    with pytest.raises(ValueError, match="not reachable"):
        estimate_creative_vision_slide_cost(allowed_ceiling="quantum_5k")


def test_estimate_slide_cost_ladder_summary_shape():
    """ladder_summary is one row per reachable tier with the unit cost +
    iteration cap surfaced. The strategy-map skill needs this to show the
    per-tier breakdown when the operator asks why a slide is expensive."""
    band = estimate_creative_vision_slide_cost(allowed_ceiling="flash_2k")
    tiers = [row["tier"] for row in band["ladder_summary"]]
    assert tiers == ["ollama", "flash_1k", "flash_2k"]
    flash_1k_row = next(r for r in band["ladder_summary"] if r["tier"] == "flash_1k")
    assert flash_1k_row["unit_cost_usd"] == 0.067
    assert flash_1k_row["iteration_cap"] == 3


def test_estimate_slide_cost_typical_gates_is_dogfood_band():
    """The gate band is independent of ceiling — it's a dogfood-observed
    range, not derived from cascade caps. Pin it to TYPICAL_GATE_BAND so
    future changes are a deliberate decision, not a drift bug."""
    assert TYPICAL_GATE_BAND == (3, 7)
    band = estimate_creative_vision_slide_cost(allowed_ceiling="flash_1k")
    assert band["typical_gates"] == TYPICAL_GATE_BAND
    assert band["gate_band_str"] == "3-7"


def test_estimate_slide_cost_uses_default_tier_costs():
    """When cost_table is omitted, cascade.TIER_COSTS is read.

    Pins the post-AC6 reconciliation: pro_2k now $0.134 (not $0.193). A
    pro_2k ceiling band should reflect that.
    """
    band = estimate_creative_vision_slide_cost(allowed_ceiling="pro_2k")
    assert band["min_cost_usd"] == TIER_COSTS["pro_2k"]
    assert band["min_cost_usd"] == 0.134


# ---------------------------------------------------------------------------
# summarise_creative_vision_spend
# ---------------------------------------------------------------------------


def _strategy_map_with_slides(slides: list[dict]) -> dict:
    """Mini strategy-map fixture builder — only the fields the summariser reads."""
    return {"slides": slides}


def test_summarise_no_creative_vision_slides_returns_empty():
    smap = _strategy_map_with_slides([
        {"slide_number": 1, "strategy": "composed"},
        {"slide_number": 2, "strategy": "backdrop"},
    ])
    summary = summarise_creative_vision_spend(smap)
    assert summary["slide_count"] == 0
    assert summary["entries"] == []
    assert summary["total_min_cost_usd"] == 0.0
    assert summary["total_max_cost_usd"] == 0.0
    assert summary["total_gate_band"] == (0, 0)
    assert "No creative_vision slides" in summary["summary_markdown"]


def test_summarise_single_creative_vision_slide_pro_1k():
    smap = _strategy_map_with_slides([
        {"slide_number": 3, "strategy": "composed"},
        {
            "slide_number": 5,
            "strategy": "creative_vision",
            "creative_vision": {
                "vision_prose": "...",
                "allowed_ceiling": "pro_1k",
            },
        },
    ])
    summary = summarise_creative_vision_spend(smap)
    assert summary["slide_count"] == 1
    assert summary["entries"][0]["slide_number"] == 5
    assert summary["entries"][0]["allowed_ceiling"] == "pro_1k"
    assert summary["entries"][0]["min_cost_usd"] == 0.134
    assert summary["total_gate_band"] == (3, 7)


def test_summarise_multi_slide_sums_totals():
    smap = _strategy_map_with_slides([
        {
            "slide_number": 1,
            "strategy": "creative_vision",
            "creative_vision": {"vision_prose": "a", "allowed_ceiling": "flash_1k"},
        },
        {"slide_number": 2, "strategy": "composed"},
        {
            "slide_number": 3,
            "strategy": "creative_vision",
            "creative_vision": {"vision_prose": "b", "allowed_ceiling": "pro_4k"},
        },
    ])
    summary = summarise_creative_vision_spend(smap)
    assert summary["slide_count"] == 2
    # Two slides × 3-7 gates each
    assert summary["total_gate_band"] == (6, 14)
    # min = flash_1k min (0.067) + pro_4k min (0.240) = 0.307 → rounded to 0.31
    assert summary["total_min_cost_usd"] == pytest.approx(0.31, abs=0.005)
    # max sums to a substantial deck-level worst case
    assert summary["total_max_cost_usd"] > 1.5


def test_summarise_default_allowed_ceiling_is_pro_4k():
    """The schema default for allowed_ceiling is pro_4k. The summariser
    must honour that default when a slide omits the field."""
    smap = _strategy_map_with_slides([
        {
            "slide_number": 1,
            "strategy": "creative_vision",
            "creative_vision": {"vision_prose": "x"},  # no allowed_ceiling
        },
    ])
    summary = summarise_creative_vision_spend(smap)
    assert summary["entries"][0]["allowed_ceiling"] == "pro_4k"


def test_summarise_slide_brand_fidelity_routes_to_recraft_ladder():
    """A slide-level brand_fidelity='exact' overrides the default and lets
    the slide reach Recraft ceilings."""
    smap = _strategy_map_with_slides([
        {
            "slide_number": 1,
            "strategy": "creative_vision",
            "brand_fidelity": "exact",
            "creative_vision": {
                "vision_prose": "logo composition",
                "allowed_ceiling": "recraft_pro_4k",
            },
        },
    ])
    summary = summarise_creative_vision_spend(smap)
    assert summary["slide_count"] == 1
    assert summary["entries"][0]["allowed_ceiling"] == "recraft_pro_4k"
    assert summary["entries"][0]["min_cost_usd"] == 0.50


def test_summarise_markdown_includes_per_slide_rows_and_totals():
    """The operator-facing markdown is the surface the strategy-map skill
    actually displays. Verify it contains the per-slide rows AND a totals
    row."""
    smap = _strategy_map_with_slides([
        {
            "slide_number": 7,
            "strategy": "creative_vision",
            "creative_vision": {"vision_prose": "x", "allowed_ceiling": "pro_1k"},
        },
        {
            "slide_number": 11,
            "strategy": "creative_vision",
            "creative_vision": {"vision_prose": "y", "allowed_ceiling": "flash_1k"},
        },
    ])
    summary = summarise_creative_vision_spend(smap)
    md = summary["summary_markdown"]
    assert "| 7 |" in md
    assert "| 11 |" in md
    assert "`pro_1k`" in md
    assert "`flash_1k`" in md
    assert "Total (2 slides)" in md
    assert "3-7" in md
    assert "6-14" in md


def test_format_spend_summary_markdown_singular_slide_label():
    """A deck with exactly one creative_vision slide should NOT say 'Total
    (1 slides)' — small polish but easy regression."""
    md = format_spend_summary_markdown(
        entries=[
            {
                "slide_number": 1,
                "allowed_ceiling": "pro_1k",
                "cost_band_str": "$0.13 - $0.80",
                "gate_band_str": "3-7",
            }
        ],
        slide_count=1,
        total_min_cost_usd=0.13,
        total_max_cost_usd=0.80,
        total_gate_band=(3, 7),
    )
    assert "Total (1 slide)" in md
    assert "Total (1 slides)" not in md


def test_format_spend_summary_markdown_empty_entries():
    """Edge case: explicit empty entries should produce the no-slides message."""
    md = format_spend_summary_markdown(
        entries=[],
        slide_count=0,
        total_min_cost_usd=0.0,
        total_max_cost_usd=0.0,
        total_gate_band=(0, 0),
    )
    assert "No creative_vision slides" in md
