"""Image quality QA checks.

Implements AP-12 (Image Resolution), AP-13 (Aspect Ratio Distortion).

Detection algorithms from: research/07-qa-heuristics-anti-patterns.md
"""

from PIL import Image
import io
from ..config import QA_CONFIG


def check_image_resolution(slide, slide_number, presentation, config=None):
    """AP-12: Check that images have sufficient resolution for placement size."""
    cfg = config or QA_CONFIG
    min_dpi = cfg['min_image_dpi_equiv']
    issues = []
    for shape in slide.shapes:
        if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
            try:
                img_blob = shape.image.blob
                pil_img = Image.open(io.BytesIO(img_blob))
                img_w, img_h = pil_img.size

                place_w_in = shape.width / 914400  # EMU to inches
                place_h_in = shape.height / 914400

                eff_dpi_x = img_w / place_w_in if place_w_in > 0 else 999
                eff_dpi_y = img_h / place_h_in if place_h_in > 0 else 999

                if eff_dpi_x < min_dpi or eff_dpi_y < min_dpi:
                    issues.append({
                        'slide_number': slide_number,
                        'severity': 'error',
                        'category': 'image_quality',
                        'description': f'Image {img_w}x{img_h}px at {place_w_in:.1f}"x{place_h_in:.1f}" = {eff_dpi_x:.0f}x{eff_dpi_y:.0f} DPI (min {min_dpi})',
                        'suggested_fix': 'Replace with a higher-resolution image.',
                        'affected_element': shape.name,
                        'auto_fixable': False,
                    })
            except Exception:
                pass  # Skip if image can't be read
    return issues


def check_aspect_ratio_distortion(slide, slide_number, presentation, config=None):
    """AP-13: Check for aspect ratio distortion on images."""
    cfg = config or QA_CONFIG
    max_distortion = cfg['max_aspect_distortion_pct']
    issues = []
    for shape in slide.shapes:
        if shape.shape_type == 13:  # Picture
            try:
                pil_img = Image.open(io.BytesIO(shape.image.blob))
                native_w, native_h = pil_img.size
                native_ratio = native_w / native_h if native_h > 0 else 1

                display_w = shape.width
                display_h = shape.height
                display_ratio = display_w / display_h if display_h > 0 else 1

                distortion_pct = abs(native_ratio - display_ratio) / native_ratio * 100
                if distortion_pct > max_distortion:
                    issues.append({
                        'slide_number': slide_number,
                        'severity': 'warning',
                        'category': 'image_quality',
                        'description': f'Image distorted by {distortion_pct:.1f}% (max {max_distortion}%)',
                        'suggested_fix': 'Lock aspect ratio when resizing. Use crop instead of stretch.',
                        'affected_element': shape.name,
                        'auto_fixable': True,
                    })
            except Exception:
                pass
    return issues
