import pytest
from pathlib import Path

from src.slide_facts import Marker, SlideFacts
from src.smartart_bridge import (
    select_layout_for_slide,
    build_spec_from_slide,
    render_carrier,
    SmartArtBridgeError,
)


def _slide_with_bullets(*items: str, marker_id="SMARTART:foo") -> SlideFacts:
    text = "Title line\n" + "\n".join(items)
    sf = SlideFacts(slide_index=1, text_content=text)
    sf.markers.append(Marker("SMARTART", marker_id.split(":")[1], 0, 0, 0, 0))
    return sf


def test_layout_selected_for_three_to_seven_items_uses_process1():
    slide = _slide_with_bullets("Discover", "Design", "Build", "Ship")
    layout_id = select_layout_for_slide(slide, marker_id="SMARTART:foo")
    assert layout_id == "process1"


def test_layout_selected_for_org_chart_marker_keyword():
    slide = SlideFacts(
        slide_index=1,
        text_content="Org chart\nCEO\n  CTO\n    Dev Lead\n  COO",
        markers=[Marker("SMARTART", "org-chart", 0, 0, 0, 0)],
    )
    layout_id = select_layout_for_slide(slide, marker_id="SMARTART:org-chart")
    assert layout_id == "orgChart1"


def test_layout_selected_for_cycle_keyword_in_marker_id():
    slide = _slide_with_bullets("Plan", "Execute", "Review", marker_id="SMARTART:cycle")
    layout_id = select_layout_for_slide(slide, marker_id="SMARTART:cycle")
    assert layout_id == "cycle2"


def test_build_spec_returns_flat_list_for_process1():
    slide = _slide_with_bullets("Discover", "Design", "Build")
    spec = build_spec_from_slide(slide, marker_id="SMARTART:foo", layout_id="process1")
    assert spec["graphic_type"] == "flowchart"
    assert spec["layout_id"] == "process1"
    assert spec["data"] == {"items": ["Discover", "Design", "Build"]}


def test_build_spec_items_are_plain_strings_not_dicts():
    """Spike 2 finding — flat-list items must be strings; dicts raise FlatListBuildError."""
    slide = _slide_with_bullets("a", "b", "c")
    spec = build_spec_from_slide(slide, marker_id="SMARTART:foo", layout_id="process1")
    for item in spec["data"]["items"]:
        assert isinstance(item, str)


def test_build_spec_org_chart_emits_tree():
    slide = SlideFacts(
        slide_index=1,
        text_content="CEO\n  CTO\n  COO",
        markers=[Marker("SMARTART", "org-chart", 0, 0, 0, 0)],
    )
    spec = build_spec_from_slide(slide, marker_id="SMARTART:org-chart", layout_id="orgChart1")
    assert spec["graphic_type"] == "org_chart"
    assert "tree" in spec["data"]
    assert spec["data"]["tree"]["title"] == "CEO"


def test_build_spec_strips_title_line_from_items():
    """If the marker text label appears as the first line, drop it from items."""
    slide = SlideFacts(
        slide_index=1,
        text_content="SMARTART:foo\nDiscover\nDesign\nBuild",
        markers=[Marker("SMARTART", "foo", 0, 0, 0, 0)],
    )
    spec = build_spec_from_slide(slide, marker_id="SMARTART:foo", layout_id="process1")
    assert spec["data"]["items"] == ["Discover", "Design", "Build"]


def test_render_carrier_writes_pptx(tmp_path):
    slide = _slide_with_bullets("Discover", "Design", "Build")
    spec = build_spec_from_slide(slide, marker_id="SMARTART:foo", layout_id="process1")
    carrier_path = render_carrier(spec, output_dir=tmp_path)
    assert carrier_path.exists()
    assert carrier_path.suffix == ".pptx"


def test_capacity_violation_raises(tmp_path):
    too_many = ["x"] * 50
    slide = _slide_with_bullets(*too_many)
    with pytest.raises(SmartArtBridgeError, match="capacity"):
        spec = build_spec_from_slide(slide, marker_id="SMARTART:foo", layout_id="process1")
        # The check is on build OR render
        render_carrier(spec, output_dir=tmp_path)
