"""Tests for the creative_vision orchestrator state machine."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.orchestrator import (  # noqa: E402
    TEXT_ITERATION_CAP,
    TextLoopState,
    advance_text_loop,
)


def test_text_loop_pass_immediately():
    """When the first prompt review is a pass, the loop terminates with approved_prompt."""
    state = TextLoopState(iterations=[])
    state = advance_text_loop(state, reviewer_verdict="pass", reviewer_issues=[], current_prompt="p")
    assert state.terminal is True
    assert state.forced_pass is False
    assert state.approved_prompt == "p"


def test_text_loop_refine_then_pass():
    """When a refinement is rejected, advance records it and continues. Then pass."""
    state = TextLoopState(iterations=[])
    state = advance_text_loop(state, reviewer_verdict="refine", reviewer_issues=["x"], current_prompt="p1")
    assert state.terminal is False
    state = advance_text_loop(state, reviewer_verdict="pass", reviewer_issues=[], current_prompt="p2")
    assert state.terminal is True
    assert state.approved_prompt == "p2"


def test_text_loop_forces_pass_at_cap():
    """After TEXT_ITERATION_CAP refine verdicts, loop terminates with forced_pass=True."""
    state = TextLoopState(iterations=[])
    for i in range(TEXT_ITERATION_CAP):
        state = advance_text_loop(state, reviewer_verdict="refine", reviewer_issues=[f"x{i}"], current_prompt=f"p{i}")
    assert state.terminal is True
    assert state.forced_pass is True
    assert state.approved_prompt == f"p{TEXT_ITERATION_CAP - 1}"


def test_text_loop_iteration_history():
    """Verify iteration history is preserved and structured correctly."""
    state = TextLoopState(iterations=[])
    state = advance_text_loop(state, reviewer_verdict="refine", reviewer_issues=["issue1", "issue2"], current_prompt="prompt1")
    assert len(state.iterations) == 1
    assert state.iterations[0]["prompt_draft"] == "prompt1"
    assert state.iterations[0]["reviewer_verdict"] == "refine"
    assert state.iterations[0]["reviewer_feedback"] == "issue1; issue2"

    state = advance_text_loop(state, reviewer_verdict="pass", reviewer_issues=[], current_prompt="prompt2")
    assert len(state.iterations) == 2
    assert state.iterations[1]["reviewer_feedback"] == ""


def test_text_loop_empty_issues():
    """Empty reviewer_issues renders as empty feedback string."""
    state = TextLoopState(iterations=[])
    state = advance_text_loop(state, reviewer_verdict="pass", reviewer_issues=[], current_prompt="p")
    assert state.iterations[0]["reviewer_feedback"] == ""


from src.creative_vision.orchestrator import (  # noqa: E402
    NextAction,
    decide_next_action,
)


def _verdict(verdict="pass", plateau=False):
    return {
        "verdict": verdict,
        "per_axis_scores": {"entity_fidelity": 80, "spatial_fidelity": 80, "style_fidelity": 80, "quality": 80, "composition": 80},
        "issues": [],
        "gap_location": "unknown",
        "recommended_action": "x",
        "tier": "flash_1k",
        "iteration_index": 1,
        "plateau_signal": plateau,
    }


def test_decide_next_action_pass_returns_accept():
    action = decide_next_action(
        critic_verdict=_verdict("pass"),
        current_tier="flash_1k",
        ladder=["ollama", "flash_1k", "flash_2k"],
        remaining_budget_usd=0.5,
        per_tier_iteration_count=1,
        per_tier_cap=3,
        allowed_ceiling="flash_2k",
    )
    assert action.kind == "accept"


def test_decide_next_action_refine_below_cap_returns_refine():
    action = decide_next_action(
        critic_verdict=_verdict("refine_at_tier"),
        current_tier="flash_1k",
        ladder=["ollama", "flash_1k", "flash_2k"],
        remaining_budget_usd=0.5,
        per_tier_iteration_count=1,
        per_tier_cap=3,
        allowed_ceiling="flash_2k",
    )
    assert action.kind == "refine_at_tier"


def test_decide_next_action_refine_at_cap_returns_escalate():
    action = decide_next_action(
        critic_verdict=_verdict("refine_at_tier"),
        current_tier="flash_1k",
        ladder=["ollama", "flash_1k", "flash_2k"],
        remaining_budget_usd=0.5,
        per_tier_iteration_count=3,
        per_tier_cap=3,
        allowed_ceiling="flash_2k",
    )
    assert action.kind == "escalate_tier"
    assert action.next_tier == "flash_2k"


def test_decide_next_action_escalate_when_budget_insufficient_returns_abort():
    action = decide_next_action(
        critic_verdict=_verdict("escalate_tier"),
        current_tier="flash_2k",
        ladder=["ollama", "flash_1k", "flash_2k", "flash_4k"],
        remaining_budget_usd=0.05,  # below flash_4k cost
        per_tier_iteration_count=3,
        per_tier_cap=3,
        allowed_ceiling="flash_4k",
    )
    assert action.kind == "abort"
    assert action.abort_reason == "budget_exhausted"


def test_decide_next_action_escalate_at_top_of_ladder_returns_accept_with_warning():
    action = decide_next_action(
        critic_verdict=_verdict("refine_at_tier"),
        current_tier="pro_4k",
        ladder=["ollama", "flash_1k", "flash_2k", "flash_4k", "pro_1k", "pro_2k", "pro_4k"],
        remaining_budget_usd=10.0,
        per_tier_iteration_count=1,
        per_tier_cap=1,
        allowed_ceiling="pro_4k",
    )
    assert action.kind == "accept"
    assert action.forced is True  # accepted because we're at ceiling and out of iterations


def test_decide_next_action_critic_abort_returns_abort():
    action = decide_next_action(
        critic_verdict=_verdict("abort"),
        current_tier="flash_1k",
        ladder=["ollama", "flash_1k"],
        remaining_budget_usd=0.5,
        per_tier_iteration_count=1,
        per_tier_cap=3,
        allowed_ceiling=None,
    )
    assert action.kind == "abort"
