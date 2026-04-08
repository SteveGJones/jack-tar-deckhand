"""Tests for Phase 4 layouts: cycle2 and orgChart1.

Covers:
  - catalog entries
  - layout builders (cycle.py and org_chart.py)
  - extractor routing for 'cycle' and 'org_chart' graphic types
  - end-to-end render through the engine
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

DGM_NS = "{http://schemas.openxmlformats.org/drawingml/2006/diagram}"
A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

STYLE_GUIDE = {
    "palette": {
        "primary": "1a73e8",
        "accent": "e8710a",
        "background": "ffffff",
        "text_primary": "1a1a1a",
        "chart_series": ["2B6CB0", "ED8936", "38A169", "E53E3E"],
    },
    "typography": {"heading_font": "Inter", "body_font": "Inter"},
}


# ---------------------------------------------------------------------------
# Catalog tests
# ---------------------------------------------------------------------------

def test_catalog_has_cycle2_entry():
    from src.smartart_pptx_native.layouts import catalog

    # Clear cache so any earlier changes pick up
    catalog.load_catalog.cache_clear()
    entry = catalog.get_entry("cycle2")
    assert entry["layout_uri"] == "urn:microsoft.com/office/officeart/2005/8/layout/cycle2"
    assert entry["v1"] is True
    assert entry["data_shape"] == "flat_list"
    assert entry["node_type_capabilities"] == []
    assert entry["integration"]["smartart_type_mappings"] == ["cycle"]


def test_catalog_has_orgchart1_entry():
    from src.smartart_pptx_native.layouts import catalog

    catalog.load_catalog.cache_clear()
    entry = catalog.get_entry("orgChart1")
    assert entry["layout_uri"] == "urn:microsoft.com/office/officeart/2005/8/layout/orgChart1"
    assert entry["v1"] is True
    assert entry["data_shape"] == "hierarchical"
    assert entry["node_type_capabilities"] == ["asst"]
    assert entry["integration"]["smartart_type_mappings"] == ["org_chart"]


def test_catalog_reverse_lookup_cycle_and_org_chart():
    from src.smartart_pptx_native.layouts import catalog

    catalog.load_catalog.cache_clear()
    assert catalog.get_layout_id_for_graphic_type("cycle") == "cycle2"
    assert catalog.get_layout_id_for_graphic_type("org_chart") == "orgChart1"


# ---------------------------------------------------------------------------
# Cycle2 builder tests
# ---------------------------------------------------------------------------

def test_cycle_builder_6_stages():
    from src.smartart_pptx_native.layouts import cycle

    result = cycle.build_data_model(
        {"stages": ["Plan", "Build", "Test", "Deploy", "Monitor", "Learn"]}
    )
    root = ET.fromstring(result)
    pts = root.findall(f"{DGM_NS}ptLst/{DGM_NS}pt")
    # 1 doc + 6 nodes + 6 parTrans + 6 sibTrans = 19
    assert len(pts) == 19
    cxns = root.findall(f"{DGM_NS}cxnLst/{DGM_NS}cxn")
    assert len(cxns) == 6

    # Doc point carries the cycle2 URI
    assert b'loTypeId="urn:microsoft.com/office/officeart/2005/8/layout/cycle2"' in result


def test_cycle_builder_rejects_too_few_stages():
    from src.smartart_pptx_native.layouts import cycle

    with pytest.raises(cycle.CycleBuildError, match="at least 3"):
        cycle.build_data_model({"stages": ["A", "B"]})


def test_cycle_builder_rejects_too_many_stages():
    from src.smartart_pptx_native.layouts import cycle

    stages = [f"S{i}" for i in range(10)]  # 10 > 8 max
    with pytest.raises(cycle.CycleBuildError, match="at most 8"):
        cycle.build_data_model({"stages": stages})


def test_cycle_builder_rejects_long_labels():
    from src.smartart_pptx_native.layouts import cycle

    with pytest.raises(cycle.CycleBuildError, match="<= 20"):
        cycle.build_data_model({"stages": ["OK", "OK2", "X" * 25]})


def test_cycle_builder_rejects_missing_stages_key():
    from src.smartart_pptx_native.layouts import cycle

    with pytest.raises(cycle.CycleBuildError, match="'stages' key"):
        cycle.build_data_model({"steps": ["A", "B", "C"]})


# ---------------------------------------------------------------------------
# OrgChart1 builder tests
# ---------------------------------------------------------------------------

SMALL_TREE = {
    "tree": {
        "title": "CEO",
        "children": [
            {
                "title": "CTO",
                "children": [
                    {"title": "Backend Lead"},
                    {"title": "Frontend Lead"},
                ],
            },
            {
                "title": "CFO",
                "children": [
                    {"title": "Finance Manager"},
                ],
            },
        ],
    }
}


def test_org_chart_builder_6_node_tree():
    from src.smartart_pptx_native.layouts import org_chart

    result = org_chart.build_data_model(SMALL_TREE)
    root = ET.fromstring(result)
    pts = root.findall(f"{DGM_NS}ptLst/{DGM_NS}pt")
    # 1 doc + 6 nodes + 6 parTrans + 6 sibTrans = 19
    assert len(pts) == 19
    cxns = root.findall(f"{DGM_NS}cxnLst/{DGM_NS}cxn")
    # One cxn per parent-child edge in the tree (doc→CEO,
    # CEO→CTO, CEO→CFO, CTO→Backend, CTO→Frontend, CFO→Finance) = 6
    assert len(cxns) == 6

    assert b'loTypeId="urn:microsoft.com/office/officeart/2005/8/layout/orgChart1"' in result
    # All six titles present
    for label in ["CEO", "CTO", "CFO", "Backend Lead", "Frontend Lead", "Finance Manager"]:
        assert f"<a:t>{label}</a:t>".encode() in result


def test_org_chart_builder_with_asst_nodes():
    from src.smartart_pptx_native.layouts import org_chart

    tree = {
        "tree": {
            "title": "CEO",
            "children": [
                {"title": "Executive Assistant", "asst": True},
                {"title": "CTO"},
                {"title": "CFO"},
            ],
        }
    }
    result = org_chart.build_data_model(tree)
    # Two places where type="asst" should appear: nowhere outside the
    # ExecAsst node (the other nodes have no type attribute)
    xml = result.decode("utf-8")
    asst_count = xml.count('type="asst"')
    assert asst_count == 1  # exactly one assistant node

    # Confirm the asst is Executive Assistant (not CTO or CFO)
    root = ET.fromstring(result)
    for pt in root.findall(f"{DGM_NS}ptLst/{DGM_NS}pt"):
        if pt.get("type") == "asst":
            t = pt.find(f"{DGM_NS}t/{A_NS}p/{A_NS}r/{A_NS}t")
            assert t is not None and t.text == "Executive Assistant"


def test_org_chart_builder_rejects_too_few_nodes():
    from src.smartart_pptx_native.layouts import org_chart

    with pytest.raises(org_chart.OrgChartBuildError, match="at least 3"):
        org_chart.build_data_model({"tree": {"title": "Only Me"}})


def test_org_chart_builder_rejects_too_many_nodes():
    from src.smartart_pptx_native.layouts import org_chart

    def make_wide_tree(n):
        return {"tree": {"title": "Root", "children": [{"title": f"C{i}"} for i in range(n)]}}

    with pytest.raises(org_chart.OrgChartBuildError, match="at most 25"):
        org_chart.build_data_model(make_wide_tree(30))


def test_org_chart_builder_rejects_long_label():
    from src.smartart_pptx_native.layouts import org_chart

    tree = {
        "tree": {
            "title": "Root",
            "children": [
                {"title": "X" * 40},  # > 32
                {"title": "OK"},
            ],
        }
    }
    with pytest.raises(org_chart.OrgChartBuildError, match="<= 32"):
        org_chart.build_data_model(tree)


def test_org_chart_builder_rejects_missing_tree_key():
    from src.smartart_pptx_native.layouts import org_chart

    with pytest.raises(org_chart.OrgChartBuildError, match="'tree' key"):
        org_chart.build_data_model({"nodes": []})


def test_org_chart_builder_rejects_non_dict_node():
    from src.smartart_pptx_native.layouts import org_chart

    with pytest.raises(org_chart.OrgChartBuildError, match="must be a dict"):
        org_chart.build_data_model({"tree": "not a dict"})


def test_org_chart_builder_rejects_node_missing_title():
    from src.smartart_pptx_native.layouts import org_chart

    tree = {
        "tree": {
            "title": "Root",
            "children": [{"no_title_here": "oops"}],
        }
    }
    with pytest.raises(org_chart.OrgChartBuildError, match="missing 'title'"):
        org_chart.build_data_model(tree)


# ---------------------------------------------------------------------------
# Extractor routing tests
# ---------------------------------------------------------------------------

def test_extract_cycle_for_pptx_native():
    from src.smartart_extractor import extract

    slide = {"slide_number": 1, "body_points": ["Plan", "Build", "Test", "Deploy"]}
    selection = {
        "slide_number": 1,
        "graphic_type": "cycle",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)
    assert spec["engine"] == "pptx_native"
    assert spec["graphic_type"] == "cycle"
    assert spec["data"] == {"stages": ["Plan", "Build", "Test", "Deploy"]}


def test_extract_org_chart_indented_body_points():
    from src.smartart_extractor import extract

    slide = {
        "slide_number": 1,
        "body_points": [
            "CEO",
            "  CTO",
            "    Backend Lead",
            "    Frontend Lead",
            "  CFO",
            "    Finance Manager",
        ],
    }
    selection = {
        "slide_number": 1,
        "graphic_type": "org_chart",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)
    tree = spec["data"]["tree"]
    assert tree["title"] == "CEO"
    assert len(tree["children"]) == 2
    cto = tree["children"][0]
    assert cto["title"] == "CTO"
    assert len(cto["children"]) == 2
    assert cto["children"][0]["title"] == "Backend Lead"


def test_extract_org_chart_with_assistant_marker():
    from src.smartart_extractor import extract

    slide = {
        "slide_number": 1,
        "body_points": [
            "CEO",
            "  Executive Assistant (asst)",
            "  CTO",
            "  CFO",
        ],
    }
    selection = {
        "slide_number": 1,
        "graphic_type": "org_chart",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)
    tree = spec["data"]["tree"]
    assert tree["title"] == "CEO"
    assert len(tree["children"]) == 3
    # The assistant should be marked
    assts = [c for c in tree["children"] if c.get("asst") is True]
    assert len(assts) == 1
    assert assts[0]["title"] == "Executive Assistant"


def test_extract_org_chart_flat_fallback():
    """body_points with no indentation: first is root, rest are direct children."""
    from src.smartart_extractor import extract

    slide = {"slide_number": 1, "body_points": ["CEO", "CTO", "CFO"]}
    selection = {
        "slide_number": 1,
        "graphic_type": "org_chart",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)
    tree = spec["data"]["tree"]
    assert tree["title"] == "CEO"
    # CTO and CFO become direct children
    child_titles = [c["title"] for c in tree["children"]]
    assert "CTO" in child_titles
    assert "CFO" in child_titles


# ---------------------------------------------------------------------------
# End-to-end through the engine
# ---------------------------------------------------------------------------

def test_engine_renders_cycle_end_to_end():
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {"slide_number": 4, "body_points": ["Plan", "Do", "Check", "Act"]}
    selection = {
        "slide_number": 4,
        "graphic_type": "cycle",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)

    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, STYLE_GUIDE, "production", tmpdir)
        assert entry["status"] == "rendered"
        assert entry["graphic_type"] == "cycle"
        assert entry["engine_used"] == "pptx_native"


def test_engine_renders_org_chart_end_to_end():
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {
        "slide_number": 5,
        "body_points": [
            "Root",
            "  Assistant (asst)",
            "  Left Branch",
            "  Right Branch",
        ],
    }
    selection = {
        "slide_number": 5,
        "graphic_type": "org_chart",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)

    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, STYLE_GUIDE, "production", tmpdir)
        assert entry["status"] == "rendered"
        assert entry["graphic_type"] == "org_chart"
        assert entry["engine_used"] == "pptx_native"


# ---------------------------------------------------------------------------
# _body_points_to_tree unit tests
# ---------------------------------------------------------------------------

def test_body_points_to_tree_simple():
    from src.smartart_extractor import _body_points_to_tree

    tree = _body_points_to_tree([
        "Root",
        "  Child A",
        "  Child B",
    ])
    assert tree["title"] == "Root"
    assert [c["title"] for c in tree["children"]] == ["Child A", "Child B"]


def test_body_points_to_tree_deep_nesting():
    from src.smartart_extractor import _body_points_to_tree

    tree = _body_points_to_tree([
        "Level 0",
        "  Level 1",
        "    Level 2",
        "      Level 3",
    ])
    assert tree["title"] == "Level 0"
    l1 = tree["children"][0]
    assert l1["title"] == "Level 1"
    l2 = l1["children"][0]
    assert l2["title"] == "Level 2"
    l3 = l2["children"][0]
    assert l3["title"] == "Level 3"


def test_body_points_to_tree_handles_empty():
    from src.smartart_extractor import _body_points_to_tree

    assert _body_points_to_tree([]) is None


def test_body_points_to_tree_asst_marker_square_brackets():
    from src.smartart_extractor import _body_points_to_tree

    tree = _body_points_to_tree([
        "CEO",
        "  Chief of Staff [asst]",
        "  CTO",
    ])
    cos = tree["children"][0]
    assert cos["title"] == "Chief of Staff"
    assert cos["asst"] is True
