"""Programmatic helpers for integrating pptx_native with the SmartArt
selector agent.

The smartart-selector agent is an LLM (Haiku) that proposes graphic
type + enrichment tier recommendations. Its prompt references this
module's documentation (see `.claude/agents/smartart-selector.md`'s
"pptx_native Engine — When to Recommend" section) rather than
restating per-layout metadata inline, so the prompt stays in sync
with the catalog.

This module provides deterministic helpers:

  - `is_pptx_native_candidate(body_points, graphic_type, tier)` —
    Given a raw slide's body_points, the proposed graphic type, and
    the proposed enrichment tier, returns a structured decision about
    whether pptx_native is eligible for this slide.
  - `score_pptx_native_candidate(...)` — Returns a 0-1 confidence
    score the selector can use when ranking options.

Both helpers consult the catalog for per-layout constraints, so the
selector's decisions stay in sync with what the engine can actually
render.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.layouts import catalog


# Only these enrichment tiers are compatible with pptx_native.
# AI enrichment overlays would defeat the editability value prop.
COMPATIBLE_ENRICHMENT_TIERS = {"pure_programmatic"}


@dataclass
class CandidacyResult:
    """Outcome of evaluating whether pptx_native fits a slide.

    Attributes:
        eligible: True if all hard constraints pass — the selector
            MAY include pptx_native as a candidate.
        layout_id: The catalog layout id pptx_native would use
            (e.g. "process1"), or None if the graphic type isn't
            supported.
        confidence: 0-1 score. 0 if ineligible. Higher means stronger
            fit. See score_pptx_native_candidate for the formula.
        reasons: Human-readable list explaining WHY. Always populated,
            both for positive and negative outcomes.
    """

    eligible: bool
    layout_id: str | None
    confidence: float
    reasons: list[str]


def is_pptx_native_candidate(
    body_points: list[str],
    graphic_type: str,
    enrichment_tier: str,
) -> CandidacyResult:
    """Evaluate whether pptx_native fits a slide under all hard
    constraints. Returns a CandidacyResult.

    Soft preferences (audience, adjacency, etc.) are NOT evaluated
    here — those belong in the selector prompt's decision-making
    because they need context this module doesn't have.
    """
    reasons: list[str] = []

    # Check 1: graphic type has a pptx_native layout binding
    layout_id = catalog.get_layout_id_for_graphic_type(graphic_type)
    if layout_id is None:
        return CandidacyResult(
            eligible=False,
            layout_id=None,
            confidence=0.0,
            reasons=[
                f"graphic_type {graphic_type!r} has no pptx_native layout "
                f"mapping in the catalog"
            ],
        )

    # Check 2: enrichment tier must be T0
    if enrichment_tier not in COMPATIBLE_ENRICHMENT_TIERS:
        return CandidacyResult(
            eligible=False,
            layout_id=layout_id,
            confidence=0.0,
            reasons=[
                f"enrichment_tier {enrichment_tier!r} is not compatible "
                f"with pptx_native — AI enrichment overlays defeat "
                f"editability, so only {sorted(COMPATIBLE_ENRICHMENT_TIERS)} "
                f"are accepted"
            ],
        )

    entry = catalog.get_entry(layout_id)

    # Check 3: node count within catalog-declared range
    # (for hierarchical layouts, we count all body_points as an
    # approximation; the extractor will do proper tree parsing)
    n_nodes = len([p for p in body_points if p.strip()])
    if n_nodes < entry["min_nodes"]:
        return CandidacyResult(
            eligible=False,
            layout_id=layout_id,
            confidence=0.0,
            reasons=[
                f"slide has {n_nodes} body points but layout "
                f"{layout_id!r} requires at least {entry['min_nodes']}"
            ],
        )
    if n_nodes > entry["max_nodes"]:
        return CandidacyResult(
            eligible=False,
            layout_id=layout_id,
            confidence=0.0,
            reasons=[
                f"slide has {n_nodes} body points but layout "
                f"{layout_id!r} supports at most {entry['max_nodes']} — "
                f"selector should recommend custom_svg instead"
            ],
        )

    # Check 4: all labels fit within max_label_chars
    max_chars = entry["max_label_chars"]
    long_labels = [p.strip() for p in body_points if len(p.strip()) > max_chars]
    if long_labels:
        return CandidacyResult(
            eligible=False,
            layout_id=layout_id,
            confidence=0.0,
            reasons=[
                f"{len(long_labels)} label(s) exceed the {max_chars}-char "
                f"limit for layout {layout_id!r}: "
                f"{[l[:30] + '...' if len(l) > 30 else l for l in long_labels]}"
            ],
        )

    reasons.append(
        f"graphic_type {graphic_type!r} → layout {layout_id!r}, "
        f"{n_nodes} nodes, all labels within "
        f"{max_chars}-char limit, T0 enrichment"
    )

    confidence = score_pptx_native_candidate(n_nodes, entry)

    reasons.append(
        f"confidence: {confidence:.2f} (based on node count fit "
        f"within {entry['min_nodes']}-{entry['max_nodes']} range)"
    )

    return CandidacyResult(
        eligible=True,
        layout_id=layout_id,
        confidence=confidence,
        reasons=reasons,
    )


def score_pptx_native_candidate(n_nodes: int, entry: dict[str, Any]) -> float:
    """Return a 0-1 confidence score for a pptx_native candidate.

    Scoring heuristic: layouts are most confident at their "sweet spot"
    — the middle of their node-count range. Very low or very high
    node counts are less confident (layouts look sparse or cluttered
    at the extremes). Assumes the caller has already verified the
    node count is within range.

    Score formula:
        sweet_spot = (min + max) / 2
        distance   = |n - sweet_spot| / ((max - min) / 2)
        confidence = 0.85 - (distance × 0.25)

    Range: roughly 0.60-0.85. The baseline is 0.85 at the sweet spot.
    Never goes above 0.85 because the selector should usually present
    pptx_native alongside a custom_svg alternative for the speaker to
    choose between.
    """
    min_n = entry["min_nodes"]
    max_n = entry["max_nodes"]
    if max_n == min_n:
        return 0.85
    sweet_spot = (min_n + max_n) / 2
    half_range = (max_n - min_n) / 2
    distance = abs(n_nodes - sweet_spot) / half_range  # 0..1
    confidence = 0.85 - (distance * 0.25)
    return round(max(0.0, min(1.0, confidence)), 2)


def format_selector_rationale(
    result: CandidacyResult,
    body_points: list[str],
) -> str:
    """Fill in a selector rationale template for the chosen layout.

    Uses the catalog entry's `selector_rationale_template` and
    interpolates `{n}`, `{first}`, `{last}` (for flat-list layouts)
    or `{n}`, `{depth}` (for hierarchical) from the slide's actual
    content.

    This is what the selector should copy into its recommendation's
    `rationale` field when proposing a pptx_native candidate.
    """
    if not result.eligible or result.layout_id is None:
        return "pptx_native not eligible"

    entry = catalog.get_entry(result.layout_id)
    template = entry["selector_rationale_template"]

    labels = [p.strip() for p in body_points if p.strip()]
    n = len(labels)
    first = labels[0] if labels else ""
    last = labels[-1] if labels else ""

    # Fill in available placeholders. Unused placeholders remain.
    formatted = template
    formatted = formatted.replace("{n}", str(n))
    formatted = formatted.replace("{first}", first)
    formatted = formatted.replace("{last}", last)
    # {depth} only makes sense for hierarchical — leave as-is if present
    # and caller hasn't supplied it

    return formatted
