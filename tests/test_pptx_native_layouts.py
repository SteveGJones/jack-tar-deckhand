"""Sanity tests for extracted SmartArt layout fixtures.

Each catalog entry's layout_dir must contain a minimum of:
  - layout.xml    (with uniqueId matching the catalog entry's layout_uri
                   base name)
  - quickStyle.xml
  - colors.xml
  - meta.json     (produced by tools/extract_smartart_layouts.py)

These tests replace the Phase 1-7 .pptx seed tests. The equivalent
checks now operate on extracted XML directories rather than on
unzipped seed .pptx files.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from src.smartart_pptx_native.layouts import catalog


def _get_v1_entries():
    return catalog.list_entries(v1_only=True)


@pytest.mark.parametrize(
    "entry", _get_v1_entries(), ids=lambda e: e["id"]
)
def test_layout_dir_exists(entry):
    layout_dir = catalog.resolve_layout_dir(entry)
    assert layout_dir.exists(), (
        f"layout_dir missing for {entry['id']}: {layout_dir}. "
        "Run tools/extract_smartart_layouts.py --sdk to populate fixtures."
    )
    assert layout_dir.is_dir()


@pytest.mark.parametrize(
    "entry", _get_v1_entries(), ids=lambda e: e["id"]
)
def test_layout_dir_contains_four_required_files(entry):
    layout_dir = catalog.resolve_layout_dir(entry)
    for required in ("layout.xml", "quickStyle.xml", "colors.xml", "meta.json"):
        path = layout_dir / required
        assert path.exists(), (
            f"entry {entry['id']!r} layout_dir is missing {required}"
        )
        assert path.stat().st_size > 0, (
            f"entry {entry['id']!r} {required} is empty"
        )


@pytest.mark.parametrize(
    "entry", _get_v1_entries(), ids=lambda e: e["id"]
)
def test_layout_xml_has_matching_unique_id(entry):
    """The layout.xml's uniqueId must match the catalog entry's layout_uri.

    Variant suffixes (#N) are preserved by the extraction script — the
    catalog entry stores whatever variant the SDK fixture had.
    """
    layout_dir = catalog.resolve_layout_dir(entry)
    layout_xml = (layout_dir / "layout.xml").read_text(encoding="utf-8")

    m = re.search(r'uniqueId="([^"]+)"', layout_xml)
    assert m is not None, (
        f"entry {entry['id']!r} layout.xml has no uniqueId attribute"
    )
    declared_uri = m.group(1)
    assert declared_uri == entry["layout_uri"], (
        f"entry {entry['id']!r} layout_uri mismatch: "
        f"catalog says {entry['layout_uri']!r} but "
        f"layout.xml has {declared_uri!r}. "
        f"Re-run extraction or update catalog."
    )


@pytest.mark.parametrize(
    "entry", _get_v1_entries(), ids=lambda e: e["id"]
)
def test_quickstyle_xml_has_matching_unique_id(entry):
    layout_dir = catalog.resolve_layout_dir(entry)
    quickstyle_xml = (layout_dir / "quickStyle.xml").read_text(encoding="utf-8")
    m = re.search(r'uniqueId="([^"]+)"', quickstyle_xml)
    assert m is not None, (
        f"entry {entry['id']!r} quickStyle.xml has no uniqueId attribute"
    )
    assert m.group(1) == entry["qs_type_id"], (
        f"entry {entry['id']!r} qs_type_id mismatch between catalog and quickStyle.xml"
    )


@pytest.mark.parametrize(
    "entry", _get_v1_entries(), ids=lambda e: e["id"]
)
def test_colors_xml_has_matching_unique_id(entry):
    layout_dir = catalog.resolve_layout_dir(entry)
    colors_xml = (layout_dir / "colors.xml").read_text(encoding="utf-8")
    m = re.search(r'uniqueId="([^"]+)"', colors_xml)
    assert m is not None, (
        f"entry {entry['id']!r} colors.xml has no uniqueId attribute"
    )
    assert m.group(1) == entry["cs_type_id"], (
        f"entry {entry['id']!r} cs_type_id mismatch between catalog and colors.xml"
    )


@pytest.mark.parametrize(
    "entry", _get_v1_entries(), ids=lambda e: e["id"]
)
def test_meta_json_records_source_file(entry):
    layout_dir = catalog.resolve_layout_dir(entry)
    meta = json.loads((layout_dir / "meta.json").read_text())
    assert "source_file" in meta, f"meta.json for {entry['id']} has no source_file"
    assert meta["source_file"], f"meta.json for {entry['id']} has empty source_file"
    assert "layout_uri" in meta
    assert meta["layout_uri"] == entry["layout_uri"]


def test_every_v1_catalog_entry_has_a_layout_dir():
    """Tripwire: if anyone adds a v1 catalog entry without populating
    the fixture dir, this test catches it immediately."""
    v1_entries = catalog.list_entries(v1_only=True)
    assert len(v1_entries) >= 1, "no v1 catalog entries"
    for entry in v1_entries:
        layout_dir = catalog.resolve_layout_dir(entry)
        assert layout_dir.exists(), (
            f"catalog declares v1 entry {entry['id']!r} but the "
            f"layout_dir {layout_dir} doesn't exist"
        )


def test_blank_slide_host_exists_and_is_valid():
    """The injection host fixture (used by Phase 3 tests) is NOT a
    SmartArt seed — it's a presentation with no diagram parts at all."""
    import zipfile
    host_path = (
        Path(__file__).resolve().parent.parent
        / "tests" / "fixtures" / "smartart_seeds" / "blank_slide.pptx"
    )
    assert host_path.exists()
    assert zipfile.is_zipfile(host_path)

    with zipfile.ZipFile(host_path, "r") as z:
        names = set(z.namelist())

    diagram_parts = [n for n in names if n.startswith("ppt/diagrams/")]
    assert diagram_parts == [], (
        f"blank_slide.pptx unexpectedly contains diagram parts: {diagram_parts}"
    )
