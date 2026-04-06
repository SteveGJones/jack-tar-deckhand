"""Gantt chart layout — horizontal task bars on a date axis."""

from datetime import datetime, date

from src.smartart_svg.primitives import svg_rect, svg_text, svg_group


def _parse_date(s):
    """Parse a YYYY-MM-DD string to a date object."""
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _interpolate_colour(hex1, hex2, t):
    """Linearly interpolate between two hex colours."""
    def _parse(h):
        h = h.lstrip('#')
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r1, g1, b1 = _parse(hex1)
    r2, g2, b2 = _parse(hex2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f'#{r:02x}{g:02x}{b:02x}'


def _compute_label_width(parsed, container):
    """Compute dynamic label column width based on the longest task label.

    Returns at least 22% of container width and at most 40% to prevent the
    label column from dominating the chart area.
    """
    char_width = 13 * 0.6
    longest_label_chars = max((len(t['label']) for t in parsed), default=10)
    estimated_label_width = longest_label_chars * char_width + 12  # padding
    return max(
        container.inner_width * 0.22,
        min(container.inner_width * 0.40, estimated_label_width),
    )


def render_gantt(data, container, tokens):
    """Render a Gantt chart as an SVG fragment.

    Args:
        data: dict with:
            - 'tasks' list of {'label': str, 'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}
            - 'show_dates' bool (default True). When False, render a sequential
              bar layout with no date axis — suitable for logical sequences
              (handoffs, roadmap phases) rather than real schedules.
        container: Container for layout bounds
        tokens: Style tokens from extract_style_tokens()
    """
    show_dates = data.get('show_dates', True)
    if not show_dates:
        return _render_gantt_sequence(data, container, tokens)
    return _render_gantt_timeline(data, container, tokens)


def _render_gantt_timeline(data, container, tokens):
    """Render a Gantt chart with a real date axis."""
    tasks = data.get('tasks', [])
    if not tasks:
        return svg_group([], role='img', aria_label='Empty Gantt chart')

    parsed = []
    for t in tasks:
        s = _parse_date(t.get('start', ''))
        e = _parse_date(t.get('end', ''))
        if s and e:
            parsed.append({'label': t.get('label', ''), 'start': s, 'end': e})
    if not parsed:
        return svg_group([], role='img', aria_label='Gantt chart (no valid dates)')

    all_starts = [t['start'] for t in parsed]
    all_ends = [t['end'] for t in parsed]
    date_min = min(all_starts)
    date_max = max(all_ends)
    total_days = max(1, (date_max - date_min).days)

    # Layout regions
    title_h = container.inner_height * 0.08
    axis_h = 28
    label_w = _compute_label_width(parsed, container)
    chart_x = container.inner_x + label_w
    chart_y = container.inner_y + title_h
    chart_w = container.inner_width - label_w
    chart_h = container.inner_height - title_h - axis_h

    n = len(parsed)
    row_h = min(chart_h / n, 40)
    bar_h = row_h * 0.6
    gap = row_h * 0.2

    primary = tokens['primary_color']
    accent = tokens['accent_color']
    text_col = tokens['text_color']
    font = tokens['font_family']
    heading_font = tokens['heading_font']
    rx = tokens.get('border_radius', 4)

    elements = []

    for i, task in enumerate(parsed):
        row_y = chart_y + i * row_h + gap / 2

        label_x = container.inner_x + 4
        label_y = row_y + bar_h / 2 + 4
        elements.append(svg_text(
            label_x, label_y, task['label'],
            font_family=heading_font, font_size=13,
            fill=text_col, anchor='start', weight='bold'
        ))

        start_offset = (task['start'] - date_min).days / total_days
        end_offset = (task['end'] - date_min).days / total_days
        bar_x = chart_x + chart_w * start_offset
        bar_w = max(4, chart_w * (end_offset - start_offset))

        t_ratio = i / max(n - 1, 1)
        fill = _interpolate_colour(primary, accent, t_ratio)
        elements.append(svg_rect(bar_x, row_y, bar_w, bar_h, rx=rx, fill=fill))

        if i > 0:
            elements.append(svg_rect(chart_x, chart_y + i * row_h, chart_w, 1, fill=text_col))

    # Date axis
    axis_y = chart_y + chart_h + 4
    current = date(date_min.year, date_min.month, 1)
    while current <= date_max:
        day_offset = (current - date_min).days / total_days
        tick_x = chart_x + chart_w * day_offset
        if chart_x <= tick_x <= chart_x + chart_w:
            elements.append(svg_rect(tick_x, chart_y, 1, chart_h, fill=text_col))
            month_label = current.strftime('%b %y')
            elements.append(svg_text(
                tick_x + 2, axis_y + 12, month_label,
                font_family=font, font_size=12, fill=text_col, anchor='start'
            ))
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    return svg_group(elements, role='img', aria_label='Gantt chart')


def _render_gantt_sequence(data, container, tokens):
    """Render a Gantt-style chart as a sequential bar layout (no date axis).

    Used for logical sequences (handoffs, roadmap phases) where dates would
    falsely imply real timing. Each task takes a 1/N slice of the chart
    width, or proportional widths if a 'weight' field is provided.
    """
    tasks = data.get('tasks', [])
    if not tasks:
        return svg_group([], role='img', aria_label='Empty Gantt chart')

    parsed = []
    for t in tasks:
        parsed.append({
            'label': t.get('label', ''),
            'weight': float(t.get('weight', 1)),
        })

    n = len(parsed)
    if n == 0:
        return svg_group([], role='img', aria_label='Empty Gantt chart')

    # Layout regions — no axis, so reclaim that vertical space.
    title_h = container.inner_height * 0.08
    label_w = _compute_label_width(parsed, container)
    chart_x = container.inner_x + label_w
    chart_y = container.inner_y + title_h
    chart_w = container.inner_width - label_w
    chart_h = container.inner_height - title_h

    row_h = min(chart_h / n, 40)
    bar_h = row_h * 0.6
    gap = row_h * 0.2

    primary = tokens['primary_color']
    accent = tokens['accent_color']
    text_col = tokens['text_color']
    heading_font = tokens['heading_font']
    rx = tokens.get('border_radius', 4)

    total_weight = sum(t['weight'] for t in parsed) or float(n)
    use_weights = any(t['weight'] != 1 for t in parsed)

    elements = []

    for i, task in enumerate(parsed):
        row_y = chart_y + i * row_h + gap / 2

        label_x = container.inner_x + 4
        label_y = row_y + bar_h / 2 + 4
        elements.append(svg_text(
            label_x, label_y, task['label'],
            font_family=heading_font, font_size=13,
            fill=text_col, anchor='start', weight='bold'
        ))

        if use_weights:
            offset_units = sum(p['weight'] for p in parsed[:i])
            start_frac = offset_units / total_weight
            width_frac = task['weight'] / total_weight
        else:
            start_frac = i / n
            width_frac = 1.0 / n

        bar_x = chart_x + chart_w * start_frac
        bar_w = max(4, chart_w * width_frac * 0.9)

        t_ratio = i / max(n - 1, 1)
        fill = _interpolate_colour(primary, accent, t_ratio)
        elements.append(svg_rect(bar_x, row_y, bar_w, bar_h, rx=rx, fill=fill))

        if i > 0:
            elements.append(svg_rect(chart_x, chart_y + i * row_h, chart_w, 1, fill=text_col))

    return svg_group(elements, role='img', aria_label='Gantt chart (sequence)')
