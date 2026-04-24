"""Structural validation of agent definitions in plugins/jack-tar-superpower-bridge/agents/."""
from pathlib import Path
import re

import pytest

PLUGIN_AGENTS_DIR = Path(__file__).resolve().parents[1] / "agents"


def _read_agent(name: str) -> str:
    return (PLUGIN_AGENTS_DIR / f"{name}.md").read_text()


def _frontmatter(content: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def test_narrative_brief_architect_definition_exists():
    fm = _frontmatter(_read_agent("narrative-brief-architect"))
    assert fm["name"] == "narrative-brief-architect"
    assert fm["model"] == "sonnet"
    # Sonnet model required by persona contract — Tier 1 risk + bounded scope
    assert "description" in fm and len(fm["description"]) > 30


def test_narrative_brief_architect_says_objectName_not_name():
    text = _read_agent("narrative-brief-architect")
    assert "objectName" in text
    # Must NOT instruct using `name:` as PptxGenJS shape-name property
    assert "name: \"IMAGE:" not in text
    assert "name: \"SMARTART:" not in text
    assert "name: \"BG:" not in text


def test_narrative_brief_architect_lists_three_arc_options():
    text = _read_agent("narrative-brief-architect")
    arcs = ["Problem-Solution", "Hero", "Build-Up"]
    found = sum(1 for a in arcs if a in text)
    assert found >= 2


def test_narrative_brief_architect_describes_user_approval_gate():
    text = _read_agent("narrative-brief-architect")
    # Must state explicit user approval before saving creative-brief.md
    assert "approval" in text.lower() or "approve" in text.lower()
    assert "creative-brief.md" in text
