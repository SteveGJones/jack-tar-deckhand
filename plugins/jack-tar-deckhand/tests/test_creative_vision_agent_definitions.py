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


def test_directors_brief_output_contract_shows_wrong_shape_anti_pattern():
    """F2 from 2026-05-22 dogfood — Brief sometimes emitted the prompt outside
    the JSON fence. The Output Contract must show the WRONG shape explicitly
    so the agent learns from a concrete failure example."""
    content = _load_agent("directors-brief")
    assert "WRONG" in content or "wrong shape" in content.lower(), (
        "Output Contract should explicitly call out a WRONG shape anti-pattern"
    )
    assert "outside the fence" in content.lower() or "two separate fences" in content.lower(), (
        "Output Contract should name the prompt-outside-fence anti-pattern"
    )
    assert "CORRECT" in content or "correct shape" in content.lower(), (
        "Output Contract should label the CORRECT shape next to the WRONG ones"
    )


def test_prompt_reviewer_agent_exists_and_has_required_sections():
    content = _load_agent("prompt-reviewer")
    assert "Prompt Reviewer" in content
    assert "haiku" in content.lower()
    assert "pass" in content.lower() and "refine" in content.lower()
    assert "elements" in content.lower()  # checks for dropped-elements detection


def test_directors_critic_agent_exists_and_has_required_sections():
    content = _load_agent("directors-critic")
    assert "Director's Critic" in content or "Directors Critic" in content
    assert "sonnet" in content.lower()
    for axis in ("entity_fidelity", "spatial_fidelity", "style_fidelity", "quality", "composition"):
        assert axis in content
    for verdict in ("pass", "refine_at_tier", "escalate_tier", "abort"):
        assert verdict in content


def test_deck_conductor_references_creative_vision_operator_gate():
    """Issue #113 AC3 — the deck-conductor agent definition must reference the
    F12 elevated cadence so a fresh orchestrator session knows that
    creative_vision slides fire the gate at EVERY iteration, not just at
    free→cost.
    """
    content = _load_agent("deck-conductor")
    assert "creative_vision" in content, (
        "deck-conductor should name the creative_vision strategy where its gate cadence differs"
    )
    assert "F12" in content or "elevated cadence" in content.lower() or "every iteration" in content.lower(), (
        "deck-conductor should describe the F12 elevated-cadence rule for creative_vision"
    )
    assert "should_fire_operator_gate" in content, (
        "deck-conductor should cite the canonical predicate helper rather than rely on prose"
    )
    assert "advisory" in content.lower() or "not authorisation" in content.lower(), (
        "deck-conductor should remind that Critic verdicts are advisory, not spend authorisation"
    )
