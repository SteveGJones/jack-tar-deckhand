"""Smoke tests pinning the figure-critic agent definition (#113 Path B)."""
from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
AGENT_PATH = PLUGIN_ROOT / "agents" / "figure-critic.md"


def _load():
    assert AGENT_PATH.is_file(), f"agent definition missing at {AGENT_PATH}"
    return AGENT_PATH.read_text()


def test_figure_critic_agent_file_exists():
    """The agent definition must exist at the canonical path so the SKILL.md
    Step 4.6.1 dispatch can find it."""
    _load()


def test_figure_critic_declared_as_sonnet():
    """Path B uses Sonnet for the academic-figure critic — same tier as
    directors-critic for creative_vision."""
    text = _load()
    assert "model: sonnet" in text.lower()


def test_figure_critic_documents_five_scoring_axes():
    """Per the schema, the agent must score against five axes. The agent
    definition must list each so a future reader knows what to score."""
    text = _load()
    for axis in (
        "methodology_fidelity",
        "caption_alignment",
        "legibility",
        "figure_type_correctness",
        "aesthetic_quality",
    ):
        assert axis in text, f"figure-critic must document axis {axis!r}"


def test_figure_critic_documents_four_verdict_values():
    """The verdict enum is pass / refine / escalate / abort."""
    text = _load()
    for verdict in ("pass", "refine", "escalate", "abort"):
        assert verdict in text, f"figure-critic must document verdict {verdict!r}"


def test_figure_critic_documents_canonical_figure_types():
    """The figure_type enum must be documented in the agent so the agent
    knows what each value means for scoring."""
    text = _load()
    for ft in (
        "architecture_diagram",
        "equation",
        "plot",
        "table",
        "algorithm_pseudocode",
        "flowchart",
        "other",
    ):
        assert ft in text


def test_figure_critic_pins_pass_requires_axes_above_80():
    """The hard rule that pass requires every axis ≥80 must be in the agent
    definition — schema enforces it but the agent needs to know not to lie."""
    text = _load()
    assert "≥ 80" in text or ">= 80" in text or "80" in text
    # Look for explicit cross-field language
    assert "verdict == \"pass\"" in text or "verdict='pass'" in text or "verdict == 'pass'" in text


def test_figure_critic_pins_equivalence_testing_posture():
    """The agent must explicitly not defer to paperbanana's verdict."""
    text = _load().lower()
    assert "do not defer" in text or "not defer to paperbanana" in text
    assert "equivalence" in text
    assert "agrees_with_paperbanana_verdict" in text


def test_figure_critic_pins_refinement_feedback_contract():
    """The agent must know refinement_feedback flows verbatim into paperbanana
    --continue-run --feedback. Vague feedback would break the loop."""
    text = _load().lower()
    assert "continue-run" in text or "continue_run" in text
    assert "verbatim" in text


def test_figure_critic_cross_references_schema_and_dispatch_module():
    """Agent definition should cite the schema and dispatch helper so a
    reader can trace the contract surface."""
    text = _load()
    assert "figure_critic_verdict.schema.json" in text
    assert "academic_figure_critic.py" in text


def test_figure_critic_documents_why_this_agent_exists():
    """Path B is a non-trivial architectural choice; the agent definition
    must explain why we moved the critic out of paperbanana into jack-tar."""
    text = _load().lower()
    assert "why this agent exists" in text
    # Specific motivations:
    assert "creative_vision" in text  # mirroring an established pattern
    assert "operator-paced" in text or "operator gate" in text


def test_figure_critic_cites_upstream_paperbanana_issues():
    """The motivation for Path B includes upstream paperbanana constraints
    (deprecated defaults, PyPI staleness). Surface them so the agent
    definition is self-explanatory."""
    text = _load()
    # At least one of our upstream issues should be referenced
    assert "#213" in text or "#214" in text or "#216" in text
