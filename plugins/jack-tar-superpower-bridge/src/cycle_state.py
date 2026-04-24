"""Pure-functional cycle state primitives for the SKILL.md-driven loop.

The /enrich-deck SKILL.md drives the iteration step-by-step (because the
cycle's reviewer and prompt-refiner are Claude subagents, which only the
harness can dispatch). Between agent dispatches, the SKILL.md calls these
primitives to compute "what should I do next given the current state and
the agent's verdict?"

`generate_with_review_cycle` (image_bridge.py) remains the canonical
reference implementation for tests — it's exercised via injected
callables. Production runs go through this state machine instead.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.image_bridge import BudgetCap, PrivacyTierGate, ImageGenerationRequest


# Pricing constants — synchronised with image_bridge cycle
FLASH_GEN_COST_USD = 0.067
PRO_GEN_COST_USD = 0.134
TYPICAL_REVIEW_COST_USD = 0.005

MAX_PHASE_A_ATTEMPTS = 3
MAX_PHASE_B_ATTEMPTS = 3


class Phase(str, Enum):
    PHASE_A_OLLAMA = "phase_a_ollama"
    PHASE_B_CLOUD_FLASH = "phase_b_cloud_flash"
    PHASE_C_CLOUD_PRO = "phase_c_cloud_pro"
    TERMINAL = "terminal"


@dataclass
class CycleState:
    request: ImageGenerationRequest
    phase: Phase
    attempt: int                                 # 1-based within current phase


@dataclass
class Decision:
    """What the SKILL.md should do next.

    kind values:
      - refine_and_retry          → SKILL.md dispatches prompt-engineer in refine mode,
                                     then loops back to image generation in next_state
      - escalate_to_cloud         → SKILL.md begins Phase B Flash generation in next_state
      - escalate_to_pro           → SKILL.md does single Phase C Pro generation in next_state
      - terminate_pass            → SKILL.md keeps the current image; tier_used reports which tier
      - terminate_accepted_with_issues
      - terminate_halt_restricted
      - terminate_pending_confirmation
      - terminate_halt_budget
    """
    kind: str
    next_state: CycleState | None = None
    tier_used: str | None = None
    reason: str = ""


def is_terminal(state: CycleState) -> bool:
    return state.phase == Phase.TERMINAL


def should_escalate_to_cloud(*, budget: BudgetCap, privacy: PrivacyTierGate) -> bool:
    """Return True if the cycle CAN move from Phase A to Phase B."""
    if not privacy.cloud_allowed():
        return False
    if privacy.requires_confirmation_before_cloud():
        return False
    if not budget.can_afford(FLASH_GEN_COST_USD + TYPICAL_REVIEW_COST_USD):
        return False
    return True


def _phase_a_decision(
    state: CycleState, verdict: str, budget: BudgetCap, privacy: PrivacyTierGate,
) -> Decision:
    if verdict == "pass":
        return Decision(kind="terminate_pass", tier_used="ollama")
    # refine: more attempts left → loop in Phase A
    if state.attempt < MAX_PHASE_A_ATTEMPTS:
        return Decision(
            kind="refine_and_retry",
            next_state=CycleState(request=state.request, phase=Phase.PHASE_A_OLLAMA,
                                    attempt=state.attempt + 1),
        )
    # refine and at max attempts: try to escalate
    if not privacy.cloud_allowed():
        return Decision(kind="terminate_halt_restricted",
                         tier_used="ollama",
                         reason="restricted tier blocks cloud escalation")
    if privacy.requires_confirmation_before_cloud():
        return Decision(kind="terminate_pending_confirmation",
                         tier_used="ollama",
                         reason="internal tier requires user confirmation before cloud")
    if not budget.can_afford(FLASH_GEN_COST_USD + TYPICAL_REVIEW_COST_USD):
        return Decision(kind="terminate_halt_budget",
                         tier_used="ollama",
                         reason="budget cannot cover Phase B Flash gen + review")
    return Decision(
        kind="escalate_to_cloud",
        next_state=CycleState(request=state.request,
                                phase=Phase.PHASE_B_CLOUD_FLASH, attempt=1),
    )


def _phase_b_decision(
    state: CycleState, verdict: str, budget: BudgetCap, privacy: PrivacyTierGate,
) -> Decision:
    if verdict == "pass":
        # Optional Phase C only when budget allows the Pro generation + a review
        if budget.can_afford(PRO_GEN_COST_USD + TYPICAL_REVIEW_COST_USD):
            return Decision(
                kind="escalate_to_pro",
                next_state=CycleState(request=state.request,
                                        phase=Phase.PHASE_C_CLOUD_PRO, attempt=1),
            )
        return Decision(kind="terminate_pass", tier_used="nanobanana_flash")
    # refine
    if state.attempt < MAX_PHASE_B_ATTEMPTS:
        if not budget.can_afford(FLASH_GEN_COST_USD + TYPICAL_REVIEW_COST_USD):
            return Decision(kind="terminate_halt_budget",
                             tier_used="nanobanana_flash",
                             reason="budget exhausted before next Flash iteration")
        return Decision(
            kind="refine_and_retry",
            next_state=CycleState(request=state.request,
                                    phase=Phase.PHASE_B_CLOUD_FLASH,
                                    attempt=state.attempt + 1),
        )
    return Decision(kind="terminate_accepted_with_issues",
                     tier_used="nanobanana_flash",
                     reason="3 Flash iterations all returned refine")


def _phase_c_decision(verdict: str) -> Decision:
    if verdict == "pass":
        return Decision(kind="terminate_pass", tier_used="nanobanana_pro")
    return Decision(kind="terminate_accepted_with_issues",
                     tier_used="nanobanana_pro",
                     reason="Pro single-shot returned refine; flag for speaker")


def advance_after_review(
    *,
    state: CycleState,
    verdict_payload: dict[str, Any],
    budget: BudgetCap,
    privacy: PrivacyTierGate,
) -> Decision:
    """Compute the next decision after the SKILL.md has dispatched the reviewer
    agent and received its JSON envelope. Pure function — does not charge
    budget or mutate state. The SKILL.md is responsible for charging budget
    BEFORE calling advance_after_review (review charges are unconditional —
    caveat #6)."""
    verdict = verdict_payload.get("verdict")
    if verdict not in ("pass", "refine"):
        raise ValueError(f"verdict {verdict!r} not in (pass, refine)")
    if state.phase == Phase.PHASE_A_OLLAMA:
        return _phase_a_decision(state, verdict, budget, privacy)
    if state.phase == Phase.PHASE_B_CLOUD_FLASH:
        return _phase_b_decision(state, verdict, budget, privacy)
    if state.phase == Phase.PHASE_C_CLOUD_PRO:
        return _phase_c_decision(verdict)
    raise ValueError(f"cannot advance from terminal phase {state.phase}")
