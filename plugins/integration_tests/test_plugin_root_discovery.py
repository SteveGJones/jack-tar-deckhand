"""Test PLUGIN_ROOT discovery works for each plugin when running from worktree."""
import subprocess
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]

DISCOVERY_SCRIPT = """
from pathlib import Path
import sys, os

name = '{name}'
env_key = 'JACK_TAR_' + name.upper().replace('-', '_') + '_ROOT'
if os.environ.get(env_key):
    print(os.environ[env_key]); sys.exit()

home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    for p in base.rglob(name + '/.claude-plugin/plugin.json'):
        print(str(p.parent.parent)); sys.exit()

dev = Path.cwd() / 'plugins' / name
if dev.exists():
    print(str(dev)); sys.exit()

print('NOT_FOUND')
"""


def _discover_root(plugin_name):
    script = DISCOVERY_SCRIPT.format(name=plugin_name)
    result = subprocess.run(
        ["python3", "-c", script],
        capture_output=True, text=True,
        cwd=str(WORKTREE)
    )
    return result.stdout.strip()


def test_ollama_root_discovered():
    root = _discover_root("jack-tar-ollama")
    assert root != "NOT_FOUND" and root != ""
    assert (Path(root) / ".claude-plugin" / "plugin.json").exists()


def test_cloud_root_discovered():
    root = _discover_root("jack-tar-cloud")
    assert root != "NOT_FOUND" and root != ""
    assert (Path(root) / ".claude-plugin" / "plugin.json").exists()


def test_msft_smartart_root_discovered():
    root = _discover_root("jack-tar-msft-smartart")
    assert root != "NOT_FOUND" and root != ""
    assert (Path(root) / "src" / "engine.py").exists()


def test_custom_smartart_root_discovered():
    root = _discover_root("jack-tar-custom-smartart")
    assert root != "NOT_FOUND" and root != ""
    assert (Path(root) / "src" / "smartart_renderer.py").exists()


def test_deckhand_root_discovered():
    root = _discover_root("jack-tar-deckhand")
    assert root != "NOT_FOUND" and root != ""
    assert (Path(root) / "src" / "deckcontext.py").exists()


def test_env_override_works():
    import os
    plugin = "jack-tar-deckhand"
    override = str(WORKTREE / "plugins" / plugin)
    env = os.environ.copy()
    env["JACK_TAR_DECKHAND_ROOT"] = override
    script = DISCOVERY_SCRIPT.format(name=plugin)
    result = subprocess.run(
        ["python3", "-c", script],
        capture_output=True, text=True,
        cwd=str(WORKTREE), env=env
    )
    assert result.stdout.strip() == override
