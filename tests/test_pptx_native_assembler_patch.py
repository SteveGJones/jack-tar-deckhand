"""Tests for src.smartart_pptx_native.assembler_patch injection module."""
from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BLANK_SLIDE_PATH = REPO_ROOT / "tests" / "fixtures" / "smartart_seeds" / "blank_slide.pptx"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_host_with_placeholder(
    dest_path: Path,
    slide_number: int = 1,
    placeholder_name: str = "pptx_native_placeholder_1",
    x: int = 914400,
    y: int = 2057400,
    cx: int = 10363200,
    cy = 2743200,
) -> Path:
    """Copy blank_slide.pptx and inject a placeholder <p:sp> into its
    only slide, returning the modified copy path.

    The placeholder is a simple rectangle with the given name and
    xfrm, placed as the last shape in the spTree before </p:spTree>.
    """
    shutil.copy(BLANK_SLIDE_PATH, dest_path)

    with zipfile.ZipFile(dest_path, "r") as zin:
        contents = {info.filename: zin.read(info.filename) for info in zin.infolist()}
        infos = {info.filename: info for info in zin.infolist()}

    slide_xml_name = f"ppt/slides/slide{slide_number}.xml"
    slide_xml = contents[slide_xml_name].decode("utf-8")

    # Determine next shape id
    ids = [int(m) for m in re.findall(r'<p:cNvPr id="(\d+)"', slide_xml)]
    next_id = (max(ids) + 1) if ids else 1

    placeholder_sp = (
        "<p:sp>"
        "<p:nvSpPr>"
        f'<p:cNvPr id="{next_id}" name="{placeholder_name}"/>'
        '<p:cNvSpPr><a:spLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noGrp="1"/></p:cNvSpPr>'
        "<p:nvPr/>"
        "</p:nvSpPr>"
        "<p:spPr>"
        f'<a:xfrm xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        f'<a:off x="{x}" y="{y}"/>'
        f'<a:ext cx="{cx}" cy="{cy}"/>'
        "</a:xfrm>"
        '<a:prstGeom xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" prst="rect"><a:avLst/></a:prstGeom>'
        "</p:spPr>"
        "<p:txBody>"
        '<a:bodyPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>'
        '<a:lstStyle xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>'
        '<a:p xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:endParaRPr lang="en-GB"/></a:p>'
        "</p:txBody>"
        "</p:sp>"
    )
    new_slide_xml = slide_xml.replace("</p:spTree>", placeholder_sp + "</p:spTree>")
    contents[slide_xml_name] = new_slide_xml.encode("utf-8")

    with zipfile.ZipFile(dest_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in contents.items():
            info = infos.get(name)
            if info is not None:
                zout.writestr(info, data)
            else:
                zout.writestr(name, data)

    return dest_path


def _make_carrier_pptx(dest_path: Path, steps: list[str]) -> Path:
    """Produce a pptx_native carrier .pptx via the real engine."""
    from src.smartart_pptx_native import engine

    spec = {"graphic_type": "flowchart", "data": {"steps": steps}}
    result = engine.render(spec, dest_path.parent, output_name=dest_path.name)
    return result.output_path


# ---------------------------------------------------------------------------
# Unit tests — parsing helpers
# ---------------------------------------------------------------------------

def test_allocate_rids_from_empty():
    from src.smartart_pptx_native.assembler_patch import _allocate_rids

    rids = _allocate_rids('<Relationships xmlns="x"></Relationships>', count=4)
    assert rids == ["rId1", "rId2", "rId3", "rId4"]


def test_allocate_rids_skips_existing():
    from src.smartart_pptx_native.assembler_patch import _allocate_rids

    rels = (
        '<Relationships xmlns="x">'
        '<Relationship Id="rId1" Type="x" Target="y"/>'
        '<Relationship Id="rId7" Type="x" Target="y"/>'
        '</Relationships>'
    )
    rids = _allocate_rids(rels, count=4)
    assert rids == ["rId8", "rId9", "rId10", "rId11"]


def test_next_free_diagram_number_empty_host():
    from src.smartart_pptx_native.assembler_patch import _next_free_diagram_number

    assert _next_free_diagram_number(set()) == 1


def test_next_free_diagram_number_host_with_diagrams():
    from src.smartart_pptx_native.assembler_patch import _next_free_diagram_number

    names = {"ppt/diagrams/data1.xml", "ppt/diagrams/data2.xml"}
    assert _next_free_diagram_number(names) == 3


def test_next_free_diagram_number_skips_gaps():
    from src.smartart_pptx_native.assembler_patch import _next_free_diagram_number

    names = {"ppt/diagrams/data2.xml", "ppt/diagrams/data3.xml"}
    assert _next_free_diagram_number(names) == 1


def test_extract_placeholder_xfrm_happy_path():
    from src.smartart_pptx_native.assembler_patch import _extract_placeholder_xfrm

    slide = (
        '<p:sld><p:cSld><p:spTree>'
        '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
        '<p:spPr><a:xfrm><a:off x="100" y="200"/><a:ext cx="300" cy="400"/></a:xfrm></p:spPr></p:sp>'
        '<p:sp><p:nvSpPr><p:cNvPr id="3" name="pptx_native_placeholder_1"/>'
        '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
        '<p:spPr><a:xfrm><a:off x="914400" y="2057400"/>'
        '<a:ext cx="10363200" cy="2743200"/></a:xfrm></p:spPr></p:sp>'
        '</p:spTree></p:cSld></p:sld>'
    )
    xfrm = _extract_placeholder_xfrm(slide, "pptx_native_placeholder_1")
    assert xfrm is not None
    offset, extents = xfrm
    assert offset == (914400, 2057400)
    assert extents == (10363200, 2743200)


def test_extract_placeholder_xfrm_missing_returns_none():
    from src.smartart_pptx_native.assembler_patch import _extract_placeholder_xfrm

    assert _extract_placeholder_xfrm("<sld/>", "nothere") is None


def test_part_to_filename():
    from src.smartart_pptx_native.assembler_patch import part_to_filename

    assert part_to_filename("data", 1) == "data1.xml"
    assert part_to_filename("quickStyle", 3) == "quickStyle3.xml"


# ---------------------------------------------------------------------------
# End-to-end injection tests
# ---------------------------------------------------------------------------

def test_inject_single_diagram_into_blank_host():
    from src.smartart_pptx_native.assembler_patch import InjectionRequest, inject

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        host = _make_host_with_placeholder(tmp / "host.pptx")
        carrier = _make_carrier_pptx(
            tmp / "carrier.pptx", ["Research", "Design", "Build", "Test", "Ship"]
        )

        results = inject(
            host_pptx=host,
            requests=[
                InjectionRequest(
                    slide_number=1,
                    carrier_pptx=carrier,
                )
            ],
        )

        assert len(results) == 1
        result = results[0]
        assert result.slide_number == 1
        assert result.diagram_number == 1
        assert result.rids_allocated == ["rId2", "rId3", "rId4", "rId5"]
        # Placeholder was at 1", 2.25", 11.3" x 3" → EMU values
        assert result.offset == (914400, 2057400)
        assert result.extents == (10363200, 2743200)

        # Verify the result .pptx structure
        with zipfile.ZipFile(host, "r") as z:
            names = set(z.namelist())
            assert "ppt/diagrams/data1.xml" in names
            assert "ppt/diagrams/layout1.xml" in names
            assert "ppt/diagrams/quickStyle1.xml" in names
            assert "ppt/diagrams/colors1.xml" in names
            # No drawing cache
            assert "ppt/diagrams/drawing1.xml" not in names

            slide_xml = z.read("ppt/slides/slide1.xml").decode("utf-8")
            # Placeholder removed
            assert "pptx_native_placeholder_1" not in slide_xml
            # Graphic frame present
            assert "<p:graphicFrame>" in slide_xml
            assert "dgm:relIds" in slide_xml
            # Rids match
            assert 'r:dm="rId2"' in slide_xml
            assert 'r:lo="rId3"' in slide_xml
            assert 'r:qs="rId4"' in slide_xml
            assert 'r:cs="rId5"' in slide_xml

            # Content types: all four diagram overrides
            ct_xml = z.read("[Content_Types].xml").decode("utf-8")
            assert "/ppt/diagrams/data1.xml" in ct_xml
            assert "/ppt/diagrams/layout1.xml" in ct_xml
            assert "/ppt/diagrams/quickStyle1.xml" in ct_xml
            assert "/ppt/diagrams/colors1.xml" in ct_xml

            # Slide rels: four diagram rels at rId2-5
            rels = z.read("ppt/slides/_rels/slide1.xml.rels").decode("utf-8")
            assert 'Id="rId2"' in rels
            assert 'Id="rId5"' in rels
            assert "diagramData" in rels
            assert "diagramLayout" in rels
            assert "diagramQuickStyle" in rels
            assert "diagramColors" in rels

            # Verify step labels made it through
            data_xml = z.read("ppt/diagrams/data1.xml").decode("utf-8")
            for label in ["Research", "Design", "Build", "Test", "Ship"]:
                assert f"<a:t>{label}</a:t>" in data_xml


def test_inject_rejects_missing_placeholder():
    from src.smartart_pptx_native.assembler_patch import (
        InjectionError,
        InjectionRequest,
        inject,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        # Host WITHOUT a placeholder (just copies blank_slide)
        shutil.copy(BLANK_SLIDE_PATH, tmp / "host.pptx")
        host = tmp / "host.pptx"
        carrier = _make_carrier_pptx(tmp / "carrier.pptx", ["A", "B", "C"])

        with pytest.raises(InjectionError, match="no placeholder"):
            inject(
                host_pptx=host,
                requests=[InjectionRequest(slide_number=1, carrier_pptx=carrier)],
            )


def test_inject_rejects_missing_carrier():
    from src.smartart_pptx_native.assembler_patch import (
        InjectionError,
        InjectionRequest,
        inject,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        host = _make_host_with_placeholder(tmp / "host.pptx")
        missing = tmp / "nonexistent.pptx"

        with pytest.raises(InjectionError, match="carrier"):
            inject(
                host_pptx=host,
                requests=[InjectionRequest(slide_number=1, carrier_pptx=missing)],
            )


def test_inject_rejects_missing_slide_number():
    from src.smartart_pptx_native.assembler_patch import (
        InjectionError,
        InjectionRequest,
        inject,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        host = _make_host_with_placeholder(tmp / "host.pptx")
        carrier = _make_carrier_pptx(tmp / "carrier.pptx", ["A", "B"])

        with pytest.raises(InjectionError, match="slide 99"):
            inject(
                host_pptx=host,
                requests=[InjectionRequest(slide_number=99, carrier_pptx=carrier)],
            )


def test_inject_preserves_non_target_slide_content():
    """Host file size and structure should be stable for everything
    other than the four surgical touch points."""
    from src.smartart_pptx_native.assembler_patch import InjectionRequest, inject

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        host = _make_host_with_placeholder(tmp / "host.pptx")
        carrier = _make_carrier_pptx(tmp / "carrier.pptx", ["A", "B", "C"])

        # Capture pre-inject file list
        with zipfile.ZipFile(host, "r") as z:
            pre_names = set(z.namelist())

        inject(
            host_pptx=host,
            requests=[InjectionRequest(slide_number=1, carrier_pptx=carrier)],
        )

        with zipfile.ZipFile(host, "r") as z:
            post_names = set(z.namelist())

        added = post_names - pre_names
        # Should have added exactly four diagram parts
        assert added == {
            "ppt/diagrams/data1.xml",
            "ppt/diagrams/layout1.xml",
            "ppt/diagrams/quickStyle1.xml",
            "ppt/diagrams/colors1.xml",
        }

        removed = pre_names - post_names
        # Nothing removed (the placeholder was in slide1.xml, not a
        # separate part — slide1.xml itself is kept, just modified)
        assert removed == set()


def test_inject_empty_requests_is_noop():
    from src.smartart_pptx_native.assembler_patch import inject

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        host = _make_host_with_placeholder(tmp / "host.pptx")
        pre_bytes = host.read_bytes()

        results = inject(host_pptx=host, requests=[])
        assert results == []
        # File should still exist (we always rewrite the zip) but content should match
        post_bytes = host.read_bytes()
        assert zipfile.is_zipfile(host)
        # Content may differ slightly in zip compression, but the file list
        # and contents should be equivalent
        with zipfile.ZipFile(host, "r") as z:
            names = set(z.namelist())
        # No diagrams added
        assert not any(n.startswith("ppt/diagrams/") for n in names)
