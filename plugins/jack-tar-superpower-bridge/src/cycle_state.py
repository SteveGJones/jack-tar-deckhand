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


@dataclass
class EscalationRecommendation:
    """Result of verifying whether a reviewer's verdict warrants a second opinion.

    Run 8 Finding #28: Haiku's image-reviewer caught the Condor's gross text
    corruption ("Gysmnogaps alfanianus") but missed the Thylacine's
    fine-grained mid-word corruption ("cynogechalus" / "Tasnia") — verdict
    was ``pass`` with confidence 0.92, even with EXACT-labels supplied.

    The escalation path is NOT automatic dual-dispatch (which doubles cost on
    every text-bearing review). It is *verification-then-confirmation*:

    1. After Haiku review, the orchestrator calls
       :func:`verify_review_evidences_comparison` with the verdict and the
       expected-text list passed at dispatch.
    2. The helper returns this dataclass: ``should_escalate`` is True when
       the verdict claims a pass but the reviewer's analysis fields do NOT
       quote any of the expected labels back. Quoting is the only evidence
       we have that Haiku actually performed the comparison; absence of
       quoting is the smell that triggers escalation.
    3. The orchestrator surfaces ``reason`` to the user and asks whether to
       dispatch a second reviewer at a higher tier (Sonnet/Opus).
    4. Only after explicit user confirmation does the second dispatch run.

    This preserves cost discipline (low-confidence reviews get scrutiny;
    high-confidence pass-with-evidence reviews don't) and respects operator
    agency (no silent budget-doubling on every text-bearing marker).
    """

    should_escalate: bool
    reason: str | None = None
    matched_labels: tuple[str, ...] = ()
    expected_labels: tuple[str, ...] = ()


def _collect_review_analysis_text(verdict_payload: dict[str, Any]) -> str:
    """Concatenate the reviewer's analysis fields into a single haystack string.

    The image-reviewer agent contract surfaces its analysis in three fields:
    ``strengths`` (list of strings), ``issues`` (list of strings), and
    ``summary`` (string), plus optional ``composition_notes`` (dict with
    ``subject_placement``, ``scale_hierarchy``, ``text_rendering`` strings).
    This helper flattens them all into one string for substring searches —
    used by :func:`verify_review_evidences_comparison` to test whether
    expected labels appear anywhere in the reviewer's prose.
    """
    parts: list[str] = []
    for key in ("strengths", "issues"):
        val = verdict_payload.get(key) or []
        if isinstance(val, list):
            parts.extend(str(item) for item in val)
        else:
            parts.append(str(val))
    summary = verdict_payload.get("summary")
    if summary:
        parts.append(str(summary))
    notes = verdict_payload.get("composition_notes")
    if isinstance(notes, dict):
        for key in ("subject_placement", "scale_hierarchy", "text_rendering"):
            val = notes.get(key)
            if val:
                parts.append(str(val))
    return "\n".join(parts)


