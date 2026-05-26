"""End-to-end GA flow exerciser for creative_vision (#113).

This test is the deterministic surrogate for the multi-slide dogfood — the
live dogfood gates on operator review of real renders (F12) and so cannot
run in CI, but the *structural* path through the GA flow can. Every AC1–AC4
helper is invoked in the order the deck-conductor would invoke them on a
multi-slide creative_vision deck:

    1. AC1 — strategy-map cost surface (summarise_creative_vision_spend)
       runs BEFORE strategy approval and shows the per-slide cost table.
    2. AC4 — creative_anchors loaded for the deck; per-slide eligibility
       resolved; section formatted for the Brief input blob.
    3. AC2 — Creative Sprint phase walks every creative_vision slide before
       composed-slide work; resumable via per-slide manifests.
    4. AC3 — should_fire_operator_gate fires at every iteration for
       creative_vision slides (free→cost AND cost→cost), and only at
       free→cost for the composed slide.

The CreativeVisionManifest writes here use the real manifest helpers — no
mocks — so any drift between the helpers and the sprint reader is caught.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.anchors import (  # noqa: E402
    anchors_for_slide,
    anchors_path,
    format_anchors_for_brief,
    load_anchors,
)
from src.creative_vision.brief import build_brief_input  # noqa: E402
from src.creative_vision.cost_estimator import (  # noqa: E402
    summarise_creative_vision_spend,
)
from src.creative_vision.manifest import (  # noqa: E402
    finalise_manifest,
    initialise_manifest,
    save_manifest,
)
from src.creative_vision.orchestrator import (  # noqa: E402
    should_fire_operator_gate,
)
from src.creative_vision.sprint import (  # noqa: E402
    creative_sprint_progress,
    format_sprint_progress_markdown,
    is_sprint_complete,
    next_unaccepted_slide,
)


def _ga_flow_strategy_map() -> dict:
    """A small multi-slide strategy map exercising the GA flow.

    - Slide 1: creative_vision, ceiling pro_1k. Sun-phases-like (single moment).
    - Slide 2: composed (baseline non-creative_vision slide).
    - Slide 3: creative_vision, ceiling pro_4k. Naval-academy-like (single moment).
    - Slide 5: creative_vision, ceiling flash_1k, references shared character anchor.
    """
    return {
        "slides": [
            {
                "slide_number": 1,
                "strategy": "creative_vision",
                "creative_vision": {
                    "vision_prose": "Sun-phases horizontal progression",
                    "allowed_ceiling": "pro_1k",
                },
            },
            {"slide_number": 2, "strategy": "composed"},
            {
                "slide_number": 3,
                "strategy": "creative_vision",
                "creative_vision": {
                    "vision_prose": "Agentic Naval Academy ceremony",
                    "allowed_ceiling": "pro_4k",
                },
            },
            {
                "slide_number": 5,
                "strategy": "creative_vision",
                "creative_vision": {
                    "vision_prose": "The Customer at his desk reviewing the invoice",
                    "allowed_ceiling": "flash_1k",
                },
            },
        ],
    }


def _ga_flow_anchors() -> dict:
    """Anchors file with one deck-wide style anchor and one slide-5 character.

    Exercises both eligibility paths: deck-wide (appears_in_slides omitted)
    AND slide-specific.
    """
    return {
        "schema_version": "1.0.0",
        "deck_brief": "1980s Wall Street cinematic style throughout",
        "anchors": [
            {
                "name": "The Customer",
                "kind": "character",
                "description": (
                    "Mid-50s man, salt-and-pepper hair, tortoiseshell glasses, "
                    "navy double-breasted blazer with crested buttons"
                ),
                "appears_in_slides": [5],
                "negative_traits": ["beard"],
            },
            {
                "name": "Period Palette",
                "kind": "style_anchor",
                "description": "Saturated 35mm film grain, deep amber + cyan + bronze",
            },
        ],
    }


def test_ga_flow_step_1_cost_surface_runs_before_approval():
    """AC1: per-slide cost summariser must produce one entry per
    creative_vision slide, with the deck totals row aggregating them."""
    smap = _ga_flow_strategy_map()
    summary = summarise_creative_vision_spend(smap)

    assert summary["slide_count"] == 3  # slides 1, 3, 5 — slide 2 is composed
    slide_numbers = [e["slide_number"] for e in summary["entries"]]
    assert slide_numbers == [1, 3, 5]

    ceilings = {e["slide_number"]: e["allowed_ceiling"] for e in summary["entries"]}
    assert ceilings == {1: "pro_1k", 3: "pro_4k", 5: "flash_1k"}

    # Gate band scales with creative_vision slide count
    assert summary["total_gate_band"] == (3 * 3, 3 * 7)  # (9, 21)

    # Markdown surfaces per-slide AND totals row
    md = summary["summary_markdown"]
    assert "| 1 |" in md and "| 3 |" in md and "| 5 |" in md
    assert "Total (3 slides)" in md


def test_ga_flow_step_2_anchors_load_and_format_per_slide(tmp_path):
    """AC4: anchors loader returns a validated dict; per-slide eligibility
    filters correctly; the formatted section flows into build_brief_input
    before the prose."""
    # Write the anchors file at the deck root
    with open(anchors_path(str(tmp_path)), "w") as f:
        json.dump(_ga_flow_anchors(), f)

    anchors_doc = load_anchors(str(tmp_path))
    assert anchors_doc is not None
    assert anchors_doc["deck_brief"] == "1980s Wall Street cinematic style throughout"

    # Slide 1 (sun-phases) is not in The Customer's appears_in_slides, so it
    # only sees Period Palette (deck-wide).
    slide_1_eligible = anchors_for_slide(anchors_doc, slide_number=1)
    names = [a["name"] for a in slide_1_eligible]
    assert "Period Palette" in names
    assert "The Customer" not in names

    # Slide 5 sees both.
    slide_5_eligible = anchors_for_slide(anchors_doc, slide_number=5)
    names = [a["name"] for a in slide_5_eligible]
    assert "Period Palette" in names
    assert "The Customer" in names

    # The Brief input for slide 5 carries the anchors section before the prose
    section = format_anchors_for_brief(
        slide_5_eligible, deck_brief=anchors_doc["deck_brief"]
    )
    blob = build_brief_input(
        vision_prose="The Customer at his desk reviewing the invoice",
        prior_parsed_vision=None,
        accumulated_feedback=[],
        current_tier="ollama",
        brand_fidelity="none",
        anchors_section=section,
    )
    # Anchors section appears before the prose
    anchors_idx = blob.index("Recurring entities from creative anchors")
    prose_idx = blob.index("Operator's vision prose")
    assert anchors_idx < prose_idx

    # Canonical Customer description is in the Brief input
    assert "tortoiseshell glasses" in blob
    assert "salt-and-pepper hair" in blob
    # Negative trait surfaced as exclusion
    assert "Must NOT have: beard" in blob


def test_ga_flow_step_3_sprint_progress_walks_creative_vision_slides_only(tmp_path):
    """AC2: Creative Sprint partitions strategy map and tracks per-slide
    status. Standard slides (slide 2) are NOT counted; resumption picks the
    earliest unaccepted slide."""
    smap = _ga_flow_strategy_map()

    # Initial state: no manifests yet.
    progress = creative_sprint_progress(str(tmp_path), smap)
    assert progress["total"] == 3
    assert progress["accepted"] == 0
    assert progress["not_started"] == 3
    assert progress["complete"] is False
    assert is_sprint_complete(str(tmp_path), smap) is False
    # next_unaccepted_slide picks the lowest creative_vision slide number
    assert next_unaccepted_slide(progress) == 1

    # Operator accepts slide 1 — write a finalised manifest using real helpers.
    manifest_1 = initialise_manifest(
        slide_number=1, vision_prose="Sun-phases horizontal progression", budget_usd=0.50
    )
    manifest_1["attempts"].append({
        "attempt_index": 1, "prose_version": 1, "tier": "flash_1k",
        "text_iterations": 1, "render": {"output_path": "ok.png", "model": "flash"},
        "image_reviewer_verdict": {"verdict": "pass"},
        "directors_critic_verdict": {"verdict": "pass"},
        "cumulative_cost_usd": 0.067,
    })
    finalise_manifest(manifest_1, image_path="ok.png", final_verdict={"verdict": "pass"})
    save_manifest(str(tmp_path), manifest_1)

    progress = creative_sprint_progress(str(tmp_path), smap)
    assert progress["accepted"] == 1
    assert progress["not_started"] == 2
    assert progress["complete"] is False
    # Next slide is 3 (slide 2 is composed, skipped by sprint)
    assert next_unaccepted_slide(progress) == 3

    # Operator finishes slides 3 and 5 — sprint completes.
    for sn in (3, 5):
        m = initialise_manifest(slide_number=sn, vision_prose="x", budget_usd=0.50)
        m["attempts"].append({
            "attempt_index": 1, "prose_version": 1, "tier": "flash_1k",
            "text_iterations": 1, "render": {"output_path": "ok.png", "model": "flash"},
            "image_reviewer_verdict": {"verdict": "pass"},
            "directors_critic_verdict": {"verdict": "pass"},
            "cumulative_cost_usd": 0.067,
        })
        finalise_manifest(m, image_path="ok.png", final_verdict={"verdict": "pass"})
        save_manifest(str(tmp_path), m)

    progress = creative_sprint_progress(str(tmp_path), smap)
    assert progress["accepted"] == 3
    assert progress["complete"] is True
    assert is_sprint_complete(str(tmp_path), smap) is True
    assert next_unaccepted_slide(progress) is None

    # Operator-facing markdown signals the next phase explicitly
    md = format_sprint_progress_markdown(progress)
    assert "Creative Sprint complete" in md
    assert "standard-slide assembly" in md.lower()


def test_ga_flow_step_4_gate_fires_per_iteration_for_creative_vision_only():
    """AC3: should_fire_operator_gate distinguishes the two cadences.

    The GA flow exercises three transitions per slide:

    - free→cost (Ollama → Flash 1K) — fires for both strategies
    - cost→cost (Flash 1K → Pro 1K) — fires ONLY for creative_vision
    - same-tier refinement (Flash 1K → Flash 1K) — fires ONLY for
      creative_vision
    """
    # Free→cost: both strategies fire.
    assert should_fire_operator_gate(
        strategy="creative_vision", current_tier="ollama", next_tier="flash_1k"
    ) is True
    assert should_fire_operator_gate(
        strategy="composed", current_tier="ollama", next_tier="flash_1k"
    ) is True

    # Cost→cost: only creative_vision fires.
    assert should_fire_operator_gate(
        strategy="creative_vision", current_tier="flash_1k", next_tier="pro_1k"
    ) is True
    assert should_fire_operator_gate(
        strategy="composed", current_tier="flash_1k", next_tier="pro_1k"
    ) is False

    # Same-tier refinement: only creative_vision fires.
    assert should_fire_operator_gate(
        strategy="creative_vision", current_tier="flash_1k", next_tier="flash_1k"
    ) is True
    assert should_fire_operator_gate(
        strategy="backdrop", current_tier="flash_1k", next_tier="flash_1k"
    ) is False


def test_ga_flow_full_ordering_is_serialised(tmp_path):
    """The GA flow's load-bearing property: standard-slide assembly is
    BLOCKED until the Creative Sprint completes. This test asserts the
    conductor's gate function returns False until every creative_vision
    slide has a finalised manifest."""
    smap = _ga_flow_strategy_map()

    # Phase 0: nothing started — sprint blocks.
    assert is_sprint_complete(str(tmp_path), smap) is False

    # Phase 1: slide 1 done, but 3 and 5 still pending — sprint blocks.
    m1 = initialise_manifest(slide_number=1, vision_prose="x", budget_usd=0.50)
    m1["attempts"].append({
        "attempt_index": 1, "prose_version": 1, "tier": "flash_1k",
        "text_iterations": 1, "render": {"output_path": "x.png", "model": "f"},
        "image_reviewer_verdict": {"verdict": "pass"},
        "directors_critic_verdict": {"verdict": "pass"},
        "cumulative_cost_usd": 0.067,
    })
    finalise_manifest(m1, image_path="x.png", final_verdict={"verdict": "pass"})
    save_manifest(str(tmp_path), m1)
    assert is_sprint_complete(str(tmp_path), smap) is False

    # Phase 2: slide 3 done — still missing slide 5.
    m3 = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=0.50)
    m3["attempts"].append({
        "attempt_index": 1, "prose_version": 1, "tier": "flash_1k",
        "text_iterations": 1, "render": {"output_path": "x.png", "model": "f"},
        "image_reviewer_verdict": {"verdict": "pass"},
        "directors_critic_verdict": {"verdict": "pass"},
        "cumulative_cost_usd": 0.067,
    })
    finalise_manifest(m3, image_path="x.png", final_verdict={"verdict": "pass"})
    save_manifest(str(tmp_path), m3)
    assert is_sprint_complete(str(tmp_path), smap) is False

    # Phase 3: slide 5 done — sprint complete, conductor proceeds.
    m5 = initialise_manifest(slide_number=5, vision_prose="x", budget_usd=0.50)
    m5["attempts"].append({
        "attempt_index": 1, "prose_version": 1, "tier": "flash_1k",
        "text_iterations": 1, "render": {"output_path": "x.png", "model": "f"},
        "image_reviewer_verdict": {"verdict": "pass"},
        "directors_critic_verdict": {"verdict": "pass"},
        "cumulative_cost_usd": 0.067,
    })
    finalise_manifest(m5, image_path="x.png", final_verdict={"verdict": "pass"})
    save_manifest(str(tmp_path), m5)
    assert is_sprint_complete(str(tmp_path), smap) is True


def test_ga_flow_anchors_optional_when_absent(tmp_path):
    """AC4: a deck without creative_anchors.json must not break the GA flow.

    The Brief input is shaped exactly as it was pre-AC4 when no anchors
    section is provided.
    """
    assert load_anchors(str(tmp_path)) is None  # no file → None, no error

    blob = build_brief_input(
        vision_prose="A lighthouse at sunset",
        prior_parsed_vision=None,
        accumulated_feedback=[],
        current_tier="ollama",
        brand_fidelity="none",
    )
    assert "Recurring entities from creative anchors" not in blob
    assert "A lighthouse at sunset" in blob
