"""Tests for the pre-deck creative_vision sprint phase (#113 AC2)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.sprint import (  # noqa: E402
    STATUS_ACCEPTED,
    STATUS_IN_PROGRESS,
    STATUS_NOT_STARTED,
    creative_sprint_progress,
    creative_sprint_slide_status,
    format_sprint_progress_markdown,
    is_sprint_complete,
    next_unaccepted_slide,
    partition_strategy_map_for_creative_sprint,
)


# ---------------------------------------------------------------------------
# strategy-map fixtures
# ---------------------------------------------------------------------------


def _slide(n: int, strategy: str) -> dict:
    """Minimal slide entry shape — just the fields sprint code reads."""
    entry = {"slide_number": n, "strategy": strategy}
    if strategy == "creative_vision":
        entry["creative_vision"] = {"vision_prose": "x"}
    return entry


def _strategy_map(slides: list[dict]) -> dict:
    return {"slides": slides}


# ---------------------------------------------------------------------------
# partition_strategy_map_for_creative_sprint
# ---------------------------------------------------------------------------


def test_partition_preserves_strategy_map_order():
    """Per-list order must match strategy-map order so narrative anchors hold."""
    smap = _strategy_map([
        _slide(1, "composed"),
        _slide(2, "creative_vision"),
        _slide(3, "backdrop"),
        _slide(4, "creative_vision"),
        _slide(5, "full_render"),
    ])
    cv_slides, other = partition_strategy_map_for_creative_sprint(smap)
    assert [s["slide_number"] for s in cv_slides] == [2, 4]
    assert [s["slide_number"] for s in other] == [1, 3, 5]


def test_partition_handles_no_creative_vision_slides():
    smap = _strategy_map([_slide(1, "composed"), _slide(2, "backdrop")])
    cv_slides, other = partition_strategy_map_for_creative_sprint(smap)
    assert cv_slides == []
    assert len(other) == 2


def test_partition_handles_all_creative_vision_slides():
    smap = _strategy_map([_slide(1, "creative_vision"), _slide(2, "creative_vision")])
    cv_slides, other = partition_strategy_map_for_creative_sprint(smap)
    assert len(cv_slides) == 2
    assert other == []


def test_partition_handles_empty_strategy_map():
    cv_slides, other = partition_strategy_map_for_creative_sprint({"slides": []})
    assert cv_slides == []
    assert other == []


# ---------------------------------------------------------------------------
# creative_sprint_slide_status — per-slide manifest reads
# ---------------------------------------------------------------------------


def _write_manifest(deck_dir, slide_number, *, final: dict | None):
    """Helper: write a minimal CreativeVisionManifest under deck_dir."""
    mdir = os.path.join(deck_dir, "creative-vision", str(slide_number))
    os.makedirs(mdir, exist_ok=True)
    manifest = {
        "run_id": "test-run",
        "slide_number": slide_number,
        "strategy": "creative_vision",
        "attempts": [],
        "final": final,
    }
    with open(os.path.join(mdir, "manifest.json"), "w") as f:
        json.dump(manifest, f)


def test_status_not_started_when_no_manifest(tmp_path):
    status = creative_sprint_slide_status(str(tmp_path), 1)
    assert status == STATUS_NOT_STARTED


def test_status_in_progress_when_manifest_has_no_final(tmp_path):
    _write_manifest(str(tmp_path), 1, final=None)
    assert creative_sprint_slide_status(str(tmp_path), 1) == STATUS_IN_PROGRESS


def test_status_accepted_when_manifest_has_final(tmp_path):
    _write_manifest(str(tmp_path), 1, final={
        "image_path": "out.png",
        "accepted_at_tier": "flash_1k",
        "total_cost_usd": 0.067,
        "total_iterations": 1,
        "final_verdict": {"verdict": "pass"},
    })
    assert creative_sprint_slide_status(str(tmp_path), 1) == STATUS_ACCEPTED


def test_status_not_started_on_corrupt_manifest(tmp_path):
    """A half-written or corrupt manifest must be re-classified as not_started
    so the operator notices on next dispatch rather than the conductor
    silently moving on."""
    mdir = os.path.join(str(tmp_path), "creative-vision", "1")
    os.makedirs(mdir, exist_ok=True)
    with open(os.path.join(mdir, "manifest.json"), "w") as f:
        f.write("not valid json {{{")
    assert creative_sprint_slide_status(str(tmp_path), 1) == STATUS_NOT_STARTED


# ---------------------------------------------------------------------------
# creative_sprint_progress — deck-level aggregate
# ---------------------------------------------------------------------------


def test_progress_no_creative_vision_slides_is_trivially_complete(tmp_path):
    smap = _strategy_map([_slide(1, "composed")])
    progress = creative_sprint_progress(str(tmp_path), smap)
    assert progress["total"] == 0
    assert progress["complete"] is True
    assert progress["slides"] == []


def test_progress_all_slides_not_started(tmp_path):
    smap = _strategy_map([
        _slide(1, "creative_vision"),
        _slide(2, "creative_vision"),
    ])
    progress = creative_sprint_progress(str(tmp_path), smap)
    assert progress["total"] == 2
    assert progress["accepted"] == 0
    assert progress["in_progress"] == 0
    assert progress["not_started"] == 2
    assert progress["complete"] is False


def test_progress_mixed_statuses(tmp_path):
    _write_manifest(str(tmp_path), 1, final={"image_path": "p1.png"})  # accepted
    _write_manifest(str(tmp_path), 2, final=None)                      # in_progress
    # slide 3 has no manifest → not_started
    smap = _strategy_map([
        _slide(1, "creative_vision"),
        _slide(2, "creative_vision"),
        _slide(3, "creative_vision"),
        _slide(4, "composed"),
    ])
    progress = creative_sprint_progress(str(tmp_path), smap)
    assert progress["total"] == 3  # composed slide not counted
    assert progress["accepted"] == 1
    assert progress["in_progress"] == 1
    assert progress["not_started"] == 1
    assert progress["complete"] is False
    assert [s["slide_number"] for s in progress["slides"]] == [1, 2, 3]


def test_progress_complete_when_all_accepted(tmp_path):
    _write_manifest(str(tmp_path), 1, final={"image_path": "p1.png"})
    _write_manifest(str(tmp_path), 2, final={"image_path": "p2.png"})
    smap = _strategy_map([
        _slide(1, "creative_vision"),
        _slide(2, "creative_vision"),
    ])
    progress = creative_sprint_progress(str(tmp_path), smap)
    assert progress["complete"] is True
    assert progress["accepted"] == 2


# ---------------------------------------------------------------------------
# is_sprint_complete — conductor gate
# ---------------------------------------------------------------------------


def test_is_sprint_complete_true_when_all_accepted(tmp_path):
    _write_manifest(str(tmp_path), 1, final={"image_path": "p1.png"})
    smap = _strategy_map([_slide(1, "creative_vision")])
    assert is_sprint_complete(str(tmp_path), smap) is True


def test_is_sprint_complete_false_when_any_in_progress(tmp_path):
    _write_manifest(str(tmp_path), 1, final={"image_path": "p1.png"})
    _write_manifest(str(tmp_path), 2, final=None)  # in progress
    smap = _strategy_map([
        _slide(1, "creative_vision"),
        _slide(2, "creative_vision"),
    ])
    assert is_sprint_complete(str(tmp_path), smap) is False


def test_is_sprint_complete_false_when_any_not_started(tmp_path):
    _write_manifest(str(tmp_path), 1, final={"image_path": "p1.png"})
    # slide 2 has no manifest
    smap = _strategy_map([
        _slide(1, "creative_vision"),
        _slide(2, "creative_vision"),
    ])
    assert is_sprint_complete(str(tmp_path), smap) is False


def test_is_sprint_complete_true_when_no_creative_vision_slides(tmp_path):
    """Empty sprint is trivially complete — conductor proceeds directly to
    standard-slide assembly. This is the common case (most decks)."""
    smap = _strategy_map([_slide(1, "composed"), _slide(2, "backdrop")])
    assert is_sprint_complete(str(tmp_path), smap) is True


# ---------------------------------------------------------------------------
# next_unaccepted_slide — conductor's "what should I work on next?"
# ---------------------------------------------------------------------------


def test_next_unaccepted_prefers_in_progress_over_not_started(tmp_path):
    """Resumption: an in-progress slide is preferred so the operator doesn't
    abandon a half-iterated cascade for a fresh slide."""
    _write_manifest(str(tmp_path), 1, final={"image_path": "p1.png"})  # accepted
    _write_manifest(str(tmp_path), 3, final=None)                      # in progress
    # slide 5 has no manifest → not_started
    smap = _strategy_map([
        _slide(1, "creative_vision"),
        _slide(3, "creative_vision"),
        _slide(5, "creative_vision"),
    ])
    progress = creative_sprint_progress(str(tmp_path), smap)
    assert next_unaccepted_slide(progress) == 3


def test_next_unaccepted_returns_first_not_started_when_no_in_progress(tmp_path):
    smap = _strategy_map([
        _slide(1, "creative_vision"),
        _slide(2, "creative_vision"),
    ])
    progress = creative_sprint_progress(str(tmp_path), smap)
    assert next_unaccepted_slide(progress) == 1


def test_next_unaccepted_returns_none_when_sprint_complete(tmp_path):
    _write_manifest(str(tmp_path), 1, final={"image_path": "p1.png"})
    smap = _strategy_map([_slide(1, "creative_vision")])
    progress = creative_sprint_progress(str(tmp_path), smap)
    assert next_unaccepted_slide(progress) is None


# ---------------------------------------------------------------------------
# format_sprint_progress_markdown — operator surface
# ---------------------------------------------------------------------------


def test_markdown_empty_sprint_says_trivially_complete():
    progress = {
        "total": 0,
        "accepted": 0,
        "in_progress": 0,
        "not_started": 0,
        "slides": [],
        "complete": True,
    }
    md = format_sprint_progress_markdown(progress)
    assert "trivially complete" in md.lower()
    assert "standard-slide assembly" in md.lower()


def test_markdown_in_progress_sprint_shows_blocked_status():
    progress = {
        "total": 3,
        "accepted": 1,
        "in_progress": 1,
        "not_started": 1,
        "slides": [
            {"slide_number": 1, "status": "accepted"},
            {"slide_number": 2, "status": "in_progress"},
            {"slide_number": 3, "status": "not_started"},
        ],
        "complete": False,
    }
    md = format_sprint_progress_markdown(progress)
    assert "1/3 accepted" in md
    assert "BLOCKED" in md
    assert "| 1 | `accepted` |" in md
    assert "| 2 | `in_progress` |" in md
    assert "| 3 | `not_started` |" in md


def test_markdown_complete_sprint_signals_next_phase():
    progress = {
        "total": 2,
        "accepted": 2,
        "in_progress": 0,
        "not_started": 0,
        "slides": [
            {"slide_number": 1, "status": "accepted"},
            {"slide_number": 2, "status": "accepted"},
        ],
        "complete": True,
    }
    md = format_sprint_progress_markdown(progress)
    assert "Creative Sprint complete" in md
    assert "standard-slide assembly" in md.lower()
