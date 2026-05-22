"""Smoke tests for the creative_vision agent definition files."""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

AGENTS_DIR = PLUGIN_ROOT / "agents"


def _load_agent(name):
    path = AGENTS_DIR / f"{name}.md"
    assert path.is_file(), f"agent file missing: {path}"
    return path.read_text()


def test_directors_brief_agent_exists_and_has_required_sections():
    content = _load_agent("directors-brief")
    assert "Director's Brief" in content or "Directors Brief" in content
    assert "ParsedVision" in content
    assert "model: sonnet" in content.lower() or "sonnet" in content.lower()
    assert "operator's prose" in content.lower() or "vision prose" in content.lower()


def test_prompt_reviewer_agent_exists_and_has_required_sections():
    content = _load_agent("prompt-reviewer")
    assert "Prompt Reviewer" in content
    assert "haiku" in content.lower()
    assert "pass" in content.lower() and "refine" in content.lower()
    assert "elements" in content.lower()  # checks for dropped-elements detection
