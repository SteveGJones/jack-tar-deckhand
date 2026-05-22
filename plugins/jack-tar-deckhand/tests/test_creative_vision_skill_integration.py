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
