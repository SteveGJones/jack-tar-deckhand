"""Tests for the pptx_native pipeline orchestration wrapper.

`run_injection_step` is the function that an orchestration script or
skill calls after `build_deck.js` finishes writing the assembled deck.
It walks the smartart manifest, filters to pptx_native entries, and
runs the injection.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BLANK_SLIDE_PATH = REPO_ROOT / "tests" / "fixtures" / "smartart_seeds" / "blank_slide.pptx"


def _make_deck_dir_with_manifest(
    tmp_dir: Path,
    entries: list[dict],
    include_assembled_pptx: bool = True,
    placeholder_name: str = "pptx_native_placeholder_1",
) -> Path:
    """Build a minimal deck_dir with smartart-manifest.json + an
    assembled .pptx that contains a placeholder on slide 1.

    Returns the deck directory path.
    """
    from tests.test_pptx_native_assembler_patch import _make_host_with_placeholder

    deck_dir = tmp_dir / "deck"
    deck_dir.mkdir()
    (deck_dir / "output").mkdir()

    if include_assembled_pptx:
        _make_host_with_placeholder(
            deck_dir / "output" / "presentation.pptx",
            slide_number=1,
            placeholder_name=placeholder_name,
        )

    manifest = {"generated_at": "2026-04-08T00:00:00Z", "graphics": entries}
    (deck_dir / "smartart-manifest.json").write_text(json.dumps(manifest, indent=2))

    return deck_dir


def _make_carrier(tmp_dir: Path, name: str, steps: list[str]) -> Path:
    from src.smartart_pptx_native import engine

    result = engine.render(
        {"graphic_type": "flowchart", "data": {"steps": steps}},
        tmp_dir,
        output_name=name,
    )
    return result.output_path


def test_run_injection_step_no_manifest_is_noop():
    from src.smartart_pptx_native.pipeline import run_injection_step

    with tempfile.TemporaryDirectory() as tmpdir:
        deck_dir = Path(tmpdir) / "deck"
        deck_dir.mkdir()
        (deck_dir / "output").mkdir()
        (deck_dir / "output" / "presentation.pptx").write_bytes(b"fake")

        result = run_injection_step(deck_dir)
        assert result.injected_count == 0
        assert result.results == []
        assert result.skipped_non_pptx_native == 0


def test_run_injection_step_empty_manifest():
    from src.smartart_pptx_native.pipeline import run_injection_step

    with tempfile.TemporaryDirectory() as tmpdir:
        deck_dir = _make_deck_dir_with_manifest(
            Path(tmpdir), [], include_assembled_pptx=False
        )
        result = run_injection_step(deck_dir)
        assert result.injected_count == 0


def test_run_injection_step_only_custom_svg_entries_noop():
    from src.smartart_pptx_native.pipeline import run_injection_step

    with tempfile.TemporaryDirectory() as tmpdir:
        deck_dir = _make_deck_dir_with_manifest(
            Path(tmpdir),
            entries=[{
                "smartart_id": "sa-1",
                "slide_number": 1,
                "engine_used": "custom_svg",
                "graphic_type": "swot",
                "enrichment_tier": "pure_programmatic",
                "file_path": "/elsewhere.svg",
                "status": "rendered",
            }],
            include_assembled_pptx=False,
        )
        result = run_injection_step(deck_dir)
        assert result.injected_count == 0
        assert result.skipped_non_pptx_native == 1


def test_run_injection_step_happy_path_single_entry():
    from src.smartart_pptx_native.pipeline import run_injection_step

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        carrier = _make_carrier(tmp, "carrier.pptx", ["Plan", "Build", "Ship"])
        deck_dir = _make_deck_dir_with_manifest(
            tmp,
            entries=[{
                "smartart_id": "sa-slide-1-flowchart",
                "slide_number": 1,
                "engine_used": "pptx_native",
                "graphic_type": "flowchart",
                "enrichment_tier": "pure_programmatic",
                "file_path": str(carrier),
                "status": "rendered",
            }],
        )

        result = run_injection_step(deck_dir)
        assert result.injected_count == 1
        assert result.skipped_non_pptx_native == 0

        # The assembled .pptx should now have the injected diagram
        with zipfile.ZipFile(result.assembled_pptx, "r") as z:
            names = set(z.namelist())
            assert "ppt/diagrams/data1.xml" in names
            assert "ppt/diagrams/layout1.xml" in names
            # Placeholder removed, graphicFrame present
            slide_xml = z.read("ppt/slides/slide1.xml").decode("utf-8")
            assert "pptx_native_placeholder_1" not in slide_xml
            assert "<p:graphicFrame>" in slide_xml


def test_run_injection_step_skips_failed_status_entries():
    from src.smartart_pptx_native.pipeline import run_injection_step

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        deck_dir = _make_deck_dir_with_manifest(
            tmp,
            entries=[{
                "smartart_id": "sa-slide-1-flowchart",
                "slide_number": 1,
                "engine_used": "pptx_native",
                "graphic_type": "flowchart",
                "enrichment_tier": "pure_programmatic",
                "file_path": "/tmp/whatever.pptx",
                "status": "failed",  # failed entries are skipped
            }],
        )
        result = run_injection_step(deck_dir)
        assert result.injected_count == 0


def test_run_injection_step_raises_if_assembled_missing_but_requests_present():
    from src.smartart_pptx_native.assembler_patch import InjectionError
    from src.smartart_pptx_native.pipeline import run_injection_step

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        carrier = _make_carrier(tmp, "carrier.pptx", ["A", "B"])
        deck_dir = _make_deck_dir_with_manifest(
            tmp,
            entries=[{
                "smartart_id": "sa-slide-1-flowchart",
                "slide_number": 1,
                "engine_used": "pptx_native",
                "graphic_type": "flowchart",
                "enrichment_tier": "pure_programmatic",
                "file_path": str(carrier),
                "status": "rendered",
            }],
            include_assembled_pptx=False,
        )
        with pytest.raises(InjectionError, match="assembled .pptx missing"):
            run_injection_step(deck_dir)


def test_run_injection_step_handles_mixed_manifest():
    """A manifest with both pptx_native and custom_svg entries — only
    the pptx_native ones should be injected; custom_svg count goes
    into skipped_non_pptx_native."""
    from src.smartart_pptx_native.pipeline import run_injection_step

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        carrier = _make_carrier(tmp, "carrier.pptx", ["A", "B"])
        deck_dir = _make_deck_dir_with_manifest(
            tmp,
            entries=[
                {
                    "smartart_id": "sa-slide-1-flowchart",
                    "slide_number": 1,
                    "engine_used": "pptx_native",
                    "graphic_type": "flowchart",
                    "enrichment_tier": "pure_programmatic",
                    "file_path": str(carrier),
                    "status": "rendered",
                },
                {
                    "smartart_id": "sa-slide-2-swot",
                    "slide_number": 2,
                    "engine_used": "custom_svg",
                    "graphic_type": "swot",
                    "enrichment_tier": "pure_programmatic",
                    "file_path": "/elsewhere.svg",
                    "status": "rendered",
                },
            ],
        )
        result = run_injection_step(deck_dir)
        assert result.injected_count == 1
        assert result.skipped_non_pptx_native == 1
