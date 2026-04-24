"""Structural validation of the /bridge-brief skill manifest."""
from pathlib import Path
import re

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = PLUGIN_ROOT / "skills" / "bridge-brief" / "SKILL.md"


def _frontmatter(content: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    out: dict[str, str] = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip()
    return out


def test_skill_exists():
    assert SKILL_PATH.exists()


def test_skill_frontmatter_valid():
    text = SKILL_PATH.read_text()
    fm = _frontmatter(text)
    assert fm["name"] == "bridge-brief"
    assert "description" in fm and len(fm["description"]) >= 40
    assert "argument-hint" in fm


def test_skill_invokes_narrative_brief_architect_agent():
    text = SKILL_PATH.read_text()
    assert "narrative-brief-architect" in text


def test_skill_writes_creative_brief_md():
    text = SKILL_PATH.read_text()
    assert "creative-brief.md" in text


def test_skill_uses_creative_brief_writer():
    text = SKILL_PATH.read_text()
    # Skill must call into the Python writer (not just produce loose markdown)
    assert "src.creative_brief" in text or "creative_brief" in text
