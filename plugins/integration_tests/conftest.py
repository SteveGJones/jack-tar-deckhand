"""Shared fixtures for cross-plugin integration tests.

Each plugin has its own `src/` package. Since multiple plugins share the `src`
namespace, we clear sys.modules['src.*'] before each test that sets PLUGIN_ROOT
at the module level — this prevents the cached src from the first-run plugin
shadowing imports in subsequent test modules.
"""
import sys
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[2]
MSFT_SMARTART_ROOT = WORKTREE / "plugins" / "jack-tar-msft-smartart"
DECKHAND_ROOT = WORKTREE / "plugins" / "jack-tar-deckhand"


@pytest.fixture(autouse=True)
def _isolate_src_namespace(request):
    """Before each test, clear cached src.* modules and ensure the test
    module's PLUGIN_ROOT is at the front of sys.path."""
    module = request.module
    plugin_root = getattr(module, "PLUGIN_ROOT", None)
    if plugin_root is not None:
        plugin_path = str(plugin_root)
        # Clear any cached src.* modules from previous plugins
        for key in list(sys.modules.keys()):
            if key == "src" or key.startswith("src."):
                del sys.modules[key]
        # Ensure this plugin's root is at position 0
        if plugin_path in sys.path:
            sys.path.remove(plugin_path)
        sys.path.insert(0, plugin_path)
    yield
