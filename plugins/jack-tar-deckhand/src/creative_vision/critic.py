"""Director's Critic agent dispatch helpers. Issue #105."""
from __future__ import annotations

import json
import re
from pathlib import Path

from jsonschema import ValidationError, validate

_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "directors_critic_verdict.schema.json"


def _load_schema():
    with open(_SCHEMA_PATH) as f:
        return json.load(f)


def build_critic_input(
    original_prose: str,
    image_path: str,
    parsed_vision: dict,
    prior_scores_history: list[dict],
    tier: str,
    iteration_index: int,
) -> str:
    return "\n".join([
        "# Operator's original vision prose (VERBATIM):",
        original_prose.strip(),
        "",
        f"# Image to evaluate: {image_path}",
        f"# Current tier: {tier}",
        f"# Iteration index: {iteration_index}",
        "",
        "# Parsed intermediate:",
        "```json",
        json.dumps(parsed_vision, indent=2),
        "```",
        "",
        "# Score history (chronological, most recent last):",
        "```json",
        json.dumps(prior_scores_history, indent=2),
        "```",
        "",
        "Return a single fenced ```json``` block conforming to the DirectorsCriticVerdict schema.",
    ])


_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def parse_critic_output(agent_response: str) -> dict:
    m = _FENCE_RE.search(agent_response)
    if m is None:
        raise ValueError("directors-critic response missing ```json``` fence")
    try:
        payload = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"directors-critic JSON parse failed: {e}") from e
    try:
        validate(instance=payload, schema=_load_schema())
    except ValidationError as e:
        raise ValueError(f"directors-critic verdict failed schema: {e.message}") from e
    return payload
