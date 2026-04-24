"""Integration test: bridge's msft_smartart_loader resolves and imports msft-smartart."""
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = WORKTREE / "plugins" / "jack-tar-superpower-bridge"


def test_loader_imports_engine_render_and_inject(monkeypatch):
    sys.path.insert(0, str(PLUGIN_ROOT))
    # Ensure no stale src.* modules
    for k in list(sys.modules):
        if k == "src" or k.startswith("src."):
            del sys.modules[k]
    monkeypatch.setenv(
        "JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT",
        str(WORKTREE / "plugins" / "jack-tar-msft-smartart"),
    )
    from src.msft_smartart_loader import load_msft_smartart_api
    api = load_msft_smartart_api()
    assert callable(api.engine.render)
    assert callable(api.inject)
    # Build a tiny carrier and verify it's a usable .pptx
    import tempfile
    from pathlib import Path as P
    with tempfile.TemporaryDirectory() as td:
        spec = {"graphic_type": "flowchart", "layout_id": "process1",
                "data": {"items": ["a", "b", "c"]}}
        result = api.engine.render(spec, P(td))
        assert P(result.output_path).exists()
