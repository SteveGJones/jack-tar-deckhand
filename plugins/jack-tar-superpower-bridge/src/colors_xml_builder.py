"""Brand palette injection for SmartArt carrier `colors.xml`.

Run 3 dogfood (2026-04-26) caught Finding #10: SmartArt carriers ship with
default Microsoft palette (Office-blue gradients, grey accents) regardless of
the brief's visual personality. Every SmartArt slide in every dogfood deck
rendered in foreign colours.

This module implements Contract 1 from the Run 3 plan: a brand palette
injector that transforms a carrier's ``ppt/diagrams/colors1.xml`` to use the
brief's hex tokens directly via ``<a:srgbClr>`` elements, replacing the
default ``<a:schemeClr val="accent1|lt1|dk1|...">`` references.

Design — schemeClr → srgbClr substitution:

The SDK fixtures' colors.xml files contain ~50 ``styleLbl`` entries (one per
diagram element category — ``node0``, ``alignNode1``, ``sibTrans2D1``,
``parChTrans1D1``, etc.). Each styleLbl references 1-4 theme scheme colours
(accent1 / lt1 / dk1 / tx1) optionally with tint / shade / alpha modifiers.

By rewriting every ``<a:schemeClr val="X">`` to ``<a:srgbClr val="<hex>">``
based on a small slot-to-hex map, we get brand-coloured rendering across all
50+ styleLbls without touching the layout algorithm or quickStyle. Tint /
shade / alpha modifier children are preserved — they apply to whatever colour
sits in the parent element regardless of its tag.

Slot model (v0.1.x):
  primary_fill   ← schemeClr accent1, accent2, ... accent6 (all map to primary)
  text_on_primary ← schemeClr lt1, lt2, bg1, bg2 (light text on dark fills)
  text_on_surface ← schemeClr dk1, dk2, tx1, tx2 (dark text on light fills)

This is deliberately reductive — Microsoft's full theme has 12+ colour roles
but most SmartArt fixtures only reference accent1 + the lt/dk pair. The slot
model is sufficient to produce brand-native rendering for every layout we
ship today. v0.2 can add per-styleLbl accent variation.
"""
from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from lxml import etree

# OOXML namespaces used in SmartArt colors.xml
_DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

# Map of <a:schemeClr val="..."/> → BrandPalette field name
_SCHEME_TO_FIELD: dict[str, str] = {
    # All accent slots route to primary fill — most layouts only use accent1
    # but a few use accent2-6 for differentiated nodes. We collapse them all
    # to the same brand colour for v0.1.x; v0.2 adds per-accent variation.
    "accent1": "primary_fill_hex",
    "accent2": "primary_fill_hex",
    "accent3": "primary_fill_hex",
    "accent4": "primary_fill_hex",
    "accent5": "primary_fill_hex",
    "accent6": "primary_fill_hex",
    # Light slots — text on dark backgrounds
    "lt1": "text_on_primary_hex",
    "lt2": "text_on_primary_hex",
    "bg1": "text_on_primary_hex",
    "bg2": "text_on_primary_hex",
    # Dark slots — text on light backgrounds
    "dk1": "text_on_surface_hex",
    "dk2": "text_on_surface_hex",
    "tx1": "text_on_surface_hex",
    "tx2": "text_on_surface_hex",
}

_HEX_RE = re.compile(r"^[0-9A-Fa-f]{6}$")


def _validate_hex(value: str, field_name: str) -> str:
    """Normalise a hex colour value — uppercase, no leading #, no whitespace.

    Accepts forms like ``"#14213D"``, ``" #14213D "``, ``"14213d"``,
    ``"  14213d  "``. Whitespace is stripped from both ends; an optional
    leading ``#`` is removed; the result is uppercased.
    """
    cleaned = value.strip()
    if cleaned.startswith("#"):
        cleaned = cleaned[1:].strip()
    if not _HEX_RE.match(cleaned):
        raise ValueError(
            f"BrandPalette.{field_name} must be a 6-char hex colour (RRGGBB), "
            f"got {value!r}"
        )
    return cleaned.upper()


@dataclass(frozen=True)
class BrandPalette:
    """The minimum viable brand palette for SmartArt rendering (v0.1.x scope).

    All values are 6-char hex strings WITHOUT a leading ``#`` (the OOXML
    convention). Constructor normalises input so callers can pass either form.

    Three slots:

    - ``primary_fill_hex`` — fill colour for diagram shapes (chevrons, nodes,
      cycle segments, matrix cells, pyramid layers, venn circles). For decks
      with a light surface (cream / off-white), this is typically the brief's
      structural / accent token. For decks with a dark surface, this is
      typically the brief's accent or a contrasting light token.
    - ``text_on_primary_hex`` — text colour for labels INSIDE shapes filled
      with primary_fill. Must contrast strongly with primary_fill.
    - ``text_on_surface_hex`` — text colour for labels OUTSIDE shapes (on the
      slide's surface colour). Must contrast strongly with the slide bg.
    """

    primary_fill_hex: str
    text_on_primary_hex: str
    text_on_surface_hex: str

    def __post_init__(self) -> None:
        # Normalise via __setattr__ since dataclass is frozen
        object.__setattr__(self, "primary_fill_hex",
                            _validate_hex(self.primary_fill_hex, "primary_fill_hex"))
        object.__setattr__(self, "text_on_primary_hex",
                            _validate_hex(self.text_on_primary_hex, "text_on_primary_hex"))
        object.__setattr__(self, "text_on_surface_hex",
                            _validate_hex(self.text_on_surface_hex, "text_on_surface_hex"))


