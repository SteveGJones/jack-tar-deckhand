"""Pipeline funnel layout — tapered bars proportional to stage values."""


from src.smartart_svg.engine import Container
from src.smartart_svg.primitives import svg_rect, svg_text, svg_group
from src.smartart_svg.tokens import resolve_text_colour


def _interpolate_colour(hex1, hex2, t):
    """Linearly interpolate between two hex colours. t in [0, 1]."""
    def _parse(h):
        h = h.lstrip('#')
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    r1, g1, b1 = _parse(hex1)
    r2, g2, b2 = _parse(hex2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f'#{r:02x}{g:02x}{b:02x}'


def render_pipeline_funnel(data, container, tokens):
    """Render a pipeline funnel as an SVG fragment.

    N equal-height rows. Each row contains a centred rect whose width is
    proportional to stage value / max value. Colour interpolates from
    primary_color (top) to accent_color (bottom). Labels are centred.
    """
    stages = data.get('stages', [])
    if not stages:
        return svg_group([], role='img', aria_label='Empty funnel')

    n = len(stages)
    primary = tokens['primary_color']
    accent = tokens['accent_color']
    text_col = tokens['text_color']
    font = tokens['font_family']
    heading_font = tokens['heading_font']
    rx = tokens.get('border_radius', 8)

    values = [s.get('value', 1) for s in stages]
    max_val = max(values) if values else 1

    rows = container.split_vertical([1] * n, gap=8)

    elements = []

    for i, (stage, row) in enumerate(zip(stages, rows)):
        label = stage.get('label', '')
        value = stage.get('value', 0)

        t = i / max(n - 1, 1)
        fill = _interpolate_colour(primary, accent, t)

        ratio = value / max_val if max_val > 0 else 1.0
        bar_w = row.inner_width * ratio
        bar_x = row.inner_x + (row.inner_width - bar_w) / 2
        bar_y = row.inner_y
        bar_h = row.inner_height

        # Bar
        elements.append(svg_rect(bar_x, bar_y, bar_w, bar_h, rx=rx, fill=fill))

        # Label centred on bar
        text_colour = resolve_text_colour(fill, text_col, None)
        cx = bar_x + bar_w / 2
        cy = bar_y + bar_h / 2

        # Label
        elements.append(svg_text(
            cx, cy,
            label,
            font_family=heading_font,
            font_size=16,
            fill=text_colour,
            anchor='middle',
            weight='bold'
        ))

        # Value hint on the right
        val_str = str(value)
        elements.append(svg_text(
            cx, cy + 18,
            val_str,
            font_family=font,
            font_size=13,
            fill=text_colour,
            anchor='middle'
        ))

    return svg_group(elements, role='img', aria_label='Pipeline funnel diagram')
