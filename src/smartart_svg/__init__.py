"""Custom SVG engine for SmartArt graphics — constraint-based layout."""

from src.smartart_svg.engine import Container
from src.smartart_svg.primitives import svg_document
from src.smartart_svg.tokens import extract_style_tokens
from src.smartart_svg.layouts import LAYOUT_REGISTRY


def render_custom_svg(spec, style_guide, width=1920, height=1080):
    """Render a SmartArt spec as a complete SVG document."""
    graphic_type = spec['graphic_type']
    render_fn = LAYOUT_REGISTRY.get(graphic_type)
    if not render_fn:
        raise ValueError(f"Unsupported graphic type: {graphic_type}")

    tokens = extract_style_tokens(style_guide)
    container = Container(0, 0, width, height, padding=40)
    fragment = render_fn(spec['data'], container, tokens)

    alt_text = f"{graphic_type} diagram"
    return svg_document(width, height, [fragment], title=alt_text, desc=alt_text)
