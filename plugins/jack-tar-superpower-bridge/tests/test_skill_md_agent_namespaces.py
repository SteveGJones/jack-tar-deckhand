"""Regression: SKILL.md files must dispatch agents using their namespaced form.

Caught during the first dogfood run (2026-04-24): bridge-brief SKILL.md said
``subagent_type="narrative-brief-architect"`` (bare name), but Claude Code
registers plugin agents under the plugin namespace, so the actual dispatch
type is ``jack-tar-superpower-bridge:narrative-brief-architect``. The bare
form raises ``Agent type not found`` at runtime.

This test scans the bridge's SKILL.md files for backtick-quoted references
to known agent identifiers and asserts every reference is namespaced.
Documentation prose ("the image-reviewer agent" without backticks) is left
alone — only code-style backtick references are checked because those are
the ones that mirror real dispatch instructions.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

PLUGIN_AGENTS_BARE = ("narrative-brief-architect", "enrichment-cohesion-reviewer")
DECKHAND_AGENTS_BARE = ("prompt-engineer", "image-reviewer")

NAMESPACE_PREFIX = {
    "narrative-brief-architect": "jack-tar-superpower-bridge",
    "enrichment-cohesion-reviewer": "jack-tar-superpower-bridge",
    "prompt-engineer": "jack-tar-deckhand",
    "image-reviewer": "jack-tar-deckhand",
}

PLUGIN_ROOT = Path(__file__).resolve().parent.parent

SKILL_FILES = (
    PLUGIN_ROOT / "skills" / "bridge-brief" / "SKILL.md",
    PLUGIN_ROOT / "skills" / "enrich-deck" / "SKILL.md",
)


def _backtick_refs(content: str, name: str) -> list[str]:
    """Return every backtick-quoted occurrence containing ``name``."""
    return re.findall(rf"`[^`]*{re.escape(name)}[^`]*`", content)


@pytest.mark.parametrize("agent", PLUGIN_AGENTS_BARE + DECKHAND_AGENTS_BARE)
@pytest.mark.parametrize("skill_md", SKILL_FILES, ids=lambda p: p.parent.name)
def test_backtick_agent_refs_are_namespaced(skill_md: Path, agent: str) -> None:
    if not skill_md.exists():
        pytest.skip(f"{skill_md} not present in this checkout")
    content = skill_md.read_text(encoding="utf-8")
    namespace = NAMESPACE_PREFIX[agent]
    expected_prefix = f"{namespace}:"

    bad: list[str] = []
    for ref in _backtick_refs(content, agent):
        # A reference is OK iff the agent name is preceded (within the same
        # backtick span) by the expected namespace + colon.
        # We allow other text inside the backticks (e.g. "subagent_type=...").
        if expected_prefix + agent in ref:
            continue
        bad.append(ref)

    assert not bad, (
        f"{skill_md.relative_to(PLUGIN_ROOT)} has backtick-quoted reference(s) "
        f"to {agent!r} without the {expected_prefix!r} namespace:\n  "
        + "\n  ".join(bad)
        + f"\nDispatch via Agent tool requires the namespaced form "
          f"({expected_prefix}{agent}); bare names raise 'Agent type not found'."
    )


def test_subagent_type_literal_is_namespaced() -> None:
    """The bridge-brief SKILL.md hard-codes ``subagent_type=`` in an example
    line. That literal string MUST contain the namespaced agent identifier —
    it is the most direct copy-paste hazard for downstream callers.
    """
    skill_md = PLUGIN_ROOT / "skills" / "bridge-brief" / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")

    matches = re.findall(r'subagent_type\s*=\s*"([^"]+)"', content)
    assert matches, "bridge-brief SKILL.md should reference subagent_type=..."
    for value in matches:
        assert value.startswith("jack-tar-superpower-bridge:"), (
            f"subagent_type literal {value!r} is not namespaced under "
            f"jack-tar-superpower-bridge: — bare names raise 'Agent type not found'."
        )
