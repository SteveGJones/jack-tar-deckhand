"""Tests for the Run 8 Finding #28 verification escalation helper.

The helper inspects an image-reviewer's verdict against the EXACT-labels
list and decides whether the verdict warrants a second-opinion dispatch
at a higher model tier. The decision is verification-then-confirmation:
this module produces the verification recommendation only; the
orchestrator (SKILL.md) is responsible for surfacing the recommendation
to the user and dispatching the second reviewer ONLY after explicit
operator confirmation (no silent dual-dispatch).
"""
from __future__ import annotations

from src.cycle_state import (
    EscalationRecommendation,
    verify_review_evidences_comparison,
)


# ---------------------------------------------------------------------------
# No-escalation cases
# ---------------------------------------------------------------------------


def test_no_expected_labels_means_no_escalation() -> None:
    """Atmospheric markers carry no expected text — never escalate."""
    rec = verify_review_evidences_comparison(
        verdict_payload={"verdict": "pass", "summary": "atmospheric BG fine"},
        expected_text_content=None,
    )
    assert rec.should_escalate is False


def test_empty_expected_labels_no_escalation() -> None:
    """Empty list is the atmospheric-marker signal — no escalation."""
    rec = verify_review_evidences_comparison(
        verdict_payload={"verdict": "pass"},
        expected_text_content=[],
    )
    assert rec.should_escalate is False


def test_refine_verdict_does_not_trigger_escalation() -> None:
    """A refine verdict already has concrete issues for the cycle to act on."""
    rec = verify_review_evidences_comparison(
        verdict_payload={
            "verdict": "refine",
            "issues": ["text rendered 'Tasnia' instead of 'Tasmania'"],
        },
        expected_text_content=["Thylacine", "Tasmania"],
    )
    assert rec.should_escalate is False


def test_pass_with_quoted_label_no_escalation() -> None:
    """Reviewer quotes back at least one expected label — comparison evidenced.

    Run 8 Condor case modelled here: when the reviewer's prose contains
    the expected text strings, it has demonstrably done the comparison.
    """
    rec = verify_review_evidences_comparison(
        verdict_payload={
            "verdict": "pass",
            "strengths": ["All four labels render — California Condor, Gymnogyps"],
            "issues": [],
            "composition_notes": {
                "text_rendering": "California Condor reads cleanly; 22 in 1987 in burgundy"
            },
            "summary": "All expected text rendered correctly",
        },
        expected_text_content=[
            "California Condor",
            "Gymnogyps californianus",
            "22 in 1987",
            "537 in 2023",
        ],
    )
    assert rec.should_escalate is False
    assert "California Condor" in rec.matched_labels


def test_pass_with_one_quoted_label_is_sufficient() -> None:
    """Even a single matched label is enough evidence — quoting is the smell test."""
    rec = verify_review_evidences_comparison(
        verdict_payload={
            "verdict": "pass",
            "summary": "Thylacine illustration is well-executed",
        },
        expected_text_content=[
            "Thylacine",
            "Thylacinus cynocephalus",
            "Tasmania",
            "1936",
        ],
    )
    assert rec.should_escalate is False
    assert rec.matched_labels == ("Thylacine",)


def test_match_is_case_insensitive() -> None:
    """Reviewer prose may capitalise differently; matching tolerates it."""
    rec = verify_review_evidences_comparison(
        verdict_payload={
            "verdict": "pass",
            "summary": "BAIJI RIVER DOLPHIN appears clearly",
        },
        expected_text_content=["Baiji River Dolphin", "2006"],
    )
    assert rec.should_escalate is False
    assert "Baiji River Dolphin" in rec.matched_labels


# ---------------------------------------------------------------------------
# Escalation cases — Run 8 Thylacine pattern
# ---------------------------------------------------------------------------


