"""Test imagegen-bridge skill uses plugin-qualified skill names and PLUGIN_ROOT pattern."""
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
SKILL_PATH = WORKTREE / "plugins" / "jack-tar-deckhand" / "skills" / "imagegen-bridge" / "SKILL.md"


def _read():
    return SKILL_PATH.read_text()


def test_uses_plugin_qualified_skill_names():
    content = _read()
    assert "jack-tar-ollama:image" in content
    assert "jack-tar-ollama:pattern" in content
    assert "jack-tar-ollama:diagram" in content
    assert "jack-tar-cloud:image" in content
    assert "jack-tar-cloud:icon" in content


def test_no_legacy_skill_names():
    content = _read()
    assert "/ollama-image " not in content
    assert "/ollama-pattern " not in content
    assert "/cloud-generate-image " not in content
    assert "/cloud-generate-icon " not in content


def test_uses_plugin_verify_for_discovery():
    content = _read()
    assert "jack-tar-ollama:verify" in content
    assert "jack-tar-cloud:verify" in content


def test_no_venv_references():
    content = _read()
    assert ".venv" not in content


def test_has_plugin_root_discovery():
    content = _read()
    assert "PLUGIN_ROOT" in content
    assert "JACK_TAR_DECKHAND_ROOT" in content


def test_deck_conductor_has_qualified_skill_names():
    conductor = (WORKTREE / "plugins" / "jack-tar-deckhand" / "agents" / "deck-conductor.md").read_text()
    assert "/jack-tar-deckhand:brand-manager" in conductor
    assert "/jack-tar-deckhand:deck-assembler" in conductor
    assert "/jack-tar-deckhand:deck-qa" in conductor


def test_deck_conductor_no_venv():
    conductor = (WORKTREE / "plugins" / "jack-tar-deckhand" / "agents" / "deck-conductor.md").read_text()
    assert ".venv" not in conductor
