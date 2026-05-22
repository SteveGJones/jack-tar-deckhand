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
