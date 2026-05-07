"""Tests for cycle_state — pure-functional state machine for the SKILL.md loop."""
from __future__ import annotations

from pathlib import Path

from src.cycle_state import (
    CycleState,
    Phase,
    Decision,
    advance_after_review,
    coerce_verdict_for_coherence,
    should_escalate_to_cloud,
    is_terminal,
)
from src.image_bridge import BudgetCap, PrivacyTierGate, ImageGenerationRequest


def _req(tmp_path: Path) -> ImageGenerationRequest:
    return ImageGenerationRequest(
        slide_index=1, marker_id="IMAGE:foo", marker_kind="IMAGE",
        prompt="initial", output_path=tmp_path / "img.png",
        width=1024, height=576, brand_palette_hex=[],
    )


def test_initial_state_is_phase_a_attempt_1(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_A_OLLAMA, attempt=1)
    assert st.phase == Phase.PHASE_A_OLLAMA
    assert st.attempt == 1
    assert is_terminal(st) is False


def test_pass_verdict_in_phase_a_terminates_with_pass(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_A_OLLAMA, attempt=2)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "pass", "summary": "looks good"},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "terminate_pass"
    assert decision.tier_used == "ollama"


def test_refine_in_phase_a_attempt_under_max_advances_to_next_attempt(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_A_OLLAMA, attempt=1)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "refine", "summary": "garbled",
                          "issues": ["x"], "strengths": [], "composition_notes": {}},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "refine_and_retry"
    assert decision.next_state.phase == Phase.PHASE_A_OLLAMA
    assert decision.next_state.attempt == 2


def test_refine_in_phase_a_at_max_attempts_advances_to_phase_b_when_allowed(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_A_OLLAMA, attempt=3)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "refine", "summary": "x",
                          "issues": ["x"], "strengths": [], "composition_notes": {}},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "escalate_to_cloud"
    assert decision.next_state.phase == Phase.PHASE_B_CLOUD_FLASH
    assert decision.next_state.attempt == 1


def test_refine_at_phase_a_max_with_restricted_tier_terminates_halt_restricted(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_A_OLLAMA, attempt=3)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "refine", "summary": "x",
                          "issues": ["x"], "strengths": [], "composition_notes": {}},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="restricted"),
    )
    assert decision.kind == "terminate_halt_restricted"


def test_refine_at_phase_a_max_with_internal_unconfirmed_terminates_halt_pending(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_A_OLLAMA, attempt=3)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "refine", "summary": "x",
                          "issues": ["x"], "strengths": [], "composition_notes": {}},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="internal"),  # not yet confirmed
    )
    assert decision.kind == "terminate_pending_confirmation"


def test_pass_verdict_in_phase_b_advances_to_phase_c_pro_when_affordable(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_B_CLOUD_FLASH, attempt=1)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "pass", "summary": "good"},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "escalate_to_pro"
    assert decision.next_state.phase == Phase.PHASE_C_CLOUD_PRO
    assert decision.next_state.attempt == 1


def test_pass_verdict_in_phase_b_terminates_with_flash_when_pro_unaffordable(tmp_path):
    cap = BudgetCap(usd=0.20)
    cap.charge(kind="generation", provider="x", cost_usd=0.15)  # only 0.05 left
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_B_CLOUD_FLASH, attempt=2)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "pass", "summary": "good"},
        budget=cap,
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "terminate_pass"
    assert decision.tier_used == "nanobanana_flash"


def test_refine_in_phase_b_at_max_iterations_terminates_accepted_with_issues(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_B_CLOUD_FLASH, attempt=3)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "refine", "summary": "still bad",
                          "issues": ["x"], "strengths": [], "composition_notes": {}},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "terminate_accepted_with_issues"


def test_pass_verdict_in_phase_c_pro_terminates_with_pro(tmp_path):
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_C_CLOUD_PRO, attempt=1)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "pass", "summary": "great"},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "terminate_pass"
    assert decision.tier_used == "nanobanana_pro"


def test_should_escalate_to_cloud_false_under_restricted(tmp_path):
    assert should_escalate_to_cloud(
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="restricted"),
    ) is False


def test_should_escalate_to_cloud_false_when_budget_below_flash_cost(tmp_path):
    cap = BudgetCap(usd=0.05)  # below Flash cost ($0.067)
    assert should_escalate_to_cloud(
        budget=cap, privacy=PrivacyTierGate(tier="public"),
    ) is False


# ---------------------------------------------------------------------------
# Verdict-coherence guard (Run 6 Finding #21)
# ---------------------------------------------------------------------------
#
# The image-reviewer agent contract requires a final self-consistency check —
# a `refine` verdict must be paired with at least one substantive issue. The
# guard implemented here is defence-in-depth: if a reviewer slips through with
# `verdict: refine` and an empty `issues[]`, the cycle treats it as `pass`
# rather than burning budget on a pointless retry. Run 6 slide 8's Phase B
# Flash review is the surfaced motivating case — verdict=refine with the
# reviewer's own analysis confirming "all five labels verified against spec".


def test_coerce_verdict_pass_through_pass_verdict_unchanged():
    payload = {"verdict": "pass", "issues": [], "summary": "great"}
    coerced, was_coerced = coerce_verdict_for_coherence(payload)
    assert was_coerced is False
    assert coerced["verdict"] == "pass"


def test_coerce_verdict_refine_with_real_issues_passes_through():
    payload = {"verdict": "refine",
               "issues": ["text garbled in subtitle"],
               "summary": "needs another pass"}
    coerced, was_coerced = coerce_verdict_for_coherence(payload)
    assert was_coerced is False
    assert coerced["verdict"] == "refine"


def test_coerce_verdict_refine_with_empty_issues_flips_to_pass():
    payload = {"verdict": "refine", "issues": [], "summary": "looks good"}
    coerced, was_coerced = coerce_verdict_for_coherence(payload)
    assert was_coerced is True
    assert coerced["verdict"] == "pass"
    # Original payload unchanged — the helper returns a new dict
    assert payload["verdict"] == "refine"


def test_coerce_verdict_refine_with_missing_issues_key_flips_to_pass():
    payload = {"verdict": "refine", "summary": "label fidelity verified"}
    coerced, was_coerced = coerce_verdict_for_coherence(payload)
    assert was_coerced is True
    assert coerced["verdict"] == "pass"


def test_advance_after_review_applies_coherence_guard_in_phase_a(tmp_path):
    """If a reviewer returns refine with no issues, the cycle should not
    refine_and_retry — it should terminate_pass immediately. This is the
    runtime guard for Finding #21."""
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_A_OLLAMA, attempt=1)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "refine", "issues": [], "summary": "ok"},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "terminate_pass"
    assert decision.tier_used == "ollama"


def test_advance_after_review_applies_coherence_guard_in_phase_b(tmp_path):
    """Run 6 slide 8 case — Phase B Flash returned refine with all labels
    confirmed correct. The cycle should treat it as pass and (budget allowing)
    escalate to Pro just as it would for a clean Flash pass."""
    st = CycleState(request=_req(tmp_path), phase=Phase.PHASE_B_CLOUD_FLASH, attempt=1)
    decision = advance_after_review(
        state=st,
        verdict_payload={"verdict": "refine", "issues": [],
                         "summary": "logo strip verified against spec"},
        budget=BudgetCap(usd=1.0),
        privacy=PrivacyTierGate(tier="public"),
    )
    assert decision.kind == "escalate_to_pro"
