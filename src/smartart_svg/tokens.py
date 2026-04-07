"""StyleGuide to SVG attribute mapping + WCAG contrast resolver."""


def _hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))


def _relative_luminance(rgb):
    """WCAG 2.2 relative luminance from sRGB."""
    vals = []
    for c in rgb:
        s = c / 255.0
        vals.append(s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4)
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def _contrast_ratio(hex1, hex2):
    l1 = _relative_luminance(_hex_to_rgb(hex1))
    l2 = _relative_luminance(_hex_to_rgb(hex2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def resolve_text_colour(background_colour, preferred_colour, style_guide):
    """Return preferred_colour if WCAG contrast passes, else fallback to white or black."""
    ratio = _contrast_ratio(background_colour, preferred_colour)
    if ratio >= 4.5:
        return preferred_colour
    white_ratio = _contrast_ratio(background_colour, '#ffffff')
    black_ratio = _contrast_ratio(background_colour, '#000000')
    return '#ffffff' if white_ratio > black_ratio else '#000000'


def extract_style_tokens(style_guide):
    """Map StyleGuide fields to flat token dict for SVG rendering."""
    palette = style_guide.get('palette', {})
    typo = style_guide.get('typography', {})
    series = palette.get('chart_series', [])
    return {
        'primary_color': '#' + palette.get('primary', '1a73e8'),
        'accent_color': '#' + palette.get('accent', 'e8710a'),
        'background_color': '#' + palette.get('background', 'ffffff'),
        'text_color': '#' + palette.get('text_primary', '1a1a1a'),
        'font_family': typo.get('body_font', 'sans-serif'),
        'heading_font': typo.get('heading_font', 'sans-serif'),
        'chart_series': ['#' + c for c in series],
        'border_radius': style_guide.get('image_style_tokens', {}).get('border_radius', 8),
    }
