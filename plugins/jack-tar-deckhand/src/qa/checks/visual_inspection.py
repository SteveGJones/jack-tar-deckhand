"""Post-assembly visual inspection — rasterise slides and check for quality issues."""

import math
import os
import subprocess

from PIL import Image


def _hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))


def _colour_distance(c1, c2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def rasterise_slide(pptx_path, slide_number, output_dir):
    """Convert a single slide to PNG via LibreOffice headless. Returns PNG path or None."""
    if pptx_path is None or not os.path.exists(pptx_path):
        return None
    try:
        result = subprocess.run(
            ['soffice', '--headless', '--convert-to', 'png', '--outdir', output_dir, pptx_path],
            capture_output=True, text=True, timeout=60,
        )
        pngs = sorted([f for f in os.listdir(output_dir) if f.endswith('.png')])
        if slide_number <= len(pngs):
            return os.path.join(output_dir, pngs[slide_number - 1])
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def inspect_slide(png_path, slide_number, outline_slide, style_guide):
    """Run automated visual checks on a rasterised slide PNG."""
    findings = []
    if png_path is None or not os.path.exists(png_path):
        findings.append({
            'slide_number': slide_number, 'severity': 'error',
            'category': 'smartart',
            'description': f'Visual inspection: could not rasterise slide {slide_number}'
        })
        return findings

    try:
        img = Image.open(png_path).convert('RGB')
    except Exception as e:
        findings.append({
            'slide_number': slide_number, 'severity': 'error',
            'category': 'smartart',
            'description': f'Visual inspection: cannot read slide PNG: {e}'
        })
        return findings

    # Blank detection (use get_flattened_data; fall back to getdata for older Pillow)
    get_pixels = getattr(img, 'get_flattened_data', img.getdata)
    pixels = list(get_pixels())
    white_count = sum(1 for r, g, b in pixels if r > 250 and g > 250 and b > 250)
    white_ratio = white_count / len(pixels) if pixels else 1.0
    if white_ratio > 0.95:
        findings.append({
            'slide_number': slide_number, 'severity': 'error',
            'category': 'smartart',
            'description': f'Visual inspection: slide is {white_ratio:.0%} blank (white)'
        })

    # Brand colour check
    palette = style_guide.get('palette', {})
    if palette:
        brand_colours = []
        for key in ('primary', 'background', 'accent', 'text_primary'):
            hex_val = palette.get(key)
            if hex_val:
                brand_colours.append(_hex_to_rgb(hex_val))

        if brand_colours:
            small = img.resize((50, 50))
            quantized = small.quantize(colors=5, method=Image.Quantize.MEDIANCUT)
            pal = quantized.getpalette()[:15]
            dominant = []
            for i in range(0, len(pal), 3):
                dominant.append((pal[i], pal[i + 1], pal[i + 2]))

            min_dist = float('inf')
            for dom in dominant:
                for brand in brand_colours:
                    d = _colour_distance(dom, brand)
                    min_dist = min(min_dist, d)

            if min_dist > 100:
                findings.append({
                    'slide_number': slide_number, 'severity': 'warning',
                    'category': 'smartart',
                    'description': f'Visual inspection: no brand colours detected (min distance: {min_dist:.0f})'
                })

    return findings


def run_visual_inspection(pptx_path, outline, style_guide, output_dir):
    """Rasterise all slides and run automated visual checks."""
    findings = []
    if not pptx_path or not os.path.exists(str(pptx_path)):
        return findings
    slides = outline.get('slides', [])
    for slide in slides:
        sn = slide.get('slide_number', 0)
        png_path = rasterise_slide(pptx_path, sn, output_dir)
        slide_findings = inspect_slide(png_path, sn, slide, style_guide)
        findings.extend(slide_findings)
    return findings
