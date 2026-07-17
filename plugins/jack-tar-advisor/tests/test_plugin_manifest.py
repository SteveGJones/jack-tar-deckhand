"""Minimal contract tests for the prose-only jack-tar-advisor plugin."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_plugin_json_parses_and_versions():
    d = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert d["name"] == "jack-tar-advisor"
    assert d["version"]


def test_model_advisor_skill_exists_with_frontmatter():
    text = (ROOT / "skills" / "model-advisor" / "SKILL.md").read_text()
    assert text.startswith("---")
    assert "name: model-advisor" in text
    assert "model catalog is the single source of truth" in text


def test_skill_carries_binding_doctrine():
    text = (ROOT / "skills" / "model-advisor" / "SKILL.md").read_text()
    assert "Nano Banana Flash, not Pro" in text
    assert "local models are more than adequate" in text.lower() or "more than adequate" in text
