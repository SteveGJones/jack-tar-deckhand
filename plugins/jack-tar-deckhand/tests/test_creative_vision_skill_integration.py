"""Confirm SKILL.md surfaces document creative_vision dispatch paths."""
from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = PLUGIN_ROOT / "skills"


def _load_skill(name):
    path = SKILLS_DIR / name / "SKILL.md"
    assert path.is_file(), f"SKILL.md missing: {path}"
    return path.read_text()


def test_imagegen_bridge_documents_creative_vision_dispatch():
    text = _load_skill("imagegen-bridge")
    assert "creative_vision" in text
    assert "creative_vision_dispatch" in text or "creative_vision/" in text
    # Must describe the full pipeline loop, not just call the dispatch
    for keyword in ("Director's Brief", "Prompt Reviewer", "Director's Critic", "tier", "cascade"):
        assert keyword in text, f"imagegen-bridge SKILL.md missing keyword: {keyword!r}"


def test_strategy_map_documents_creative_vision_authoring():
    text = _load_skill("strategy-map")
    assert "creative_vision" in text
    assert "vision_prose" in text
    # Must explain cost banner / operator opt-in
    for keyword in ("budget", "operator-opt-in", "prose"):
        assert keyword in text.lower(), f"strategy-map SKILL.md missing keyword: {keyword!r}"


def test_iterate_slide_documents_three_channels():
    text = _load_skill("iterate-slide")
    assert "creative_vision" in text
    for channel in ("revise prose", "refine prompt", "escalate tier"):
        assert channel in text.lower()


def test_strategy_map_documents_per_slide_cost_surface():
    """Issue #113 AC1 — strategy-map SKILL.md must instruct the dispatcher to
    invoke summarise_creative_vision_spend BEFORE asking for approval, AND to
    offer fallback strategies if the operator declines on cost grounds.
    """
    text = _load_skill("strategy-map")
    assert "summarise_creative_vision_spend" in text, (
        "strategy-map SKILL.md must call summarise_creative_vision_spend to "
        "produce the per-slide cost surface (#113 AC1)."
    )
    assert "AC1" in text or "per-slide cost" in text.lower(), (
        "strategy-map SKILL.md should name the AC1 cost-surface section so "
        "future readers can trace it back to issue #113."
    )
    text_lower = text.lower()
    for fallback in ("composed", "backdrop", "full_render"):
        assert fallback in text_lower, (
            f"strategy-map SKILL.md must offer {fallback!r} as a fallback "
            f"when the operator declines creative_vision on cost grounds."
        )


def test_deck_conductor_invokes_per_slide_cost_surface_before_approval():
    """The conductor agent definition mirrors the SKILL.md instruction so a
    dedicated deck-conductor session also fires the cost surface at Step 3.5
    before presenting the strategy map for approval.
    """
    text = (PLUGIN_ROOT / "agents" / "deck-conductor.md").read_text()
    assert "summarise_creative_vision_spend" in text, (
        "deck-conductor agent definition must reference summarise_creative_vision_spend"
    )
    assert "AC1" in text or "per-creative-vision-slide cost surface" in text.lower(), (
        "deck-conductor must name the AC1 cost-surface step so the rule is auditable"
    )


def test_imagegen_bridge_loads_creative_anchors_before_brief():
    """Issue #113 AC4 — the imagegen-bridge SKILL.md must instruct the
    dispatcher to load creative anchors and inline them into the Brief
    input. Without this, the Brief never sees the anchors section even
    when the deck has one."""
    text = _load_skill("imagegen-bridge")
    assert "load_anchors" in text, (
        "imagegen-bridge must call load_anchors before building the Brief input"
    )
    assert "anchors_for_slide" in text, (
        "imagegen-bridge must filter anchors per slide via anchors_for_slide"
    )
    assert "format_anchors_for_brief" in text, (
        "imagegen-bridge must render the anchors section via format_anchors_for_brief"
    )
    assert "anchors_section=" in text, (
        "imagegen-bridge must pass anchors_section= into build_brief_input"
    )
    assert "AC4" in text or "creative_anchors" in text, (
        "imagegen-bridge should anchor the anchors step to issue #113 / AC4"
    )
