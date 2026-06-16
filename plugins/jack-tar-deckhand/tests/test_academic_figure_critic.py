"""Tests for academic_figure_critic dispatch helpers (#113 Path B)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.academic_figure_critic import (  # noqa: E402
    _VALID_FIGURE_TYPES,
    build_critic_input,
    decide_next_action,
    parse_critic_output,
)


# ---------------------------------------------------------------------------
# build_critic_input
# ---------------------------------------------------------------------------


def test_build_critic_input_includes_methodology_caption_and_image_path():
    blob = build_critic_input(
        methodology_text="The encoder applies multi-head attention with 8 heads.",
        caption="Figure 3: Encoder architecture",
        figure_type="architecture_diagram",
        image_path="/tmp/out.png",
        prior_scores_history=[],
        iteration_index=1,
        iteration_cap=4,
    )
    assert "multi-head attention with 8 heads" in blob
    assert "Figure 3: Encoder architecture" in blob
    assert "architecture_diagram" in blob
    assert "/tmp/out.png" in blob
    assert "Iteration index: 1" in blob
    assert "Iteration cap: 4" in blob


def test_build_critic_input_rejects_unknown_figure_type():
    """Defensive: an unknown figure_type would yield unpredictable critic
    scoring. Caller has to pick a canonical value."""
    with pytest.raises(ValueError, match="figure_type"):
        build_critic_input(
            methodology_text="x",
            caption="y",
            figure_type="schematic_blueprint",  # not in enum
            image_path="/tmp/x.png",
            prior_scores_history=[],
            iteration_index=1,
            iteration_cap=4,
        )


def test_build_critic_input_accepts_every_canonical_figure_type():
    """Pin the figure_type enum — adding a new one means schema + agent +
    test must all update in lockstep."""
    for ft in _VALID_FIGURE_TYPES:
        build_critic_input(
            methodology_text="x",
            caption="y",
            figure_type=ft,
            image_path="/tmp/x.png",
            prior_scores_history=[],
            iteration_index=1,
            iteration_cap=4,
        )


def test_build_critic_input_no_side_by_side_when_none_provided():
    blob = build_critic_input(
        methodology_text="x",
        caption="y",
        figure_type="other",
        image_path="/tmp/x.png",
        prior_scores_history=[],
        iteration_index=1,
        iteration_cap=4,
    )
    assert "side-by-side" not in blob.lower()
    assert "Paperbanana" not in blob


def test_build_critic_input_includes_side_by_side_when_provided():
    """Equivalence-testing path: paperbanana verdict is included so the agent
    can record whether it agrees. The blob must explicitly label it as
    'do NOT defer to this' so the agent doesn't anchor to it."""
    blob = build_critic_input(
        methodology_text="x",
        caption="y",
        figure_type="other",
        image_path="/tmp/x.png",
        prior_scores_history=[],
        iteration_index=1,
        iteration_cap=4,
        paperbanana_side_by_side_verdict={"verdict": "pass", "score": 92},
    )
    assert "side-by-side" in blob.lower()
    assert "Do NOT defer to this" in blob
    assert '"verdict": "pass"' in blob


def test_build_critic_input_prior_history_rendered_as_json():
    history = [
        {"iteration": 1, "methodology_fidelity": 70, "verdict": "refine"},
        {"iteration": 2, "methodology_fidelity": 78, "verdict": "refine"},
    ]
    blob = build_critic_input(
        methodology_text="x",
        caption="y",
        figure_type="other",
        image_path="/tmp/x.png",
        prior_scores_history=history,
        iteration_index=3,
        iteration_cap=5,
    )
    assert '"methodology_fidelity": 70' in blob
    assert '"methodology_fidelity": 78' in blob


# ---------------------------------------------------------------------------
# parse_critic_output — schema validation + semantic checks
# ---------------------------------------------------------------------------


def _verdict(
    *,
    verdict="pass",
    scores=None,
    issues=None,
    refinement_feedback="",
    iteration_index=1,
    plateau_signal=False,
    agrees=None,
):
    """Build a valid FigureCriticVerdict payload for tests."""
    if scores is None:
        scores = {
            "methodology_fidelity": 85,
            "caption_alignment": 90,
            "legibility": 82,
            "figure_type_correctness": 88,
            "aesthetic_quality": 85,
        }
    if issues is None:
        issues = [] if verdict == "pass" else [{"axis": "legibility", "detail": "ok"}]
    return {
        "verdict": verdict,
        "per_axis_scores": scores,
        "issues": issues,
        "refinement_feedback": refinement_feedback,
        "iteration_index": iteration_index,
        "plateau_signal": plateau_signal,
        "agrees_with_paperbanana_verdict": agrees,
    }


def _fence(payload):
    return f"```json\n{json.dumps(payload)}\n```"


def test_parse_critic_output_happy_path():
    out = parse_critic_output(_fence(_verdict()))
    assert out["verdict"] == "pass"
    assert out["per_axis_scores"]["legibility"] == 82


def test_parse_critic_output_rejects_missing_fence():
    with pytest.raises(ValueError, match="missing"):
        parse_critic_output(json.dumps(_verdict()))


def test_parse_critic_output_rejects_malformed_json():
    with pytest.raises(ValueError, match="parse failed"):
        parse_critic_output("```json\n{not valid json}\n```")


