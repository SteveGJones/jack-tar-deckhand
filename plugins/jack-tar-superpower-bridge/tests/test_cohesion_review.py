import pytest

from src.cohesion_review import (
    DeckVerdict,
    SlideVerdict,
    parse_reviewer_envelope,
    decide_action,
    AutoAction,
    aggregate_for_report,
)


def test_parse_reviewer_envelope_minimal():
    payload = {
        "aggregate_verdict": "pass",
        "slide_verdicts": [],
    }
    dv = parse_reviewer_envelope(payload)
    assert dv.aggregate_verdict == "pass"
    assert dv.slide_verdicts == []


def test_parse_envelope_rejects_unknown_aggregate():
    with pytest.raises(ValueError, match="aggregate"):
        parse_reviewer_envelope({"aggregate_verdict": "weird", "slide_verdicts": []})


def test_parse_envelope_rejects_unknown_slide_verdict():
    payload = {
        "aggregate_verdict": "pass",
        "slide_verdicts": [{
            "slide_index": 1, "enrichment_kind": "background",
            "verdict": "WAT", "severity": "blocking", "confidence": 0.9,
            "reason": "x",
        }],
    }
    with pytest.raises(ValueError, match="verdict"):
        parse_reviewer_envelope(payload)


def test_decide_action_pass_returns_no_action():
    sv = SlideVerdict(slide_index=1, enrichment_kind="background",
                       verdict="pass", severity="suggestion",
                       confidence=0.9, reason="x")
    assert decide_action(sv).kind == "no_action"


def test_decide_action_flag_contrast_blocking_triggers_regen():
    sv = SlideVerdict(slide_index=1, enrichment_kind="background",
                       verdict="flag_contrast", severity="blocking",
                       confidence=0.9, reason="text obscured")
    a = decide_action(sv)
    assert a.kind == "regenerate"
    assert "contrast" in a.guidance.lower()


def test_decide_action_flag_contrast_suggestion_records_only():
    sv = SlideVerdict(slide_index=1, enrichment_kind="background",
                       verdict="flag_contrast", severity="suggestion",
                       confidence=0.9, reason="borderline")
    a = decide_action(sv)
    assert a.kind == "record_only"


def test_decide_action_flag_overcrowded_smartart_retry_with_clear():
    sv = SlideVerdict(slide_index=4, enrichment_kind="smartart",
                       verdict="flag_overcrowded", severity="blocking",
                       confidence=0.9, reason="body text bleeds through")
    a = decide_action(sv)
    assert a.kind == "retry_clear_overlap"


def test_decide_action_flag_overcrowded_image_surfaces_to_user():
    sv = SlideVerdict(slide_index=2, enrichment_kind="image",
                       verdict="flag_overcrowded", severity="blocking",
                       confidence=0.9, reason="image too big")
    a = decide_action(sv)
    assert a.kind == "surface_to_user"


def test_decide_action_unassessable_records_with_powerpoint_note():
    sv = SlideVerdict(slide_index=4, enrichment_kind="smartart",
                       verdict="unassessable_rasterisation", severity="suggestion",
                       confidence=0.5, reason="LibreOffice SmartArt artefact")
    a = decide_action(sv)
    assert a.kind == "record_only"
    assert "powerpoint" in a.guidance.lower()


def test_decide_action_flag_inconsistency_blocking_surfaces_to_user():
    sv = SlideVerdict(slide_index=5, enrichment_kind="background",
                       verdict="flag_inconsistency", severity="blocking",
                       confidence=0.9, reason="cinematic vs flat clash")
    a = decide_action(sv)
    assert a.kind == "surface_to_user"


def test_aggregate_for_report_summarises_actions():
    verdicts = [
        SlideVerdict(1, "background", "pass", "suggestion", 0.9, "ok"),
        SlideVerdict(2, "image", "flag_contrast", "suggestion", 0.8, "borderline"),
        SlideVerdict(3, "smartart", "flag_overcrowded", "blocking", 0.9,
                      "body bleeds through"),
    ]
    summary = aggregate_for_report(verdicts)
    assert summary["pass_count"] == 1
    assert summary["suggestion_count"] == 1
    assert summary["blocking_count"] == 1
    assert any("retry_clear_overlap" in act["action"] for act in summary["actions"])
