"""Timeline layout — horizontal spine with nodes, alternating labels."""

from src.smartart_svg.engine import Container
from src.smartart_svg.primitives import svg_rect, svg_circle, svg_text, svg_group
from src.smartart_svg.tokens import resolve_text_colour


def _truncate(text, max_chars):
    """Truncate text to max_chars with ellipsis if needed."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 1] + '\u2026'


def _wrap_text(text, max_chars):
    """Word-wrap text into lines of max_chars. Returns list of lines."""
    words = text.split()
    lines = []
    current = ''
    for word in words:
        test = (current + ' ' + word).strip()
        if len(test) <= max_chars:
            current = test
        else:
            if current:
                lines.append(current)
            current = word if len(word) <= max_chars else _truncate(word, max_chars)
    if current:
        lines.append(current)
    return lines if lines else [text[:max_chars]]


def render_timeline(data, container, tokens):
    """Render a horizontal timeline as an SVG fragment.

    Layout:
    - Horizontal spine runs across the upper third
    - Circle nodes sit on the spine
    - Labels (bold, larger) appear ABOVE each node
    - Descriptions (smaller, multi-line) appear BELOW each node
    - All stages use the same vertical layout (no alternation) for visual consistency
    """
    stages = data.get('stages', [])
    if not stages:
        return svg_group([], role='img', aria_label='Empty timeline')

    n = len(stages)
    primary = tokens['primary_color']
    text_col = tokens['text_color']
    font = tokens['font_family']
    heading_font = tokens['heading_font']

    # Spine sits in the upper portion so descriptions get most of the canvas
    spine_y = container.inner_y + container.inner_height * 0.30

    spine = svg_rect(
        container.inner_x, spine_y - 2,
        container.inner_width, 4,
        fill=primary
    )

    cols = container.split_horizontal([1] * n, gap=4)

    node_r = min(12, container.inner_height * 0.04)

    label_font_size = max(12, min(15, cols[0].width / 6))
    desc_font_size = max(10, min(12, cols[0].width / 8))
    char_width_label = label_font_size * 0.55
    char_width_desc = desc_font_size * 0.55
    max_label_chars = max(8, int(cols[0].width / char_width_label))
    max_desc_chars = max(10, int(cols[0].width / char_width_desc))

    # Vertical anchors
    label_top_y = spine_y - node_r - 12   # label sits above the node
    desc_top_y = spine_y + node_r + 18    # description sits below the node
    desc_band_h = container.inner_y + container.inner_height - desc_top_y - 4
    max_desc_lines = max(2, int(desc_band_h / (desc_font_size + 2)))

    elements = [spine]

    for i, (stage, col) in enumerate(zip(stages, cols)):
        label = stage.get('label', '')
        description = stage.get('description', '')

        node_cx, _ = col.center_point()

        elements.append(svg_circle(node_cx, spine_y, node_r, fill=primary))

        # LABEL ABOVE (always — no alternation)
        # Allow up to 2 lines for the label
        label_lines = _wrap_text(label, max_label_chars)[:2]
        # Render bottom-up so the last line sits at label_top_y
        for li, line in enumerate(reversed(label_lines)):
            ly = label_top_y - li * (label_font_size + 2)
            elements.append(svg_text(
                node_cx, ly,
                line,
                font_family=heading_font,
                font_size=label_font_size,
                fill=text_col,
                anchor='middle',
                weight='bold'
            ))

        # DESCRIPTION BELOW (always — no alternation)
        if description:
            desc_lines = _wrap_text(description, max_desc_chars)
            visible_lines = desc_lines[:max_desc_lines]

            # If truncated, add ellipsis to last visible line
            if len(desc_lines) > max_desc_lines and visible_lines:
                last = visible_lines[-1]
                if len(last) > max_desc_chars - 1:
                    last = last[:max_desc_chars - 1]
                visible_lines[-1] = last + '\u2026'

            for di, dline in enumerate(visible_lines):
                dy = desc_top_y + di * (desc_font_size + 2)
                elements.append(svg_text(
                    node_cx, dy,
                    dline,
                    font_family=font,
                    font_size=desc_font_size,
                    fill=text_col,
                    anchor='middle'
                ))

    return svg_group(elements, role='img', aria_label='Timeline diagram')
