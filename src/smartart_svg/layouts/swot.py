"""SWOT analysis layout — 2x2 quadrant grid with coloured backgrounds."""

from src.smartart_svg.engine import Container
from src.smartart_svg.primitives import svg_rect, svg_text, svg_group
from src.smartart_svg.tokens import resolve_text_colour


def render_swot(data, container, tokens):
    """Render a SWOT diagram as an SVG fragment.

    Splits the container into a title row and 2x2 grid. Each quadrant gets a
    background colour from chart_series and renders label + bullet items.
    """
    quadrants = data.get('quadrants', [])

    # Split: small top title bar + body grid area
    sections = container.split_vertical([1, 9], gap=8)
    title_area = sections[0]
    body_area = sections[1]

    # Title
    tx, ty = title_area.center_point()
    title_el = svg_text(
        tx, ty + 6, 'SWOT Analysis',
        font_family=tokens['heading_font'],
        font_size=28,
        fill=tokens['text_color'],
        anchor='middle',
        weight='bold'
    )

    # 2x2 grid for the 4 quadrants
    cells = body_area.split_grid(2, 2, gap=16)

    # Map position strings to cell index
    position_map = {
        'top_left': 0,
        'top_right': 1,
        'bottom_left': 2,
        'bottom_right': 3,
    }

    # Default ordering if position not specified
    quadrant_by_position = {}
    for i, q in enumerate(quadrants):
        pos = q.get('position', list(position_map.keys())[i % 4])
        idx = position_map.get(pos, i % 4)
        quadrant_by_position[idx] = q

    series = tokens.get('chart_series', ['#2B6CB0', '#ED8936', '#38A169', '#E53E3E'])
    # Pad series to at least 4 colours
    while len(series) < 4:
        series = series + series

    quadrant_groups = []
    for idx, cell in enumerate(cells):
        q = quadrant_by_position.get(idx, {})
        label = q.get('label', '')
        items = q.get('items', [])
        bg_colour = series[idx % len(series)]

        elements = []

        # Background rect
        elements.append(svg_rect(
            cell.x, cell.y, cell.width, cell.height,
            rx=tokens.get('border_radius', 8),
            fill=bg_colour
        ))

        # Header background band
        header_h = 44
        elements.append(svg_rect(
            cell.x, cell.y, cell.width, header_h,
            rx=tokens.get('border_radius', 8),
            fill=bg_colour,
            stroke='rgba(0,0,0,0.15)'
        ))

        # Label text
        text_colour = resolve_text_colour(bg_colour, tokens['text_color'], None)
        elements.append(svg_text(
            cell.x + cell.width / 2,
            cell.y + 28,
            label,
            font_family=tokens['heading_font'],
            font_size=20,
            fill=text_colour,
            anchor='middle',
            weight='bold'
        ))

        # Bullet items — each on its own line
        item_font_size = 15
        line_height = item_font_size + 6
        start_y = cell.y + header_h + 20
        for j, item in enumerate(items):
            iy = start_y + j * line_height
            if iy + item_font_size > cell.y + cell.height:
                break
            bullet = '\u2022 ' + item
            elements.append(svg_text(
                cell.x + 12,
                iy,
                bullet,
                font_family=tokens['font_family'],
                font_size=item_font_size,
                fill=text_colour,
                anchor='start'
            ))

        quadrant_groups.append(svg_group(elements, aria_label=label))

    return svg_group([title_el] + quadrant_groups, role='img', aria_label='SWOT Analysis diagram')
