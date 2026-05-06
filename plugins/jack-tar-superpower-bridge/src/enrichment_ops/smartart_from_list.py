"""Op4 — SMARTART-FROM-LIST: extract bullet-list content from a marker shape.

Contract 2 (Finding #9 from Run 3 dogfood, 2026-04-26): /pptx authors a real
text shape with bullets at the slide's natural content position. The shape's
``objectName`` carries the ``SMARTART-FROM-LIST:slug`` marker. The bridge
reads the bullets, builds a SmartArt spec, renders + brand-colours the
graphic (Contract 1), and replaces the list shape with the SmartArt at the
SAME position. Title and supporting prose on the slide are untouched.

This module owns the *extraction* half of the contract — turning a list
shape's text frame into ``items: list[str]``. The substitution half is
already handled by the existing ``inject_smartart_into_file`` op (which
finds shape-by-objectName and replaces it with the rendered SmartArt at
the same coordinates) — Contract 2 reuses that substitution unchanged.

Graceful degradation: if enrichment is skipped or fails, the source list
shape remains visible on the slide. The author's intent isn't lost.

Layout selection (Runs 4/5/6 Finding #13, Run 7 Finding #22):
``select_layout_for_bullets`` routes by the longest item — process1 (≤24),
list1 (≤30), vList2 (≤60). Caps match the msft-smartart catalog's
``max_label_chars`` exactly (the engine's load-bearing truth); the
parametric consistency test in tests/test_layout_caps_match_catalog.py
asserts the two systems agree.

Bullets exceeding the vList2 cap raise ``BulletsTooLongError`` rather
than silent truncation. Run 7 evidence: silent ellipsis-truncation
mangles operator content (mid-word "ent..."). Better to fail loudly so
the operator can either rewrite within 60 chars or pick a different
layout.
"""
from __future__ import annotations


class SmartArtFromListExtractError(LookupError):
    """Raised when the marker shape can't be found OR has no list content."""


class BulletsTooLongError(ValueError):
    """Raised when bullets exceed the largest available layout cap.

    Run 7 (Finding #22) replaced silent truncation with a hard fail.
    The bridge previously clipped bullets >60 chars at 57 + "..."; the
    mid-word ellipsis looked like garbage and silently mangled operator
    content. Hard-failing forces the operator to either rewrite within
    60 chars or pick a different layout — their content stays intact.

    The exception message names the offending bullets verbatim so the
    operator can locate and shorten them in the source build.js.
    """


# Per-layout bullet caps — MUST match the msft-smartart catalog's
# ``max_label_chars`` field for each layout. The parametric consistency
# test in tests/test_layout_caps_match_catalog.py asserts agreement.
#
# Caps derived from manual gate validation in PowerPoint Mac:
#   process1 = 24 (chevron flow — narrowest box; canonical SmartArt cap)
#   list1    = 30 (vertical bullet list — wider single-line cells)
#   vList2   = 60 (vertical list with accent — Run 7 spike validated
#                  prose-length bullets render cleanly via INF-height
#                  + auto-shrink at sub-page and banner scales)
LAYOUT_BULLET_CAPS: dict[str, int] = {
    "process1": 24,
    "list1": 30,
    "vList2": 60,
}


