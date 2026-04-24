"""SmartArt bridge — marker → spec → carrier .pptx.

Caveat #4 decision (do not relitigate without spec amendment):
the bridge does its OWN bullet → spec parsing rather than reusing the
deckhand `smartart-extractor` skill. Reasons:

  - The extractor consumes DeckContext + SlideOutline; the bridge has
    raw OOXML-extracted slide text instead.
  - The extractor handles pptx_native, mermaid, and vega; the bridge
    only ever uses pptx_native.
  - A bridge-side parser is ~50 lines and locks the data shapes that
    Spike 2 validated end-to-end.

If you change this decision, update spec Section 3.3 (SmartArt) and
this module's contract tests in test_smartart_bridge.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.msft_smartart_loader import load_msft_smartart_api
from src.slide_facts import SlideFacts


class SmartArtBridgeError(RuntimeError):
    """Raised on any spec-build or render error from the SmartArt bridge."""


# Layout selection heuristics. Marker identifier keywords are the primary signal,
# bullet count + indentation are the secondary signals. Catalog-aware extension
# (multi-candidate ranking) is deliberately out of v1 scope — see Caveat #4.
_KEYWORD_TO_LAYOUT = {
    "cycle": ("cycle", "cycle2"),
    "org": ("org_chart", "orgChart1"),
    "hierarchy": ("org_chart", "orgChart1"),
    "tree": ("org_chart", "orgChart1"),
    "venn": ("relationship", "venn1"),
    "pyramid": ("pyramid", "pyramid2"),
    "list": ("list", "list1"),
    "matrix": ("relationship", "matrix2"),
    "funnel": ("relationship", "funnel1"),
    "target": ("relationship", "target3"),
    "flow": ("flowchart", "process1"),
    "process": ("flowchart", "process1"),
    "step": ("flowchart", "process1"),
}

# Layout capacity caps (subset of catalog data; extended in v2).
_CAPACITY = {
    "process1": (2, 9),
    "cycle2": (3, 8),
    "orgChart1": (2, 25),
    "list1": (2, 9),
    "venn1": (2, 5),
    "pyramid2": (3, 5),
    "matrix2": (4, 4),
    "funnel1": (3, 6),
    "target3": (3, 5),
}

# Per-layout maximum label character counts. Mirrors the msft-smartart catalog
# `max_label_chars` field. The bridge truncates labels to this cap as a graceful
# degradation when the slide body contains prose rather than crisp bullets.
_MAX_LABEL_CHARS = {
    "process1": 24,
    "cycle2": 24,
    "list1": 24,
    "venn1": 24,
    "pyramid2": 24,
    "matrix2": 24,
    "funnel1": 24,
    "target3": 24,
    "orgChart1": 32,
}

# Delimiters used to split a label-style line like
#   "SMARTART: three pillars — Planning  |  Memory  |  Tool Use"
# into individual items. Order matters: try strongest signal first.
_LABEL_DELIMITERS = ("|", "→", "->", ";")


def _split_label_line(line: str) -> list[str] | None:
    """If `line` is a marker-style descriptor line containing a delimiter,
    return the delimiter-split items. Otherwise return None.

    Example input:
      "SMARTART: three pillars — Planning  |  Memory  |  Tool Use  (radial)"
    Output:
      ["Planning", "Memory", "Tool Use"]
    """
    # Strip leading "SMARTART:"/"BG:"/"IMAGE:" prefix and any em-dash preamble.
    body = line
    for prefix in ("SMARTART:", "BG:", "IMAGE:"):
        if body.startswith(prefix):
            body = body[len(prefix):].strip()
            break
    # If the line contains an em-dash, the post-dash portion is usually the item list.
    for em in (" — ", " - "):
        if em in body:
            body = body.split(em, 1)[1].strip()
            break
    for delim in _LABEL_DELIMITERS:
        if delim in body:
            parts = [p.strip() for p in body.split(delim) if p.strip()]
            # Drop trailing parenthetical commentary on the last item, e.g. "Tool Use (radial)"
            cleaned = []
            for p in parts:
                if "(" in p:
                    p = p.split("(", 1)[0].strip()
                if p:
                    cleaned.append(p)
            if len(cleaned) >= 2:
                return cleaned
    return None


def _items_from_text(text_content: str, marker_id: str) -> list[str]:
    """Split slide text into items; drop the marker label line if present.

    If a line in the slide body looks like a marker descriptor (starts with
    SMARTART:/BG:/IMAGE: and contains a delimiter), use ITS sub-items rather
    than the surrounding prose lines. This handles Spike 1 Variant A style
    content where the SMARTART label encodes the intended items inline.
    """
    raw_lines = [ln.strip() for ln in text_content.splitlines() if ln.strip()]
    # Look for an inline label-style line first — strongest signal.
    for ln in raw_lines:
        if ln.startswith(("SMARTART:", "BG:", "IMAGE:")):
            split = _split_label_line(ln)
            if split:
                return split

    lines = list(raw_lines)
    # Drop leading lines that ARE the marker label
    marker_label_dropped = False
    while lines and lines[0] == marker_id:
        lines = lines[1:]
        marker_label_dropped = True
    # Drop a single non-bullet "title" line if it looks like a title (no leading dash/digit).
    # Skip this heuristic if we already consumed the marker label — the remaining lines are
    # the items the speaker authored beneath the marker, and we should not eat the first one.
    if not marker_label_dropped and lines and not lines[0].startswith(("-", "•", "*")):
        # Heuristic: if the first line is short and the rest are clearly bullets,
        # treat the first as a title. Otherwise keep all lines.
        if len(lines) > 2 and len(lines[0]) < 40:
            lines = lines[1:]
    # Strip leading bullet glyphs
    return [ln.lstrip("-•* \t") for ln in lines]


def _truncate_to_cap(items: list[str], layout_id: str) -> list[str]:
    """Truncate each item to the layout's max_label_chars cap with an ellipsis.

    Graceful degradation when prose lines find their way into a SMARTART spec.
    The unit tests use crisp inputs that fit the cap, so this is a no-op for
    them; only triggers on real prose content.
    """
    cap = _MAX_LABEL_CHARS.get(layout_id)
    if cap is None:
        return items
    out = []
    for it in items:
        if len(it) <= cap:
            out.append(it)
        else:
            # Reserve 1 char for the ellipsis
            out.append(it[: cap - 1].rstrip() + "…")
    return out


def _detect_keyword(marker_id: str) -> tuple[str, str] | None:
    ident = marker_id.split(":", 1)[1].lower() if ":" in marker_id else marker_id.lower()
    for keyword, (graphic_type, layout_id) in _KEYWORD_TO_LAYOUT.items():
        if keyword in ident:
            return graphic_type, layout_id
    return None


def _is_hierarchical_text(text: str) -> bool:
    """Heuristic — text is hierarchical if at least one non-first line is indented."""
    lines = text.splitlines()
    return any(ln.startswith(("  ", "\t")) for ln in lines[1:])


def _parse_tree(text: str) -> dict[str, Any]:
    """Parse 2-space-indented text into a tree dict per pptx_native hierarchical schema.

    Format expected:
      Root
        Child A
          Grandchild
        Child B
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise SmartArtBridgeError("hierarchical text is empty")
    # First line is root
    root = {"title": lines[0].strip(), "children": []}
    stack: list[tuple[int, dict]] = [(-2, root)]  # (indent, node)
    for line in lines[1:]:
        # measure indent (spaces only; tabs treated as 2 spaces)
        stripped = line.lstrip(" \t")
        indent = len(line) - len(stripped)
        if "\t" in line[:indent]:
            indent = indent  # treat tab-using files identically — both lift to depth
        node = {"title": stripped, "children": []}
        # Find parent: the top-of-stack whose indent < this indent
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if not stack:
            raise SmartArtBridgeError(f"no parent found for {stripped!r}")
        stack[-1][1]["children"].append(node)
        stack.append((indent, node))
    return root


