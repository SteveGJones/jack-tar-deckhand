"""Tests verifying build_deck.js emits named placeholder rects for
pptx_native SmartArt entries so the Python post-process can find and
inject them.

These run the real Node assembler against a fixture deck configured
to use pptx_native for one slide.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MINIMAL_DECK_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "minimal_deck"


def _prepare_pptx_native_deck(tmp_path: Path) -> Path:
    """Copy the minimal_deck fixture, then patch its contracts to
    configure slide 2 as a pptx_native SmartArt slide.

    Returns the path to the prepared deck directory.
    """
    deck_dir = tmp_path / "deck"
    shutil.copytree(MINIMAL_DECK_FIXTURE, deck_dir)

    # Change slide 2's strategy to smartart
    strategy = json.loads((deck_dir / "strategy-map.json").read_text())
    for slide in strategy["slides"]:
        if slide["slide_number"] == 2:
            slide["strategy"] = "smartart"
            slide["rationale"] = "pptx_native flowchart test"
    (deck_dir / "strategy-map.json").write_text(json.dumps(strategy, indent=2))

    # Add a smartart-manifest.json with a single pptx_native entry for slide 2
    manifest = {
        "generated_at": "2026-04-08T00:00:00Z",
        "graphics": [
            {
                "smartart_id": "sa-slide-2-flowchart",
                "slide_number": 2,
                "graphic_type": "flowchart",
                "engine_used": "pptx_native",
                "enrichment_tier": "pure_programmatic",
                "file_path": "/placeholder/not-used-by-js.pptx",
                "svg_source_path": "",
                "status": "rendered",
                "dimensions": {"width": 1920, "height": 1080},
                "node_count": 3,
                "alt_text": "Three-step process",
                "content_hash": "test0000",
            }
        ],
    }
    (deck_dir / "smartart-manifest.json").write_text(json.dumps(manifest, indent=2))

    # Ensure output dir exists
    (deck_dir / "output").mkdir(exist_ok=True)
    (deck_dir / "images").mkdir(exist_ok=True)

    return deck_dir


def _run_assembler(deck_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["node", "src/assembler/build_deck.js", "--deck-dir", str(deck_dir)],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(REPO_ROOT),
    )


def test_buildsmartartslide_emits_placeholder_for_pptx_native_entry():
    """The Node assembler should produce a slide containing a shape
    named 'pptx_native_placeholder_<slide_number>' when the manifest
    entry has engine_used='pptx_native'."""
    with tempfile.TemporaryDirectory() as tmpdir:
        deck_dir = _prepare_pptx_native_deck(Path(tmpdir))
        result = _run_assembler(deck_dir)
        assert result.returncode == 0, (
            f"build_deck.js failed: stdout={result.stdout} stderr={result.stderr}"
        )

        pptx_path = deck_dir / "output" / "presentation.pptx"
        assert pptx_path.exists(), "presentation.pptx not created"

        # Slide 2 should contain the placeholder shape
        with zipfile.ZipFile(pptx_path, "r") as z:
            slide2_xml = z.read("ppt/slides/slide2.xml").decode("utf-8")

        assert "pptx_native_placeholder_2" in slide2_xml, (
            "expected placeholder shape name in slide 2 XML — "
            "buildSmartArtSlide's pptx_native branch may not be emitting "
            "the placeholder correctly"
        )
        # Should be a shape, not a graphicFrame (that comes in the Python post-process)
        assert "<p:sp>" in slide2_xml


def test_pptx_native_placeholder_has_correct_position():
    """The placeholder's xfrm should match the graphicXContain/graphicY
    position used by the T0/T2 image path, so the post-process captures
    a sensible position for the injected graphicFrame."""
    with tempfile.TemporaryDirectory() as tmpdir:
        deck_dir = _prepare_pptx_native_deck(Path(tmpdir))
        result = _run_assembler(deck_dir)
        assert result.returncode == 0

        pptx_path = deck_dir / "output" / "presentation.pptx"
        with zipfile.ZipFile(pptx_path, "r") as z:
            slide2_xml = z.read("ppt/slides/slide2.xml").decode("utf-8")

        # Locate the placeholder xfrm and verify it has sensible EMU values
        import re
        placeholder_idx = slide2_xml.find("pptx_native_placeholder_2")
        assert placeholder_idx != -1
        # Walk to enclosing <p:sp> and find the xfrm inside it
        sp_start = slide2_xml.rfind("<p:sp>", 0, placeholder_idx)
        sp_end = slide2_xml.find("</p:sp>", placeholder_idx)
        sp_xml = slide2_xml[sp_start:sp_end]

        off_match = re.search(r'<a:off\s+x="(\d+)"\s+y="(\d+)"/>', sp_xml)
        ext_match = re.search(r'<a:ext\s+cx="(\d+)"\s+cy="(\d+)"/>', sp_xml)
        assert off_match, f"no offset in placeholder xfrm: {sp_xml[:500]}"
        assert ext_match, f"no extents in placeholder xfrm: {sp_xml[:500]}"

        x, y = int(off_match.group(1)), int(off_match.group(2))
        cx, cy = int(ext_match.group(1)), int(ext_match.group(2))

        # minimal_deck fixture uses a 10" x 5.625" slide
        # (style-guide.json layout.slide_width_inches=10,
        #  slide_height_inches=5.625). At those dimensions:
        #   graphicXContain = 10 × 0.075 = 0.75"  ≈ 685800 EMU
        #   graphicY        = 5.625 × 0.30 = 1.6875" ≈ 1543050 EMU
        #   graphicWContain = 10 × 0.85 = 8.5" ≈ 7772400 EMU
        #   graphicH        = 5.625 × 0.64 = 3.6" ≈ 3291840 EMU
        # Allow ±10% tolerance for rounding in the JS → XML pipeline.
        assert 600000 < x < 750000, f"unexpected x={x}"
        assert 1400000 < y < 1700000, f"unexpected y={y}"
        assert 7500000 < cx < 8000000, f"unexpected cx={cx}"
        assert 3100000 < cy < 3500000, f"unexpected cy={cy}"


def test_placeholder_compatible_with_assembler_patch_lookup():
    """The placeholder the JS emits should be findable by the
    Python assembler_patch module's extraction logic."""
    from src.smartart_pptx_native.assembler_patch import _extract_placeholder_xfrm

    with tempfile.TemporaryDirectory() as tmpdir:
        deck_dir = _prepare_pptx_native_deck(Path(tmpdir))
        result = _run_assembler(deck_dir)
        assert result.returncode == 0

        pptx_path = deck_dir / "output" / "presentation.pptx"
        with zipfile.ZipFile(pptx_path, "r") as z:
            slide2_xml = z.read("ppt/slides/slide2.xml").decode("utf-8")

        xfrm = _extract_placeholder_xfrm(slide2_xml, "pptx_native_placeholder_2")
        assert xfrm is not None, (
            "assembler_patch._extract_placeholder_xfrm could not find "
            "the placeholder the JS emitted — contract mismatch"
        )
        offset, extents = xfrm
        assert offset[0] > 0 and offset[1] > 0
        assert extents[0] > 0 and extents[1] > 0


def test_non_pptx_native_smartart_still_uses_image_path():
    """Regression check: if the manifest has a custom_svg entry,
    the JS should still use the existing addImage path, not the
    pptx_native placeholder branch."""
    with tempfile.TemporaryDirectory() as tmpdir:
        deck_dir = _prepare_pptx_native_deck(Path(tmpdir))

        # Flip the manifest entry back to custom_svg
        manifest = json.loads((deck_dir / "smartart-manifest.json").read_text())
        manifest["graphics"][0]["engine_used"] = "custom_svg"
        manifest["graphics"][0]["file_path"] = str(
            REPO_ROOT / "tests" / "fixtures" / "minimal_deck" / "images" / "slide2-bg.png"
        )
        (deck_dir / "smartart-manifest.json").write_text(json.dumps(manifest, indent=2))

        result = _run_assembler(deck_dir)
        assert result.returncode == 0

        pptx_path = deck_dir / "output" / "presentation.pptx"
        with zipfile.ZipFile(pptx_path, "r") as z:
            slide2_xml = z.read("ppt/slides/slide2.xml").decode("utf-8")

        # No placeholder for non-pptx_native entries
        assert "pptx_native_placeholder" not in slide2_xml
