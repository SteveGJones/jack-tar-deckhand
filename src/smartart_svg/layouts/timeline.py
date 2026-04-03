"""Timeline layout — horizontal spine with nodes, alternating labels."""

from src.smartart_svg.engine import Container
from src.smartart_svg.primitives import svg_rect, svg_circle, svg_text, svg_group
from src.smartart_svg.tokens import resolve_text_colour


def render_timeline(data, container, tokens):
    """Render a horizontal timeline as an SVG fragment.

    A thin horizontal spine runs through the vertical centre.
    Equal columns house each stage. Circle nodes sit on the spine.
    Labels alternate above/below the spine to avoid crowding.
    Descriptions appear on the opposite side from the label.
    """
    stages = data.get('stages', [])
    if not stages:
        return svg_group([], role='img', aria_label='Empty timeline')

    n = len(stages)
    primary = tokens['primary_color']
    text_col = tokens['text_color']
    font = tokens['font_family']
    heading_font = tokens['heading_font']

    # Vertical midpoint of the container for the spine
    spine_y = container.inner_y + container.inner_height / 2

    # Spine rectangle — full width, 4px tall
    spine = svg_rect(
        container.inner_x, spine_y - 2,
        container.inner_width, 4,
        fill=primary
    )

    # Split into n equal horizontal columns
    cols = container.split_horizontal([1] * n, gap=0)

    node_r = 14
    label_offset = 40     # distance from spine centre to label baseline
    desc_offset = 70      # distance from spine centre to description baseline

    elements = [spine]

    for i, (stage, col) in enumerate(zip(stages, cols)):
        label = stage.get('label', '')
        description = stage.get('description', '')

        node_cx, _ = col.center_point()

        # Draw node circle on the spine
        elements.append(svg_circle(node_cx, spine_y, node_r, fill=primary))

        # Alternate: even stages label above, odd below
        above = (i % 2 == 0)

        # Label
        label_y = spine_y - label_offset if above else spine_y + label_offset + 14
        elements.append(svg_text(
            node_cx, label_y,
            label,
            font_family=heading_font,
            font_size=16,
            fill=text_col,
            anchor='middle',
            weight='bold'
        ))

        # Description — on opposite side from label
        if description:
            desc_y = spine_y + desc_offset if above else spine_y - desc_offset + 14
            elements.append(svg_text(
                node_cx, desc_y,
                description,
                font_family=font,
                font_size=13,
                fill=text_col,
                anchor='middle'
            ))

    return svg_group(elements, role='img', aria_label='Timeline diagram')
