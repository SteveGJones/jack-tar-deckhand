"""Tests for the pptx_native layout catalog loader."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_catalog_loads_without_error():
    """Catalog file is valid JSON and passes schema validation."""
    from src.smartart_pptx_native.layouts import catalog

    catalog.load_catalog.cache_clear()
    result = catalog.load_catalog()
    assert result["version"] == "2.0.0"
    assert isinstance(result["entries"], list)
    assert len(result["entries"]) >= 27  # Phase 8 minimum


def test_catalog_has_process1_entry():
    """process1 is one of the Phase 8 canonical Process layouts."""
    from src.smartart_pptx_native.layouts import catalog

    entry = catalog.get_entry("process1")
    assert entry["layout_uri"].startswith(
        "urn:microsoft.com/office/officeart/2005/8/layout/process1"
    )
    assert entry["category"] == "Process"
    assert entry["v1"] is True
    assert entry["engine"] == "pptx_native"
    assert entry["data_shape"] == "flat_list"
    assert entry["node_type_capabilities"] == []
    assert entry["min_nodes"] >= 2
    assert entry["max_nodes"] >= 5
    assert entry["max_label_chars"] >= 10
    assert "flowchart" in entry["integration"]["smartart_type_mappings"]


def test_catalog_has_orgchart1_entry_with_asst():
    """orgChart1 is Phase 8's hierarchical layout with assistant support."""
    from src.smartart_pptx_native.layouts import catalog

    entry = catalog.get_entry("orgChart1")
    assert entry["category"] == "Hierarchy"
    assert entry["data_shape"] == "hierarchical"
    assert entry["node_type_capabilities"] == ["asst"]
    assert "org_chart" in entry["integration"]["smartart_type_mappings"]


def test_catalog_covers_all_core_categories():
    """Phase 8 should have at least one layout in each of the core
    categories: Process, Cycle, Hierarchy, List, Matrix, Pyramid,
    Relationship."""
    from src.smartart_pptx_native.layouts import catalog

    categories = {
        e["category"] for e in catalog.list_entries(v1_only=True)
    }
    for required in ("Process", "Cycle", "Hierarchy", "List", "Matrix", "Pyramid", "Relationship"):
        assert required in categories, (
            f"no v1 catalog entries in category {required!r}"
        )


def test_get_entry_raises_for_unknown_id():
    from src.smartart_pptx_native.layouts import catalog

    with pytest.raises(catalog.CatalogError, match="no catalog entry"):
        catalog.get_entry("notarealthing")


def test_list_entries_v1_only_filter():
    from src.smartart_pptx_native.layouts import catalog

    all_entries = catalog.list_entries()
    v1_entries = catalog.list_entries(v1_only=True)
    assert len(v1_entries) <= len(all_entries)
    for entry in v1_entries:
        assert entry["v1"] is True


def test_resolve_layout_dir_points_at_real_directory():
    """Every v1 catalog entry must reference a layout_dir that exists
    and contains the extracted XML files."""
    from src.smartart_pptx_native.layouts import catalog

    for entry in catalog.list_entries(v1_only=True):
        layout_dir = catalog.resolve_layout_dir(entry)
        assert layout_dir.exists(), f"layout_dir missing for {entry['id']}: {layout_dir}"
        assert layout_dir.is_dir()
        assert (layout_dir / "layout.xml").exists()
        assert (layout_dir / "quickStyle.xml").exists()
        assert (layout_dir / "colors.xml").exists()


def test_get_layout_id_for_graphic_type():
    from src.smartart_pptx_native.layouts import catalog

    # flowchart is backed by multiple process layouts; the lookup
    # returns the first match in catalog order
    result = catalog.get_layout_id_for_graphic_type("flowchart")
    assert result is not None
    assert catalog.get_layout_id_for_graphic_type("nonexistent") is None


def test_list_layout_ids_for_graphic_type_returns_all_candidates():
    from src.smartart_pptx_native.layouts import catalog

    # flowchart should have multiple backing layouts (process1,
    # hProcess4, hProcess7, hProcess9, etc.)
    flowchart_layouts = catalog.list_layout_ids_for_graphic_type("flowchart")
    assert len(flowchart_layouts) >= 2, (
        "flowchart should be backed by multiple process layouts"
    )
    # org_chart should have exactly one (orgChart1 is canonical)
    org_layouts = catalog.list_layout_ids_for_graphic_type("org_chart")
    assert "orgChart1" in org_layouts


def test_catalog_rejects_duplicate_ids(tmp_path, monkeypatch):
    """Semantic check: catalog with duplicate ids should fail load."""
    from src.smartart_pptx_native.layouts import catalog

    # Build a bad catalog with two process1 entries
    good = catalog.load_catalog()
    bad = {
        "version": good["version"],
        "entries": good["entries"] + [good["entries"][0]],  # duplicate
    }
    bad_path = tmp_path / "catalog.json"
    bad_path.write_text(json.dumps(bad))

    monkeypatch.setattr(catalog, "_CATALOG_PATH", bad_path)
    catalog.load_catalog.cache_clear()
    with pytest.raises(catalog.CatalogError, match="duplicate"):
        catalog.load_catalog()
    catalog.load_catalog.cache_clear()  # reset for other tests


def test_catalog_rejects_inverted_min_max(tmp_path, monkeypatch):
    """Semantic check: min_nodes > max_nodes should fail."""
    from src.smartart_pptx_native.layouts import catalog

    good = catalog.load_catalog()
    entry_copy = dict(good["entries"][0])
    entry_copy["min_nodes"] = 10
    entry_copy["max_nodes"] = 5
    bad = {"version": good["version"], "entries": [entry_copy]}
    bad_path = tmp_path / "catalog.json"
    bad_path.write_text(json.dumps(bad))

    monkeypatch.setattr(catalog, "_CATALOG_PATH", bad_path)
    catalog.load_catalog.cache_clear()
    with pytest.raises(catalog.CatalogError, match="min_nodes"):
        catalog.load_catalog()
    catalog.load_catalog.cache_clear()


def test_schema_file_is_valid_json_schema():
    """The schema file itself must be valid JSON and parseable by jsonschema."""
    import jsonschema

    schema_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "smartart_pptx_native"
        / "layouts"
        / "catalog.schema.json"
    )
    with schema_path.open() as f:
        schema = json.load(f)
    jsonschema.Draft7Validator.check_schema(schema)
