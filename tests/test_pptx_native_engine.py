"""End-to-end smoke tests for the pptx_native engine render() entry point.

Phase 8: the engine now builds carrier .pptx files from scratch
(layout XML files read directly from tests/fixtures/smartart_layouts/)
rather than unzipping seed .pptx files. Tests verify the carrier has
the expected structure but no longer compare against a seed.
"""
from __future__ import annotations

import re
import tempfile
import zipfile
from pathlib import Path

import pytest


def _assert_editable_smartart(
    pptx_path: Path,
    expected_labels: list[str],
    expected_layout_uri_prefix: str,
) -> None:
    """Structural assertions on a rendered pptx — the automated
    proxy for 'PowerPoint treats this as editable SmartArt'."""
    with zipfile.ZipFile(pptx_path, "r") as z:
        names = set(z.namelist())

        # All four diagram parts present.
        for required in [
            "ppt/diagrams/data1.xml",
            "ppt/diagrams/layout1.xml",
            "ppt/diagrams/quickStyle1.xml",
            "ppt/diagrams/colors1.xml",
        ]:
            assert required in names, f"missing: {required}"

        # No cached drawing — PowerPoint regenerates on first open.
        assert "ppt/diagrams/drawing1.xml" not in names

        # Data model carries the expected layout URI (may have variant suffix)
        data_xml = z.read("ppt/diagrams/data1.xml").decode("utf-8")
        assert expected_layout_uri_prefix in data_xml, (
            f"expected layout URI prefix {expected_layout_uri_prefix!r} "
            f"not found in data1.xml"
        )

        for label in expected_labels:
            assert f"<a:t>{label}</a:t>" in data_xml, (
                f"label {label!r} not found in data1.xml"
            )

        # Content types: all four diagram overrides, no drawing1
        ct_xml = z.read("[Content_Types].xml").decode("utf-8")
        assert "/ppt/diagrams/drawing1.xml" not in ct_xml
        for part in ("data1", "layout1", "quickStyle1", "colors1"):
            assert f"/ppt/diagrams/{part}.xml" in ct_xml

        # Slide rels: all four diagram rels, no drawing
        rels_xml = z.read("ppt/slides/_rels/slide1.xml.rels").decode("utf-8")
        assert "drawing1.xml" not in rels_xml
        for rel_type in ("diagramData", "diagramLayout", "diagramQuickStyle", "diagramColors"):
            assert rel_type in rels_xml

        # Slide XML references the diagram via graphicFrame + relIds
        slide_xml = z.read("ppt/slides/slide1.xml").decode("utf-8")
        assert "<p:graphicFrame>" in slide_xml
        assert "dgm:relIds" in slide_xml


def test_render_process1_five_step_end_to_end():
    """Full pipeline: spec → .pptx file with editable SmartArt structure."""
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "flowchart",
        "slide_number": 4,
        "data": {"items": ["Research", "Design", "Build", "Test", "Ship"]},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir)

        assert result.layout_id == "process1"
        # URI may carry a variant suffix — check prefix only
        assert result.layout_uri.startswith(
            "urn:microsoft.com/office/officeart/2005/8/layout/process1"
        )
        assert result.node_count == 5
        assert result.engine == "pptx_native"
        assert result.output_path.exists()
        assert result.output_path.name == "pptx_native_process1_slide4.pptx"

        _assert_editable_smartart(
            result.output_path,
            expected_labels=["Research", "Design", "Build", "Test", "Ship"],
            expected_layout_uri_prefix="urn:microsoft.com/office/officeart/2005/8/layout/process1",
        )


