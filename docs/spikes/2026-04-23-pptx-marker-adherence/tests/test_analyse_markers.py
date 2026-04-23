"""Unit tests for the marker analyser."""
import sys
from pathlib import Path

SPIKE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE_DIR / "tools"))

from analyse_markers import analyse_pptx

FIXTURE = SPIKE_DIR / "tests" / "fixtures" / "minimal.pptx"


def test_finds_all_three_marker_types():
    report = analyse_pptx(FIXTURE)
    kinds = sorted(m["kind"] for m in report["markers"])
    assert kinds == ["BG", "IMAGE", "SMARTART"]


def test_extracts_identifier_after_colon():
    report = analyse_pptx(FIXTURE)
    ids = {m["kind"]: m["identifier"] for m in report["markers"]}
    assert ids["IMAGE"] == "agent-architecture"
    assert ids["SMARTART"] == "flowchart"
    assert ids["BG"] == "dramatic-contrast"


def test_records_slide_index_per_marker():
    report = analyse_pptx(FIXTURE)
    for m in report["markers"]:
        assert m["slide_index"] >= 1, f"slide_index should be 1-based, got {m}"


def test_records_shape_geometry():
    report = analyse_pptx(FIXTURE)
    img = next(m for m in report["markers"] if m["kind"] == "IMAGE")
    assert "left_emu" in img and img["left_emu"] > 0
    assert "top_emu" in img and img["top_emu"] > 0
    assert "width_emu" in img and img["width_emu"] > 0
    assert "height_emu" in img and img["height_emu"] > 0


def test_ignores_non_marker_shapes():
    report = analyse_pptx(FIXTURE)
    names = [m["shape_name"] for m in report["markers"]]
    assert "TitleBox" not in names, "Distractor shape should not be treated as a marker"


def test_totals_reported():
    report = analyse_pptx(FIXTURE)
    assert report["totals"]["markers"] == 3
    assert report["totals"]["slides"] == 4
    assert report["totals"]["by_kind"] == {"IMAGE": 1, "SMARTART": 1, "BG": 1}
