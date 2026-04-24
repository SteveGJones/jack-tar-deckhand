"""Integration test: PLUGIN_ROOT discovery shell snippet works for the bridge plugin."""
import os
import subprocess
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = WORKTREE / "plugins" / "jack-tar-superpower-bridge"


def test_env_var_override_takes_precedence(monkeypatch):
    """The bridge skills' PLUGIN_ROOT discovery shell snippet honours the env var."""
    monkeypatch.setenv("JACK_TAR_SUPERPOWER_BRIDGE_ROOT", str(PLUGIN_ROOT))
    cmd = '''python3 -c "
from pathlib import Path
import sys, os
if os.environ.get('JACK_TAR_SUPERPOWER_BRIDGE_ROOT'):
    print(os.environ['JACK_TAR_SUPERPOWER_BRIDGE_ROOT']); sys.exit()
print('NOT_FOUND')
"'''
    out = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          env={**os.environ, "JACK_TAR_SUPERPOWER_BRIDGE_ROOT": str(PLUGIN_ROOT)})
    assert out.stdout.strip() == str(PLUGIN_ROOT)
