"""Tests for Phase 6 delivery messaging."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


def _make_manifest(entries):
    return {"generated_at": "2026-04-08", "graphics": entries}


def _make_deck_dir(tmp: Path, manifest: dict, outline: dict | None = None) -> Path:
    # Accept either "base dir" or "specific deck path" — if the caller
    # passes Path(tmpdir) / "one", create all parent dirs too.
    deck = tmp if tmp.name.startswith("tmp") else tmp
    # If tmp is the temporary directory itself, add a "deck" subdir.
    # Otherwise treat tmp AS the deck path and mkdir parents.
    if tmp.exists() and tmp.name.startswith("tmp"):
        deck = tmp / "deck"
        deck.mkdir(parents=True, exist_ok=True)
    else:
        deck = tmp
        deck.mkdir(parents=True, exist_ok=True)
    (deck / "smartart-manifest.json").write_text(json.dumps(manifest))
    if outline is not None:
        (deck / "outline.json").write_text(json.dumps(outline))
    return deck


def test_no_pptx_native_entries_returns_none():
    from src.smartart_pptx_native.pipeline import format_delivery_message

    with tempfile.TemporaryDirectory() as tmpdir:
        deck = _make_deck_dir(
            Path(tmpdir),
            _make_manifest([]),
        )
        assert format_delivery_message(deck) is None


def test_only_custom_svg_entries_returns_none():
    from src.smartart_pptx_native.pipeline import format_delivery_message

    with tempfile.TemporaryDirectory() as tmpdir:
        deck = _make_deck_dir(
            Path(tmpdir),
            _make_manifest([{
                "slide_number": 1,
                "engine_used": "custom_svg",
                "graphic_type": "swot",
                "status": "rendered",
                "node_count": 4,
            }]),
        )
        assert format_delivery_message(deck) is None


def test_single_pptx_native_entry():
    from src.smartart_pptx_native.pipeline import format_delivery_message

    with tempfile.TemporaryDirectory() as tmpdir:
        deck = _make_deck_dir(
            Path(tmpdir),
            _make_manifest([{
                "slide_number": 4,
                "engine_used": "pptx_native",
                "graphic_type": "flowchart",
                "status": "rendered",
                "node_count": 5,
            }]),
        )
        msg = format_delivery_message(deck)
        assert msg is not None
        assert "1 slide uses editable PowerPoint SmartArt" in msg
        assert "PowerPoint Mac" in msg
        assert "Slide  4" in msg
        assert "process diagram" in msg
        assert "5 steps" in msg


def test_multiple_pptx_native_entries_sorted_by_slide_number():
    from src.smartart_pptx_native.pipeline import format_delivery_message

    with tempfile.TemporaryDirectory() as tmpdir:
        deck = _make_deck_dir(
            Path(tmpdir),
            _make_manifest([
                {"slide_number": 9, "engine_used": "pptx_native",
                 "graphic_type": "org_chart", "status": "rendered", "node_count": 6},
                {"slide_number": 4, "engine_used": "pptx_native",
                 "graphic_type": "flowchart", "status": "rendered", "node_count": 5},
                {"slide_number": 7, "engine_used": "pptx_native",
                 "graphic_type": "cycle", "status": "rendered", "node_count": 4},
            ]),
        )
        msg = format_delivery_message(deck)
        assert "3 slides use editable" in msg
        # Order: 4, 7, 9 — verify by finding the positions in the string
        idx4 = msg.find("Slide  4")
        idx7 = msg.find("Slide  7")
        idx9 = msg.find("Slide  9")
        assert 0 < idx4 < idx7 < idx9


def test_message_includes_headlines_when_outline_available():
    from src.smartart_pptx_native.pipeline import format_delivery_message

    with tempfile.TemporaryDirectory() as tmpdir:
        deck = _make_deck_dir(
            Path(tmpdir),
            _make_manifest([{
                "slide_number": 4,
                "engine_used": "pptx_native",
                "graphic_type": "flowchart",
                "status": "rendered",
                "node_count": 3,
            }]),
            outline={"slides": [
                {"slide_number": 4, "headline": "Our Development Process"},
            ]},
        )
        msg = format_delivery_message(deck)
        assert "Our Development Process" in msg


def test_message_works_without_outline():
    """Missing outline.json shouldn't crash the formatter."""
    from src.smartart_pptx_native.pipeline import format_delivery_message

    with tempfile.TemporaryDirectory() as tmpdir:
        deck = _make_deck_dir(
            Path(tmpdir),
            _make_manifest([{
                "slide_number": 4,
                "engine_used": "pptx_native",
                "graphic_type": "flowchart",
                "status": "rendered",
                "node_count": 3,
            }]),
            outline=None,
        )
        msg = format_delivery_message(deck)
        assert msg is not None
        # Works without headline suffix
        assert "Slide  4" in msg


