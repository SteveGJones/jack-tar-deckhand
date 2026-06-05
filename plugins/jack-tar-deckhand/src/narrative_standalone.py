"""Narrative standalone — generate a SlideOutline from a TalkBrief without a StyleGuide.

This module enables the narrative-architect → speaker-notes-writer path without
first running brand-manager or slide-stylist. Speakers who only need the generators
(objective 4) can call generate_outline_from_brief_only(deck_dir) and get a valid
SlideOutline using tone-keyed default styles.
"""

from __future__ import annotations

from typing import Any

from src.deckcontext import read_contract
from src.content_validation import build_outline_from_brief

# Tone-keyed default style profiles synthesized when style-guide.json is absent.
# These mirror the three primary audience profiles; other tones fall back to "narrative".
DEFAULT_STYLES: dict[str, dict[str, Any]] = {
    "technical": {"pace": "dense", "slide_cadence_seconds": 90},
    "executive": {"pace": "spacious", "slide_cadence_seconds": 120},
    "professional": {"pace": "spacious", "slide_cadence_seconds": 120},
    "narrative": {"pace": "moderate", "slide_cadence_seconds": 75},
    "conversational": {"pace": "moderate", "slide_cadence_seconds": 75},
    "inspirational": {"pace": "moderate", "slide_cadence_seconds": 75},
    "provocative": {"pace": "moderate", "slide_cadence_seconds": 75},
    "storytelling": {"pace": "moderate", "slide_cadence_seconds": 75},
}


def generate_outline_from_brief_only(deck_dir: str) -> dict[str, Any]:
    """Build a SlideOutline from a TalkBrief alone, synthesizing a style if needed.

    Reads talk-brief.json and (optionally) style-guide.json from deck_dir.
    If style-guide.json is absent, a tone-keyed default is synthesized.

    Args:
        deck_dir: Path to the deck working directory containing talk-brief.json.

    Returns:
        A dict conforming to the SlideOutline schema.

    Raises:
        FileNotFoundError: If talk-brief.json is not present in deck_dir.
    """
    brief = read_contract(deck_dir, "talk-brief")
    if brief is None:
        raise FileNotFoundError(f"talk-brief.json not found in {deck_dir}")

    style_guide = read_contract(deck_dir, "style-guide")
    if style_guide is None:
        tone = brief.get("tone", "narrative")
        style_guide = DEFAULT_STYLES.get(tone, DEFAULT_STYLES["narrative"]).copy()
        style_guide["_synthesized"] = True

    return build_outline_from_brief(brief, style_guide)
