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


# ---------------------------------------------------------------------------
# should_fire_operator_gate — issue #113 AC3
#
# The gate has two cadences depending on slide strategy:
#   - non-creative_vision: standard F10 rule — fire only at free→cost
#     transition (Ollama → any cloud tier).
#   - creative_vision: F12 elevated cadence — fire on EVERY iteration,
#     including cost-to-cost and same-tier refinement.
# ---------------------------------------------------------------------------

from src.creative_vision.orchestrator import should_fire_operator_gate  # noqa: E402


# Default cost table used by these tests. Matches cascade.TIER_COSTS values
# semantically (ollama free, flash_1k / pro_1k both costly) but is local to
# the test so changes upstream don't accidentally tug at the gate semantics.
_TEST_TIER_COSTS = {
    "ollama": 0.0,
    "flash_1k": 0.067,
    "flash_2k": 0.101,
    "pro_1k": 0.134,
    "pro_4k": 0.240,
}


# --- creative_vision elevated cadence (F12) ---


def test_gate_fires_on_creative_vision_free_to_cost():
    """creative_vision + Ollama→Flash 1K (free→cost) — fires per both F10 and F12."""
    assert should_fire_operator_gate(
        strategy="creative_vision",
        current_tier="ollama",
        next_tier="flash_1k",
        tier_costs=_TEST_TIER_COSTS,
    ) is True


def test_gate_fires_on_creative_vision_cost_to_cost():
    """creative_vision + Flash 1K → Pro 1K — F12 fires the gate even though
    the cascade has already paid (cost→cost transition).

    AC3 acceptance criterion verbatim: 'dispatching imagegen-bridge with a
    creative_vision slide and a cost-to-cost transition (Flash 1K → Flash 1K
    iteration) MUST fire the operator gate, not auto-render.'
    """
    assert should_fire_operator_gate(
        strategy="creative_vision",
        current_tier="flash_1k",
        next_tier="pro_1k",
        tier_costs=_TEST_TIER_COSTS,
    ) is True


def test_gate_fires_on_creative_vision_same_tier_refinement():
    """creative_vision + Flash 1K → Flash 1K — F12 fires on same-tier refine.

    The image IS the slide; every iteration must be operator-visible.
    """
    assert should_fire_operator_gate(
        strategy="creative_vision",
        current_tier="flash_1k",
        next_tier="flash_1k",
        tier_costs=_TEST_TIER_COSTS,
    ) is True


def test_gate_fires_on_creative_vision_ollama_to_ollama():
    """creative_vision + Ollama→Ollama refinement — F12 fires; operator sees
    every draft, even at zero cost.

    Distinguishes F12 from F10: F10 only cares about money, F12 cares about
    operator-visibility because the image IS the deliverable.
    """
    assert should_fire_operator_gate(
        strategy="creative_vision",
        current_tier="ollama",
        next_tier="ollama",
        tier_costs=_TEST_TIER_COSTS,
    ) is True


# --- non-creative_vision standard F10 cadence ---


def test_gate_does_not_fire_on_composed_cost_to_cost():
    """composed strategy + Flash 1K → Pro 1K — gate does NOT fire.

    AC3 acceptance criterion verbatim: 'dispatching imagegen-bridge with a
    non-creative_vision slide and a cost-to-cost transition does NOT fire
    the gate (only free→cost fires).'
    """
    assert should_fire_operator_gate(
        strategy="composed",
        current_tier="flash_1k",
        next_tier="pro_1k",
        tier_costs=_TEST_TIER_COSTS,
    ) is False


def test_gate_fires_on_composed_free_to_cost():
    """composed + Ollama→Flash 1K — F10 fires (free→cost crossing)."""
    assert should_fire_operator_gate(
        strategy="composed",
        current_tier="ollama",
        next_tier="flash_1k",
        tier_costs=_TEST_TIER_COSTS,
    ) is True


