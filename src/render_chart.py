"""Chart renderer — Matplotlib/Seaborn charts at 300 DPI styled to brand palette.

Renders publication-quality data visualisations for presentation slides.
Uses the Agg backend (no display server needed). Charts are styled to
the brand palette from the StyleGuide contract.

Supported chart types (from SlideOutline data.chart_type enum):
  bar, line, area, pie, donut, scatter
"""

import hashlib
import os
import uuid

import matplotlib
matplotlib.use('Agg')  # Must be before pyplot import
import matplotlib.pyplot as plt
from PIL import Image

SUPPORTED_CHART_TYPES = {'bar', 'line', 'area', 'pie', 'donut', 'scatter'}

# Default brand colours used when no StyleGuide is provided
_DEFAULT_COLOURS = [
    (0.169, 0.424, 0.690),   # #2B6CB0
    (0.929, 0.537, 0.212),   # #ED8936
    (0.220, 0.631, 0.412),   # #38A169
    (0.898, 0.243, 0.243),   # #E53E3E
    (0.502, 0.353, 0.835),   # #805AD5
]


def render_chart(chart_type, data, output_path, style_guide=None,
                 width=1920, height=1080, dpi=300):
    """Render a chart to a PNG file.

    Args:
        chart_type: One of 'bar', 'line', 'area', 'pie', 'donut', 'scatter'.
        data: Dict with chart-specific data:
            - bar/line/area/scatter: {'labels': [...], 'values': [...]}
              or {'labels': [...], 'series': {'name1': [...], 'name2': [...]}}
            - pie/donut: {'labels': [...], 'values': [...]}
        output_path: Where to save the PNG.
        style_guide: Optional StyleGuide dict. If provided, uses palette.chart_series
                     for colours and typography fonts for labels.
        width: Output width in pixels (default 1920).
        height: Output height in pixels (default 1080).
        dpi: Output DPI (default 300).

    Returns:
        dict: ChartManifest entry with keys:
            chart_id, file_path, chart_type, status, dimensions,
            alt_text, content_hash
    """
    if chart_type not in SUPPORTED_CHART_TYPES:
        raise ValueError(
            f"Unsupported chart_type '{chart_type}'. "
            f"Must be one of: {', '.join(sorted(SUPPORTED_CHART_TYPES))}. "
            f"Check the chart_type argument."
        )

    w_inches = width / dpi
    h_inches = height / dpi

    fig, ax = plt.subplots(figsize=(w_inches, h_inches), dpi=dpi)

    colours = _resolve_colours(style_guide)

    if chart_type == 'bar':
        _render_bar(ax, data, colours)
    elif chart_type == 'line':
        _render_line(ax, data, colours)
    elif chart_type == 'area':
        _render_area(ax, data, colours)
    elif chart_type in ('pie', 'donut'):
        _render_pie(ax, data, colours, donut=(chart_type == 'donut'))
    elif chart_type == 'scatter':
        _render_scatter(ax, data, colours)

    _apply_brand_style(fig, ax, style_guide)

    fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)

    # Read actual pixel dimensions from the saved file
    with Image.open(output_path) as img:
        actual_width, actual_height = img.size

    content_hash = _sha256_file(output_path)
    chart_id = _derive_chart_id(output_path, chart_type)
    alt_text = _generate_alt_text(chart_type, data)

    return {
        'chart_id': chart_id,
        'file_path': output_path,
        'chart_type': chart_type,
        'status': 'rendered',
        'dimensions': {
            'width': int(actual_width),
            'height': int(actual_height),
        },
        'alt_text': alt_text,
        'content_hash': content_hash,
    }


# ---------------------------------------------------------------------------
# Chart-type renderers
# ---------------------------------------------------------------------------

def _render_bar(ax, data, colours):
    """Render a bar chart (single or multi-series grouped bars)."""
    if 'series' in data:
        series = data['series']
        labels = data['labels']
        n_groups = len(labels)
        n_series = len(series)
        import numpy as np
        x = np.arange(n_groups)
        bar_width = 0.8 / n_series
        for i, (name, values) in enumerate(series.items()):
            colour = colours[i % len(colours)]
            offset = (i - n_series / 2 + 0.5) * bar_width
            ax.bar(x + offset, values, width=bar_width, label=name, color=colour)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
    else:
        labels = data['labels']
        values = data['values']
        bar_colours = [colours[i % len(colours)] for i in range(len(labels))]
        ax.bar(labels, values, color=bar_colours)


