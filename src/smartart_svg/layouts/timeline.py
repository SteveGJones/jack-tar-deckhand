"""Timeline layout — horizontal spine with nodes, alternating labels."""

from src.smartart_svg.engine import Container
from src.smartart_svg.primitives import svg_rect, svg_circle, svg_text, svg_group
from src.smartart_svg.tokens import resolve_text_colour


def _truncate(text, max_chars):
    """Truncate text to max_chars with ellipsis if needed."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 1] + '\u2026'


def render_timeline(data, container, tokens):
    """Render a horizontal timeline as an SVG fragment.

    A thin horizontal spine runs through the vertical centre.
    Equal columns house each stage. Circle nodes sit on the spine.
    Labels alternate above/below. Text is truncated to fit column width.
    """
    stages = data.get('stages', [])
    if not stages:
        return svg_group([], role='img', aria_label='Empty timeline')

    n = len(stages)
    primary = tokens['primary_color']
    text_col = tokens['text_color']
    font = tokens['font_family']
    heading_font = tokens['heading_font']

    spine_y = container.inner_y + container.inner_height / 2

    spine = svg_rect(
        container.inner_x, spine_y - 2,
        container.inner_width, 4,
        fill=primary
    )

    cols = container.split_horizontal([1] * n, gap=4)

    node_r = min(12, container.inner_height * 0.04)

    half_h = container.inner_height / 2
    label_offset = min(half_h * 0.30, 36)
    desc_offset = min(half_h * 0.55, 60)

    label_font_size = max(12, min(16, cols[0].width / 5))
    desc_font_size = max(12, min(13, cols[0].width / 6))
    char_width_label = label_font_size * 0.6
    char_width_desc = desc_font_size * 0.6
    max_label_chars = max(6, int(cols[0].width / char_width_label))
    max_desc_chars = max(8, int(cols[0].width / char_width_desc))

    elements = [spine]

    for i, (stage, col) in enumerate(zip(stages, cols)):
        label = stage.get('label', '')
        description = stage.get('description', '')

        node_cx, _ = col.center_point()

        elements.append(svg_circle(node_cx, spine_y, node_r, fill=primary))

        above = (i % 2 == 0)

        truncated_label = _truncate(label, max_label_chars)
        label_y = spine_y - label_offset if above else spine_y + label_offset + label_font_size
        elements.append(svg_text(
            node_cx, label_y,
            truncated_label,
            font_family=heading_font,
            font_size=label_font_size,
            fill=text_col,
            anchor='middle',
            weight='bold'
        ))

        if description:
            truncated_desc = _truncate(description, max_desc_chars)
            desc_y = spine_y + desc_offset if above else spine_y - desc_offset + desc_font_size
            elements.append(svg_text(
                node_cx, desc_y,
                truncated_desc,
                font_family=font,
                font_size=desc_font_size,
                fill=text_col,
                anchor='middle'
            ))

    return svg_group(elements, role='img', aria_label='Timeline diagram')
