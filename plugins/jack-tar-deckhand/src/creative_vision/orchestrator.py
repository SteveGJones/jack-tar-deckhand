"""Creative-vision orchestrator state machine.

Pure logic — knows nothing about agent dispatch. The SKILL.md drives the agent
calls and invokes these helpers to advance state between dispatches. Issue #105.
"""
from __future__ import annotations

from dataclasses import dataclass, field

TEXT_ITERATION_CAP = 3


@dataclass
class TextLoopState:
    """State of the text-side refinement loop (Brief↔Prompt Reviewer).

    Attributes:
        iterations: List of iteration records, each with prompt_draft, reviewer_verdict, reviewer_feedback.
        terminal: True when the loop has reached a decision (pass or forced cap).
        forced_pass: True if terminal=True and we hit the iteration cap (forced), False if reviewer approved.
        approved_prompt: The final prompt to use; None until terminal=True.
    """
    iterations: list[dict] = field(default_factory=list)
    terminal: bool = False
    forced_pass: bool = False
    approved_prompt: str | None = None


def advance_text_loop(
    state: TextLoopState,
    *,
    reviewer_verdict: str,
    reviewer_issues: list[str],
    current_prompt: str,
) -> TextLoopState:
    """Advance the text-side state given the latest Prompt Reviewer verdict.

    The Prompt Reviewer evaluates the current prompt against the Brief and returns
    a verdict (pass / refine) plus optional feedback issues.

    - pass: Approve the prompt; loop terminates with approved_prompt set.
    - refine: Reject and continue; SKILL.md will invoke Prompt Engineer to refine.

    After TEXT_ITERATION_CAP refine verdicts, the loop forces a pass (approved_prompt
    is set from the last prompt_draft) and sets forced_pass=True to signal the outcome.

    Returns a NEW state object; state should be treated as immutable by the caller.
    """
    iterations = state.iterations + [
        {
            "prompt_draft": current_prompt,
            "reviewer_verdict": reviewer_verdict,
            "reviewer_feedback": "; ".join(reviewer_issues) if reviewer_issues else "",
        }
    ]

    if reviewer_verdict == "pass":
        return TextLoopState(
            iterations=iterations,
            terminal=True,
            forced_pass=False,
            approved_prompt=current_prompt,
        )

    if len(iterations) >= TEXT_ITERATION_CAP:
        return TextLoopState(
            iterations=iterations,
            terminal=True,
            forced_pass=True,
            approved_prompt=current_prompt,
        )

    return TextLoopState(
        iterations=iterations,
        terminal=False,
        forced_pass=False,
        approved_prompt=None,
    )


from src.creative_vision.cascade import can_afford, next_tier  # noqa: E402


@dataclass
class NextAction:
    """Encodes the decision made by the image-side state machine.

    Attributes:
        kind: 'refine_at_tier' | 'escalate_tier' | 'accept' | 'abort'
        next_tier: The tier to escalate to (when kind == 'escalate_tier'), or None.
        abort_reason: Reason for abort (when kind == 'abort'), or None. E.g. 'budget_exhausted', 'critic_abort'.
        forced: True when we accepted a non-passing image because we hit a hard ceiling (iteration cap + top of ladder).
    """
    kind: str
    next_tier: str | None = None
    abort_reason: str | None = None
    forced: bool = False


def decide_next_action(
    *,
    critic_verdict: dict,
    current_tier: str,
    ladder: list[str],
    remaining_budget_usd: float,
    per_tier_iteration_count: int,
    per_tier_cap: int,
    allowed_ceiling: str | None,
) -> NextAction:
    """Decide what to do next based on the Director's Critic verdict + cascade state.

    This is the image-side state machine. Given a Critic verdict plus the current
    cascade state (tier, ladder, budget, iterations), it returns the next action:

    - 'accept': The image is good enough; stop iterating.
    - 'refine_at_tier': Iterate again at the current tier (prompt refinement + regenerate).
    - 'escalate_tier': Escalate to the next tier in the ladder and regenerate.
    - 'abort': Give up (budget exhausted, critic says abort, or forced accept at ceiling).

    Args:
        critic_verdict: Dict from the Director's Critic, with 'verdict' key ('pass' | 'refine_at_tier' | 'escalate_tier' | 'abort').
        current_tier: The tier we're currently at (e.g. 'flash_1k').
        ladder: The full tier ladder (e.g. ['ollama', 'flash_1k', 'flash_2k', ...]).
        remaining_budget_usd: How much budget is left.
        per_tier_iteration_count: Number of iterations already done at the current tier.
        per_tier_cap: Max iterations allowed per tier (e.g. 3).
        allowed_ceiling: Max tier we're allowed to escalate to (e.g. 'flash_2k'). None means no cap.

    Returns:
        A NextAction with kind set and relevant fields filled in.
    """
    verdict = critic_verdict["verdict"]

    if verdict == "pass":
        return NextAction(kind="accept")

    if verdict == "abort":
        return NextAction(kind="abort", abort_reason="critic_abort")

    # refine_at_tier OR escalate_tier — check whether we can stay at this tier
    cap_reached = per_tier_iteration_count >= per_tier_cap

    if verdict == "refine_at_tier" and not cap_reached:
        return NextAction(kind="refine_at_tier")

    # We need to escalate (either Critic said so OR cap reached on refine)
    candidate = next_tier(current_tier, ladder, allowed_ceiling=allowed_ceiling)
    if candidate is None:
        # At the ceiling — forced accept
        return NextAction(kind="accept", forced=True)
    if not can_afford(remaining_budget_usd, candidate):
        return NextAction(kind="abort", abort_reason="budget_exhausted")
    return NextAction(kind="escalate_tier", next_tier=candidate)