def _render_line(ax, data, colours):
    """Render a line chart (single or multi-series)."""
    if 'series' in data:
        labels = data['labels']
        for i, (name, values) in enumerate(data['series'].items()):
            colour = colours[i % len(colours)]
            ax.plot(labels, values, label=name, color=colour, linewidth=2)
        ax.legend()
    else:
        labels = data['labels']
        values = data['values']
        ax.plot(labels, values, color=colours[0], linewidth=2)


def _render_area(ax, data, colours):
    """Render an area chart (single or multi-series stacked)."""
    if 'series' in data:
        labels = data['labels']
        for i, (name, values) in enumerate(data['series'].items()):
            colour = colours[i % len(colours)]
            ax.fill_between(range(len(labels)), values, alpha=0.5,
                            color=colour, label=name)
            ax.plot(range(len(labels)), values, color=colour, linewidth=1.5)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels)
        ax.legend()
    else:
        labels = data['labels']
        values = data['values']
        ax.fill_between(range(len(labels)), values, alpha=0.6, color=colours[0])
        ax.plot(range(len(labels)), values, color=colours[0], linewidth=1.5)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels)


def _render_pie(ax, data, colours, donut=False):
    """Render a pie or donut chart."""
    labels = data['labels']
    values = data['values']
    pie_colours = [colours[i % len(colours)] for i in range(len(labels))]
    wedge_props = {'width': 0.4} if donut else {}
    ax.pie(values, labels=labels, colors=pie_colours,
           autopct='%1.1f%%', wedgeprops=wedge_props)
    ax.set_aspect('equal')


def _render_scatter(ax, data, colours):
    """Render a scatter chart (index as x, values as y)."""
    labels = data['labels']
    values = data['values']
    x = list(range(len(values)))
    ax.scatter(x, values, color=colours[0], s=80, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)


# ---------------------------------------------------------------------------
# Styling helpers
# ---------------------------------------------------------------------------

def _apply_brand_style(fig, ax, style_guide):
    """Apply brand palette and typography from StyleGuide to a chart."""
    if style_guide is None:
        return

    typography = style_guide.get('typography', {})
    palette = style_guide.get('palette', {})

    heading_font = typography.get('heading_font', None)
    body_font = typography.get('body_font', None)
    body_size = typography.get('body_size', 12)

    # Background colour
    bg_hex = palette.get('background', None)
    if bg_hex:
        r, g, b = _hex_to_rgb_normalised(bg_hex)
        fig.patch.set_facecolor((r, g, b))
        ax.set_facecolor((r, g, b))

    # Text colour
    text_hex = palette.get('text_primary', None)
    if text_hex:
        r, g, b = _hex_to_rgb_normalised(text_hex)
        text_colour = (r, g, b)
        ax.tick_params(colors=text_colour, labelsize=body_size)
        for spine in ax.spines.values():
            spine.set_edgecolor(text_colour)
        if body_font:
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontfamily(body_font)


def _hex_to_rgb_normalised(hex_str):
    """Convert 6-char hex string to matplotlib-compatible (r, g, b) tuple (0.0-1.0)."""
    hex_str = hex_str.lstrip('#')
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0
    return r, g, b


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------

def _resolve_colours(style_guide):
    """Return a list of normalised RGB tuples from the style guide, or defaults."""
    if style_guide is None:
        return _DEFAULT_COLOURS
    chart_series = style_guide.get('palette', {}).get('chart_series', [])
    if not chart_series:
        return _DEFAULT_COLOURS
    return [_hex_to_rgb_normalised(h) for h in chart_series]


def _sha256_file(path):
    """Return the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _derive_chart_id(output_path, chart_type):
    """Derive a chart_id from the output filename and chart_type."""
    basename = os.path.splitext(os.path.basename(output_path))[0]
    return f"chart-{chart_type}-{basename}"


def _generate_alt_text(chart_type, data):
    """Auto-generate alt text from chart_type and labels."""
    labels = data.get('labels', [])
    if labels:
        label_str = ', '.join(str(l) for l in labels)
        return f"{chart_type.capitalize()} chart showing {label_str}"
    return f"{chart_type.capitalize()} chart"
