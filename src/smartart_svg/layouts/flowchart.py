"""Flowchart layout — sequential boxes connected by arrows.

Uses an optimal grid (1xN, 2x2, 2x3, 3x3) so the resulting graphic
fits the slide zone aspect ratio better than Mermaid's auto-layout.

Boxes contain a header line followed by item lines. Arrows connect
boxes in sequential order, including row-to-row "wrap" connections.
"""

from src.smartart_svg.primitives import svg_rect, svg_text, svg_group


def _grid_for(n):
    """Choose the rows/cols grid that best fits a 16:9 zone for N nodes."""
    if n <= 3:
        return (1, n)
    if n == 4:
        return (2, 2)
    if n <= 6:
        return (2, 3)
    if n <= 9:
        return (3, 3)
    # For larger N, fall back to 3 rows x ceil(n/3) cols
    cols = (n + 2) // 3
    return (3, cols)


def _split_header_items(text):
    """Split a body point into (header, [items]) on the first colon.

    'Phase 1 — Setup: Validate Brief, Brand Manager, Slide Stylist' →
    ('Phase 1 — Setup', ['Validate Brief', 'Brand Manager', 'Slide Stylist'])
    """
    if ':' in text:
        header, rest = text.split(':', 1)
        items = [it.strip() for it in rest.split(',') if it.strip()]
        return header.strip(), items
    return text.strip(), []


def render_flowchart(data, container, tokens):
    """Render a sequential flowchart as an SVG fragment.

    Data shape:
        {'nodes': ['Phase 1 — Setup: A, B, C', 'Phase 2 — Plan: D, E', ...]}

    Layout:
        - Auto-grid based on node count
        - Each cell holds one node (header + bullet items)
        - Arrows between adjacent cells in reading order (left-to-right,
          top-to-bottom, with wrap arrows back to the start of next row)
    """
    nodes = data.get('nodes', [])
    if not nodes:
        return svg_group([], role='img', aria_label='Empty flowchart')

    n = len(nodes)
    rows, cols = _grid_for(n)

    primary = tokens['primary_color']
    accent = tokens['accent_color']
    text_col_white = '#FFFFFF'
    font = tokens['font_family']
    heading_font = tokens['heading_font']
    rx = tokens.get('border_radius', 8)

    # Cell layout
    h_gap = 24
    v_gap = 36
    cell_w = (container.inner_width - h_gap * (cols - 1)) / cols
    cell_h = (container.inner_height - v_gap * (rows - 1)) / rows

    # Font sizing — scale with cell width
    header_font_size = max(13, min(18, int(cell_w / 14)))
    item_font_size = max(11, min(15, int(cell_w / 17)))
    line_h_header = header_font_size + 4
    line_h_item = item_font_size + 3
    padding_inside = 14

    elements = []
    cell_centers = []  # (cx, cy, x, y, w, h) per cell

    for i in range(n):
        row = i // cols
        col = i % cols
        x = container.inner_x + col * (cell_w + h_gap)
        y = container.inner_y + row * (cell_h + v_gap)

        # Box (filled with primary, orange border)
        elements.append(svg_rect(
            x, y, cell_w, cell_h, rx=rx,
            fill=primary, stroke=accent
        ))

        # Header + items
        header, items = _split_header_items(nodes[i])
        # Limit items to what fits
        max_items = max(1, int((cell_h - 2 * padding_inside - line_h_header) / line_h_item))
        visible_items = items[:max_items]

        total_text_h = line_h_header + len(visible_items) * line_h_item
        text_top = y + (cell_h - total_text_h) / 2 + header_font_size

        # Header
        elements.append(svg_text(
            x + cell_w / 2, text_top,
            header,
            font_family=heading_font,
            font_size=header_font_size,
            fill=text_col_white,
            anchor='middle',
            weight='bold',
        ))

        # Items
        for j, item in enumerate(visible_items):
            iy = text_top + line_h_header + j * line_h_item
            elements.append(svg_text(
                x + cell_w / 2, iy,
                item,
                font_family=font,
                font_size=item_font_size,
                fill=text_col_white,
                anchor='middle',
            ))

        cell_centers.append((x + cell_w / 2, y + cell_h / 2, x, y, cell_w, cell_h))

    # Arrows in reading order
    arrow_marker = (
        '<defs><marker id="fc-arrow" markerWidth="10" markerHeight="7" '
        'refX="9" refY="3.5" orient="auto">'
        f'<polygon points="0 0, 10 3.5, 0 7" fill="{accent}"/></marker></defs>'
    )
    elements.insert(0, arrow_marker)

    for i in range(n - 1):
        cur = cell_centers[i]
        nxt = cell_centers[i + 1]
        cur_row = i // cols
        nxt_row = (i + 1) // cols
        if cur_row == nxt_row:
            # Same row → horizontal arrow from right of cur to left of nxt
            x1 = cur[2] + cur[4] + 2
            y1 = cur[1]
            x2 = nxt[2] - 2
            y2 = nxt[1]
            elements.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="{accent}" stroke-width="3" marker-end="url(#fc-arrow)"/>'
            )
        else:
            # Wrap to next row — two-segment orthogonal path:
            # 1) vertical down from bottom-center of last cell in the current row
            # 2) horizontal across to the top-center of the first cell in the new row
            # This avoids the visually-confusing diagonal that appears to go backward.
            seg_x = cur[0]                    # x stays at current cell center-x
            seg_y1 = cur[3] + cur[5] + 2     # bottom edge of current cell
            seg_y2 = nxt[3] - 2              # just above top edge of next cell
            seg_x2 = nxt[0]                  # center-x of next cell
            # Vertical leg (no arrowhead)
            elements.append(
                f'<line x1="{seg_x}" y1="{seg_y1}" x2="{seg_x}" y2="{seg_y2}" '
                f'stroke="{accent}" stroke-width="3"/>'
            )
            # Horizontal leg (arrowhead at destination)
            elements.append(
                f'<line x1="{seg_x}" y1="{seg_y2}" x2="{seg_x2}" y2="{seg_y2}" '
                f'stroke="{accent}" stroke-width="3" marker-end="url(#fc-arrow)"/>'
            )

    return svg_group(elements, role='img', aria_label='Flowchart diagram')
