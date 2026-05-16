"""Decision tree layout — 2-column 'if Q then A' rule list.

Renders a sequential decision tree as a list of question→outcome rows.
Each row has a diamond-shaped question block on the left, an arrow, and
a rectangular outcome block on the right.

This produces a 16:9-friendly graphic, in contrast to Mermaid's TB layout
which becomes a tall narrow strip when there are many cascading questions.
"""

from src.smartart_svg.primitives import svg_rect, svg_text, svg_group


def _truncate(text, max_chars):
    """Truncate text to max_chars with ellipsis if it exceeds the limit."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 1] + '…'


def render_decision_tree(data, container, tokens):
    """Render a decision tree as an SVG fragment.

    Data shape:
        {'rules': [
            {'question': 'Is the talk persuasive?', 'outcome': 'hook-body-callback-cta'},
            {'question': 'Is it problem-solving?', 'outcome': 'situation-complication-resolution'},
            ...
         ]}
    """
    rules = data.get('rules', [])
    if not rules:
        return svg_group([], role='img', aria_label='Empty decision tree')

    n = len(rules)
    primary = tokens['primary_color']
    accent = tokens['accent_color']
    text_col_white = '#FFFFFF'
    font = tokens['font_family']
    heading_font = tokens['heading_font']
    rx = tokens.get('border_radius', 8)

    # Layout: each rule is a row.
    row_gap = 8
    row_h = (container.inner_height - row_gap * (n - 1)) / n

    # Column widths: question (left), arrow gap, outcome (right)
    arrow_w = 56
    col_gap = 8
    available_w = container.inner_width - arrow_w - col_gap * 2
    q_w = available_w * 0.50
    o_w = available_w * 0.50

    q_x = container.inner_x
    arrow_x = q_x + q_w + col_gap
    o_x = arrow_x + arrow_w + col_gap

    # Font sizing — scale with row height
    q_font = max(13, min(18, int(row_h / 3)))
    o_font = max(13, min(18, int(row_h / 3)))
    # Max outcome chars before SVG viewBox right boundary is exceeded
    max_o_chars = int(o_w / (o_font * 0.6))

    elements = []

    # Arrow marker definition (once)
    arrow_marker = (
        '<defs><marker id="dt-arrow" markerWidth="10" markerHeight="7" '
        'refX="9" refY="3.5" orient="auto">'
        f'<polygon points="0 0, 10 3.5, 0 7" fill="{accent}"/></marker></defs>'
    )
    elements.append(arrow_marker)

    for i, rule in enumerate(rules):
        question = rule.get('question', '')
        outcome = rule.get('outcome', '')
        row_y = container.inner_y + i * (row_h + row_gap)
        cy = row_y + row_h / 2

        # Question box (rounded rect, primary fill, accent border)
        elements.append(svg_rect(
            q_x, row_y, q_w, row_h, rx=rx,
            fill=primary, stroke=accent
        ))
        elements.append(svg_text(
            q_x + q_w / 2, cy + q_font / 3,
            question,
            font_family=heading_font,
            font_size=q_font,
            fill=text_col_white,
            anchor='middle',
            weight='bold',
        ))

        # Arrow with "Yes" label
        ax1 = q_x + q_w + 4
        ax2 = o_x - 4
        elements.append(
            f'<line x1="{ax1}" y1="{cy}" x2="{ax2}" y2="{cy}" '
            f'stroke="{accent}" stroke-width="3" marker-end="url(#dt-arrow)"/>'
        )
        elements.append(svg_text(
            (ax1 + ax2) / 2, cy - 6,
            'Yes',
            font_family=font,
            font_size=max(11, q_font - 4),
            fill=accent,
            anchor='middle',
            weight='bold',
        ))

        # Outcome box
        elements.append(svg_rect(
            o_x, row_y, o_w, row_h, rx=rx,
            fill=accent, stroke=primary
        ))
        elements.append(svg_text(
            o_x + o_w / 2, cy + o_font / 3,
            _truncate(outcome, max_o_chars),
            font_family=font,
            font_size=o_font,
            fill=text_col_white,
            anchor='middle',
        ))

    return svg_group(elements, role='img', aria_label='Decision tree diagram')