def test_parse_critic_output_rejects_pass_with_axis_below_80():
    """F3-style semantic check: pass requires every axis >= 80."""
    bad = _verdict(scores={
        "methodology_fidelity": 75,  # < 80
        "caption_alignment": 90,
        "legibility": 90,
        "figure_type_correctness": 90,
        "aesthetic_quality": 90,
    })
    bad["issues"] = []  # pass has no issues
    with pytest.raises(ValueError, match="pass but min axis score is 75"):
        parse_critic_output(_fence(bad))


def test_parse_critic_output_rejects_refine_with_empty_feedback():
    """refine requires concrete refinement_feedback."""
    bad = _verdict(verdict="refine", refinement_feedback="")
    bad["issues"] = [{"axis": "legibility", "detail": "labels garbled"}]
    with pytest.raises(ValueError, match="refine but refinement_feedback is empty"):
        parse_critic_output(_fence(bad))


def test_parse_critic_output_rejects_pass_with_feedback():
    """pass must not carry refinement_feedback."""
    bad = _verdict(verdict="pass", refinement_feedback="ignored", scores={
        "methodology_fidelity": 85, "caption_alignment": 85,
        "legibility": 85, "figure_type_correctness": 85, "aesthetic_quality": 85,
    })
    bad["issues"] = []
    with pytest.raises(ValueError, match="pass but refinement_feedback is non-empty"):
        parse_critic_output(_fence(bad))


def test_parse_critic_output_rejects_pass_with_issues():
    """pass and issues are mutually exclusive."""
    bad = _verdict(verdict="pass", scores={
        "methodology_fidelity": 85, "caption_alignment": 85,
        "legibility": 85, "figure_type_correctness": 85, "aesthetic_quality": 85,
    })
    bad["issues"] = [{"axis": "legibility", "detail": "leftover from refine"}]
    with pytest.raises(ValueError, match="pass but issues array is non-empty"):
        parse_critic_output(_fence(bad))


def test_parse_critic_output_rejects_non_pass_with_no_issues():
    """non-pass verdicts must name at least one issue."""
    bad = _verdict(verdict="refine", refinement_feedback="redraw the encoder block")
    bad["issues"] = []
    with pytest.raises(ValueError, match="issues array is empty"):
        parse_critic_output(_fence(bad))


def test_parse_critic_output_rejects_unknown_verdict_value():
    """Schema enum: verdict must be pass/refine/escalate/abort."""
    bad = _verdict(verdict="needs_work")
    with pytest.raises(ValueError, match="schema"):
        parse_critic_output(_fence(bad))


def test_parse_critic_output_accepts_escalate_with_issues_no_feedback():
    """escalate verdict: at least one issue; no refinement_feedback."""
    payload = _verdict(verdict="escalate")
    payload["issues"] = [{"axis": "legibility", "detail": "tier ceiling reached"}]
    out = parse_critic_output(_fence(payload))
    assert out["verdict"] == "escalate"


def test_parse_critic_output_accepts_abort_with_issues_no_feedback():
    payload = _verdict(verdict="abort")
    payload["issues"] = [{"axis": "methodology_fidelity", "detail": "methodology malformed"}]
    out = parse_critic_output(_fence(payload))
    assert out["verdict"] == "abort"


def test_parse_critic_output_logs_paperbanana_agreement():
    """agrees_with_paperbanana_verdict round-trips."""
    payload = _verdict(agrees=True)
    out = parse_critic_output(_fence(payload))
    assert out["agrees_with_paperbanana_verdict"] is True

    payload = _verdict(agrees=False)
    out = parse_critic_output(_fence(payload))
    assert out["agrees_with_paperbanana_verdict"] is False

    payload = _verdict(agrees=None)
    out = parse_critic_output(_fence(payload))
    assert out["agrees_with_paperbanana_verdict"] is None


# ---------------------------------------------------------------------------
# decide_next_action — state machine
# ---------------------------------------------------------------------------


def test_decide_next_action_pass_returns_accept():
    action = decide_next_action(_verdict(verdict="pass"), iteration_index=1, iteration_cap=4)
    assert action["action"] == "accept"


def test_decide_next_action_refine_below_cap_returns_refine_with_feedback():
    payload = _verdict(verdict="refine", refinement_feedback="add the missing axis label")
    payload["issues"] = [{"axis": "legibility", "detail": "axis label missing"}]
    action = decide_next_action(payload, iteration_index=2, iteration_cap=4)
    assert action["action"] == "refine"
    assert action["refinement_feedback"] == "add the missing axis label"


def test_decide_next_action_refine_at_cap_returns_abort():
    """Iteration cap reached + critic still wants to refine → operator must intervene."""
    payload = _verdict(verdict="refine", refinement_feedback="more iterations needed")
    payload["issues"] = [{"axis": "legibility", "detail": "still iterating"}]
    action = decide_next_action(payload, iteration_index=4, iteration_cap=4)
    assert action["action"] == "abort"
    assert "iteration_cap 4 reached" in action["reason"]


def test_decide_next_action_escalate_returns_escalate():
    payload = _verdict(verdict="escalate")
    payload["issues"] = [{"axis": "legibility", "detail": "tier ceiling"}]
    action = decide_next_action(payload, iteration_index=2, iteration_cap=4)
    assert action["action"] == "escalate"


def test_decide_next_action_abort_returns_abort():
    payload = _verdict(verdict="abort")
    payload["issues"] = [{"axis": "methodology_fidelity", "detail": "malformed source"}]
    action = decide_next_action(payload, iteration_index=1, iteration_cap=4)
    assert action["action"] == "abort"
    assert "abort verdict" in action["reason"]
