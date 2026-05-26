"""Deck-level creative anchors — loader, validator, Brief integration helpers.

Issue #113 AC4. When a deck has multiple ``creative_vision`` slides sharing
a recurring character / prop / location / style anchor, capture them in
``<deck_dir>/creative_anchors.json``. The Director's Brief reads the anchors
when authoring each slide's prompt and weaves them in by name so all renders
agree on the canonical description.

The anchors file is **optional** — most decks don't need it. When absent,
``load_anchors`` returns None and the Brief skips the inlining step.

Public surface:

- :func:`load_anchors` — read the deck's anchors file, validate, return dict
  or None.
- :func:`validate_anchors` — schema-validate an in-memory anchors dict.
- :func:`lookup_anchor` — case-sensitive name lookup, returns the anchor
  dict or None.
- :func:`anchors_for_slide` — filter anchors to those eligible for a given
  slide based on ``appears_in_slides`` (deck-wide anchors are always
  eligible).
- :func:`format_anchors_for_brief` — render a list of anchors as the Brief
  input blob's ``# Recurring entities from creative anchors`` section.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from jsonschema import ValidationError, validate

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "schemas" / "creative_anchors.schema.json"
)
_ANCHORS_FILENAME = "creative_anchors.json"


def _load_schema() -> dict:
    with open(_SCHEMA_PATH) as f:
        return json.load(f)


def anchors_path(deck_dir: str) -> str:
    """Return the canonical path to the deck's creative anchors file."""
    return os.path.join(deck_dir, _ANCHORS_FILENAME)


def load_anchors(deck_dir: str) -> dict | None:
    """Load + validate the deck's creative anchors file.

    Args:
        deck_dir: Path to the deck working directory.

    Returns:
        The validated anchors dict, or ``None`` when ``creative_anchors.json``
        is not present in ``deck_dir``. Absence is the common case (most decks
        don't need anchors) — the caller treats None as "no anchors, skip
        anchor-related Brief decoration".

    Raises:
        ValueError: When the file exists but fails JSON parsing or schema
            validation. Failing loud here means the operator gets a clear
            error pointing at the malformed anchors file rather than the
            Brief silently dropping anchor references.
    """
    path = anchors_path(deck_dir)
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            anchors = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"creative_anchors.json failed to parse: {e.msg} at line {e.lineno}"
        ) from e
    validate_anchors(anchors)
    return anchors


def validate_anchors(anchors: dict) -> None:
    """Validate an in-memory anchors dict against the schema.

    Raises:
        ValueError: When validation fails. The message names the failing
            field's JSON-pointer-style path so the operator can locate it.
    """
    try:
        validate(instance=anchors, schema=_load_schema())
    except ValidationError as e:
        path = "/" + "/".join(str(p) for p in e.absolute_path)
        raise ValueError(
            f"creative_anchors validation failed at {path}: {e.message}"
        ) from e


def lookup_anchor(anchors: dict, name: str) -> dict | None:
    """Return the anchor dict for ``name``, or None when not found.

    Case-sensitive — the Brief's prompt references must match the anchor
    name verbatim. Returning None on miss (rather than raising) lets the
    caller decide whether a missing anchor is an error or just a slide that
    happened not to reference any.
    """
    for anchor in anchors.get("anchors", []):
        if anchor["name"] == name:
            return anchor
    return None


def anchors_for_slide(anchors: dict, slide_number: int) -> list[dict]:
    """Return anchors eligible for the given slide.

    An anchor is eligible iff:

    - It declares no ``appears_in_slides`` field, OR
    - The slide number appears in its ``appears_in_slides`` list.

    Deck-wide anchors (no ``appears_in_slides``) are always returned so the
    Brief can include them in every slide's prompt. Slide-specific anchors
    are filtered.

    Order matches the anchors file (operator-controlled — useful for
    deterministic prompt assembly).
    """
    result = []
    for anchor in anchors.get("anchors", []):
        slides = anchor.get("appears_in_slides")
        if not slides or slide_number in slides:
            result.append(anchor)
    return result


def format_anchors_for_brief(
    anchors_subset: list[dict],
    *,
    deck_brief: str | None = None,
) -> str:
    """Render anchors as the input-blob section the Director's Brief consumes.

    Returns a single sectioned text block ready to inline into
    ``brief.build_brief_input``. The format is human-readable and stable so
    the Brief can be trained / validated against it.

    Args:
        anchors_subset: List of anchor dicts (typically from
            :func:`anchors_for_slide`).
        deck_brief: Optional deck-wide creative-direction one-liner. When
            provided, included as the first paragraph.

    Returns:
        Empty string when ``anchors_subset`` is empty AND ``deck_brief`` is
        None — the caller can append the result unconditionally without
        leaving an orphan section header.
    """
    if not anchors_subset and not deck_brief:
        return ""

    lines: list[str] = ["# Recurring entities from creative anchors"]

    if deck_brief:
        lines.append("")
        lines.append("Deck-wide creative direction:")
        lines.append(f"  {deck_brief.strip()}")

    grouped: dict[str, list[dict]] = {}
    for anchor in anchors_subset:
        grouped.setdefault(anchor["kind"], []).append(anchor)

    for kind in ("character", "prop", "location", "style_anchor"):
        if kind not in grouped:
            continue
        lines.append("")
        lines.append(f"## {kind}s" if not kind.endswith("anchor") else f"## {kind}s")
        for anchor in grouped[kind]:
            line = f"- **{anchor['name']}** — {anchor['description'].strip()}"
            lines.append(line)
            negative = anchor.get("negative_traits") or []
            if negative:
                lines.append(
                    f"    Must NOT have: {', '.join(negative)}"
                )

    lines.append("")
    lines.append(
        "When the prompt references any of these names, use the description "
        "above verbatim so all slides agree on the entity."
    )

    return "\n".join(lines)
