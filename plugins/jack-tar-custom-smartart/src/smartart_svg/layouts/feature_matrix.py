"""Feature matrix layout — rows x columns grid with ✓/✗ indicators."""

from src.smartart_svg.engine import Container
from src.smartart_svg.primitives import svg_rect, svg_text, svg_group
from src.smartart_svg.tokens import resolve_text_colour

_MIN_COL_WIDTH = 50


def render_feature_matrix(data, container, tokens):
    """Render a feature matrix as an SVG fragment.

    Row 0 = column headers. Column 0 = row labels.
    Inner cells show ✓ / ✗ for boolean values, raw string for others.
    When columns exceed available width at min column width, excess
    columns are dropped and a '+N...' overflow indicator is shown.
    """
    columns = data.get('columns', [])
    rows = data.get('rows', [])

    label_col_width = max(80, container.inner_width * 0.15)
    available_for_data = container.inner_width - label_col_width
    max_data_cols = max(1, int(available_for_data / _MIN_COL_WIDTH))

    truncated = len(columns) > max_data_cols
    if truncated:
        n_real = max_data_cols - 1
        visible_columns = columns[:n_real]
        overflow_label = f"+{len(columns) - n_real}..."
    else:
        visible_columns = columns
        n_real = len(visible_columns)
        overflow_label = None

    display_columns = visible_columns + ([overflow_label] if truncated else [])

    num_rows = len(rows) + 1
    num_cols = len(display_columns) + 1

    cells = container.split_grid(num_rows, num_cols, gap=2)

    primary = tokens['primary_color']
    text_col = tokens['text_color']

    elements = []

    def cell_at(row, col):
        return cells[row * num_cols + col]

    # Header row
    for col_idx, col_label in enumerate(display_columns):
        c = cell_at(0, col_idx + 1)
        elements.append(svg_rect(c.x, c.y, c.width, c.height, fill=primary, rx=4))
        header_text_col = resolve_text_colour(primary, '#ffffff', None)
        fitted = c.fit_text(col_label, font_size=13, max_lines=2)
        cx, cy = c.center_point()
        elements.append(svg_text(
            cx, cy + fitted.font_size / 2,
            col_label,
            font_family=tokens['heading_font'],
            font_size=fitted.font_size,
            fill=header_text_col,
            anchor='middle',
            weight='bold'
        ))

    # Top-left corner
    corner = cell_at(0, 0)
    elements.append(svg_rect(corner.x, corner.y, corner.width, corner.height, fill=primary, rx=4))

    # Data rows
    for row_idx, row in enumerate(rows):
        row_label = row.get('label', '')
        values = row.get('values', [])
        actual_row = row_idx + 1

        tint = 'rgba(26,115,232,0.06)' if row_idx % 2 == 0 else 'rgba(0,0,0,0)'
        row_cells_start = actual_row * num_cols
        first_cell = cells[row_cells_start]
        last_cell = cells[row_cells_start + num_cols - 1]
        row_w = last_cell.x + last_cell.width - first_cell.x
        elements.append(svg_rect(first_cell.x, first_cell.y, row_w, first_cell.height, fill=tint))

        # Row label — allow 2 lines and use fitted text (may truncate)
        lc = cell_at(actual_row, 0)
        fitted = lc.fit_text(row_label, font_size=13, max_lines=2)
        lx, ly = lc.center_point()
        # Render each fitted line
        n_lines = len(fitted.lines)
        line_h = fitted.font_size + 2
        start_ly = ly - (n_lines - 1) * line_h / 2 + fitted.font_size * 0.35
        for li, line in enumerate(fitted.lines):
            elements.append(svg_text(
                lx, start_ly + li * line_h,
                line,
                font_family=tokens['font_family'],
                font_size=fitted.font_size,
                fill=text_col,
                anchor='middle',
                weight='bold'
            ))

        # Value cells
        for col_idx in range(n_real):
            if col_idx >= len(values):
                break
            value = values[col_idx]
            vc = cell_at(actual_row, col_idx + 1)
            vx, vy = vc.center_point()
            if isinstance(value, bool):
                symbol = '\u2713' if value else '\u2717'
                symbol_colour = '#38A169' if value else '#E53E3E'
                elements.append(svg_text(
                    vx, vy + 8, symbol,
                    font_family=tokens['font_family'], font_size=18,
                    fill=symbol_colour, anchor='middle', weight='bold'
                ))
            else:
                cell_val = str(value)
                fitted = vc.fit_text(cell_val, font_size=13, max_lines=1)
                elements.append(svg_text(
                    vx, vy + fitted.font_size / 2, cell_val,
                    font_family=tokens['font_family'], font_size=fitted.font_size,
                    fill=text_col, anchor='middle'
                ))

        # Overflow indicator cell
        if truncated:
            oc = cell_at(actual_row, num_cols - 1)
            ox, oy = oc.center_point()
            elements.append(svg_text(
                ox, oy + 6, '...',
                font_family=tokens['font_family'], font_size=14,
                fill=text_col, anchor='middle'
            ))

    return svg_group(elements, role='img', aria_label='Feature matrix diagram')