def apply_brand_palette_to_colors_xml(xml_bytes: bytes, palette: BrandPalette) -> bytes:
    """Transform a SmartArt colors.xml: replace ``<a:schemeClr val="X"/>`` with
    ``<a:srgbClr val="<hex>"/>`` based on the BrandPalette slot map.

    Preserves all child modifier elements (``<a:tint>``, ``<a:shade>``,
    ``<a:alpha>``) — they continue to apply to the parent colour element
    regardless of its tag. Preserves all unrelated XML structure
    (``<dgm:styleLbl>`` wrappers, ``<dgm:catLst>``, etc.).

    Unmapped scheme references (e.g. ``phClr``, ``hlink``, ``folHlink``,
    or theme variants we did not enumerate) are left unchanged. They are
    rare in SmartArt fixtures and represent edge cases the v0.1.x slot model
    does not aim to brand-map.

    Returns the modified XML as bytes, ready to write back into a carrier
    zip via ``patch_carrier_palette``.
    """
    root = etree.fromstring(xml_bytes)

    scheme_qname = f"{{{_A_NS}}}schemeClr"
    srgb_qname = f"{{{_A_NS}}}srgbClr"

    for scheme_el in root.iter(scheme_qname):
        val = scheme_el.get("val")
        field = _SCHEME_TO_FIELD.get(val) if val else None
        if field is None:
            continue
        hex_color = getattr(palette, field)
        # Mutate in place: tag becomes srgbClr; val becomes the hex colour.
        # Children (tint / shade / alpha) and tail are preserved automatically.
        scheme_el.tag = srgb_qname
        scheme_el.set("val", hex_color)

    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=True,
    )


def patch_carrier_palette(carrier_path: Path, palette: BrandPalette) -> None:
    """In-place brand-palette patch of a SmartArt carrier .pptx.

    Reads ``ppt/diagrams/colors1.xml`` from the carrier zip, applies the brand
    palette via ``apply_brand_palette_to_colors_xml``, writes the carrier back
    with the patched colours. All other parts (layout, quickStyle, data,
    content types, etc.) are passed through unchanged.

    The file is rewritten via a tempfile + ``shutil.move`` for atomic
    replacement — partial writes on failure are eliminated.

    Raises ``FileNotFoundError`` if the carrier or its ``colors1.xml`` is
    missing.
    """
    carrier_path = Path(carrier_path)
    if not carrier_path.exists():
        raise FileNotFoundError(f"Carrier .pptx not found: {carrier_path}")

    target_part = "ppt/diagrams/colors1.xml"

    # Stage to a tempfile in the same dir (so shutil.move is rename-only)
    tmp_fd, tmp_name = tempfile.mkstemp(
        suffix=".pptx", dir=str(carrier_path.parent)
    )
    tmp_path = Path(tmp_name)
    import os
    os.close(tmp_fd)

    found_target = False
    try:
        with zipfile.ZipFile(carrier_path, "r") as src:
            if target_part not in src.namelist():
                raise FileNotFoundError(
                    f"Carrier missing {target_part}: {carrier_path}"
                )
            with zipfile.ZipFile(
                tmp_path, "w", compression=zipfile.ZIP_DEFLATED
            ) as dst:
                for info in src.infolist():
                    data = src.read(info.filename)
                    if info.filename == target_part:
                        data = apply_brand_palette_to_colors_xml(data, palette)
                        found_target = True
                    dst.writestr(info, data)

        if not found_target:
            raise FileNotFoundError(
                f"Carrier missing {target_part}: {carrier_path}"
            )

        # Atomic replace
        os.replace(tmp_path, carrier_path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


# Tiered keyword preferences for each palette slot. Tier 0 is most-preferred;
# Tier 1 is fallback. The heuristic does a tiered pass — first, scan all hex
# values for tier-0 matches; if all 3 slots are filled, return early. Else,
# scan again allowing tier-1 matches for any unfilled slots.
#
# Tiering matters because brief palette tables often include both a
# "structural" colour (the dominant deck fill) AND an "accent" colour. We
# want primary_fill_hex to be the structural one when both are present —
# otherwise SmartArt shapes render in accent (correct on dark slides, wrong
# on light slides like Blueprint Retrospective). Tier-0 prefers "structural";
# tier-1 falls back to "accent" if structural isn't named.
_SLOT_KEYWORD_TIERS: dict[str, tuple[tuple[str, ...], ...]] = {
    "primary_fill_hex": (
        # Tier 0 — most preferred
        ("structural", "primary fill"),
        # Tier 1 — fallback. Run 4 Finding #12 fix: 'brand' / 'brand colour'
        # / 'hero' join the accent slot since some briefs name the dominant
        # fill colour with these tokens instead of "structural". 'primary '
        # was removed because it ambiguously matches 'Primary body copy' and
        # would steal the body text hex into the primary_fill slot.
        ("accent (", "accent ", "brand", "hero"),
    ),
    "text_on_primary_hex": (
        # Tier 0 — explicit "text on brand colour" / "text on primary" row.
        # v0.2 #24 fix: when the operator declares the contrasting text
        # colour explicitly in the palette table (e.g. "Text on Brand
        # colour | #FFFFFF | white-on-navy for SmartArt body labels"),
        # that row WINS over surface inference. Run 7 + Run 8 evidence:
        # without an explicit row, the heuristic collapsed text_on_primary
        # to primary_fill (illegible navy-on-navy SmartArt body text);
        # with an explicit row, the operator gets the contrast they
        # actually intend.
        ("text on brand", "text on primary", "text on accent", "white on", "cream on"),
        # Tier 1 — surface inference (the v0.1.x fallback). Most decks
        # use the surface colour as the contrasting text on primary fills.
        ("surface", "cream", "off-white", "near-white", "warm light", "ivory"),
        # Tier 2 — last-resort surface synonyms.
        ("background base", "background (", "parchment", "vellum"),
    ),
    "text_on_surface_hex": (
        # Tier 0 — most preferred
        ("body text",),
        # Tier 1 — fallback
        ("body ", "primary text", "text on "),
    ),
}


def _line_for_match(text: str, match: re.Match) -> str:
    """Return the line of ``text`` containing the regex match, lowercased."""
    line_start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", match.end())
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end].lower()


