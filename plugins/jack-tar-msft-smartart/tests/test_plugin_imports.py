"""Verify jack-tar-msft-smartart modules load from plugin directory."""
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))


def test_engine_imports():
    from src.engine import render
    assert callable(render)


def test_data_model_imports():
    from src.data_model import make_node_pt, wrap_data_model
    assert callable(make_node_pt)
    assert callable(wrap_data_model)


def test_catalog_loads():
    from src.layouts.catalog import load_catalog, get_entry
    catalog = load_catalog()
    assert len(catalog["entries"]) >= 27
    entry = get_entry("process1")
    assert entry["id"] == "process1"


def test_layout_fixtures_present():
    from src.layouts.catalog import load_catalog, resolve_layout_dir
    catalog = load_catalog()
    for entry in catalog["entries"]:
        layout_dir = resolve_layout_dir(entry)
        assert layout_dir.exists(), f"Missing layout dir: {layout_dir}"
        assert (layout_dir / "layout.xml").exists(), f"Missing layout.xml in {layout_dir}"


def test_flat_list_builder_imports():
    from src.builders.flat_list import build
    assert callable(build)


def test_hierarchical_builder_imports():
    from src.builders.hierarchical import build
    assert callable(build)


def test_assembler_patch_imports():
    from src.assembler_patch import inject
    assert callable(inject)