def select_layout_for_slide(slide: SlideFacts, *, marker_id: str) -> str:
    """Pick a layout id from the catalog based on marker keyword + content shape."""
    detected = _detect_keyword(marker_id)
    if detected is not None:
        return detected[1]
    # Default by content shape
    if _is_hierarchical_text(slide.text_content):
        return "orgChart1"
    return "process1"


_GRAPHIC_TYPE_BY_LAYOUT = {
    "process1": "flowchart",
    "cycle2": "cycle",
    "orgChart1": "org_chart",
    "list1": "list",
    "venn1": "relationship",
    "pyramid2": "pyramid",
    "matrix2": "relationship",
    "funnel1": "relationship",
    "target3": "relationship",
}


def build_spec_from_slide(
    slide: SlideFacts, *, marker_id: str, layout_id: str
) -> dict[str, Any]:
    """Construct the spec the msft-smartart engine consumes."""
    graphic_type = _GRAPHIC_TYPE_BY_LAYOUT.get(layout_id, "flowchart")
    if layout_id == "orgChart1":
        # Hierarchical
        # Strip marker label if it's the first line
        text = slide.text_content
        lines = [ln for ln in text.splitlines() if ln.strip()]
        if lines and lines[0].strip() == marker_id:
            text = "\n".join(lines[1:])
        tree = _parse_tree(text)
        return {
            "graphic_type": graphic_type,
            "layout_id": layout_id,
            "data": {"tree": tree},
        }
    items = _items_from_text(slide.text_content, marker_id=marker_id)
    if not items:
        raise SmartArtBridgeError(f"no items extracted from slide {slide.slide_index}")
    cap = _CAPACITY.get(layout_id)
    if cap and not (cap[0] <= len(items) <= cap[1]):
        raise SmartArtBridgeError(
            f"layout {layout_id} capacity {cap} violated by {len(items)} items"
        )
    # Truncate to per-layout char cap (graceful degradation for prose content).
    items = _truncate_to_cap(items, layout_id)
    return {
        "graphic_type": graphic_type,
        "layout_id": layout_id,
        "data": {"items": items},
    }


def render_carrier(spec: dict[str, Any], *, output_dir: Path) -> Path:
    """Render a single-slide carrier .pptx via msft-smartart engine.render()."""
    output_dir.mkdir(parents=True, exist_ok=True)
    api = load_msft_smartart_api()
    try:
        result = api.engine.render(spec, output_dir)
    except Exception as exc:
        raise SmartArtBridgeError(f"engine.render failed: {exc}") from exc
    return Path(result.output_path)
