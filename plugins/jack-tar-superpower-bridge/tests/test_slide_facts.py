import pytest
from src.slide_facts import (
    Marker,
    SlideFacts,
    EnrichmentChoice,
    AnalyserResult,
    OverlapWarning,
)


def test_marker_rejects_unknown_kind():
    with pytest.raises(ValueError, match="invalid kind"):
        Marker(kind="LOGO", identifier="foo", left_emu=0, top_emu=0, width_emu=0, height_emu=0)


def test_marker_roundtrip_dict():
    m = Marker(kind="IMAGE", identifier="agent-architecture", left_emu=1, top_emu=2,
               width_emu=3, height_emu=4)
    d = m.to_dict()
    assert d == {"kind": "IMAGE", "identifier": "agent-architecture",
                 "left_emu": 1, "top_emu": 2, "width_emu": 3, "height_emu": 4}


def test_marker_from_dict_ignores_unknown_keys():
    m = Marker.from_dict({"kind": "IMAGE", "identifier": "x",
                          "left_emu": 0, "top_emu": 0,
                          "width_emu": 0, "height_emu": 0,
                          "future_field": 99})
    assert m.kind == "IMAGE"
    assert m.identifier == "x"


def test_slide_facts_default_collections():
    sf = SlideFacts(slide_index=1, text_content="")
    assert sf.markers == []
    assert sf.background_kind == "default"
    assert sf.element_types == {}


def test_slide_facts_roundtrip():
    sf = SlideFacts(
        slide_index=3,
        text_content="hello",
        markers=[Marker("BG", "dark", 0, 0, 0, 0)],
        background_kind="image",
        element_types={"text": 1},
    )
    out = SlideFacts.from_dict(sf.to_dict())
    assert out.slide_index == 3
    assert out.markers[0].kind == "BG"
    assert out.background_kind == "image"


def test_enrichment_choice_rejects_unknown_action():
    with pytest.raises(ValueError, match="invalid action"):
        EnrichmentChoice(slide_index=1, kind="background", marker_id="BG:foo",
                         action="float-in-the-air")


def test_enrichment_choice_smartart_overlap_options():
    for action in ("apply", "apply_clear_overlap", "skip"):
        EnrichmentChoice(slide_index=1, kind="smartart", marker_id="SMARTART:foo",
                         action=action)


def test_overlap_warning_holds_intersecting_shape_names():
    w = OverlapWarning(slide_index=4, marker_id="SMARTART:three-pillars",
                       overlapping_shape_names=["Body 1", "Body 2"])
    assert "Body 1" in w.overlapping_shape_names


def test_analyser_result_aggregates_facts_and_warnings():
    sf = SlideFacts(slide_index=1, text_content="x")
    r = AnalyserResult(
        slides=[sf],
        duplicate_marker_ids=["IMAGE:foo"],
        overlap_warnings=[],
        js_fallback_used=False,
        notes=["zero markers found"],
    )
    assert r.total_slides == 1
    assert r.total_markers == 0
    assert r.duplicate_marker_ids == ["IMAGE:foo"]
