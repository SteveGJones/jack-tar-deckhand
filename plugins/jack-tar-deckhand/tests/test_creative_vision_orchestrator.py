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
