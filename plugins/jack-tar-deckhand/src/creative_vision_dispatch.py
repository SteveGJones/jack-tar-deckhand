"""Top-level dispatch entry for creative_vision strategy.

Called by imagegen-bridge for each slide with strategy=creative_vision.
Mirror of paperbanana_dispatch.py — provides a single function the bridge
calls AND a dataclass describing the request. The actual orchestration
loop runs inside SKILL.md (imagegen-bridge), invoking the helpers in
src/creative_vision/ between agent dispatches. Issue #105.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.creative_vision.cascade import ladder_for
from src.creative_vision.manifest import initialise_manifest, save_manifest


@dataclass
class DispatchRequest:
    """Request to initialise a creative_vision dispatch for a slide.

    Attributes:
        deck_dir: absolute path to the deck working directory.
        slide_number: 1-based slide index.
        vision_prose: the vision direction for the slide (prose description).
        budget_usd: image generation budget (USD) allocated to this slide.
        allowed_ceiling: the highest tier the loop is allowed to escalate to
            (e.g., "pro_4k", "recraft_pro_4k"). Used to cap escalation.
        brand_fidelity: "exact" routes through Recraft ladder; everything
            else routes through the default Nano Banana ladder.
    """

    deck_dir: str
    slide_number: int
    vision_prose: str
    budget_usd: float
    allowed_ceiling: str
    brand_fidelity: str


def initialise_dispatch(req: DispatchRequest) -> dict:
    """Persist a fresh manifest for this slide and return it.

    The orchestration loop (driven by SKILL.md) takes over from here, reading
    the manifest, dispatching agents, and updating the manifest between
    attempts. Pure-logic helpers in src/creative_vision/ are the kernel; the
    SKILL.md is the shell.

    Args:
        req: the dispatch request containing deck location, slide number,
            vision prose, budget, and tier ceiling / brand fidelity constraints.

    Returns:
        The initialised manifest dict (also persisted to disk).
    """
    manifest = initialise_manifest(
        slide_number=req.slide_number,
        vision_prose=req.vision_prose,
        budget_usd=req.budget_usd,
    )
    ladder = ladder_for(req.brand_fidelity)
    # Update hooks with the correct ladder's next tier from ollama
    manifest["iterate_slide_hooks"]["next_tier_available"] = ladder[1] if len(ladder) > 1 else None
    save_manifest(req.deck_dir, manifest)
    return manifest
