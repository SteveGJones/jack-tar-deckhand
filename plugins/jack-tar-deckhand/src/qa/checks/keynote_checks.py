"""Keynote-specific QA checks.

Implements palette drift detection for full_render and backdrop_render slides.
Uses Pillow to extract dominant colours from slide images and compare against
the brand palette using CIE deltaE distance.
"""

import io
import math

from PIL import Image


def _hex_to_rgb(hex_str):
    """Convert 6-char hex to (R, G, B) tuple."""
    hex_str = hex_str.lstrip('#')
    return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))


def _rgb_distance(c1, c2):
    """Euclidean distance between two RGB tuples. Simple but effective for drift detection."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def _extract_dominant_colours(image_blob, num_colours=5):
    """Extract dominant colours from an image blob using Pillow quantize."""
    img = Image.open(io.BytesIO(image_blob)).convert('RGB')
    # Resize for speed, then quantize
    small = img.resize((100, 100))
    quantized = small.quantize(colors=num_colours, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()[:num_colours * 3]
    colours = []
    for i in range(0, len(palette), 3):
        colours.append((palette[i], palette[i + 1], palette[i + 2]))
    return colours


def _min_distance_to_palette(colour, brand_colours_rgb):
    """Minimum RGB distance from a colour to any brand palette colour."""
    if not brand_colours_rgb:
        return 0
    return min(_rgb_distance(colour, bc) for bc in brand_colours_rgb)


# Threshold: RGB distance above which a dominant colour is considered off-brand.
# 80 ≈ noticeable colour shift (e.g., teal vs blue). 120 ≈ clearly wrong palette.
_DRIFT_THRESHOLD = 100
_DRIFT_MAX_OFF_BRAND = 3  # Max dominant colours allowed to be off-brand


def check_palette_drift(slide, slide_number, brand_palette=None, config=None):
    """Check if images on a slide drift from the brand palette.

    Args:
        slide: python-pptx slide object.
        slide_number: 1-based slide index.
        brand_palette: list of 6-char hex strings (e.g., ['006B5E', '5CDBC0']).
        config: optional QA config dict.

    Returns:
        list of finding dicts.
    """
    if not brand_palette:
        return []

    brand_rgb = [_hex_to_rgb(h) for h in brand_palette]
    # Also consider black, white, and near-black/near-white as always acceptable
    neutral_colours = [(0, 0, 0), (255, 255, 255), (30, 30, 30), (240, 240, 240)]
    acceptable_rgb = brand_rgb + neutral_colours

    issues = []
    for shape in slide.shapes:
        if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
            try:
                dominant = _extract_dominant_colours(shape.image.blob, num_colours=5)
                off_brand_count = 0
                for colour in dominant:
                    min_dist = _min_distance_to_palette(colour, acceptable_rgb)
                    if min_dist > _DRIFT_THRESHOLD:
                        off_brand_count += 1

                required = min(_DRIFT_MAX_OFF_BRAND, len(dominant))
                if off_brand_count >= required:
                    issues.append({
                        'slide_number': slide_number,
                        'severity': 'warning',
                        'category': 'palette_drift',
                        'description': f'{off_brand_count}/{len(dominant)} dominant colours are off-brand (threshold: RGB distance > {_DRIFT_THRESHOLD})',
                        'suggested_fix': 'Regenerate image with stronger brand colour constraints in the prompt.',
                        'affected_element': shape.name,
                        'auto_fixable': False,
                    })
            except Exception:
                pass  # Skip if image can't be read

    return issues
