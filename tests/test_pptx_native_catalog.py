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
    assert result["version"] == "1.0.0"
    assert isinstance(result["entries"], list)
    assert len(result["entries"]) >= 1


def test_catalog_has_process1_entry():
    """Process1 is the v1 seed layout — must be present and fully populated."""
    from src.smartart_pptx_native.layouts import catalog

    entry = catalog.get_entry("process1")
    assert entry["layout_uri"] == "urn:microsoft.com/office/officeart/2005/8/layout/process1"
    assert entry["category"] == "Process"
    assert entry["v1"] is True
    assert entry["engine"] == "pptx_native"
    assert entry["data_shape"] == "flat_list"
    assert entry["node_type_capabilities"] == []
    assert entry["min_nodes"] == 2
    assert entry["max_nodes"] == 9
    assert entry["max_label_chars"] == 24
    assert "Sequential" in " ".join(entry["when_to_use"])
    assert entry["integration"]["smartart_type_mappings"] == ["flowchart"]


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


def test_resolve_seed_path_points_at_real_file():
    """Every v1 catalog entry must reference a seed file that exists."""
    from src.smartart_pptx_native.layouts import catalog

    for entry in catalog.list_entries(v1_only=True):
        seed = catalog.resolve_seed_path(entry)
        assert seed.exists(), f"seed missing for {entry['id']}: {seed}"
        assert seed.suffix == ".pptx"


def test_get_layout_id_for_graphic_type():
    from src.smartart_pptx_native.layouts import catalog

    assert catalog.get_layout_id_for_graphic_type("flowchart") == "process1"
    assert catalog.get_layout_id_for_graphic_type("nonexistent") is None


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
