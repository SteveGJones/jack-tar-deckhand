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


# --- edit tier — Step 4.9 (issue #143) ---------------------------------------


def test_step_4_9_edit_subsection_present():
    content = _read()
    assert "Step 4.9" in content
    assert "Local edit" in content


def test_step_4_9_references_edit_dispatch_functions():
    content = _read()
    assert "from src.edit_dispatch import" in content
    assert "detect_mlx_edit_backend" in content
    assert "edit_channel_available" in content
    assert "edit_channel_unavailable_reason" in content
    assert "classify_edit_locality" in content
    assert "build_edit_args" in content


def test_step_4_9_references_mlx_edit_backend_and_persistence():
    content = _read()
    assert "mlx_edit" in content
    assert "edit_action" in content
    assert "append_attempt" in content


def test_step_4_9_references_edit_image_wrapper():
    content = _read()
    assert "edit_image.py" in content
    assert "MLX_PLUGIN_ROOT" in content


def test_step_4_9_documents_text_carve_out_and_f12():
    content = _read()
    assert "text_excluded" in content
    assert "F12" in content