def test_gate_does_not_fire_on_backdrop_same_cost_tier():
    """backdrop + Flash 1K → Flash 1K refinement — gate does not fire (same-tier
    refinement within cloud is the standard imagegen-bridge Step 7 review loop,
    not an operator-pause point)."""
    assert should_fire_operator_gate(
        strategy="backdrop",
        current_tier="flash_1k",
        next_tier="flash_1k",
        tier_costs=_TEST_TIER_COSTS,
    ) is False


def test_gate_does_not_fire_on_full_render_ollama_to_ollama():
    """full_render + Ollama → Ollama — no crossing, no gate."""
    assert should_fire_operator_gate(
        strategy="full_render",
        current_tier="ollama",
        next_tier="ollama",
        tier_costs=_TEST_TIER_COSTS,
    ) is False


def test_gate_does_not_fire_when_next_tier_is_free():
    """composed + Flash 1K → Ollama (downgrade / regression) — gate does
    not fire because the transition is not a free→cost crossing.

    Edge case: a cost-to-free transition is unusual but the rule is "free
    to cost", not "any transition involving free", so it must return False.
    """
    assert should_fire_operator_gate(
        strategy="composed",
        current_tier="flash_1k",
        next_tier="ollama",
        tier_costs=_TEST_TIER_COSTS,
    ) is False


# --- defaults + error contract ---


def test_gate_uses_cascade_tier_costs_by_default():
    """When tier_costs is omitted, the helper reads from cascade.TIER_COSTS.

    Pins the post-AC6 reconciled pro_2k=$0.134 value: a creative_vision
    cost-to-cost transition through pro_2k fires regardless of the actual
    numerical cost.
    """
    assert should_fire_operator_gate(
        strategy="creative_vision",
        current_tier="pro_1k",
        next_tier="pro_2k",
    ) is True


def test_gate_raises_keyerror_for_unknown_tier():
    """Unknown tiers MUST raise rather than silently default to 'free'.

    The cascade ladder is well-typed; if the orchestrator ever produces a
    tier the cost table doesn't know about, that's a hard bug, not a
    "default to don't fire the gate" situation.
    """
    with pytest.raises(KeyError):
        should_fire_operator_gate(
            strategy="creative_vision",
            current_tier="flash_99k",  # unknown
            next_tier="ollama",
            tier_costs=_TEST_TIER_COSTS,
        )


# --- defensive edge cases on strategy argument ---


@pytest.mark.parametrize("bad_strategy", [None, "", "creativ_vision", "CREATIVE_VISION"])
def test_gate_unknown_or_misspelled_strategy_falls_through_to_f10(bad_strategy):
    """A strategy value that isn't the exact literal "creative_vision" gets
    the F10 default cadence (free→cost only). The strategy-map schema
    rejects misspelled / case-wrong strategy values at save time, so this
    code path is only reachable when the helper is called outside the
    normal flow — but the defensive behaviour is to fall through to F10
    rather than silently break gate firing or apply F12.

    Cost-to-cost transition with unknown strategy → False (F10 doesn't fire).
    Free→cost transition with unknown strategy → True (F10 fires; budget
    protection is the conservative default).
    """
    assert should_fire_operator_gate(
        strategy=bad_strategy,
        current_tier="flash_1k",
        next_tier="pro_1k",
        tier_costs=_TEST_TIER_COSTS,
    ) is False
    assert should_fire_operator_gate(
        strategy=bad_strategy,
        current_tier="ollama",
        next_tier="flash_1k",
        tier_costs=_TEST_TIER_COSTS,
    ) is True


def test_gate_strategy_match_is_case_sensitive():
    """``"creative_vision"`` matches F12 cadence. ``"Creative_Vision"`` does
    not. This is intentional — the schema enum is lowercase only and
    forgiving casing here would mask schema violations elsewhere.

    The cost-to-cost transition is the discriminator: F12 fires it, F10
    does not.
    """
    assert should_fire_operator_gate(
        strategy="creative_vision",
        current_tier="flash_1k",
        next_tier="pro_1k",
        tier_costs=_TEST_TIER_COSTS,
    ) is True
    assert should_fire_operator_gate(
        strategy="Creative_Vision",
        current_tier="flash_1k",
        next_tier="pro_1k",
        tier_costs=_TEST_TIER_COSTS,
    ) is False