def test_pass_without_quoted_labels_escalates() -> None:
    """Run 8 Thylacine motivating case.

    Reviewer claimed all four labels rendered correctly with confidence
    0.92, but the actual image had ``cynogechalus`` and ``Tasnia``. The
    reviewer's prose was generic ("All four expected text strings
    rendered correctly and legibly") with no actual quotation of the
    expected text. This pattern triggers escalation.
    """
    rec = verify_review_evidences_comparison(
        verdict_payload={
            "verdict": "pass",
            "confidence": 0.92,
            "strengths": [
                "All four expected text strings rendered correctly and legibly",
                "Warm vellum palette matches brand direction",
                "Naturalist-engraving aesthetic achieved",
            ],
            "issues": [],
            "composition_notes": {
                "subject_placement": "left/center, caption right — correct positioning",
                "scale_hierarchy": "animal dominates frame, text secondary",
                "text_rendering": "all present and spelled correctly",
            },
            "summary": "Museum-quality naturalist engraving with all four expected labels",
        },
        expected_text_content=[
            "Thylacine",
            "Thylacinus cynocephalus",
            "Tasmania",
            "1936",
        ],
    )
    assert rec.should_escalate is True
    assert rec.reason is not None
    assert "Haiku may have confabulated" in rec.reason
    assert rec.matched_labels == ()
    assert "Thylacine" in rec.expected_labels


def test_one_full_match_among_many_expected_is_sufficient() -> None:
    """Reviewer needs to quote at least ONE expected label verbatim — not all."""
    rec = verify_review_evidences_comparison(
        verdict_payload={
            "verdict": "pass",
            "summary": "Tasmania caption set in italic serif renders cleanly",
        },
        expected_text_content=["Thylacine", "Thylacinus cynocephalus", "Tasmania", "1936"],
    )
    assert rec.should_escalate is False
    assert "Tasmania" in rec.matched_labels
    # The other 3 labels don't appear in the prose — but one match is enough
    # to evidence the comparison.
    assert len(rec.matched_labels) == 1


def test_short_labels_are_skipped() -> None:
    """Tokens shorter than 3 alnum chars are skipped to avoid false matches.

    A label like "37" or "of" would match almost any prose; the helper
    deliberately does not test against them. If ALL expected labels are
    too short, the helper passes through without triggering escalation
    (insufficient signal to make a recommendation).
    """
    rec = verify_review_evidences_comparison(
        verdict_payload={
            "verdict": "pass",
            "summary": "image renders with appropriate composition",
        },
        expected_text_content=["of", "in", "37"],
    )
    assert rec.should_escalate is False  # not enough signal to escalate
    assert rec.matched_labels == ()


def test_short_labels_filtered_in_significant_check() -> None:
    """When some labels are short and some are long, only the long ones gate the decision.

    If all LONG labels are missing from the reviewer's prose, escalate even
    if shorter labels exist in the expected list.
    """
    rec = verify_review_evidences_comparison(
        verdict_payload={
            "verdict": "pass",
            "summary": "the image renders cleanly with appropriate context",
        },
        expected_text_content=[
            "Thylacine",                # long, distinctive — must appear
            "Thylacinus cynocephalus",   # long, distinctive — must appear
            "1936",                       # 4 alnum, kept
            "Tasmania",                   # long, distinctive — must appear
        ],
    )
    # None of the long labels appear in the prose — escalate.
    assert rec.should_escalate is True


def test_recommendation_is_dataclass_with_diagnostic_fields() -> None:
    """The dataclass surfaces matched_labels + expected_labels for orchestrator UI."""
    rec = verify_review_evidences_comparison(
        verdict_payload={"verdict": "pass", "summary": "rendered cleanly"},
        expected_text_content=["California Condor", "Gymnogyps californianus"],
    )
    assert isinstance(rec, EscalationRecommendation)
    assert rec.expected_labels == ("California Condor", "Gymnogyps californianus")
    assert rec.matched_labels == ()
    assert rec.should_escalate is True


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_missing_analysis_fields_treated_as_empty() -> None:
    """A minimal verdict payload (just `verdict`) parses safely."""
    rec = verify_review_evidences_comparison(
        verdict_payload={"verdict": "pass"},
        expected_text_content=["California Condor"],
    )
    assert rec.should_escalate is True


def test_strengths_as_string_not_list_handled() -> None:
    """Defensive: if a reviewer returns ``strengths`` as a string, handle gracefully."""
    rec = verify_review_evidences_comparison(
        verdict_payload={
            "verdict": "pass",
            "strengths": "California Condor renders cleanly",  # wrong type but parseable
            "summary": "good",
        },
        expected_text_content=["California Condor"],
    )
    assert rec.should_escalate is False
    assert "California Condor" in rec.matched_labels
