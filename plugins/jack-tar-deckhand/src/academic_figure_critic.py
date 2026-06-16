"""Figure Critic agent dispatch helpers — academic_figure Claude-critic path.

Issue #113 follow-up, Path B. When a slide is marked ``strategy: academic_figure``
AND ``academic_figure_critic: "claude"``, jack-tar's imagegen-bridge runs the
following loop INSTEAD of paperbanana's internal VLM-critic loop:

    1. paperbanana renders ONE image (--iterations 1)
    2. dispatch ``figure-critic`` (Sonnet) with this module's helpers
    3. operator gate (F12 cadence — every iteration)
    4. on refine: paperbanana --continue-run --feedback "<refinement_feedback>"
    5. loop until pass / abort / iteration_cap

This module owns the contract between the orchestrator and the agent dispatch:
input-blob builder + response parser + schema validator + per-axis sanity
checks. The schema validator catches malformed agent output at the boundary
(parallel to the F1 schema-validation fix in ``creative_vision/brief.py``).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from jsonschema import ValidationError, validate

_SCHEMA_PATH = (
    Path(__file__).resolve().parent / "schemas" / "figure_critic_verdict.schema.json"
)


def _load_schema() -> dict:
    with open(_SCHEMA_PATH) as f:
        return json.load(f)


_VALID_FIGURE_TYPES = {
    "architecture_diagram",
    "equation",
    "plot",
    "table",
    "algorithm_pseudocode",
    "flowchart",
    "other",
}


def build_critic_input(
    methodology_text: str,
    caption: str,
    figure_type: str,
    image_path: str,
    prior_scores_history: list[dict],
    iteration_index: int,
    iteration_cap: int,
    *,
    paperbanana_side_by_side_verdict: dict | None = None,
) -> str:
    """Compose the input blob for the figure-critic agent dispatch.

    Args:
        methodology_text: Operator's verbatim methodology / source text the
            figure should depict. NOT paraphrased.
        caption: One-line communicative intent ("Figure 3: System architecture").
        figure_type: One of the canonical types — see :data:`_VALID_FIGURE_TYPES`.
            Tunes which scoring axes weigh most.
        image_path: Path to the rendered image the agent will read.
        prior_scores_history: Chronological per-iteration score dicts. Empty
            on iteration 1.
        iteration_index: 1-based. Echoed back in the verdict.
        iteration_cap: Max iterations the operator authorised. The agent uses
            this to decide whether `refine` is still allowed or `abort` is the
            honest call.
        paperbanana_side_by_side_verdict: Optional. When the operator is
            running the equivalence-testing phase, the paperbanana VLM's own
            verdict for the same image is included so the agent can record
            whether its decision agrees. Does NOT influence the agent's
            verdict; logged only.

    Raises:
        ValueError: When ``figure_type`` is not a canonical value. The agent
            contract requires a known type; ambiguous input would yield
            unpredictable scoring.
    """
    if figure_type not in _VALID_FIGURE_TYPES:
        raise ValueError(
            f"figure_type={figure_type!r} is not valid. "
            f"Allowed: {sorted(_VALID_FIGURE_TYPES)}"
        )

    sections = [
        "# Methodology source (VERBATIM):",
        methodology_text.strip(),
        "",
        f"# Caption: {caption.strip()}",
        f"# Figure type: {figure_type}",
        "",
        f"# Image to evaluate: {image_path}",
        f"# Iteration index: {iteration_index}",
        f"# Iteration cap: {iteration_cap}",
        "",
        "# Prior score history (chronological, most recent last):",
        "```json",
        json.dumps(prior_scores_history, indent=2),
        "```",
    ]

    if paperbanana_side_by_side_verdict is not None:
        sections += [
            "",
            "# Paperbanana side-by-side verdict (equivalence-testing only):",
            "# (Do NOT defer to this. Your verdict is what the orchestrator uses.)",
            "```json",
            json.dumps(paperbanana_side_by_side_verdict, indent=2),
            "```",
        ]

    sections += [
        "",
        "Return a single fenced ```json``` block conforming to the FigureCriticVerdict schema.",
    ]
    return "\n".join(sections)


_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def parse_critic_output(agent_response: str) -> dict:
    """Extract + validate the figure-critic verdict from the agent's response.

    Validates against ``figure_critic_verdict.schema.json`` and applies semantic
    checks that the schema can't express:

    - ``verdict == "pass"`` requires every per-axis score >= 80.
    - ``verdict != "pass"`` requires at least one issue.
    - ``verdict == "refine"`` requires non-empty ``refinement_feedback``.
    - ``verdict != "refine"`` requires empty ``refinement_feedback``.

    Raises:
        ValueError: When the response is missing the fence, malformed JSON,
            fails schema validation, or violates any of the semantic checks.
    """
    m = _FENCE_RE.search(agent_response)
    if m is None:
        raise ValueError("figure-critic response missing ```json``` fence")
    try:
        payload = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"figure-critic JSON parse failed: {e}") from e

    try:
        validate(instance=payload, schema=_load_schema())
    except ValidationError as e:
        path = "/" + "/".join(str(p) for p in e.absolute_path)
        raise ValueError(
            f"figure-critic verdict failed schema at {path}: {e.message}"
        ) from e

    _validate_verdict_score_coherence(payload)
    _validate_verdict_issues_coherence(payload)
    _validate_refinement_feedback_coherence(payload)

    return payload


def _validate_verdict_score_coherence(payload: dict) -> None:
    """Enforce: verdict='pass' requires every axis >= 80.

    Mirrors the F3 fix proposed for directors-critic — the schema validator
    can't express cross-field invariants, so this semantic check pairs with
    schema validation.
    """
    verdict = payload["verdict"]
    scores = payload["per_axis_scores"]
    min_score = min(scores.values())
    if verdict == "pass" and min_score < 80:
        raise ValueError(
            f"figure-critic verdict=pass but min axis score is {min_score} < 80; "
            f"the schema requires every axis >= 80 for a pass verdict."
        )


def _validate_verdict_issues_coherence(payload: dict) -> None:
    """Enforce: verdict != 'pass' must have at least one issue; pass must have none."""
    verdict = payload["verdict"]
    issues = payload["issues"]
    if verdict == "pass" and issues:
        raise ValueError(
            "figure-critic verdict=pass but issues array is non-empty; "
            "pass requires no issues."
        )
    if verdict != "pass" and not issues:
        raise ValueError(
            f"figure-critic verdict={verdict} but issues array is empty; "
            f"non-pass verdicts require at least one issue naming the failing axis."
        )


def _validate_refinement_feedback_coherence(payload: dict) -> None:
    """Enforce: refinement_feedback non-empty iff verdict=='refine'."""
    verdict = payload["verdict"]
    feedback = payload["refinement_feedback"]
    if verdict == "refine" and not feedback.strip():
        raise ValueError(
            "figure-critic verdict=refine but refinement_feedback is empty; "
            "refine requires concrete imperatives passed verbatim to paperbanana."
        )
    if verdict != "refine" and feedback.strip():
        raise ValueError(
            f"figure-critic verdict={verdict} but refinement_feedback is non-empty; "
            f"refinement_feedback is only meaningful when verdict=='refine'."
        )


def decide_next_action(
    verdict_payload: dict,
    *,
    iteration_index: int,
    iteration_cap: int,
) -> dict:
    """Return the next action for the orchestrator based on the critic verdict.

    This is the small state machine that translates a critic verdict into
    "what should the orchestrator do next?" — equivalent to
    ``creative_vision.orchestrator.decide_next_action`` but for the academic-
    figure cascade.

    Returns:
        Dict with keys:
        - ``action``: one of ``"accept"``, ``"refine"``, ``"escalate"``, ``"abort"``
        - ``reason``: short string explaining the choice
        - ``refinement_feedback``: present iff action == "refine"; the string
          to pass to ``paperbanana generate --continue-run --feedback``
    """
    verdict = verdict_payload["verdict"]

    if verdict == "pass":
        return {"action": "accept", "reason": "all axes >= 80 (pass verdict)"}

    if verdict == "abort":
        return {"action": "abort", "reason": "critic returned abort verdict"}

    if verdict == "escalate":
        return {
            "action": "escalate",
            "reason": "critic returned escalate (gap not addressable by prompt refinement)",
        }

    # verdict == "refine"
    if iteration_index >= iteration_cap:
        return {
            "action": "abort",
            "reason": (
                f"iteration_cap {iteration_cap} reached without convergence; "
                f"critic still wanted to refine. Operator must intervene."
            ),
        }
    return {
        "action": "refine",
        "reason": "critic returned refine; iteration cap not reached",
        "refinement_feedback": verdict_payload["refinement_feedback"],
    }
