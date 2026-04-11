"""Pipeline funnel layout — tapered bars proportional to stage values."""


from src.smartart_svg.engine import Container
from src.smartart_svg.primitives import svg_rect, svg_text, svg_group


def _interpolate_colour(hex1, hex2, t):
    """Linearly interpolate between two hex colours. t in [0, 1]."""
    def _parse(h):
        h = h.lstrip('#')
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    r1, g1, b1 = _parse(hex1)
    r2, g2, b2 = _parse(hex2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f'#{r:02x}{g:02x}{b:02x}'


def _wrap_label(label, max_chars, allow_hard_break=True):
    """Word-wrap a label into lines no longer than max_chars characters.

    If allow_hard_break is False and a single word exceeds max_chars, returns
    None (the caller should treat this as 'doesn't fit').
    """
    if max_chars <= 0:
        return [label]
    words = label.split()
    if not words:
        return [label]
    lines = []
    current = ''
    for word in words:
        if len(word) > max_chars:
            if not allow_hard_break:
                return None
            if current:
                lines.append(current)
                current = ''
            for i in range(0, len(word), max_chars):
                lines.append(word[i:i + max_chars])
            continue
        candidate = (current + ' ' + word).strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _try_fit_inside_bar(label, bar_w, max_height_for_label, base_font=16, min_font=12):
    """Try to fit 'label' inside a bar of width bar_w (points).

    Returns (font_size, lines) if a layout from base_font down to min_font
    fits within bar_w (each line) AND max_height_for_label (total). Returns
    None if no font down to min_font fits.

    min_font is 12pt to satisfy the PA-03 minimum-font check.
    """
    horizontal_padding = 10  # breathing room either side
    available_w = max(1, bar_w - horizontal_padding)

    for font_size in range(base_font, min_font - 1, -1):
        char_w = font_size * 0.55
        line_h = font_size + 2
        max_chars = max(1, int(available_w / char_w))
        lines = _wrap_label(label, max_chars, allow_hard_break=False)
        if lines is None:
            # A word didn't fit — this font size is too big for the bar.
            continue
        max_line_w = max((len(line) * char_w for line in lines), default=0)
        if max_line_w > available_w:
            continue
        total_h = len(lines) * line_h
        if total_h <= max_height_for_label:
            return font_size, lines

    return None


def render_pipeline_funnel(data, container, tokens):
    """Render a pipeline funnel as an SVG fragment.

    Tapered bars proportional to stage value / max value (floor 8%) so the
    funnel narrowing is always visually present.

    Label placement:
    - If the label fits inside the bar at >=12pt with multi-line wrapping,
      render inside in white.
    - Otherwise render the label OUTSIDE the bar (to the right) in dark text
      with a small leader line. The bar still tapers and the value sits
      inside the bar in white.

    The 12pt minimum honours the PA-03 pre-assembly font-size check.
    """
    stages = data.get('stages', [])
    if not stages:
        return svg_group([], role='img', aria_label='Empty funnel')

    n = len(stages)
    primary = tokens['primary_color']
    accent = tokens['accent_color']
    text_col_dark = tokens.get('text_color', '#1A1A1A')
    font = tokens['font_family']
    heading_font = tokens['heading_font']
    rx = tokens.get('border_radius', 8)

    values = [s.get('value', 1) for s in stages]
    max_val = max(values) if values else 1

    rows = container.split_vertical([1] * n, gap=8)

    elements = []

    val_font_size = 12
    val_line_h = val_font_size + 4
    label_base_font = 16
    label_min_font = 12

    for i, (stage, row) in enumerate(zip(stages, rows)):
        label = stage.get('label', '')
        value = stage.get('value', 0)

        t = i / max(n - 1, 1)
        fill = _interpolate_colour(primary, accent, t)

        ratio = value / max_val if max_val > 0 else 1.0
        # Floor at 8% so even the narrowest stage still has a visible bar.
        effective_ratio = max(0.08, ratio)
        bar_w = row.inner_width * effective_ratio
        bar_x = row.inner_x + (row.inner_width - bar_w) / 2
        bar_y = row.inner_y
        bar_h = row.inner_height

        # Bar
        elements.append(svg_rect(bar_x, bar_y, bar_w, bar_h, rx=rx, fill=fill))

        white = '#FFFFFF'
        bar_cx = bar_x + bar_w / 2

        # Reserve a value strip at the bottom of every bar (always visible
        # inside the bar in white).
        padding_v = 6
        available_h_for_label = max(10, bar_h - val_line_h - 2 * padding_v)

        fit = _try_fit_inside_bar(
            label, bar_w, available_h_for_label,
            base_font=label_base_font, min_font=label_min_font,
        )

        if fit is not None:
            # Inside the bar: white wrapped label centred, value below.
            adaptive_size, lines = fit
            n_lines = len(lines)
            line_h = adaptive_size + 2
            descender = int(val_font_size * 0.3)
            # Visual span from top of first glyph to bottom of value descender:
            #   font_size (first ascender) + (n-1)*line_h + val_line_h + descender
            visual_span = adaptive_size + (n_lines - 1) * line_h + val_line_h + descender
            top_pad = max(2, (bar_h - visual_span) / 2)
            first_baseline = bar_y + top_pad + adaptive_size

            for li, line in enumerate(lines):
                elements.append(svg_text(
                    bar_cx, first_baseline + li * line_h,
                    line,
                    font_family=heading_font,
                    font_size=adaptive_size,
                    fill=white,
                    anchor='middle',
                    weight='bold',
                ))
            value_baseline = first_baseline + (n_lines - 1) * line_h + val_line_h
            elements.append(svg_text(
                bar_cx, value_baseline,
                str(value),
                font_family=font,
                font_size=val_font_size,
                fill=white,
                anchor='middle',
            ))
        else:
            # Bar is too narrow even at 12pt: render label OUTSIDE the bar.
            # The value sits inside the bar in white; the descriptive label
            # sits to the right of the bar in dark text on cream background.
            elements.append(svg_text(
                bar_cx, bar_y + bar_h / 2 + val_font_size / 3,
                str(value),
                font_family=font,
                font_size=val_font_size,
                fill=white,
                anchor='middle',
                weight='bold',
            ))
            # Choose right or left side based on which side has more room.
            # Right side from bar's right edge to container right edge.
            right_room = (row.inner_x + row.inner_width) - (bar_x + bar_w)
            left_room = bar_x - row.inner_x
            if right_room >= left_room:
                outside_x = bar_x + bar_w + 8
                outside_w = max(40, right_room - 12)
                anchor = 'start'
                leader_x1 = bar_x + bar_w
                leader_x2 = outside_x - 4
            else:
                outside_x = bar_x - 8
                outside_w = max(40, left_room - 12)
                anchor = 'end'
                leader_x1 = bar_x
                leader_x2 = outside_x + 4

            # Wrap the outside label so each line fits in outside_w
            outside_font = label_min_font
            char_w = outside_font * 0.55
            outside_max_chars = max(8, int(outside_w / char_w))
            outside_lines = _wrap_label(label, outside_max_chars)
            line_h = outside_font + 2
            total_h = len(outside_lines) * line_h
            outside_top = bar_y + (bar_h - total_h) / 2 + outside_font

            # Leader line from bar edge to label start
            leader_y = bar_y + bar_h / 2
            elements.append(
                f'<line x1="{leader_x1}" y1="{leader_y}" x2="{leader_x2}" y2="{leader_y}" '
                f'stroke="{text_col_dark}" stroke-width="1"/>'
            )

            for li, line in enumerate(outside_lines):
                elements.append(svg_text(
                    outside_x, outside_top + li * line_h,
                    line,
                    font_family=heading_font,
                    font_size=outside_font,
                    fill=text_col_dark,
                    anchor=anchor,
                    weight='bold',
                ))

    return svg_group(elements, role='img', aria_label='Pipeline funnel diagram')
