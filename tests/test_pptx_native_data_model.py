"""Tests for pptx_native data model primitives."""
from __future__ import annotations

import re
from xml.etree import ElementTree as ET

import pytest


DGM_NS = "{http://schemas.openxmlformats.org/drawingml/2006/diagram}"
A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def _parse_fragment(fragment: str) -> ET.Element:
    """Parse a fragment of data model XML by wrapping it in the dataModel envelope."""
    from src.smartart_pptx_native import data_model

    doc = data_model.wrap_data_model(fragment, "")
    return ET.fromstring(doc)


def test_gid_format():
    """GIDs must be brace-wrapped uppercase UUIDs."""
    from src.smartart_pptx_native.data_model import gid

    for _ in range(20):
        g = gid()
        assert re.fullmatch(
            r"\{[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}\}",
            g,
        ), f"bad gid format: {g}"


def test_gid_uniqueness():
    from src.smartart_pptx_native.data_model import gid

    ids = {gid() for _ in range(1000)}
    assert len(ids) == 1000  # no collisions in 1000 draws


def test_build_doc_prset_defaults():
    from src.smartart_pptx_native.data_model import build_doc_prset

    prset = build_doc_prset("urn:microsoft.com/office/officeart/2005/8/layout/process1")
    assert 'loTypeId="urn:microsoft.com/office/officeart/2005/8/layout/process1"' in prset
    assert 'qsTypeId="urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1"' in prset
    assert 'csTypeId="urn:microsoft.com/office/officeart/2005/8/colors/accent1_2"' in prset
    assert 'phldr="0"' in prset


def test_build_doc_prset_override():
    from src.smartart_pptx_native.data_model import build_doc_prset

    prset = build_doc_prset(
        "urn:example/custom",
        qs_type_id="urn:example/qs",
        cs_type_id="urn:example/cs",
    )
    assert 'qsTypeId="urn:example/qs"' in prset
    assert 'csTypeId="urn:example/cs"' in prset


def test_make_doc_pt_produces_well_formed_xml():
    from src.smartart_pptx_native.data_model import build_doc_prset, make_doc_pt

    prset = build_doc_prset("urn:microsoft.com/office/officeart/2005/8/layout/process1")
    frag = make_doc_pt("{FAKE-DOC-ID}", prset)
    root = _parse_fragment(frag)
    doc_pt = root.find(f"{DGM_NS}ptLst/{DGM_NS}pt")
    assert doc_pt is not None
    assert doc_pt.get("modelId") == "{FAKE-DOC-ID}"
    assert doc_pt.get("type") == "doc"


def test_make_node_pt_regular():
    from src.smartart_pptx_native.data_model import make_node_pt

    frag = make_node_pt("{N1}", "Research")
    root = _parse_fragment(frag)
    pt = root.find(f"{DGM_NS}ptLst/{DGM_NS}pt")
    assert pt is not None
    assert pt.get("modelId") == "{N1}"
    assert pt.get("type") is None  # regular node has no type attribute
    text = pt.find(f"{DGM_NS}t/{A_NS}p/{A_NS}r/{A_NS}t")
    assert text is not None and text.text == "Research"


def test_make_node_pt_assistant():
    from src.smartart_pptx_native.data_model import make_node_pt

    frag = make_node_pt("{A1}", "Executive Assistant", is_asst=True)
    root = _parse_fragment(frag)
    pt = root.find(f"{DGM_NS}ptLst/{DGM_NS}pt")
    assert pt.get("type") == "asst"
    text = pt.find(f"{DGM_NS}t/{A_NS}p/{A_NS}r/{A_NS}t")
    assert text.text == "Executive Assistant"


def test_make_node_pt_escapes_xml_special_chars():
    """Labels with <, >, &, ', \" must be escaped to keep XML well-formed."""
    from src.smartart_pptx_native.data_model import make_node_pt

    frag = make_node_pt("{N1}", "A & B <C>")
    root = _parse_fragment(frag)
    text = root.find(f"{DGM_NS}ptLst/{DGM_NS}pt/{DGM_NS}t/{A_NS}p/{A_NS}r/{A_NS}t")
    assert text.text == "A & B <C>"  # ElementTree un-escapes on read


