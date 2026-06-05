"""Content validation utilities — timing arithmetic and reference integrity.

This module handles ONLY machine-checkable validation:
- Schema conformance (SlideOutline, SpeakerNotes)
- Timing arithmetic (do note durations sum to talk duration?)
- Reference integrity (layout templates, slide numbers)

All narrative reasoning — arc selection, slide sequencing, headline quality,
visual direction prose — is Claude's contextual reasoning in the SKILL.md,
NOT codified rules here.
"""

import json
import os

import jsonschema

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), 'schemas')

TIMING_TOLERANCE_PCT = 20  # Allow 20% deviation from target duration


def validate_outline_schema(outline):
    """Validate a SlideOutline dict against the JSON schema. Returns list of error messages."""
    schema_path = os.path.join(SCHEMA_DIR, 'slide_outline.schema.json')
    with open(schema_path) as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)
    return [e.message for e in validator.iter_errors(outline)]


def validate_notes_schema(notes):
    """Validate a SpeakerNotes dict against the JSON schema. Returns list of error messages."""
    schema_path = os.path.join(SCHEMA_DIR, 'speaker_notes.schema.json')
    with open(schema_path) as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)
    return [e.message for e in validator.iter_errors(notes)]


def check_timing_total(notes, duration_minutes):
    """Check that note durations sum to approximately the talk duration.

    Returns list of issue strings. Tolerates TIMING_TOLERANCE_PCT deviation.
    """
    issues = []
    total_seconds = 0
    has_timing = False
    for note in notes.get('notes', []):
        est = note.get('estimated_seconds')
        if est is not None:
            total_seconds += est
            has_timing = True

    if not has_timing:
        return []

    target_seconds = duration_minutes * 60
    deviation_pct = abs(total_seconds - target_seconds) / target_seconds * 100

    if total_seconds > target_seconds * (1 + TIMING_TOLERANCE_PCT / 100):
        issues.append(
            f'Notes total {total_seconds}s ({total_seconds/60:.1f}min) exceeds '
            f'talk duration {duration_minutes}min by {deviation_pct:.0f}%'
        )
    elif total_seconds < target_seconds * (1 - TIMING_TOLERANCE_PCT / 100):
        issues.append(
            f'Notes total {total_seconds}s ({total_seconds/60:.1f}min) under '
            f'talk duration {duration_minutes}min by {deviation_pct:.0f}%'
        )

    return issues


def check_notes_slide_references(notes, outline):
    """Check that every note references a slide that exists in the outline."""
    issues = []
    outline_slides = {s['slide_number'] for s in outline.get('slides', [])}
    for note in notes.get('notes', []):
        sn = note.get('slide_number')
        if sn is not None and sn not in outline_slides:
            issues.append(f'Note references slide {sn} which does not exist in outline')
    return issues


def check_outline_layout_references(outline, style_guide):
    """Check that every layout_template in the outline exists in the StyleGuide."""
    issues = []
    templates = style_guide.get('layout', {}).get('templates', {})
    for slide in outline.get('slides', []):
        lt = slide.get('layout_template')
        if lt and lt not in templates:
            issues.append(
                f'Slide {slide["slide_number"]} references layout template '
                f'"{lt}" which does not exist in StyleGuide'
            )
    return issues


# ---------------------------------------------------------------------------
# Standalone shims — used by src.narrative_standalone (objective 4)
# These enable outline + notes generation without brand-manager or slide-stylist.
# ---------------------------------------------------------------------------

def build_outline_from_brief(brief: dict, style_guide: dict) -> dict:
    """Build a minimal but schema-valid SlideOutline from a TalkBrief.

    Produces a title slide, one content slide per key_takeaway, and a closing
    slide. The result passes validate_outline_schema().

    Args:
        brief: A TalkBrief dict (talk-brief.json).
        style_guide: A StyleGuide dict or synthesized style defaults.

    Returns:
        A SlideOutline-compatible dict.
    """
    topic = brief.get("topic", "Untitled Talk")
    takeaways = brief.get("key_takeaways", [])
    duration = brief.get("duration_minutes", 30)
    tone = brief.get("tone", "narrative")

    slides = [
        {
            "slide_number": 1,
            "slide_type": "title",
            "headline": topic,
            "body_points": [],
            "narrative_beat": "opening",
        }
    ]

    for i, takeaway in enumerate(takeaways, start=2):
        slides.append(
            {
                "slide_number": i,
                "slide_type": "content",
                "headline": takeaway,
                "body_points": [],
                "narrative_beat": "body",
            }
        )

    slides.append(
        {
            "slide_number": len(slides) + 1,
            "slide_type": "closing",
            "headline": "Thank you",
            "body_points": [],
            "narrative_beat": "closing",
        }
    )

    return {
        "narrative_arc": f"{tone}-standalone",
        "estimated_duration_minutes": duration,
        "total_slides": len(slides),
        "slides": slides,
        "metadata": {"source": "standalone"},
    }


def generate_speaker_notes_from_outline(outline: dict, tone: str = "narrative") -> dict:
    """Generate minimal speaker notes for every slide in an outline.

    Produces one note per slide conforming to speaker_notes.schema.json:
    top-level key is 'notes', each item requires 'slide_number' and 'text',
    with 'estimated_seconds' derived from the tone's default cadence and a
    structured 'cues' list.

    Args:
        outline: A SlideOutline dict.
        tone: Tone string used to derive per-slide cadence.

    Returns:
        A dict conforming to speaker_notes.schema.json with a 'notes' key.
    """
    cadence = {"technical": 90, "executive": 120, "professional": 120}.get(tone, 75)
    all_slides = outline.get("slides", [])
    last_index = len(all_slides) - 1
    notes_items = [
        {
            "slide_number": s["slide_number"],
            "text": f"Speak to: {s.get('headline', 'slide')}",
            "estimated_seconds": cadence,
            "cues": [
                {
                    "type": "transition",
                    "text": "closing" if i == last_index else "next",
                }
            ],
        }
        for i, s in enumerate(all_slides)
    ]
    return {"notes": notes_items}
