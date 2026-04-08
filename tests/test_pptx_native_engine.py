"""End-to-end smoke tests for the pptx_native engine render() entry point."""
from __future__ import annotations

import re
import tempfile
import zipfile
from pathlib import Path

import pytest


def test_render_process1_five_step_end_to_end():
    """Full pipeline: spec → .pptx file with editable SmartArt structure."""
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "flowchart",
        "slide_number": 4,
        "data": {"steps": ["Research", "Design", "Build", "Test", "Ship"]},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir)

        assert result.layout_id == "process1"
        assert result.layout_uri == (
            "urn:microsoft.com/office/officeart/2005/8/layout/process1"
        )
        assert result.node_count == 5
        assert result.engine == "pptx_native"
        assert result.output_path.exists()
        assert result.output_path.name == "pptx_native_process1_slide4.pptx"

        _assert_editable_smartart(result.output_path, expected_labels=[
            "Research", "Design", "Build", "Test", "Ship"
        ])


def test_render_without_slide_number_uses_default_name():
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "flowchart",
        "data": {"steps": ["A", "B", "C"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir)
        assert result.output_path.name == "pptx_native_process1.pptx"


def test_render_with_explicit_output_name():
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "flowchart",
        "data": {"steps": ["A", "B"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir, output_name="custom.pptx")
        assert result.output_path.name == "custom.pptx"


def test_render_creates_output_dir_if_missing():
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "flowchart",
        "data": {"steps": ["A", "B"]},
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
        "data": {"steps": ["A", "B"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        first = engine.render(spec, tmpdir, output_name="out.pptx")
        first_size = first.output_path.stat().st_size

        # Render again with different data — should overwrite
        spec2 = {"graphic_type": "flowchart", "data": {"steps": ["X", "Y", "Z"]}}
        second = engine.render(spec2, tmpdir, output_name="out.pptx")
        assert second.output_path == first.output_path
        assert second.node_count == 3

        with zipfile.ZipFile(second.output_path, "r") as z:
            data_xml = z.read("ppt/diagrams/data1.xml")
        assert b"<a:t>X</a:t>" in data_xml
        assert b"<a:t>A</a:t>" not in data_xml  # old data gone


def test_render_rejects_unknown_graphic_type():
    from src.smartart_pptx_native import engine

    spec = {"graphic_type": "nonexistent_type", "data": {"steps": ["A", "B"]}}
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(engine.RenderError, match="no pptx_native layout supports"):
            engine.render(spec, tmpdir)


def test_render_rejects_missing_graphic_type():
    from src.smartart_pptx_native import engine

    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(engine.RenderError, match="graphic_type"):
            engine.render({"data": {"steps": ["A", "B"]}}, tmpdir)


def test_render_rejects_missing_data():
    from src.smartart_pptx_native import engine

    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(engine.RenderError, match="'data'"):
            engine.render({"graphic_type": "flowchart"}, tmpdir)


def test_render_propagates_builder_validation_errors():
    """A too-long label should bubble up as ProcessBuildError, not RenderError."""
    from src.smartart_pptx_native import engine
    from src.smartart_pptx_native.layouts import process

    spec = {
        "graphic_type": "flowchart",
        "data": {"steps": ["OK", "A" * 30]},  # exceeds max_label_chars=24
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(process.ProcessBuildError):
            engine.render(spec, tmpdir)


def _assert_editable_smartart(pptx_path: Path, expected_labels: list[str]) -> None:
    """Structural assertions on a rendered pptx — the automated
    proxy for 'PowerPoint treats this as editable SmartArt'.

    The only 100% proof is opening in PowerPoint, but these checks
    catch 95%+ of the ways a render could go wrong before it ever
    hits PowerPoint.
    """
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

        # The cached drawing MUST be absent — it was deleted deliberately.
        assert "ppt/diagrams/drawing1.xml" not in names, (
            "drawing1.xml should have been deleted; its presence would "
            "cause PowerPoint to render the stale cache instead of "
            "regenerating from layout1.xml"
        )

        # Data model carries the expected layout URI and labels.
        data_xml = z.read("ppt/diagrams/data1.xml")
        assert (
            b'loTypeId="urn:microsoft.com/office/officeart/2005/8/layout/process1"'
            in data_xml
        )
        for label in expected_labels:
            assert f"<a:t>{label}</a:t>".encode() in data_xml, (
                f"label {label!r} not found in data1.xml"
            )

        # Content types: no drawing1 override, all four diagram overrides present.
        ct_xml = z.read("[Content_Types].xml").decode("utf-8")
        assert "/ppt/diagrams/drawing1.xml" not in ct_xml
        for part in ["data1", "layout1", "quickStyle1", "colors1"]:
            assert f'/ppt/diagrams/{part}.xml' in ct_xml

        # Slide rels: no diagramDrawing relationship, all four diagram rels present.
        rels_xml = z.read("ppt/slides/_rels/slide1.xml.rels").decode("utf-8")
        assert "drawing1.xml" not in rels_xml
        for rel_type in ["diagramData", "diagramLayout", "diagramQuickStyle", "diagramColors"]:
            assert rel_type in rels_xml

        # Slide XML: the graphic frame must reference the diagram.
        slide_xml = z.read("ppt/slides/slide1.xml").decode("utf-8")
        assert "dgm:relIds" in slide_xml or "<p:graphicFrame>" in slide_xml


def test_render_produces_structurally_valid_editable_smartart():
    """Same check as the happy path test but as a standalone test so
    future failures point at structural issues distinctly from counting."""
    from src.smartart_pptx_native import engine

    spec = {
        "graphic_type": "flowchart",
        "data": {"steps": ["Alpha", "Beta", "Gamma"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir)
        _assert_editable_smartart(result.output_path, ["Alpha", "Beta", "Gamma"])


def test_render_output_differs_only_in_expected_files_from_seed():
    """Surgical diff guarantee — the output should differ from the seed
    in exactly four places: data1.xml (rewritten), drawing1.xml (removed),
    [Content_Types].xml (patched), slide1.xml.rels (patched). Every
    other file must be byte-identical."""
    from src.smartart_pptx_native import engine
    from src.smartart_pptx_native.layouts import catalog

    spec = {
        "graphic_type": "flowchart",
        "data": {"steps": ["A", "B", "C"]},
    }
    seed_path = catalog.resolve_seed_path(catalog.get_entry("process1"))

    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir)

        with zipfile.ZipFile(seed_path, "r") as seed_zip:
            seed_names = set(seed_zip.namelist())
            seed_contents = {n: seed_zip.read(n) for n in seed_names}

        with zipfile.ZipFile(result.output_path, "r") as out_zip:
            out_names = set(out_zip.namelist())
            out_contents = {n: out_zip.read(n) for n in out_names}

    # Files removed from seed to output:
    removed = seed_names - out_names
    assert removed == {"ppt/diagrams/drawing1.xml"}, removed

    # Files added to output:
    added = out_names - seed_names
    assert added == set(), added

    # Files present in both — check which differ.
    differing = {
        n for n in (seed_names & out_names)
        if seed_contents[n] != out_contents[n]
    }
    assert differing == {
        "ppt/diagrams/data1.xml",
        "[Content_Types].xml",
        "ppt/slides/_rels/slide1.xml.rels",
    }, f"unexpected differences: {differing}"