def test_make_par_trans_and_sib_trans_types():
    from src.smartart_pptx_native.data_model import make_par_trans, make_sib_trans

    par_frag = make_par_trans("{P1}")
    sib_frag = make_sib_trans("{S1}")

    par_root = _parse_fragment(par_frag)
    sib_root = _parse_fragment(sib_frag)

    par_pt = par_root.find(f"{DGM_NS}ptLst/{DGM_NS}pt")
    sib_pt = sib_root.find(f"{DGM_NS}ptLst/{DGM_NS}pt")

    assert par_pt.get("type") == "parTrans"
    assert sib_pt.get("type") == "sibTrans"


def test_make_cxn_structure():
    from src.smartart_pptx_native.data_model import make_cxn

    # Use the cxn primitive in a cxnLst context.
    frag = make_cxn("{SRC}", "{DST}", 2, "{PAR}", "{SIB}")
    root = _parse_fragment("")  # empty pt list
    # Manually wrap cxn for parsing
    from src.smartart_pptx_native.data_model import wrap_data_model

    doc = wrap_data_model("", frag)
    root = ET.fromstring(doc)
    cxn = root.find(f"{DGM_NS}cxnLst/{DGM_NS}cxn")
    assert cxn is not None
    assert cxn.get("srcId") == "{SRC}"
    assert cxn.get("destId") == "{DST}"
    assert cxn.get("srcOrd") == "2"
    assert cxn.get("destOrd") == "0"
    assert cxn.get("parTransId") == "{PAR}"
    assert cxn.get("sibTransId") == "{SIB}"
    assert cxn.get("type") is None  # untyped data cxn


def test_make_cxn_has_unique_model_ids():
    """Each call to make_cxn must generate a fresh modelId."""
    from src.smartart_pptx_native.data_model import make_cxn

    ids = set()
    for _ in range(50):
        frag = make_cxn("{SRC}", "{DST}", 0, "{PAR}", "{SIB}")
        m = re.search(r'modelId="(\{[^}]+\})"', frag)
        assert m
        ids.add(m.group(1))
    assert len(ids) == 50


def test_wrap_data_model_produces_valid_xml_with_all_namespaces():
    from src.smartart_pptx_native.data_model import (
        build_doc_prset,
        make_cxn,
        make_doc_pt,
        make_node_pt,
        make_par_trans,
        make_sib_trans,
        wrap_data_model,
    )

    doc_id = "{DOC}"
    n1, p1, s1 = "{N1}", "{P1}", "{S1}"
    n2, p2, s2 = "{N2}", "{P2}", "{S2}"

    prset = build_doc_prset("urn:microsoft.com/office/officeart/2005/8/layout/process1")
    pts = (
        make_doc_pt(doc_id, prset)
        + make_node_pt(n1, "Alpha")
        + make_par_trans(p1)
        + make_sib_trans(s1)
        + make_node_pt(n2, "Beta")
        + make_par_trans(p2)
        + make_sib_trans(s2)
    )
    cxns = (
        make_cxn(doc_id, n1, 0, p1, s1)
        + make_cxn(doc_id, n2, 1, p2, s2)
    )
    doc_bytes = wrap_data_model(pts, cxns)
    root = ET.fromstring(doc_bytes)

    assert root.tag == f"{DGM_NS}dataModel"

    all_pts = root.findall(f"{DGM_NS}ptLst/{DGM_NS}pt")
    assert len(all_pts) == 7  # 1 doc + 2 nodes + 2 parTrans + 2 sibTrans

    types = [p.get("type") for p in all_pts]
    assert types.count("doc") == 1
    assert types.count("parTrans") == 2
    assert types.count("sibTrans") == 2
    assert types.count(None) == 2  # untyped regular nodes

    all_cxns = root.findall(f"{DGM_NS}cxnLst/{DGM_NS}cxn")
    assert len(all_cxns) == 2

    assert root.find(f"{DGM_NS}bg") is not None
    assert root.find(f"{DGM_NS}whole") is not None


def test_wrap_data_model_output_is_utf8_bytes():
    from src.smartart_pptx_native.data_model import wrap_data_model

    result = wrap_data_model("", "")
    assert isinstance(result, bytes)
    assert result.startswith(b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
