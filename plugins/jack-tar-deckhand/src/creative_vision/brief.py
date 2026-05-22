"""Director's Brief agent dispatch helpers.

The Director's Brief is the only agent that touches the prompt. This module
prepares its input blob and parses its output back into a (ParsedVision, prompt)
tuple ready for downstream consumers (Prompt Reviewer, Visualizer). Issue #105.
"""
from __future__ import annotations

import json
import re


def build_brief_input(
    vision_prose: str,
    prior_parsed_vision: dict | None,
    accumulated_feedback: list[str],
    current_tier: str,
    brand_fidelity: str,
) -> str:
    """Compose the input blob to dispatch to the directors-brief agent.

    The agent reads a single text input and returns a JSON object. We marshal
    everything it needs (prose verbatim, prior parse if any, feedback, tier,
    brand_fidelity routing hint) into a sectioned blob.
    """
    lines = [
        "# Operator's vision prose (VERBATIM — preserve named entities)",
        vision_prose.strip(),
        "",
        f"# Current tier: {current_tier}",
        f"# Brand fidelity: {brand_fidelity}",
    ]
    if prior_parsed_vision is not None:
        lines.append("")
        lines.append("# Prior ParsedVision (from previous iteration):")
        lines.append("```json")
        lines.append(json.dumps(prior_parsed_vision, indent=2))
        lines.append("```")
    if accumulated_feedback:
        lines.append("")
        lines.append("# Accumulated feedback to address:")
        for item in accumulated_feedback:
            lines.append(f"- {item}")
    lines.append("")
    lines.append("Return a single fenced ```json``` block with keys `parsed_vision` and `prompt`.")
    return "\n".join(lines)


_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def parse_brief_output(agent_response: str) -> tuple[dict, str]:
    """Extract (parsed_vision, prompt) from the agent's response.

    Raises ValueError when the response doesn't contain a JSON fence with both keys.
    """
    m = _FENCE_RE.search(agent_response)
    if m is None:
        raise ValueError("directors-brief response did not contain a ```json``` fence")
    try:
        payload = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"directors-brief JSON parse failed: {e}") from e
    if "parsed_vision" not in payload or "prompt" not in payload:
        raise ValueError("directors-brief response missing parsed_vision or prompt key")
    return payload["parsed_vision"], payload["prompt"]
