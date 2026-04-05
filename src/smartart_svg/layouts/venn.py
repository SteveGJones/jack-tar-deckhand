"""Venn diagram layout — two overlapping semi-transparent circles."""

from src.smartart_svg.primitives import svg_circle, svg_text, svg_group
from src.smartart_svg.tokens import resolve_text_colour


def render_venn(data, container, tokens):
    """Render a 2-set Venn diagram as an SVG fragment.

    Overlap is proportional to intersection/total item ratio.
    More shared items = more overlap; fewer = less.
    """
    sets = data.get('sets', [])
    intersection = data.get('intersection', {})
    intersection_items = intersection.get('items', [])

    cx, cy = container.center_point()
    r = min(container.inner_width, container.inner_height) * 0.30

    left_items = sets[0].get('items', []) if len(sets) >= 1 else []
    right_items = sets[1].get('items', []) if len(sets) >= 2 else []
    total_items = len(left_items) + len(right_items) + len(intersection_items)
    if total_items > 0:
        shared_ratio = len(intersection_items) / total_items
    else:
        shared_ratio = 0.3

    min_overlap_pct = 0.15
    max_overlap_pct = 0.60
    overlap_pct = min_overlap_pct + (max_overlap_pct - min_overlap_pct) * shared_ratio
    separation = 2 * r * (1 - overlap_pct)

    left_cx = cx - separation / 2
    right_cx = cx + separation / 2

    series = tokens.get('chart_series', ['#2B6CB0', '#ED8936'])
    left_fill = series[0] if len(series) > 0 else '#2B6CB0'
    right_fill = series[1] if len(series) > 1 else '#ED8936'

    elements = []
    elements.append(svg_circle(left_cx, cy, r, fill=left_fill, opacity=0.4))
    elements.append(svg_circle(right_cx, cy, r, fill=right_fill, opacity=0.4))

    font = tokens['font_family']
    heading_font = tokens['heading_font']
    text_col = tokens['text_color']

    if len(sets) >= 1:
        elements.append(svg_text(
            left_cx, cy - r - 12,
            sets[0].get('label', ''),
            font_family=heading_font, font_size=18,
            fill=text_col, anchor='middle', weight='bold'
        ))
    if len(sets) >= 2:
        elements.append(svg_text(
            right_cx, cy - r - 12,
            sets[1].get('label', ''),
            font_family=heading_font, font_size=18,
            fill=text_col, anchor='middle', weight='bold'
        ))

    line_h = 18
    font_size = 13

    if left_items:
        excl_x = left_cx - r * 0.45
        start_y = cy - (len(left_items) - 1) * line_h / 2
        for i, item in enumerate(left_items):
            elements.append(svg_text(
                excl_x, start_y + i * line_h, item,
                font_family=font, font_size=font_size,
                fill=text_col, anchor='middle'
            ))

    if right_items:
        excl_x = right_cx + r * 0.45
        start_y = cy - (len(right_items) - 1) * line_h / 2
        for i, item in enumerate(right_items):
            elements.append(svg_text(
                excl_x, start_y + i * line_h, item,
                font_family=font, font_size=font_size,
                fill=text_col, anchor='middle'
            ))

    if intersection_items:
        start_y = cy - (len(intersection_items) - 1) * line_h / 2
        for i, item in enumerate(intersection_items):
            elements.append(svg_text(
                cx, start_y + i * line_h, item,
                font_family=font, font_size=font_size,
                fill=text_col, anchor='middle', weight='bold'
            ))

    return svg_group(elements, role='img', aria_label='Venn diagram')
