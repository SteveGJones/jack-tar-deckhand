"""Venn diagram layout — two overlapping semi-transparent circles."""

from src.smartart_svg.primitives import svg_circle, svg_text, svg_group
from src.smartart_svg.tokens import resolve_text_colour


def render_venn(data, container, tokens):
    """Render a 2-set Venn diagram as an SVG fragment.

    Two semi-transparent circles overlap ~30% of their radius.
    Set labels appear above each circle.
    Intersection items appear centred in the overlap zone.
    Exclusive items appear outside (left / right of overlap).
    """
    sets = data.get('sets', [])
    intersection = data.get('intersection', {})
    intersection_items = intersection.get('items', [])

    cx, cy = container.center_point()
    # Radius is 38% of the smaller dimension so circles fit comfortably
    r = min(container.inner_width, container.inner_height) * 0.38

    # Offset: circles overlap by ~30% of radius
    overlap_offset = r * 0.6
    left_cx = cx - overlap_offset / 2
    right_cx = cx + overlap_offset / 2

    series = tokens.get('chart_series', ['#2B6CB0', '#ED8936'])
    left_fill = series[0] if len(series) > 0 else '#2B6CB0'
    right_fill = series[1] if len(series) > 1 else '#ED8936'

    elements = []

    # Left circle
    elements.append(svg_circle(left_cx, cy, r, fill=left_fill, opacity=0.4))
    # Right circle
    elements.append(svg_circle(right_cx, cy, r, fill=right_fill, opacity=0.4))

    font = tokens['font_family']
    heading_font = tokens['heading_font']
    text_col = tokens['text_color']

    # Set labels — above each circle, outside the overlap zone
    if len(sets) >= 1:
        label_a = sets[0].get('label', '')
        elements.append(svg_text(
            left_cx - r * 0.15,
            cy - r - 12,
            label_a,
            font_family=heading_font,
            font_size=22,
            fill=text_col,
            anchor='middle',
            weight='bold'
        ))

    if len(sets) >= 2:
        label_b = sets[1].get('label', '')
        elements.append(svg_text(
            right_cx + r * 0.15,
            cy - r - 12,
            label_b,
            font_family=heading_font,
            font_size=22,
            fill=text_col,
            anchor='middle',
            weight='bold'
        ))

    # Exclusive items for left set — positioned to the left of overlap
    if len(sets) >= 1:
        left_items = sets[0].get('items', [])
        item_x = left_cx - overlap_offset * 0.4
        line_h = 20
        start_y = cy - (len(left_items) - 1) * line_h / 2
        for i, item in enumerate(left_items):
            elements.append(svg_text(
                item_x, start_y + i * line_h,
                item,
                font_family=font,
                font_size=14,
                fill=text_col,
                anchor='middle'
            ))

    # Exclusive items for right set
    if len(sets) >= 2:
        right_items = sets[1].get('items', [])
        item_x = right_cx + overlap_offset * 0.4
        line_h = 20
        start_y = cy - (len(right_items) - 1) * line_h / 2
        for i, item in enumerate(right_items):
            elements.append(svg_text(
                item_x, start_y + i * line_h,
                item,
                font_family=font,
                font_size=14,
                fill=text_col,
                anchor='middle'
            ))

    # Intersection items — centred in overlap zone
    inter_x = cx
    line_h = 20
    start_y = cy - (len(intersection_items) - 1) * line_h / 2
    for i, item in enumerate(intersection_items):
        elements.append(svg_text(
            inter_x, start_y + i * line_h,
            item,
            font_family=font,
            font_size=14,
            fill=text_col,
            anchor='middle',
            weight='bold'
        ))

    return svg_group(elements, role='img', aria_label='Venn diagram')
