"""Venn diagram layout — two or three overlapping semi-transparent circles."""

from src.smartart_svg.primitives import svg_circle, svg_text, svg_group
from src.smartart_svg.tokens import resolve_text_colour


def render_venn(data, container, tokens):
    """Render a Venn diagram as an SVG fragment.

    Dispatches to 2-set or 3-set implementation based on the number of
    sets in the data.
    """
    sets = data.get('sets', [])
    if len(sets) >= 3:
        return _render_venn_3set(data, container, tokens)
    return _render_venn_2set(data, container, tokens)


def _render_venn_2set(data, container, tokens):
    """Render a 2-set Venn diagram as an SVG fragment.

    Overlap is proportional to intersection/total item ratio.
    More shared items = more overlap; fewer = less.
    """
    sets = data.get('sets', [])
    intersection = data.get('intersection', {})
    intersection_items = intersection.get('items', [])

    cx, cy = container.center_point()
    r = min(container.inner_width, container.inner_height) * 0.40

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
            font_family=heading_font, font_size=22,
            fill=text_col, anchor='middle', weight='bold'
        ))
    if len(sets) >= 2:
        elements.append(svg_text(
            right_cx, cy - r - 12,
            sets[1].get('label', ''),
            font_family=heading_font, font_size=22,
            fill=text_col, anchor='middle', weight='bold'
        ))

    line_h = 18
    font_size = 15

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


def _render_venn_3set(data, container, tokens):
    """Render a 3-set Venn diagram as an SVG fragment.

    Three circles are arranged in a triangle: top-centre, bottom-left,
    bottom-right. Each circle's exclusive items are placed inside its
    own circle but offset away from the triangle centroid. The central
    3-way intersection items are placed at the container centre.
    Pairwise intersections are not rendered in v1.
    """
    sets = data.get('sets', [])
    intersection = data.get('intersection', {})
    intersection_items = intersection.get('items', [])

    cx, cy = container.center_point()
    r = min(container.inner_width, container.inner_height) * 0.32
    offset = r * 0.55

    # Triangle circle centres
    top_cx = cx
    top_cy = cy - offset
    bl_cx = cx - offset * 0.866
    bl_cy = cy + offset * 0.5
    br_cx = cx + offset * 0.866
    br_cy = cy + offset * 0.5

    series = tokens.get('chart_series', ['#2B6CB0', '#ED8936', '#6B7280'])
    fill0 = series[0] if len(series) > 0 else '#2B6CB0'
    fill1 = series[1] if len(series) > 1 else '#ED8936'
    fill2 = series[2] if len(series) > 2 else '#6B7280'

    elements = []
    elements.append(svg_circle(top_cx, top_cy, r, fill=fill0, opacity=0.4))
    elements.append(svg_circle(bl_cx, bl_cy, r, fill=fill1, opacity=0.4))
    elements.append(svg_circle(br_cx, br_cy, r, fill=fill2, opacity=0.4))

    font = tokens['font_family']
    heading_font = tokens['heading_font']
    text_col = tokens['text_color']

    # Set labels OUTSIDE each circle with generous clearance so they
    # never collide with exclusive item text rendered inside the circles.
    # Top: well above the top circle
    if len(sets) >= 1:
        elements.append(svg_text(
            top_cx, top_cy - r - 20,
            sets[0].get('label', ''),
            font_family=heading_font, font_size=22,
            fill=text_col, anchor='middle', weight='bold'
        ))
    # Bottom-left: further left of the bottom-left circle
    if len(sets) >= 2:
        elements.append(svg_text(
            bl_cx - r * 1.1, bl_cy + 6,
            sets[1].get('label', ''),
            font_family=heading_font, font_size=22,
            fill=text_col, anchor='end', weight='bold'
        ))
    # Bottom-right: further right of the bottom-right circle
    if len(sets) >= 3:
        elements.append(svg_text(
            br_cx + r * 1.1, br_cy + 6,
            sets[2].get('label', ''),
            font_family=heading_font, font_size=22,
            fill=text_col, anchor='start', weight='bold'
        ))

    line_h = 18
    font_size = 15

    # Exclusive items: offset from each circle centre in the direction
    # OPPOSITE the triangle centroid (which is (cx, cy)). A larger factor
    # pushes items toward the outer edge of each circle so they sit clear
    # of the central intersection text and leave room for outside labels.
    # Top circle: offset upward
    # Bottom-left: offset down-left
    # Bottom-right: offset down-right
    exclusive_factor = 0.70

    def _place_items(items, anchor_x, anchor_y):
        start_y = anchor_y - (len(items) - 1) * line_h / 2
        for i, item in enumerate(items):
            elements.append(svg_text(
                anchor_x, start_y + i * line_h, item,
                font_family=font, font_size=font_size,
                fill=text_col, anchor='middle'
            ))

    if len(sets) >= 1:
        top_items = sets[0].get('items', [])
        if top_items:
            # Direction from centroid to top circle centre is (0, -offset)
            ex = top_cx
            ey = top_cy - r * exclusive_factor
            _place_items(top_items, ex, ey)

    if len(sets) >= 2:
        bl_items = sets[1].get('items', [])
        if bl_items:
            # Direction from centroid to bl circle centre: (-0.866, +0.5)
            ex = bl_cx - r * exclusive_factor * 0.866
            ey = bl_cy + r * exclusive_factor * 0.5
            _place_items(bl_items, ex, ey)

    if len(sets) >= 3:
        br_items = sets[2].get('items', [])
        if br_items:
            # Direction from centroid to br circle centre: (+0.866, +0.5)
            ex = br_cx + r * exclusive_factor * 0.866
            ey = br_cy + r * exclusive_factor * 0.5
            _place_items(br_items, ex, ey)

    # Central 3-way intersection at container centre
    if intersection_items:
        start_y = cy - (len(intersection_items) - 1) * line_h / 2
        for i, item in enumerate(intersection_items):
            elements.append(svg_text(
                cx, start_y + i * line_h, item,
                font_family=font, font_size=font_size,
                fill=text_col, anchor='middle', weight='bold'
            ))

    return svg_group(elements, role='img', aria_label='Venn diagram')
