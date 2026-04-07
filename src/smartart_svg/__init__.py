"""Custom SVG engine for SmartArt graphics — constraint-based layout.

COORDINATE SYSTEM: The SVG uses POINT-BASED coordinates so that font sizes
map 1:1 to displayed points in the slide. A font-size="12" in the SVG = 12pt
displayed. The viewBox is set to the graphic zone dimensions in points
(~612×324 for an 85%×80% zone of a 10"×5.625" slide), while the SVG
width/height attributes are set to pixel dimensions for rendering resolution.
"""

from src.smartart_svg.engine import Container
from src.smartart_svg.primitives import svg_document
from src.smartart_svg.tokens import extract_style_tokens
from src.smartart_svg.layouts import LAYOUT_REGISTRY

# Slide dimensions in points (72pt/inch)
_SLIDE_W_PT = 10.0 * 72     # 720pt
_SLIDE_H_PT = 5.625 * 72    # 405pt

# Graphic zone: 85% width, 80% height (matching assembler placement)
_ZONE_W_PT = _SLIDE_W_PT * 0.85   # 612pt
_ZONE_H_PT = _SLIDE_H_PT * 0.80   # 324pt

# Render resolution (pixels) — high-res for sharp display
_RENDER_W_PX = 1920
_RENDER_H_PX = 1080


def render_custom_svg(spec, style_guide, width=None, height=None):
    """Render a SmartArt spec as a complete SVG document.

    Coordinates are in POINTS (1pt = 1/72 inch). Font sizes map 1:1 to
    displayed sizes — font-size="12" = 12pt on the slide.

    The SVG viewBox uses point dimensions, while width/height use pixel
    dimensions for high-resolution rendering.
    """
    graphic_type = spec['graphic_type']
    render_fn = LAYOUT_REGISTRY.get(graphic_type)
    if not render_fn:
        raise ValueError(f"Unsupported graphic type: {graphic_type}")

    # Use point-based dimensions for the coordinate system
    logical_w = width or _ZONE_W_PT
    logical_h = height or _ZONE_H_PT

    tokens = extract_style_tokens(style_guide)
    container = Container(0, 0, logical_w, logical_h, padding=16)
    fragment = render_fn(spec['data'], container, tokens)

    alt_text = f"{graphic_type} diagram"
    return svg_document(
        logical_w, logical_h, [fragment],
        title=alt_text, desc=alt_text,
        render_width=_RENDER_W_PX, render_height=_RENDER_H_PX
    )
