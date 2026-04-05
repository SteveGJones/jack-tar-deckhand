"""Radar/Spider chart layout — polar coordinate multi-axis comparison.

Renders a radar chart with N axes radiating from centre, data points
plotted along each axis, and a filled polygon connecting the values.
"""

import math

from src.smartart_svg.primitives import svg_circle, svg_text, svg_group, svg_rect
from src.smartart_svg.tokens import resolve_text_colour


def render_radar_chart(data, container, tokens):
    """Render a radar chart as an SVG fragment.

    Args:
        data: dict with 'series' list of {'label': str, 'value': number}
        container: Container for layout bounds
        tokens: Style tokens from extract_style_tokens()

    Returns:
        SVG fragment string
    """
    series = data.get('series', [])
    if not series:
        return ''

    n = len(series)
    max_value = max(item['value'] for item in series)
    if max_value == 0:
        max_value = 1

    # Layout: title at top, radar in centre
    title_h = container.inner_height * 0.08
    chart_region = container.inner_height - title_h
    cx, _ = container.center_point()
    cy = container.inner_y + title_h + chart_region / 2
    radius = min(chart_region / 2, container.inner_width / 2) * 0.7  # Leave room for labels

    elements = []

    # Background circle
    elements.append(svg_circle(cx, cy, radius, fill=tokens.get('background_color', '#ffffff'), opacity=0.3))

    # Concentric guide rings (at 25%, 50%, 75%, 100%)
    ring_color = tokens.get('text_color', '#1a1a1a')
    for pct in (0.25, 0.5, 0.75, 1.0):
        r = radius * pct
        elements.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
            f'stroke="{ring_color}" stroke-width="0.5" stroke-dasharray="2,2" opacity="0.3"/>'
        )

    # Axis lines and labels
    angle_step = 2 * math.pi / n
    label_font = tokens.get('font_family', 'sans-serif')
    label_size = 12  # points — PA-03 minimum
    label_color = tokens.get('text_color', '#1a1a1a')

    data_points = []

    for i, item in enumerate(series):
        angle = -math.pi / 2 + i * angle_step  # Start from top

        # Axis endpoint
        ax = cx + radius * math.cos(angle)
        ay = cy + radius * math.sin(angle)
        elements.append(
            f'<line x1="{cx}" y1="{cy}" x2="{ax}" y2="{ay}" '
            f'stroke="{ring_color}" stroke-width="0.5" opacity="0.4"/>'
        )

        # Data point
        value_ratio = item['value'] / max_value
        dx = cx + radius * value_ratio * math.cos(angle)
        dy = cy + radius * value_ratio * math.sin(angle)
        data_points.append((dx, dy))

        # Axis label (positioned outside the radar)
        label_radius = radius + 14
        lx = cx + label_radius * math.cos(angle)
        ly = cy + label_radius * math.sin(angle)

        # Anchor based on position
        if abs(math.cos(angle)) < 0.1:
            anchor = 'middle'
        elif math.cos(angle) > 0:
            anchor = 'start'
        else:
            anchor = 'end'

        # Adjust vertical position
        if math.sin(angle) > 0.3:
            ly += label_size * 0.8
        elif math.sin(angle) < -0.3:
            ly -= label_size * 0.3

        label_text = f"{item['label']}: {item['value']}"
        elements.append(svg_text(
            lx, ly, label_text,
            font_family=label_font, font_size=label_size,
            fill=label_color, anchor=anchor
        ))

    # Data polygon (filled)
    primary = tokens.get('primary_color', '#1B3A4B')
    if data_points:
        points_str = ' '.join(f'{x},{y}' for x, y in data_points)
        elements.append(
            f'<polygon points="{points_str}" fill="{primary}" fill-opacity="0.25" '
            f'stroke="{primary}" stroke-width="2"/>'
        )

        # Data point dots
        accent = tokens.get('accent_color', '#C67B2F')
        for dx, dy in data_points:
            elements.append(svg_circle(dx, dy, 4, fill=accent))

    return svg_group(elements, role='img', aria_label='Radar chart')
