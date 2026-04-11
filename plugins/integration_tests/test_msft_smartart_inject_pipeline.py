"""Integration test: msft-smartart render + inject pipeline works from plugin root."""
import sys
import json
import importlib
from pathlib import Path
import tempfile

WORKTREE = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = WORKTREE / "plugins" / "jack-tar-msft-smartart"

# Ensure the msft-smartart plugin root is at the front of sys.path.
# Other plugin roots are removed to avoid src/ namespace collision.
_DECKHAND_ROOT = str(WORKTREE / "plugins" / "jack-tar-deckhand")


def _ensure_msft_path():
    """Put msft-smartart plugin root first, remove deckhand root to avoid collision."""
    root = str(PLUGIN_ROOT)
    if _DECKHAND_ROOT in sys.path:
        sys.path.remove(_DECKHAND_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    elif sys.path[0] != root:
        sys.path.remove(root)
        sys.path.insert(0, root)
    # Invalidate cached src.* modules from the deckhand plugin
    for key in list(sys.modules):
        if key == "src" or key.startswith("src."):
            del sys.modules[key]


def test_render_process1_carrier():
    _ensure_msft_path()
    from src.engine import render, RenderResult
    spec = {
        "graphic_type": "flowchart",
        "layout_id": "process1",
        "data": {"items": ["Discover", "Design", "Build", "Ship"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = render(spec, tmpdir)
        assert isinstance(result, RenderResult)
        assert result.output_path.exists()
        assert result.layout_id == "process1"
        assert result.node_count == 4


def test_render_cycle_carrier():
    _ensure_msft_path()
    from src.engine import render, RenderResult
    spec = {
        "graphic_type": "cycle",
        "layout_id": "cycle2",
        "data": {"items": ["Plan", "Execute", "Review"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = render(spec, tmpdir)
        assert isinstance(result, RenderResult)
        assert result.output_path.exists()
        assert result.layout_id == "cycle2"
        assert result.node_count == 3


def test_render_org_chart_carrier():
    _ensure_msft_path()
    from src.engine import render, RenderResult
    # Hierarchical builder expects 'title' not 'text'
    spec = {
        "graphic_type": "org_chart",
        "layout_id": "orgChart1",
        "data": {
            "tree": {
                "title": "CEO",
                "children": [
                    {"title": "CTO", "children": [{"title": "Dev Lead", "children": []}]},
                    {"title": "COO", "children": []},
                ],
            }
        },
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = render(spec, tmpdir)
        assert isinstance(result, RenderResult)
        assert result.output_path.exists()
        assert result.layout_id == "orgChart1"
        assert result.node_count >= 3


def test_catalog_loads_from_plugin_data():
    _ensure_msft_path()
    from src.layouts.catalog import load_catalog, get_entry, list_entries
    load_catalog.cache_clear()
    catalog = load_catalog()
    assert len(catalog["entries"]) >= 27
    entry = get_entry("process1")
    assert entry["id"] == "process1"
    entries = list_entries(v1_only=True)
    assert len(entries) >= 27


def test_layout_fixtures_resolve_to_existing_dirs():
    _ensure_msft_path()
    from src.layouts.catalog import list_entries, resolve_layout_dir, load_catalog
    load_catalog.cache_clear()
    for entry in list_entries(v1_only=True):
        layout_dir = resolve_layout_dir(entry)
        assert layout_dir.exists(), f"Missing: {layout_dir}"
        assert (layout_dir / "layout.xml").exists()