def test_failed_entries_excluded_from_message():
    """A failed entry should not appear in the delivery message."""
    from src.smartart_pptx_native.pipeline import format_delivery_message

    with tempfile.TemporaryDirectory() as tmpdir:
        deck = _make_deck_dir(
            Path(tmpdir),
            _make_manifest([
                {"slide_number": 1, "engine_used": "pptx_native",
                 "graphic_type": "flowchart", "status": "failed", "node_count": 0},
                {"slide_number": 2, "engine_used": "pptx_native",
                 "graphic_type": "cycle", "status": "rendered", "node_count": 4},
            ]),
        )
        msg = format_delivery_message(deck)
        # Only the rendered entry appears
        assert "1 slide uses editable" in msg
        assert "Slide  2" in msg
        assert "Slide  1" not in msg


def test_plural_handling():
    """Grammar: '1 slide uses' vs 'N slides use'."""
    from src.smartart_pptx_native.pipeline import format_delivery_message

    with tempfile.TemporaryDirectory() as tmpdir:
        deck_one = _make_deck_dir(
            Path(tmpdir) / "one",
            _make_manifest([{"slide_number": 1, "engine_used": "pptx_native",
                             "graphic_type": "flowchart", "status": "rendered",
                             "node_count": 3}]),
        )
        deck_two = _make_deck_dir(
            Path(tmpdir) / "two",
            _make_manifest([
                {"slide_number": 1, "engine_used": "pptx_native",
                 "graphic_type": "flowchart", "status": "rendered", "node_count": 3},
                {"slide_number": 2, "engine_used": "pptx_native",
                 "graphic_type": "cycle", "status": "rendered", "node_count": 4},
            ]),
        )

        msg_one = format_delivery_message(deck_one)
        msg_two = format_delivery_message(deck_two)

        assert "1 slide uses" in msg_one
        assert "Slide with editable" in msg_one  # singular header line
        assert "2 slides use" in msg_two
        assert "Slides with editable" in msg_two  # plural header line


def test_type_labels_are_human_readable():
    from src.smartart_pptx_native.pipeline import format_delivery_message

    with tempfile.TemporaryDirectory() as tmpdir:
        deck = _make_deck_dir(
            Path(tmpdir),
            _make_manifest([
                {"slide_number": 1, "engine_used": "pptx_native",
                 "graphic_type": "flowchart", "status": "rendered", "node_count": 5},
                {"slide_number": 2, "engine_used": "pptx_native",
                 "graphic_type": "cycle", "status": "rendered", "node_count": 4},
                {"slide_number": 3, "engine_used": "pptx_native",
                 "graphic_type": "org_chart", "status": "rendered", "node_count": 8},
            ]),
        )
        msg = format_delivery_message(deck)
        assert "process diagram" in msg
        assert "cycle diagram" in msg
        assert "org chart" in msg
        assert "5 steps" in msg
        assert "4 stages" in msg
        assert "8 nodes" in msg


def test_pre_loaded_manifest_bypasses_file_read():
    """If the caller passes an explicit manifest, the function uses
    that instead of reading the deck dir."""
    from src.smartart_pptx_native.pipeline import format_delivery_message

    with tempfile.TemporaryDirectory() as tmpdir:
        # Deck dir doesn't have the file, but we pass manifest explicitly
        deck = Path(tmpdir) / "no-manifest"
        deck.mkdir()

        manifest = _make_manifest([{
            "slide_number": 3,
            "engine_used": "pptx_native",
            "graphic_type": "flowchart",
            "status": "rendered",
            "node_count": 4,
        }])
        msg = format_delivery_message(deck, manifest=manifest)
        assert msg is not None
        assert "Slide  3" in msg
