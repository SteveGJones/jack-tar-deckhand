"""Integration tests — full pipeline for pptx_native through
extract → render → manifest schema validation.

These exercise the complete Phase 2 wiring end-to-end, beyond the
unit-level coverage in test_pptx_native_dispatch.py and
test_pptx_native_extractor.py.
"""
from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

import jsonschema
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


def _manifest_schema():
    schema_path = (
        Path(__file__).resolve().parent.parent
        / "src" / "schemas" / "smartart_manifest.schema.json"
    )
    with schema_path.open() as f:
        return json.load(f)


def test_full_pipeline_single_slide_pptx_native_flowchart():
    """Slide with body_points → extract → render → valid manifest entry."""
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {
        "slide_number": 1,
        "headline": "Development Process",
        "body_points": ["Research", "Design", "Build", "Test", "Ship"],
    }
    selection = {
        "slide_number": 1,
        "graphic_type": "flowchart",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }

    spec = extract(slide, selection, STYLE_GUIDE)
    assert spec["validation_status"] == "valid"

    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, STYLE_GUIDE, "production", tmpdir)

        assert entry["status"] == "rendered"
        assert entry["engine_used"] == "pptx_native"
        assert Path(entry["file_path"]).exists()

        # Schema validation
        jsonschema.validate({"graphics": [entry]}, _manifest_schema())

        # Content check: the five step labels must appear in data1.xml
        with zipfile.ZipFile(entry["file_path"], "r") as z:
            data_xml = z.read("ppt/diagrams/data1.xml").decode("utf-8")
        for label in ["Research", "Design", "Build", "Test", "Ship"]:
            assert f"<a:t>{label}</a:t>" in data_xml


def test_full_pipeline_multi_slide_manifest():
    """Multiple slides in one manifest — typical deck-level scenario."""
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slides = [
        {
            "slide_number": 1,
            "headline": "Phase 1",
            "body_points": ["Plan", "Execute"],
        },
        {
            "slide_number": 5,
            "headline": "Phase 2",
            "body_points": ["Design", "Build", "Test", "Ship"],
        },
        {
            "slide_number": 9,
            "headline": "Phase 3",
            "body_points": ["Review", "Refine", "Release"],
        },
    ]
    selections = [
        {
            "slide_number": s["slide_number"],
            "graphic_type": "flowchart",
            "enrichment_tier": "pure_programmatic",
            "engine": "pptx_native",
        }
        for s in slides
    ]

    manifest = {"graphics": []}
    with tempfile.TemporaryDirectory() as tmpdir:
        for slide, selection in zip(slides, selections):
            spec = extract(slide, selection, STYLE_GUIDE)
            entry = render(spec, STYLE_GUIDE, "production", tmpdir)
            manifest["graphics"].append(entry)

        assert len(manifest["graphics"]) == 3
        assert all(e["status"] == "rendered" for e in manifest["graphics"])
        assert all(e["engine_used"] == "pptx_native" for e in manifest["graphics"])

        # Output filenames are disambiguated by slide_number.
        filenames = [Path(e["file_path"]).name for e in manifest["graphics"]]
        assert len(set(filenames)) == 3

        # Full manifest validates.
        jsonschema.validate(manifest, _manifest_schema())


def test_full_pipeline_with_overflow_violation_produces_failed_entry():
    """Label exceeding max_label_chars → render fails gracefully with
    status='failed', not a hard exception."""
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {
        "slide_number": 1,
        "body_points": ["OK label", "X" * 30],  # 30 > 24
    }
    selection = {
        "slide_number": 1,
        "graphic_type": "flowchart",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)

    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, STYLE_GUIDE, "production", tmpdir)

    assert entry["status"] == "failed"
    assert entry["engine_used"] == "pptx_native"


def test_full_pipeline_with_too_few_steps_produces_failed_entry():
    """Single step fails min_nodes=2 constraint."""
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {"slide_number": 1, "body_points": ["Lonely"]}
    selection = {
        "slide_number": 1,
        "graphic_type": "flowchart",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)

    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, STYLE_GUIDE, "production", tmpdir)

    assert entry["status"] == "failed"


def test_full_pipeline_with_inline_data_passthrough():
    """Pre-structured inline_data should take precedence over body_points."""
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {
        "slide_number": 1,
        "body_points": ["these should be ignored"],
        "data": {
            "inline_data": {"steps": ["From", "Inline", "Data"]}
        },
    }
    selection = {
        "slide_number": 1,
        "graphic_type": "flowchart",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)
    assert spec["data"] == {"steps": ["From", "Inline", "Data"]}

    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, STYLE_GUIDE, "production", tmpdir)
        assert entry["status"] == "rendered"

        with zipfile.ZipFile(entry["file_path"], "r") as z:
            data_xml = z.read("ppt/diagrams/data1.xml").decode("utf-8")
        assert "<a:t>From</a:t>" in data_xml
        assert "<a:t>Inline</a:t>" in data_xml
        assert "<a:t>Data</a:t>" in data_xml
        assert b"ignored" not in data_xml.encode()


def test_full_pipeline_manifest_entry_has_all_required_fields():
    """Defensive: every required field in the manifest schema is populated."""
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {"slide_number": 3, "body_points": ["A", "B"]}
    selection = {
        "slide_number": 3,
        "graphic_type": "flowchart",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)

    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, STYLE_GUIDE, "production", tmpdir)

    required = {
        "smartart_id", "slide_number", "graphic_type", "engine_used",
        "enrichment_tier", "file_path", "status",
    }
    assert required.issubset(entry.keys())
    assert entry["smartart_id"] == "sa-slide-3-flowchart"
