"""Marker grammar, parsing, and uniqueness checks.

Grammar: ^(IMAGE|SMARTART|BG):[a-z0-9_-]+$  (lowercase-only after the colon).
Per spec Section 3.1 — duplicate marker identifiers are a brief-authoring
error and must be surfaced to the user before enrichment proceeds.
"""
from __future__ import annotations

import re
from collections import Counter

from src.slide_facts import Marker, SlideFacts

MARKER_RE = re.compile(r"^(IMAGE|SMARTART|BG):([a-z0-9_-]+)$")


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
