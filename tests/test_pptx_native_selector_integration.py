"""Tests for Phase 5 selector integration helpers."""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# is_pptx_native_candidate
# ---------------------------------------------------------------------------

def test_flowchart_with_5_steps_is_eligible():
    from src.smartart_pptx_native.selector_integration import is_pptx_native_candidate

    result = is_pptx_native_candidate(
        body_points=["Research", "Design", "Build", "Test", "Ship"],
        graphic_type="flowchart",
        enrichment_tier="pure_programmatic",
    )
    assert result.eligible is True
    assert result.layout_id == "process1"
    assert result.confidence > 0.7


def test_cycle_with_6_stages_is_eligible():
    from src.smartart_pptx_native.selector_integration import is_pptx_native_candidate

    result = is_pptx_native_candidate(
        body_points=["Plan", "Build", "Test", "Deploy", "Monitor", "Learn"],
        graphic_type="cycle",
        enrichment_tier="pure_programmatic",
    )
    assert result.eligible is True
    assert result.layout_id == "cycle2"


def test_org_chart_with_small_tree_is_eligible():
    from src.smartart_pptx_native.selector_integration import is_pptx_native_candidate

    result = is_pptx_native_candidate(
        body_points=["CEO", "CTO", "CFO", "Backend Lead", "Frontend Lead"],
        graphic_type="org_chart",
        enrichment_tier="pure_programmatic",
    )
    assert result.eligible is True
    assert result.layout_id == "orgChart1"


def test_unsupported_graphic_type_is_ineligible():
    from src.smartart_pptx_native.selector_integration import is_pptx_native_candidate

    result = is_pptx_native_candidate(
        body_points=["S", "W", "O", "T"],
        graphic_type="swot",
        enrichment_tier="pure_programmatic",
    )
    assert result.eligible is False
    assert result.layout_id is None
    assert any("no pptx_native layout mapping" in r for r in result.reasons)


def test_ai_background_tier_is_ineligible():
    from src.smartart_pptx_native.selector_integration import is_pptx_native_candidate

    result = is_pptx_native_candidate(
        body_points=["A", "B", "C"],
        graphic_type="flowchart",
        enrichment_tier="ai_background",
    )
    assert result.eligible is False
    assert any("AI enrichment" in r for r in result.reasons)


def test_too_few_body_points_is_ineligible():
    from src.smartart_pptx_native.selector_integration import is_pptx_native_candidate

    result = is_pptx_native_candidate(
        body_points=["Only one"],
        graphic_type="flowchart",
        enrichment_tier="pure_programmatic",
    )
    assert result.eligible is False
    assert any("at least 2" in r for r in result.reasons)


def test_too_many_body_points_is_ineligible():
    from src.smartart_pptx_native.selector_integration import is_pptx_native_candidate

    # process1 maxes at 9
    result = is_pptx_native_candidate(
        body_points=[f"Step {i}" for i in range(12)],
        graphic_type="flowchart",
        enrichment_tier="pure_programmatic",
    )
    assert result.eligible is False
    assert any("at most 9" in r for r in result.reasons)
    assert any("custom_svg" in r for r in result.reasons)


def test_label_too_long_is_ineligible():
    from src.smartart_pptx_native.selector_integration import is_pptx_native_candidate

    result = is_pptx_native_candidate(
        body_points=["Short", "X" * 30, "OK"],  # process1 max_label=24
        graphic_type="flowchart",
        enrichment_tier="pure_programmatic",
    )
    assert result.eligible is False
    assert any("exceed" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# score_pptx_native_candidate
# ---------------------------------------------------------------------------

def test_score_is_highest_at_sweet_spot():
    from src.smartart_pptx_native.layouts import catalog
    from src.smartart_pptx_native.selector_integration import score_pptx_native_candidate

    entry = catalog.get_entry("process1")
    # process1: min=2, max=9, sweet_spot = 5.5
    # At n=5 or n=6, distance is smallest, score should be highest
    sweet_score = score_pptx_native_candidate(5, entry)
    min_score = score_pptx_native_candidate(2, entry)
    max_score = score_pptx_native_candidate(9, entry)

    assert sweet_score > min_score
    assert sweet_score > max_score
    assert sweet_score <= 0.85  # capped


def test_score_never_exceeds_cap():
    from src.smartart_pptx_native.layouts import catalog
    from src.smartart_pptx_native.selector_integration import score_pptx_native_candidate

    entry = catalog.get_entry("cycle2")
    for n in range(entry["min_nodes"], entry["max_nodes"] + 1):
        score = score_pptx_native_candidate(n, entry)
        assert 0 <= score <= 0.85


def test_score_never_negative():
    from src.smartart_pptx_native.layouts import catalog
    from src.smartart_pptx_native.selector_integration import score_pptx_native_candidate

    entry = catalog.get_entry("orgChart1")
    # Even at the extremes, score should be >= 0
    assert score_pptx_native_candidate(entry["min_nodes"], entry) >= 0
    assert score_pptx_native_candidate(entry["max_nodes"], entry) >= 0


# ---------------------------------------------------------------------------
# format_selector_rationale
# ---------------------------------------------------------------------------

def test_format_rationale_interpolates_n_first_last():
    from src.smartart_pptx_native.selector_integration import (
        format_selector_rationale,
        is_pptx_native_candidate,
    )

    body_points = ["Plan", "Execute", "Review"]
    result = is_pptx_native_candidate(
        body_points, "flowchart", "pure_programmatic"
    )
    rationale = format_selector_rationale(result, body_points)
    assert "3" in rationale  # {n}
    assert "Plan" in rationale  # {first}
    assert "Review" in rationale  # {last}
    assert "{n}" not in rationale  # not left as placeholder
    assert "{first}" not in rationale
    assert "{last}" not in rationale


def test_format_rationale_for_ineligible_result():
    from src.smartart_pptx_native.selector_integration import (
        CandidacyResult,
        format_selector_rationale,
    )

    result = CandidacyResult(
        eligible=False, layout_id=None, confidence=0.0, reasons=[]
    )
    rationale = format_selector_rationale(result, [])
    assert "not eligible" in rationale


# ---------------------------------------------------------------------------
# Agent prompt contract tests
# ---------------------------------------------------------------------------

def test_agent_prompt_mentions_pptx_native():
    """The smartart-selector agent's definition must document when
    to recommend pptx_native. Phase 5's main deliverable for the
    agent is updating its prompt."""
    from pathlib import Path

    prompt_path = (
        Path(__file__).resolve().parent.parent
        / "plugins" / "jack-tar-deckhand" / "agents" / "smartart-selector.md"
    )
    content = prompt_path.read_text(encoding="utf-8")

    assert "pptx_native" in content
    assert "editable" in content.lower()
    assert "pure_programmatic" in content
    # Must document the three v1 layouts by name
    assert "flowchart" in content.lower()
    assert "cycle" in content.lower()
    assert "org_chart" in content.lower() or "orgChart" in content
    # Must reference the catalog doc as authoritative source
    assert "catalog" in content.lower()
