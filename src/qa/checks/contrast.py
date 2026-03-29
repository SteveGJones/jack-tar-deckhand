"""Contrast and colour QA checks.

Implements AP-07 (Low Contrast), AP-08 (Clashing Colours),
AP-25 (Colourblind Safety).

Detection algorithms from: research/07-qa-heuristics-anti-patterns.md
"""

import colorsys
from ..config import QA_CONFIG


def relative_luminance(r, g, b):
    """Calculate relative luminance per WCAG 2.0."""
    def linearize(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(rgb1, rgb2):
    """Calculate WCAG contrast ratio between two RGB tuples."""
    l1 = relative_luminance(*rgb1)
    l2 = relative_luminance(*rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def simulate_deuteranopia(r, g, b):
    """Simplified deuteranopia simulation (Brettel et al.)."""
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    rl, gl, bl = lin(r), lin(g), lin(b)
    r2 = 0.625 * rl + 0.375 * gl + 0.0 * bl
    g2 = 0.7 * rl + 0.3 * gl + 0.0 * bl
    b2 = 0.0 * rl + 0.3 * gl + 0.7 * bl

    def delin(c):
        c = max(0, min(1, c))
        return int((c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1/2.4) - 0.055) * 255)

    return (delin(r2), delin(g2), delin(b2))


def check_contrast(slide, slide_number, config=None):
    """AP-07: Check text-to-background contrast ratio."""
    cfg = config or QA_CONFIG
    min_ratio = cfg['min_contrast_ratio']
    issues = []

    # Get slide background colour (default white)
    bg_color = (255, 255, 255)
    try:
        bg = slide.background
        if bg.fill.type is not None:
            bg_rgb = bg.fill.fore_color.rgb
            bg_color = (bg_rgb[0], bg_rgb[1], bg_rgb[2])
    except Exception:
        pass

    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if run.font.color and run.font.color.rgb:
                        fg = run.font.color.rgb
                        fg_color = (fg[0], fg[1], fg[2])
                        ratio = contrast_ratio(fg_color, bg_color)
                        if ratio < min_ratio:
                            issues.append({
                                'slide_number': slide_number,
                                'severity': 'error',
                                'category': 'contrast',
                                'description': f'Contrast ratio {ratio:.1f}:1 below {min_ratio}:1',
                                'suggested_fix': 'Use higher contrast text/background combination.',
                                'affected_element': shape.name,
                                'auto_fixable': True,
                            })
    return issues


def check_clashing_colours(colours_used, config=None):
    """AP-08: Check for colour pairs that clash."""
    issues = []
    colour_list = list(colours_used)
    for i in range(len(colour_list)):
        for j in range(i + 1, len(colour_list)):
            h1, s1, v1 = colorsys.rgb_to_hsv(
                colour_list[i][0] / 255.0, colour_list[i][1] / 255.0, colour_list[i][2] / 255.0)
            h2, s2, v2 = colorsys.rgb_to_hsv(
                colour_list[j][0] / 255.0, colour_list[j][1] / 255.0, colour_list[j][2] / 255.0)
            hue_diff = abs(h1 - h2)
            if hue_diff > 0.5:
                hue_diff = 1.0 - hue_diff

            # Complementary at high saturation
            if 0.4 < hue_diff < 0.6 and s1 > 0.7 and s2 > 0.7:
                issues.append({
                    'slide_number': 0,
                    'severity': 'warning',
                    'category': 'contrast',
                    'description': 'Potentially clashing complementary colours at high saturation',
                    'suggested_fix': 'Desaturate one of the complementary pair.',
                    'affected_element': f'rgb{colour_list[i]} vs rgb{colour_list[j]}',
                    'auto_fixable': False,
                })

            # Red-green specifically
            is_red_i = (h1 > 0.95 or h1 < 0.05) and s1 > 0.5
            is_green_i = 0.25 < h1 < 0.42 and s1 > 0.5
            is_red_j = (h2 > 0.95 or h2 < 0.05) and s2 > 0.5
            is_green_j = 0.25 < h2 < 0.42 and s2 > 0.5
            if (is_red_i and is_green_j) or (is_green_i and is_red_j):
                issues.append({
                    'slide_number': 0,
                    'severity': 'error',
                    'category': 'contrast',
                    'description': 'Red-green colour combination detected',
                    'suggested_fix': 'Replace red-green with blue-orange or another colourblind-safe pair.',
                    'affected_element': f'rgb{colour_list[i]} vs rgb{colour_list[j]}',
                    'auto_fixable': False,
                })
    return issues


def check_colourblind_safety(colours_used, config=None):
    """AP-25: Check colours remain distinguishable under CVD simulation."""
    cfg = config or QA_CONFIG
    min_distance = cfg['colourblind_min_distance']
    issues = []
    colour_list = list(colours_used)
    for i in range(len(colour_list)):
        for j in range(i + 1, len(colour_list)):
            sim_i = simulate_deuteranopia(*colour_list[i])
            sim_j = simulate_deuteranopia(*colour_list[j])
            dist = sum((a - b) ** 2 for a, b in zip(sim_i, sim_j)) ** 0.5
            if dist < min_distance:
                issues.append({
                    'slide_number': 0,
                    'severity': 'warning',
                    'category': 'accessibility',
                    'description': f'Colours {colour_list[i]} and {colour_list[j]} may be indistinguishable for deuteranopia viewers (distance: {dist:.0f})',
                    'suggested_fix': 'Use blue-orange instead of red-green. Add patterns for redundant encoding.',
                    'affected_element': 'palette',
                    'auto_fixable': False,
                })
    return issues
