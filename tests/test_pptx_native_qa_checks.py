"""Tests for SA-06 / SA-07 / SA-08 QA checks for pptx_native SmartArt."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BLANK_SLIDE_PATH = REPO_ROOT / "tests" / "fixtures" / "smartart_seeds" / "blank_slide.pptx"


def _make_fully_injected_deck(tmp_dir: Path, steps: list[str]) -> tuple[Path, dict]:
    """Build a .pptx that has been through the full Phase 3 injection flow:
    blank host → placeholder inserted → carrier generated → assembler_patch
    run. Returns (pptx_path, manifest).
    """
    from src.smartart_pptx_native import engine
    from src.smartart_pptx_native.assembler_patch import InjectionRequest, inject
    from tests.test_pptx_native_assembler_patch import _make_host_with_placeholder

    host = _make_host_with_placeholder(tmp_dir / "deck.pptx")
    carrier = engine.render(
        {"graphic_type": "flowchart", "data": {"steps": steps}},
        tmp_dir,
        output_name="carrier.pptx",
    )
    inject(
        host_pptx=host,
        requests=[InjectionRequest(slide_number=1, carrier_pptx=carrier.output_path)],
    )

    manifest = {
        "generated_at": "2026-04-08T00:00:00Z",
        "graphics": [
            {
                "smartart_id": "sa-slide-1-flowchart",
                "slide_number": 1,
                "graphic_type": "flowchart",
                "engine_used": "pptx_native",
                "enrichment_tier": "pure_programmatic",
                "file_path": str(carrier.output_path),
                "svg_source_path": "",
                "status": "rendered",
                "dimensions": {"width": 1920, "height": 1080},
                "node_count": len(steps),
                "alt_text": "Test process diagram",
                "content_hash": "test0000",
            }
        ],
    }
    return host, manifest


def test_sa06_sa07_sa08_pass_on_freshly_injected_deck():
    from src.qa.checks.smartart_checks import check_all_pptx_native_graphics

    with tempfile.TemporaryDirectory() as tmpdir:
        pptx_path, manifest = _make_fully_injected_deck(
            Path(tmpdir), ["Research", "Design", "Build"]
        )
        findings = check_all_pptx_native_graphics(pptx_path, manifest)
        assert findings == [], f"unexpected findings: {findings}"


def test_sa06_flags_missing_diagram_part():
    """If one of the four diagram parts is deleted post-injection,
    SA-06 should fire."""
    from src.qa.checks.smartart_checks import check_pptx_native_integrity

    with tempfile.TemporaryDirectory() as tmpdir:
        pptx_path, manifest = _make_fully_injected_deck(
            Path(tmpdir), ["Alpha", "Beta"]
        )

        # Corrupt by removing the colors1.xml diagram part
        corrupted = Path(tmpdir) / "corrupted.pptx"
        with zipfile.ZipFile(pptx_path, "r") as zin, zipfile.ZipFile(
            corrupted, "w", zipfile.ZIP_DEFLATED
        ) as zout:
            for item in zin.infolist():
                if item.filename == "ppt/diagrams/colors1.xml":
                    continue
                zout.writestr(item, zin.read(item.filename))

        findings = check_pptx_native_integrity(corrupted, manifest, 1)
        assert any("SA-06" in f["description"] for f in findings)
        assert any("colors1.xml" in f["description"] for f in findings)


def test_sa07_flags_slide_without_diagram_relationship():
    """If the slide rels has no diagramData relationship, SA-07 fires."""
    from src.qa.checks.smartart_checks import check_pptx_native_integrity

    with tempfile.TemporaryDirectory() as tmpdir:
        # Start from a blank host — no diagram anywhere
        host = Path(tmpdir) / "deck.pptx"
        shutil.copy(BLANK_SLIDE_PATH, host)

        # Manifest claims there's a pptx_native graphic on slide 1,
        # but the .pptx has no such graphic
        manifest = {
            "graphics": [{
                "smartart_id": "sa-slide-1-flowchart",
                "slide_number": 1,
                "graphic_type": "flowchart",
                "engine_used": "pptx_native",
                "enrichment_tier": "pure_programmatic",
                "file_path": "/nonexistent.pptx",
                "status": "rendered",
            }]
        }
        findings = check_pptx_native_integrity(host, manifest, 1)
        assert any("SA-07" in f["description"] for f in findings)
        assert any("no diagram relationship" in f["description"] for f in findings)


def test_sa07_flags_orphaned_placeholder():
    """If the placeholder rect was not removed during injection, SA-07 fires."""
    from src.qa.checks.smartart_checks import check_pptx_native_integrity
    from tests.test_pptx_native_assembler_patch import _make_host_with_placeholder

    with tempfile.TemporaryDirectory() as tmpdir:
        # Build a host with placeholder but DO NOT run injection —
        # then manually add a diagram relationship and parts so SA-06
        # passes but SA-07 sees the orphan.
        from src.smartart_pptx_native import engine

        host = _make_host_with_placeholder(Path(tmpdir) / "host.pptx")
        carrier = engine.render(
            {"graphic_type": "flowchart", "data": {"steps": ["A", "B"]}},
            Path(tmpdir),
            output_name="carrier.pptx",
        )

        # Rather than running full injection, simulate a half-baked
        # state: copy the carrier's diagram parts into the host and
        # add the rels/content-types, BUT don't remove the placeholder.
        from src.smartart_pptx_native.assembler_patch import (
            _patch_content_types,
            _patch_slide_rels,
        )

        with zipfile.ZipFile(host, "r") as zin:
            contents = {i.filename: zin.read(i.filename) for i in zin.infolist()}

        with zipfile.ZipFile(carrier.output_path, "r") as zc:
            for part in ("data", "layout", "quickStyle", "colors"):
                contents[f"ppt/diagrams/{part}1.xml"] = zc.read(
                    f"ppt/diagrams/{part}1.xml"
                )

        # Add rels and content types but leave placeholder in slide XML
        rels_name = "ppt/slides/_rels/slide1.xml.rels"
        rids = {
            "data": "rId2", "layout": "rId3",
            "quickStyle": "rId4", "colors": "rId5",
        }
        contents[rels_name] = _patch_slide_rels(
            contents[rels_name].decode("utf-8"), rids, 1
        ).encode("utf-8") if isinstance(contents[rels_name], bytes) else _patch_slide_rels(
            contents[rels_name], rids, 1
        ).encode("utf-8")
        contents["[Content_Types].xml"] = _patch_content_types(
            contents["[Content_Types].xml"].decode("utf-8"), 1
        ).encode("utf-8") if isinstance(contents["[Content_Types].xml"], bytes) else _patch_content_types(
            contents["[Content_Types].xml"], 1
        ).encode("utf-8")

        corrupted = Path(tmpdir) / "corrupted.pptx"
        with zipfile.ZipFile(corrupted, "w", zipfile.ZIP_DEFLATED) as zout:
            for name, data in contents.items():
                zout.writestr(name, data)

        manifest = {
            "graphics": [{
                "smartart_id": "sa-slide-1-flowchart",
                "slide_number": 1,
                "graphic_type": "flowchart",
                "engine_used": "pptx_native",
                "enrichment_tier": "pure_programmatic",
                "file_path": str(carrier.output_path),
                "status": "rendered",
            }]
        }
        findings = check_pptx_native_integrity(corrupted, manifest, 1)
        # SA-07 should fire for the orphaned placeholder
        sa07_findings = [f for f in findings if "SA-07" in f["description"]]
        assert sa07_findings
        assert any("placeholder" in f["description"] for f in sa07_findings)


def test_sa08_flags_stale_drawing_cache():
    """If drawing1.xml is mistakenly present after injection, SA-08 fires."""
    from src.qa.checks.smartart_checks import check_pptx_native_integrity

    with tempfile.TemporaryDirectory() as tmpdir:
        pptx_path, manifest = _make_fully_injected_deck(Path(tmpdir), ["A", "B", "C"])

        # Inject a fake drawing1.xml to simulate a stale cache
        corrupted = Path(tmpdir) / "corrupted.pptx"
        with zipfile.ZipFile(pptx_path, "r") as zin, zipfile.ZipFile(
            corrupted, "w", zipfile.ZIP_DEFLATED
        ) as zout:
            for item in zin.infolist():
                zout.writestr(item, zin.read(item.filename))
            zout.writestr("ppt/diagrams/drawing1.xml", b"<?xml version='1.0'?><stale/>")

        findings = check_pptx_native_integrity(corrupted, manifest, 1)
        assert any("SA-08" in f["description"] for f in findings)
        assert any("drawing1.xml" in f["description"] for f in findings)


def test_checks_skip_non_pptx_native_entries():
    """Custom_svg entries should be silently ignored — SA-06/07/08
    only apply to pptx_native."""
    from src.qa.checks.smartart_checks import check_all_pptx_native_graphics

    with tempfile.TemporaryDirectory() as tmpdir:
        host = Path(tmpdir) / "deck.pptx"
        shutil.copy(BLANK_SLIDE_PATH, host)

        manifest = {
            "graphics": [
                {
                    "smartart_id": "sa-slide-1",
                    "slide_number": 1,
                    "engine_used": "custom_svg",
                    "graphic_type": "flowchart",
                    "enrichment_tier": "pure_programmatic",
                    "file_path": "/anywhere.svg",
                    "status": "rendered",
                },
                {
                    "smartart_id": "sa-slide-2",
                    "slide_number": 2,
                    "engine_used": "mermaid",
                    "graphic_type": "flowchart",
                    "enrichment_tier": "pure_programmatic",
                    "file_path": "/anywhere.png",
                    "status": "rendered",
                },
            ],
        }
        findings = check_all_pptx_native_graphics(host, manifest)
        # No pptx_native entries → no findings
        assert findings == []


def test_empty_manifest_produces_no_findings():
    from src.qa.checks.smartart_checks import check_all_pptx_native_graphics

    with tempfile.TemporaryDirectory() as tmpdir:
        host = Path(tmpdir) / "deck.pptx"
        shutil.copy(BLANK_SLIDE_PATH, host)
        findings = check_all_pptx_native_graphics(host, {"graphics": []})
        assert findings == []


def test_missing_pptx_file_produces_error_finding():
    from src.qa.checks.smartart_checks import check_pptx_native_integrity

    manifest = {
        "graphics": [{
            "slide_number": 1,
            "engine_used": "pptx_native",
            "graphic_type": "flowchart",
        }]
    }
    findings = check_pptx_native_integrity("/nonexistent.pptx", manifest, 1)
    assert findings
    assert any("not found" in f["description"].lower() for f in findings)
