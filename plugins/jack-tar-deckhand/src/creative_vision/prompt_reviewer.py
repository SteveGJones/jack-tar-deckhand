"""Prompt Reviewer agent dispatch helpers.

Prepares the input blob for the prompt-reviewer agent and parses its output
into a (verdict, issues) tuple. Issue #105.
"""
from __future__ import annotations

import json
import re


def build_reviewer_input(original_prose: str, proposed_prompt: str, parsed_vision: dict) -> str:
    return "\n".join([
        "# Operator's original vision prose (VERBATIM):",
        original_prose.strip(),
        "",
        "# Proposed render prompt (from Director's Brief):",
        proposed_prompt.strip(),
        "",
        "# Parsed intermediate:",
        "```json",
        json.dumps(parsed_vision, indent=2),
        "```",
        "",
        "Return a single fenced ```json``` block with keys `verdict` (pass|refine) and `issues` (string array).",
    ])


_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def parse_reviewer_output(agent_response: str) -> tuple[str, list[str]]:
    m = _FENCE_RE.search(agent_response)
    if m is None:
        raise ValueError("prompt-reviewer response missing ```json``` fence")
    payload = json.loads(m.group(1))
    verdict = payload.get("verdict")
    if verdict not in ("pass", "refine"):
        raise ValueError(f"prompt-reviewer verdict invalid: {verdict!r}")
    issues = payload.get("issues", [])
    return verdict, issues