def select_layout_for_bullets(
    items: list[str],
) -> tuple[str, list[str], list[str]]:
    """Route a SMARTART-FROM-LIST bullet list to the smallest layout that
    fits all items.

    Returns ``(layout_id, items_to_render, warnings)``:

    - ``layout_id`` is the chosen layout
    - ``items_to_render`` is the items list (always identical to ``items``;
      kept in the return signature for stable orchestrator code)
    - ``warnings`` is a list of human-readable strings the orchestrator can
      surface to the Speaker (rationale for routing away from the default)

    Routing rules:

    - All items ≤24 chars → ``process1`` (preserves the default chevron flow)
    - 25–30 chars → ``list1`` (escapes process1 into a roomier vertical list)
    - 31–60 chars → ``vList2`` (accent-decorated vertical list with prose room)
    - >60 chars → ``BulletsTooLongError`` (operator must rewrite or pick a
      different layout; silent truncation is the worst of both worlds)

    Empty input is a defensive case — callers should never pass it, but the
    helper returns ``("process1", [], [])`` instead of crashing so apply-time
    errors surface the missing bullets at the extraction step instead.
    """
    if not items:
        return "process1", [], []

    max_len = max(len(item) for item in items)
    p1_cap = LAYOUT_BULLET_CAPS["process1"]
    l1_cap = LAYOUT_BULLET_CAPS["list1"]
    v2_cap = LAYOUT_BULLET_CAPS["vList2"]

    if max_len <= p1_cap:
        return "process1", list(items), []

    if max_len <= l1_cap:
        return (
            "list1",
            list(items),
            [f"layout=list1 chosen because longest bullet ({max_len} chars) "
             f"exceeds process1 cap ({p1_cap})"],
        )

    if max_len <= v2_cap:
        return (
            "vList2",
            list(items),
            [f"layout=vList2 chosen because longest bullet ({max_len} chars) "
             f"exceeds list1 cap ({l1_cap})"],
        )

    # Hard fail — bullets exceed the largest layout cap. Run 7 Finding #22
    # replaced silent truncation with this error so the operator's intent
    # stays intact. They can either rewrite the offending bullets within
    # 60 chars or use a different layout (e.g. an authored bulleted list
    # via /pptx native, which doesn't have the SmartArt char limit).
    offenders = [item for item in items if len(item) > v2_cap]
    offender_lines = "\n".join(f"  - ({len(item)} chars) {item!r}" for item in offenders)
    raise BulletsTooLongError(
        f"{len(offenders)} of {len(items)} SMARTART-FROM-LIST bullets exceed "
        f"the vList2 cap ({v2_cap} chars). Either rewrite the offending "
        f"bullets within {v2_cap} chars, or replace the SMARTART-FROM-LIST "
        f"marker with a native bulleted text shape (no char limit).\n"
        f"Offending bullets:\n{offender_lines}"
    )


def extract_list_items_from_marker_shape(
    *,
    prs,
    slide_index_1based: int,
    marker_name: str,
) -> list[str]:
    """Read a SMARTART-FROM-LIST marker shape's text frame and return its
    paragraphs as a list of item strings.

    The marker shape must:
    - exist on the given slide (1-based index)
    - have ``shape.name == marker_name``
    - contain at least one non-empty paragraph

    Empty paragraphs are skipped (a common artefact when authors press Enter
    after the last bullet). Whitespace at each paragraph's edges is stripped.

    Raises ``SmartArtFromListExtractError`` if:
    - the slide index is out of range
    - no shape with the given marker_name is found
    - the shape has no text frame
    - the text frame has zero non-empty paragraphs (the marker is present
      but the author left the list empty)
    """
    if slide_index_1based < 1 or slide_index_1based > len(prs.slides):
        raise SmartArtFromListExtractError(
            f"slide_index_1based {slide_index_1based} out of range "
            f"(deck has {len(prs.slides)} slides)"
        )

    slide = prs.slides[slide_index_1based - 1]
    target_shape = None
    for shape in slide.shapes:
        if shape.name == marker_name:
            target_shape = shape
            break
    if target_shape is None:
        raise SmartArtFromListExtractError(
            f"shape {marker_name!r} not found on slide {slide_index_1based}"
        )

    if not target_shape.has_text_frame:
        raise SmartArtFromListExtractError(
            f"shape {marker_name!r} has no text frame; SMARTART-FROM-LIST "
            f"requires the marker to be a text shape with bullet content"
        )

    items: list[str] = []
    for paragraph in target_shape.text_frame.paragraphs:
        # Concatenate runs in the paragraph; strip whitespace
        text = "".join(run.text for run in paragraph.runs).strip()
        if text:
            items.append(text)

    if not items:
        raise SmartArtFromListExtractError(
            f"shape {marker_name!r} has no non-empty paragraphs; "
            f"SMARTART-FROM-LIST requires at least one bullet item"
        )

    return items