def verify_review_evidences_comparison(
    verdict_payload: dict[str, Any],
    expected_text_content: list[str] | tuple[str, ...] | None,
) -> EscalationRecommendation:
    """Decide whether a reviewer's pass verdict warrants escalation (Finding #28).

    Run 8 evidence: Haiku reviewers have a character-level reliability gap.
    With identical patch surface and identical EXACT-labels structure, Haiku
    caught the Condor's gross corruption but missed the Thylacine's
    fine-grained mid-word corruption. The reviewer's prose claimed
    correctness without quoting back any of the expected labels — a smell
    we can detect deterministically.

    The verification heuristic:

    - If ``expected_text_content`` is empty or None — no escalation. (The
      marker is atmospheric; text-content fidelity is not load-bearing.)
    - If ``verdict != "pass"`` — no escalation. (A refine verdict already
      surfaces concrete issues the cycle can act on.)
    - If at least one expected label appears verbatim in the reviewer's
      prose — no escalation. (The reviewer has evidenced the comparison.)
    - Otherwise — escalation recommended. (The reviewer claimed a pass
      without quoting evidence; trust is unverified.)

    The match is case-insensitive substring containment to tolerate small
    rendering variations in the reviewer's prose. Labels with fewer than
    3 alphanumeric characters are skipped to avoid false matches on common
    short tokens (e.g. ``"of"`` would match almost any prose).

    The orchestrator should surface :attr:`EscalationRecommendation.reason`
    to the user and ask whether to dispatch a second reviewer. Escalation
    must NOT be automatic (operator-cost discipline + Run 8 user-feedback
    requirement: "verification escalation, and confirmation of escalation,
    not just going from Haiku to Opus").
    """
    if not expected_text_content:
        return EscalationRecommendation(should_escalate=False)

    if verdict_payload.get("verdict") != "pass":
        return EscalationRecommendation(should_escalate=False)

    expected_tuple = tuple(str(item) for item in expected_text_content)
    haystack = _collect_review_analysis_text(verdict_payload).lower()

    matched: list[str] = []
    significant: list[str] = []
    for label in expected_tuple:
        # Skip tokens too short to be reliably distinctive in prose.
        alnum = "".join(ch for ch in label if ch.isalnum())
        if len(alnum) < 3:
            continue
        significant.append(label)
        if label.lower() in haystack:
            matched.append(label)

    if not significant:
        # All expected labels were too short to verify; pass through without
        # escalation rather than over-trigger.
        return EscalationRecommendation(should_escalate=False)

    if matched:
        return EscalationRecommendation(
            should_escalate=False,
            matched_labels=tuple(matched),
            expected_labels=expected_tuple,
        )

    return EscalationRecommendation(
        should_escalate=True,
        reason=(
            f"Reviewer returned verdict=pass but did not quote any of "
            f"{len(significant)} expected labels in its analysis. "
            f"Haiku may have confabulated correctness without performing "
            f"the comparison. Recommend dispatching a second reviewer at "
            f"Sonnet/Opus tier for verification — operator confirmation "
            f"required (Run 8 Finding #28)."
        ),
        matched_labels=(),
        expected_labels=expected_tuple,
    )


def coerce_verdict_for_coherence(
    verdict_payload: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    """Defence-in-depth guard for Run 6 Finding #21 — verdict-text contradictions.

    The image-reviewer agent contract requires a final self-consistency check
    (a ``refine`` verdict must be paired with at least one substantive issue).
    The Run 6 motivating case slipped through anyway: a Phase B Flash review
    returned ``verdict: refine`` while its own ``issues`` array, ``strengths``,
    and ``summary`` confirmed the image rendered all expected text correctly.
    The cycle would have refined-and-retried unnecessarily, burning ~$0.067
    per affected marker on a no-op.

    The guard rule (deliberately conservative):

    - ``verdict == "refine"`` AND ``issues`` is empty (or missing) → coerce
      to ``pass``. The reviewer has no concrete defect to act on, so a retry
      cannot improve the outcome.

    The original payload is not mutated — a shallow copy is returned alongside
    a boolean indicating whether coercion happened (so callers can log the
    coercion in the cost ledger / report).

    More aggressive heuristics (e.g. detecting "verify against source"-style
    hedges in non-empty issues lists) are deliberately out of scope here —
    those judgments belong in the agent's self-check, not in defence-in-depth.
    """
    if verdict_payload.get("verdict") != "refine":
        return verdict_payload, False
    issues = verdict_payload.get("issues")
    if issues:
        return verdict_payload, False
    coerced = dict(verdict_payload)
    coerced["verdict"] = "pass"
    return coerced, True


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
    caveat #6).

    The verdict-coherence guard (Finding #21) is applied first, so callers
    who consume ``advance_after_review`` directly cannot accidentally bypass
    it. Callers that need to log the coercion should call
    ``coerce_verdict_for_coherence`` separately and pass the returned payload
    in.
    """
    verdict_payload, _ = coerce_verdict_for_coherence(verdict_payload)
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
