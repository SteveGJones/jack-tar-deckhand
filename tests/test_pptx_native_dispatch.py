"""Tests for pptx_native integration with smartart_renderer dispatch."""
from __future__ import annotations

import json
import os
import tempfile
import zipfile
from pathlib import Path

import pytest


STYLE_GUIDE = {
    "palette": {
        "primary": "1a73e8",
        "accent": "e8710a",
        "background": "ffffff",
        "text_primary": "1a1a1a",
        "chart_series": ["2B6CB0", "ED8936", "38A169", "E53E3E"],
    },
    "typography": {"heading_font": "Inter", "body_font": "Inter"},
}


def test_pptx_native_registered_in_engine_dispatch():
    from src import smartart_renderer

    assert "pptx_native" in smartart_renderer._ENGINE_DISPATCH
    dispatch_fn = smartart_renderer._ENGINE_DISPATCH["pptx_native"]
    assert callable(dispatch_fn)


def test_render_pptx_native_engine_adapter_returns_pptx_path():
    """The adapter function should return a string path to an existing .pptx file."""
    from src.smartart_renderer import render_pptx_native_engine

    spec = {
        "slide_number": 4,
        "graphic_type": "flowchart",
        "data": {"steps": ["Research", "Design", "Build", "Test", "Ship"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        path_str = render_pptx_native_engine(spec, STYLE_GUIDE, tmpdir)
        path = Path(path_str)
        assert path.exists()
        assert path.suffix == ".pptx"
        assert path.stat().st_size > 1000


def test_top_level_render_dispatches_to_pptx_native():
    """Full smartart_renderer.render() path with engine='pptx_native'."""
    from src.smartart_renderer import render

    spec = {
        "slide_number": 7,
        "graphic_type": "flowchart",
        "engine": "pptx_native",
        "enrichment_tier": "pure_programmatic",
        "data": {"steps": ["Plan", "Do", "Check", "Act"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, STYLE_GUIDE, "production", tmpdir)

        assert entry["engine_used"] == "pptx_native"
        assert entry["graphic_type"] == "flowchart"
        assert entry["slide_number"] == 7
        assert entry["status"] == "rendered"
        assert entry["file_path"].endswith(".pptx")
        assert Path(entry["file_path"]).exists()
        # pptx_native has no SVG source
        assert entry["svg_source_path"] == ""


def test_render_pptx_native_produces_valid_editable_smartart_structure():
    """The carrier .pptx returned from dispatch must have all four
    diagram parts and no cached drawing — the same guarantees the
    standalone engine tests enforce."""
    from src.smartart_renderer import render

    spec = {
        "slide_number": 1,
        "graphic_type": "flowchart",
        "engine": "pptx_native",
        "enrichment_tier": "pure_programmatic",
        "data": {"steps": ["Alpha", "Beta", "Gamma"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, STYLE_GUIDE, "production", tmpdir)
        assert entry["status"] == "rendered"

        with zipfile.ZipFile(entry["file_path"], "r") as z:
            names = set(z.namelist())

        assert "ppt/diagrams/data1.xml" in names
        assert "ppt/diagrams/layout1.xml" in names
        assert "ppt/diagrams/quickStyle1.xml" in names
        assert "ppt/diagrams/colors1.xml" in names
        assert "ppt/diagrams/drawing1.xml" not in names


def test_render_pptx_native_with_builder_error_sets_status_failed():
    """If the pptx_native engine raises (e.g. too-long label), the
    top-level renderer should catch and return status='failed'."""
    from src.smartart_renderer import render

    spec = {
        "slide_number": 1,
        "graphic_type": "flowchart",
        "engine": "pptx_native",
        "enrichment_tier": "pure_programmatic",
        "data": {"steps": ["OK", "A" * 30]},  # exceeds max_label_chars=24
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, STYLE_GUIDE, "production", tmpdir)
    assert entry["status"] == "failed"
    assert entry["engine_used"] == "pptx_native"


def test_manifest_entry_validates_against_schema_with_pptx_native():
    """Entry produced by pptx_native dispatch must satisfy the manifest schema."""
    import jsonschema
    from src.smartart_renderer import render

    spec = {
        "slide_number": 2,
        "graphic_type": "flowchart",
        "engine": "pptx_native",
        "enrichment_tier": "pure_programmatic",
        "data": {"steps": ["A", "B", "C"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, STYLE_GUIDE, "production", tmpdir)

    schema_path = (
        Path(__file__).resolve().parent.parent
        / "src" / "schemas" / "smartart_manifest.schema.json"
    )
    with schema_path.open() as f:
        schema = json.load(f)

    doc = {"graphics": [entry]}
    jsonschema.validate(doc, schema)