def derive_palette_from_brief_text(visual_personality: str) -> Optional[BrandPalette]:
    """Best-effort heuristic to extract a BrandPalette from a brief's
    Section B visual_personality (prose + palette table).

    For each hex value found in the text, the heuristic looks at the WHOLE
    LINE containing the hex (not just preceding-character context — that
    breaks on markdown table cell boundaries like backticks around ``#hex``)
    and matches the line against tiered role keywords.

    Two-pass tiering ensures structural beats accent for primary_fill when
    both are present in the brief. See ``_SLOT_KEYWORD_TIERS``.

    Returns ``None`` if the brief text doesn't yield enough hex values to
    fill all three slots after both tier passes — in that case the caller
    should pass an explicit BrandPalette or skip palette injection.
    """
    if not visual_personality:
        return None

    # Pre-extract all hex values with their containing lines, lowercased
    matches: list[tuple[str, str]] = []  # (hex_upper, line_lower)
    for m in re.finditer(r"#([0-9A-Fa-f]{6})", visual_personality):
        matches.append((m.group(1).upper(), _line_for_match(visual_personality, m)))

    if not matches:
        return None

    primary_fill: Optional[str] = None
    text_on_primary: Optional[str] = None
    text_on_surface: Optional[str] = None

    # Tiered search — iterate across the maximum tier depth across slots.
    # Slots may declare different numbers of tiers (e.g. v0.2 #24 added a
    # third tier to text_on_primary_hex). Each slot's lookup is bounded
    # by its own tier count to avoid IndexError.
    max_tiers = max(len(slot_tiers) for slot_tiers in _SLOT_KEYWORD_TIERS.values())
    for tier in range(max_tiers):
        for hex_val, line in matches:
            if primary_fill is None:
                slot_tiers = _SLOT_KEYWORD_TIERS["primary_fill_hex"]
                if tier < len(slot_tiers) and any(kw in line for kw in slot_tiers[tier]):
                    primary_fill = hex_val
            if text_on_primary is None:
                slot_tiers = _SLOT_KEYWORD_TIERS["text_on_primary_hex"]
                if tier < len(slot_tiers) and any(kw in line for kw in slot_tiers[tier]):
                    text_on_primary = hex_val
            if text_on_surface is None:
                slot_tiers = _SLOT_KEYWORD_TIERS["text_on_surface_hex"]
                if tier < len(slot_tiers) and any(kw in line for kw in slot_tiers[tier]):
                    text_on_surface = hex_val
        if primary_fill and text_on_primary and text_on_surface:
            break

    if primary_fill and text_on_primary and text_on_surface:
        return BrandPalette(
            primary_fill_hex=primary_fill,
            text_on_primary_hex=text_on_primary,
            text_on_surface_hex=text_on_surface,
        )
    return None
