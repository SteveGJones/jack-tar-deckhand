"""Tests for the process1 layout builder."""
from __future__ import annotations

from xml.etree import ElementTree as ET

import pytest


DGM_NS = "{http://schemas.openxmlformats.org/drawingml/2006/diagram}"
A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def _parse(xml_bytes: bytes) -> ET.Element:
    return ET.fromstring(xml_bytes)


def test_build_data_model_happy_path_5_steps():
    from src.smartart_pptx_native.layouts import process

    result = process.build_data_model(
        {"steps": ["Research", "Design", "Build", "Test", "Ship"]}
    )
    root = _parse(result)

    pts = root.findall(f"{DGM_NS}ptLst/{DGM_NS}pt")
    # 1 doc + 5 nodes + 5 parTrans + 5 sibTrans = 16
    assert len(pts) == 16

    types = [p.get("type") for p in pts]
    assert types.count("doc") == 1
    assert types.count("parTrans") == 5
    assert types.count("sibTrans") == 5
    assert types.count(None) == 5  # regular nodes have no type attribute

    cxns = root.findall(f"{DGM_NS}cxnLst/{DGM_NS}cxn")
    assert len(cxns) == 5

    # Verify all cxns are from the doc to a node
    doc_pt = next(p for p in pts if p.get("type") == "doc")
    doc_id = doc_pt.get("modelId")
    for cxn in cxns:
        assert cxn.get("srcId") == doc_id
        assert cxn.get("type") is None
        assert cxn.get("destOrd") == "0"
    # srcOrd should be 0..4 in insertion order
    assert [c.get("srcOrd") for c in cxns] == ["0", "1", "2", "3", "4"]


def test_build_data_model_minimum_2_steps():
    """min_nodes is 2 per catalog; this should succeed."""
    from src.smartart_pptx_native.layouts import process

    result = process.build_data_model({"steps": ["Plan", "Execute"]})
    root = _parse(result)
    cxns = root.findall(f"{DGM_NS}cxnLst/{DGM_NS}cxn")
    assert len(cxns) == 2


def test_build_data_model_maximum_9_steps():
    """max_nodes is 9 per catalog; this should succeed."""
    from src.smartart_pptx_native.layouts import process

    steps = [f"Step {i}" for i in range(1, 10)]
    result = process.build_data_model({"steps": steps})
    root = _parse(result)
    cxns = root.findall(f"{DGM_NS}cxnLst/{DGM_NS}cxn")
    assert len(cxns) == 9


def test_text_content_preserved_in_order():
    from src.smartart_pptx_native.layouts import process

    labels = ["Alpha", "Bravo", "Charlie"]
    result = process.build_data_model({"steps": labels})
    root = _parse(result)

    # Collect node text in document order
    texts = []
    for pt in root.findall(f"{DGM_NS}ptLst/{DGM_NS}pt"):
        if pt.get("type") is None:  # regular node
            t = pt.find(f"{DGM_NS}t/{A_NS}p/{A_NS}r/{A_NS}t")
            if t is not None and t.text:
                texts.append(t.text)
    assert texts == labels


def test_doc_point_carries_layout_uri_from_catalog():
    from src.smartart_pptx_native.layouts import process

    result = process.build_data_model({"steps": ["A", "B"]})
    # Raw string check — prSet attrs live in the doc point
    assert b'loTypeId="urn:microsoft.com/office/officeart/2005/8/layout/process1"' in result


def test_build_rejects_missing_steps_key():
    from src.smartart_pptx_native.layouts import process

    with pytest.raises(process.ProcessBuildError, match="'steps' key"):
        process.build_data_model({"items": ["A", "B"]})


def test_build_rejects_non_list_steps():
    from src.smartart_pptx_native.layouts import process

    with pytest.raises(process.ProcessBuildError, match="must be a list"):
        process.build_data_model({"steps": "not a list"})


def test_build_rejects_non_string_steps():
    from src.smartart_pptx_native.layouts import process

    with pytest.raises(process.ProcessBuildError, match="must contain only strings"):
        process.build_data_model({"steps": ["ok", 42, "ok"]})


def test_build_rejects_too_few_steps():
    from src.smartart_pptx_native.layouts import process

    with pytest.raises(process.ProcessBuildError, match="at least 2"):
        process.build_data_model({"steps": ["Lonely"]})


def test_build_rejects_too_many_steps():
    from src.smartart_pptx_native.layouts import process

    steps = [f"Step {i}" for i in range(1, 12)]  # 11 steps > 9
    with pytest.raises(process.ProcessBuildError, match="at most 9"):
        process.build_data_model({"steps": steps})


def test_build_rejects_long_labels():
    from src.smartart_pptx_native.layouts import process

    # max_label_chars = 24
    long_label = "A" * 25
    with pytest.raises(process.ProcessBuildError, match="<= 24"):
        process.build_data_model({"steps": ["OK", long_label]})


def test_build_strips_whitespace_from_labels():
    """Labels should be trimmed of leading/trailing whitespace."""
    from src.smartart_pptx_native.layouts import process

    result = process.build_data_model({"steps": ["  Alpha  ", "Beta\n"]})
    root = _parse(result)
    texts = [
        t.text
        for t in root.findall(
            f"{DGM_NS}ptLst/{DGM_NS}pt/{DGM_NS}t/{A_NS}p/{A_NS}r/{A_NS}t"
        )
    ]
    assert texts == ["Alpha", "Beta"]


def test_get_layout_uri():
    from src.smartart_pptx_native.layouts import process

    assert process.get_layout_uri() == (
        "urn:microsoft.com/office/officeart/2005/8/layout/process1"
    )


def test_get_seed_path_resolves_to_existing_file():
    from src.smartart_pptx_native.layouts import process

    path = process.get_seed_path()
    assert path.exists()
    assert path.suffix == ".pptx"


def test_each_cxn_has_unique_transition_ids():
    """parTransId and sibTransId must be unique per cxn — no reuse across edges."""
    from src.smartart_pptx_native.layouts import process

    result = process.build_data_model({"steps": ["A", "B", "C", "D"]})
    root = _parse(result)
    cxns = root.findall(f"{DGM_NS}cxnLst/{DGM_NS}cxn")
    par_ids = [c.get("parTransId") for c in cxns]
    sib_ids = [c.get("sibTransId") for c in cxns]
    assert len(set(par_ids)) == len(par_ids)
    assert len(set(sib_ids)) == len(sib_ids)
    # par and sib should not collide with each other either
    assert not set(par_ids) & set(sib_ids)
