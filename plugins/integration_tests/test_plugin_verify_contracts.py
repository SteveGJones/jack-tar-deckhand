"""Verify each plugin's verify skill follows the STATUS line contract."""
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
PLUGINS_DIR = WORKTREE / "plugins"


def _read_skill(plugin_name, skill_name="verify"):
    path = PLUGINS_DIR / plugin_name / "skills" / skill_name / "SKILL.md"
    assert path.exists(), f"Missing skill: {path}"
    return path.read_text()


def test_ollama_verify_has_status_lines():
    content = _read_skill("jack-tar-ollama")
    assert "STATUS: FULLY_AVAILABLE" in content
    assert "STATUS: NOT_AVAILABLE" in content
    assert "PLUGIN: jack-tar-ollama" in content


def test_cloud_verify_has_status_lines():
    content = _read_skill("jack-tar-cloud")
    # The cloud verify skill's example shows PARTIALLY_AVAILABLE and mentions
    # FULLY_AVAILABLE in the prose description of the count logic
    assert "PARTIALLY_AVAILABLE" in content
    assert "NOT_AVAILABLE" in content
    assert "PLUGIN: jack-tar-cloud" in content
    assert "PROVIDERS:" in content


def test_msft_smartart_verify_has_status_lines():
    content = _read_skill("jack-tar-msft-smartart")
    assert "STATUS: FULLY_AVAILABLE" in content
    assert "PLUGIN: jack-tar-msft-smartart" in content
    assert "LAYOUT FIXTURES:" in content


def test_custom_smartart_verify_has_status_lines():
    content = _read_skill("jack-tar-custom-smartart")
    assert "STATUS: FULLY_AVAILABLE" in content
    # PARTIALLY_AVAILABLE and NOT_AVAILABLE appear as prose conditions
    assert "PARTIALLY_AVAILABLE" in content
    assert "NOT_AVAILABLE" in content
    assert "PLUGIN: jack-tar-custom-smartart" in content


def test_deckhand_verify_has_status_lines():
    content = _read_skill("jack-tar-deckhand")
    # Deckhand verify example shows PARTIALLY_AVAILABLE; all three values
    # are referenced in the STATUS rules section
    assert "PARTIALLY_AVAILABLE" in content
    assert "NOT_AVAILABLE" in content
    assert "FULLY_AVAILABLE" in content
    assert "PLUGIN: jack-tar-deckhand" in content
    assert "ENGINE PLUGINS:" in content
    assert "PIPELINE CAPABILITY:" in content


def test_deckhand_verify_mentions_engine_plugins():
    content = _read_skill("jack-tar-deckhand")
    assert "jack-tar-ollama" in content
    assert "jack-tar-cloud" in content
    assert "jack-tar-msft-smartart" in content
    assert "jack-tar-custom-smartart" in content


def test_all_plugins_have_plugin_json():
    for name in ["jack-tar-ollama", "jack-tar-cloud", "jack-tar-msft-smartart",
                 "jack-tar-custom-smartart", "jack-tar-deckhand"]:
        pj = PLUGINS_DIR / name / ".claude-plugin" / "plugin.json"
        assert pj.exists(), f"Missing plugin.json: {pj}"


def test_marketplace_json_lists_all_5_plugins():
    import json
    mp = WORKTREE / ".claude-plugin" / "marketplace.json"
    assert mp.exists()
    data = json.loads(mp.read_text())
    names = {p["name"] for p in data["plugins"]}
    assert "jack-tar-ollama" in names
    assert "jack-tar-cloud" in names
    assert "jack-tar-msft-smartart" in names
    assert "jack-tar-custom-smartart" in names
    assert "jack-tar-deckhand" in names
