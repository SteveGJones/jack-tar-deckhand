"""Integration test: superpower-bridge skill manifests are discoverable from plugin root."""
import json
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = WORKTREE / "plugins" / "jack-tar-superpower-bridge"


def test_plugin_json_present_and_valid():
    plugin_json = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    assert plugin_json.exists()
    data = json.loads(plugin_json.read_text())
    assert data["name"] == "jack-tar-superpower-bridge"


def test_three_skills_present():
    for skill in ("bridge-brief", "enrich-deck", "verify"):
        assert (PLUGIN_ROOT / "skills" / skill / "SKILL.md").exists(), \
            f"missing skill {skill}"


def test_two_agents_present():
    for agent in ("narrative-brief-architect", "enrichment-cohesion-reviewer"):
        assert (PLUGIN_ROOT / "agents" / f"{agent}.md").exists(), \
            f"missing agent {agent}"
