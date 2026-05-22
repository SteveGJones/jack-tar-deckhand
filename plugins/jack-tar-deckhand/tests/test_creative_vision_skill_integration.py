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
