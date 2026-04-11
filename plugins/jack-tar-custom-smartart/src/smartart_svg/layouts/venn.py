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

    Set labels are placed:
    - Top: above the top circle, clamped to canvas top
    - Bottom-left: BELOW the bottom-left circle (avoids horizontal collision with body items)
    - Bottom-right: BELOW the bottom-right circle
    """
    sets = data.get('sets', [])
    intersection = data.get('intersection', {})
    intersection_items = intersection.get('items', [])

    label_clearance = 8  # px clearance between circle edge and label
    label_font_size = 18

    # Reserve vertical space for top label (above top circle) and bottom labels (below bottom circles)
    label_band = label_font_size + label_clearance  # ~26pt band each
    drawable_h = container.inner_height - 2 * label_band

    # Triangle vertical span = (top_cy - r) to (bl_cy + r)
    # = (triangle_cy - offset - r) to (triangle_cy + 0.5*offset + r)
    # With offset = 0.55r: span = (1.55r) above + (1.275r) below = 2.825r total
    r_by_h = drawable_h / 2.83
    # Width constraint: 2*0.866*offset + 2r = 2*0.866*0.55r + 2r = 2.953r
    r_by_w = container.inner_width / 2.953
    r = min(r_by_h, r_by_w) * 0.95
    offset = r * 0.55

    cx = container.x + container.width / 2
    # Centre the (asymmetric) triangle within the drawable region.
    # Triangle vertical extent: 1.55r above triangle_cy, 1.275r below.
    # Centre of extent = triangle_cy + (1.275-1.55)/2 r = triangle_cy - 0.1375r
    triangle_cy = container.inner_y + label_band + drawable_h / 2 + 0.1375 * r

    # Triangle circle centres
    top_cx = cx
    top_cy = triangle_cy - offset
    bl_cx = cx - offset * 0.866
    bl_cy = triangle_cy + offset * 0.5
    br_cx = cx + offset * 0.866
    br_cy = triangle_cy + offset * 0.5

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

    # Set labels are placed in the reserved bands so they never collide with
    # body items inside the circles.
    # Top: above the top circle
    if len(sets) >= 1:
        top_label_y = max(container.inner_y + label_font_size,
                          top_cy - r - label_clearance)
        elements.append(svg_text(
            top_cx, top_label_y,
            sets[0].get('label', ''),
            font_family=heading_font, font_size=label_font_size,
            fill=text_col, anchor='middle', weight='bold'
        ))
    # Bottom-left: BELOW the bottom-left circle (no horizontal collision with body text)
    if len(sets) >= 2:
        bl_label_y = min(container.inner_y + container.inner_height - 4,
                         bl_cy + r + label_clearance + label_font_size)
        elements.append(svg_text(
            bl_cx, bl_label_y,
            sets[1].get('label', ''),
            font_family=heading_font, font_size=label_font_size,
            fill=text_col, anchor='middle', weight='bold'
        ))
    # Bottom-right: BELOW the bottom-right circle
    if len(sets) >= 3:
        br_label_y = min(container.inner_y + container.inner_height - 4,
                         br_cy + r + label_clearance + label_font_size)
        elements.append(svg_text(
            br_cx, br_label_y,
            sets[2].get('label', ''),
            font_family=heading_font, font_size=label_font_size,
            fill=text_col, anchor='middle', weight='bold'
        ))

    line_h = 14
    font_size = 12

    # Exclusive items: offset from each circle centre in the direction
    # OPPOSITE the triangle centroid (which is at triangle_cy). A smaller
    # factor keeps items closer to the circle centre, leaving room for
    # set labels at the outer edge of each circle.
    exclusive_factor = 0.45

    # Maximum characters per line so body items fit within their circle's
    # exclusive band without colliding with neighbouring circles' text.
    # The exclusive band width ≈ r (which is ~r=80pt). At font 12, char width
    # ≈ 6.6pt → ~12 chars per line max for safety.
    max_item_chars = max(10, int(r * 1.2 / (font_size * 0.55)))

    def _wrap_item(text):
        """Wrap a single body item into multiple lines if too long.

        Splits on em-dash (most natural break for "Topic — detail" patterns),
        else on whitespace.
        """
        if len(text) <= max_item_chars:
            return [text]
        # Try em-dash split first
        if '\u2014' in text:
            parts = text.split('\u2014', 1)
            head = parts[0].strip()
            tail = parts[1].strip()
            lines = [head]
            if tail:
                lines.append(tail)
            return lines
        # Word wrap
        words = text.split()
        lines = []
        current = ''
        for w in words:
            test = (current + ' ' + w).strip()
            if len(test) <= max_item_chars:
                current = test
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)
        return lines if lines else [text]

    def _place_items(items, anchor_x, anchor_y):
        # Expand each item into wrapped lines
        all_lines = []
        for item in items:
            all_lines.extend(_wrap_item(item))
        start_y = anchor_y - (len(all_lines) - 1) * line_h / 2
        for i, line in enumerate(all_lines):
            elements.append(svg_text(
                anchor_x, start_y + i * line_h, line,
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

    # Central 3-way intersection at the triangle's vertical centre
    if intersection_items:
        start_y = triangle_cy - (len(intersection_items) - 1) * line_h / 2
        for i, item in enumerate(intersection_items):
            elements.append(svg_text(
                cx, start_y + i * line_h, item,
                font_family=font, font_size=font_size,
                fill=text_col, anchor='middle', weight='bold'
            ))

    return svg_group(elements, role='img', aria_label='Venn diagram')