def test_render_without_slide_number_uses_default_name():
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "flowchart",
        "data": {"items": ["A", "B", "C"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir)
        assert result.output_path.name == "pptx_native_process1.pptx"


def test_render_with_explicit_output_name():
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "flowchart",
        "data": {"items": ["A", "B"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir, output_name="custom.pptx")
        assert result.output_path.name == "custom.pptx"


def test_render_creates_output_dir_if_missing():
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "flowchart",
        "data": {"items": ["A", "B"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        nested = Path(tmpdir) / "deep" / "nested" / "dir"
        result = engine.render(spec, nested)
        assert nested.exists()
        assert result.output_path.parent == nested


def test_render_overwrites_existing_output():
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "flowchart",
        "data": {"items": ["A", "B"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        first = engine.render(spec, tmpdir, output_name="out.pptx")

        spec2 = {"graphic_type": "flowchart", "data": {"items": ["X", "Y", "Z"]}}
        second = engine.render(spec2, tmpdir, output_name="out.pptx")
        assert second.output_path == first.output_path
        assert second.node_count == 3

        with zipfile.ZipFile(second.output_path, "r") as z:
            data_xml = z.read("ppt/diagrams/data1.xml")
        assert b"<a:t>X</a:t>" in data_xml
        assert b"<a:t>A</a:t>" not in data_xml  # old data gone


def test_render_rejects_unknown_graphic_type():
    from src.smartart_pptx_native import engine

    spec = {"graphic_type": "nonexistent_type", "data": {"items": ["A", "B"]}}
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(engine.RenderError, match="no pptx_native layout supports"):
            engine.render(spec, tmpdir)


def test_render_rejects_missing_graphic_type():
    from src.smartart_pptx_native import engine

    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(engine.RenderError, match="graphic_type"):
            engine.render({"data": {"items": ["A", "B"]}}, tmpdir)


def test_render_rejects_missing_data():
    from src.smartart_pptx_native import engine

    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(engine.RenderError, match="'data'"):
            engine.render({"graphic_type": "flowchart"}, tmpdir)


def test_render_propagates_builder_validation_errors():
    """A too-long label should bubble up as FlatListBuildError, not RenderError."""
    from src.smartart_pptx_native import engine
    from src.smartart_pptx_native.builders import flat_list

    spec = {
        "graphic_type": "flowchart",
        "data": {"items": ["OK", "A" * 30]},  # exceeds max_label_chars=24
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(flat_list.FlatListBuildError):
            engine.render(spec, tmpdir)


def test_render_produces_structurally_valid_editable_smartart():
    """Same check as the happy path test but as a standalone test so
    future failures point at structural issues distinctly from counting."""
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "flowchart",
        "data": {"items": ["Alpha", "Beta", "Gamma"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir)
        _assert_editable_smartart(
            result.output_path,
            expected_labels=["Alpha", "Beta", "Gamma"],
            expected_layout_uri_prefix="urn:microsoft.com/office/officeart/2005/8/layout/process1",
        )


def test_render_explicit_layout_id_override():
    """Spec can specify layout_id to target a specific variant."""
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "flowchart",
        "layout_id": "hProcess4",
        "data": {"items": ["A", "B", "C"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir)
        assert result.layout_id == "hProcess4"


def test_render_cycle_layout_end_to_end():
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "cycle",
        "data": {"items": ["Plan", "Do", "Check", "Act"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir)
        assert result.layout_id == "cycle2"
        assert result.node_count == 4


def test_render_org_chart_end_to_end():
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "org_chart",
        "data": {
            "tree": {
                "title": "CEO",
                "children": [
                    {"title": "CTO"},
                    {"title": "CFO"},
                ],
            },
        },
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir)
        assert result.layout_id == "orgChart1"
        assert result.node_count == 3  # 3 data nodes (doc is excluded)


def test_render_accepts_legacy_steps_key_for_backward_compat():
    """The flat_list builder accepts 'steps' as an alias for 'items'
    so Phase 1-7 callers still work."""
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "flowchart",
        "data": {"steps": ["Research", "Design"]},  # legacy key
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir)
        assert result.node_count == 2


# ── flat_list dict-item acceptance ──────────────────────────────────


def test_flat_list_accepts_dict_items_with_text_key():
    from src.smartart_pptx_native.builders.flat_list import _extract_items

    catalog_entry = {"id": "process1", "min_nodes": 2, "max_nodes": 9, "max_label_chars": 24}
    extracted = {"items": [{"text": "Plan"}, {"text": "Build"}, {"text": "Ship"}]}
    items = _extract_items(extracted, catalog_entry)
    assert items == ["Plan", "Build", "Ship"]


def test_flat_list_accepts_dict_items_with_label_key():
    from src.smartart_pptx_native.builders.flat_list import _extract_items

    catalog_entry = {"id": "process1", "min_nodes": 2, "max_nodes": 9, "max_label_chars": 24}
    extracted = {"items": [{"label": "Alpha"}, {"label": "Beta"}]}
    items = _extract_items(extracted, catalog_entry)
    assert items == ["Alpha", "Beta"]


def test_flat_list_accepts_mixed_string_and_dict():
    from src.smartart_pptx_native.builders.flat_list import _extract_items

    catalog_entry = {"id": "process1", "min_nodes": 2, "max_nodes": 9, "max_label_chars": 24}
    extracted = {"items": ["Plain", {"text": "Dict"}, {"label": "Label"}]}
    items = _extract_items(extracted, catalog_entry)
    assert items == ["Plain", "Dict", "Label"]
