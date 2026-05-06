"""Marker grammar, parsing, and uniqueness checks.

Grammar: ^(IMAGE|SMARTART-FROM-LIST|SMARTART|BG):[a-z0-9_-]+$  (lowercase
identifier after the colon). Kind names are uppercase / hyphenated; the
identifier accepts lowercase letters, digits, hyphens, and underscores.

Marker kinds:

- ``BG``  — full-bleed atmospheric background (the slide's background image
  is replaced).
- ``IMAGE``  — hero illustration in a placeholder rectangle (the rectangle
  is replaced with the AI-generated image).
- ``SMARTART``  — full content-zone replacement: a placeholder rectangle is
  replaced by an editable PowerPoint SmartArt graphic. The graphic's content
  comes from a separate spec passed to ``apply_enrichment``.
- ``SMARTART-FROM-LIST``  *(Contract 2, Finding #9)* — the marker IS a real
  text shape with bullet content. The bridge extracts the bullet items, builds
  a SmartArt spec from them, renders + brand-colours it, and replaces the
  list shape with the SmartArt graphic at the same position. Title and
  supporting prose on the slide are untouched. Graceful degradation: if
  enrichment is skipped, the bullet list remains on the slide.

Per spec Section 3.1 — duplicate marker identifiers are a brief-authoring
error and must be surfaced to the user before enrichment proceeds.
"""
from __future__ import annotations

import re
from collections import Counter

from src.slide_facts import Marker, SlideFacts

# SMARTART-FROM-LIST appears before SMARTART so the regex engine matches the
# more-specific (longer) kind first when both could prefix-match.
MARKER_RE = re.compile(r"^(IMAGE|SMARTART-FROM-LIST|SMARTART|BG):([a-z0-9_-]+)$")


def parse_marker(name: str) -> tuple[str, str] | None:
    """Return (kind, identifier) if `name` matches the grammar, else None."""
    if not isinstance(name, str):
        return None
    m = MARKER_RE.match(name)
    if m is None:
        return None
    return m.group(1), m.group(2)


def is_marker_name(name: str) -> bool:
    return parse_marker(name) is not None


def find_duplicate_marker_ids(slides: list[SlideFacts]) -> list[str]:
    """Return marker ids (as `KIND:identifier` strings) that appear on more than one slide
    OR more than once on a single slide."""
    counter: Counter[str] = Counter()
    for slide in slides:
        for marker in slide.markers:
            counter[f"{marker.kind}:{marker.identifier}"] += 1
    return sorted(mid for mid, count in counter.items() if count > 1)
