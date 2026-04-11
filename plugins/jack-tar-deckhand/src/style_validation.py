"""StyleGuide validation utilities.

Validates StyleGuide outputs for contrast, completeness, and brand compliance.
Reuses contrast functions from src/qa/checks/contrast.py.
"""

import json
import os

import jsonschema

from src.qa.checks.contrast import relative_luminance, contrast_ratio

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schemas', 'style_guide.schema.json')

REQUIRED_LAYOUT_TEMPLATES = [
    'title', 'section_divider', 'content', 'two_column',
    'image_feature', 'data_chart', 'stat_callout', 'quote',
    'icon_grid', 'diagram', 'closing', 'blank_visual',
]

MIN_CONTRAST_NORMAL = 4.5
MIN_CONTRAST_PROJECTION = 7.0

CONTRAST_PAIRS = [
    ('text_primary', 'background', MIN_CONTRAST_PROJECTION),
    ('text_on_dark', 'background_alt', MIN_CONTRAST_PROJECTION),
    ('text_muted', 'background', MIN_CONTRAST_NORMAL),
]


def _hex_to_rgb(hex_str):
    """Convert 6-char hex string to (r, g, b) tuple."""
    return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))


def validate_style_guide(style_guide):
    """Validate a StyleGuide dict against the JSON schema. Returns list of error messages."""
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)
    return [e.message for e in validator.iter_errors(style_guide)]


def check_palette_contrast(palette):
    """Check that palette colour pairings meet contrast requirements. Returns list of issue strings."""
    issues = []
    for fg_key, bg_key, min_ratio in CONTRAST_PAIRS:
        fg_hex = palette.get(fg_key)
        bg_hex = palette.get(bg_key)
        if not fg_hex or not bg_hex:
            continue
        fg_rgb = _hex_to_rgb(fg_hex)
        bg_rgb = _hex_to_rgb(bg_hex)
        ratio = contrast_ratio(fg_rgb, bg_rgb)
        if ratio < min_ratio:
            issues.append(
                f'{fg_key} on {bg_key}: contrast {ratio:.1f}:1 below minimum {min_ratio}:1'
            )
    return issues


def check_completeness(style_guide):
    """Check that all required fields and templates are present. Returns list of issue strings."""
    issues = []
    templates = style_guide.get('layout', {}).get('templates', {})
    missing = [t for t in REQUIRED_LAYOUT_TEMPLATES if t not in templates]
    if missing:
        issues.append(f'Missing layout templates: {", ".join(missing)}')
    typography = style_guide.get('typography', {})
    if not typography.get('heading_font'):
        issues.append('Missing heading_font in typography')
    if not typography.get('body_font'):
        issues.append('Missing body_font in typography')
    palette = style_guide.get('palette', {})
    if not palette.get('chart_series'):
        issues.append('Missing chart_series in palette')
    return issues


def check_brand_compliance(style_guide, brand_profile):
    """Check StyleGuide compliance with BrandProfile. Returns list of issue strings."""
    if brand_profile.get('compliance_mode') != 'strict':
        return []
    issues = []
    bp_palette = brand_profile.get('palette', {})
    sg_palette = style_guide.get('palette', {})
    for key in ['primary', 'secondary']:
        bp_val = bp_palette.get(key)
        sg_val = sg_palette.get(key)
        if bp_val and sg_val and bp_val.lower() != sg_val.lower():
            issues.append(
                f'Strict compliance: palette.{key} is {sg_val} but brand mandates {bp_val}'
            )
    bp_typo = brand_profile.get('typography', {})
    sg_typo = style_guide.get('typography', {})
    for key in ['heading_font', 'body_font']:
        bp_val = bp_typo.get(key)
        sg_val = sg_typo.get(key)
        if bp_val and sg_val and bp_val != sg_val:
            issues.append(
                f'Strict compliance: typography.{key} is "{sg_val}" but brand mandates "{bp_val}"'
            )
    return issues
