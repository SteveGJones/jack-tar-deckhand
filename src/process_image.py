"""Image processing utilities for the Jack-Tar Deckhand pipeline.

Operations for post-processing generated images: resize, crop,
background removal, PNG optimisation, placeholder generation,
and metadata extraction. Uses Pillow for all operations.
Does NOT use Real-ESRGAN (too slow on CPU — use Lanczos instead).
"""

import hashlib
import os

from PIL import Image


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resample_filter(method: str):
    """Map a method name string to a Pillow resampling filter."""
    filters = {
        'lanczos': Image.LANCZOS,
        'bicubic': Image.BICUBIC,
        'nearest': Image.NEAREST,
    }
    key = method.lower()
    if key not in filters:
        raise ValueError(f"Unknown resampling method '{method}'. "
                         f"Choose from: {list(filters)}")
    return filters[key]


def _parse_aspect_ratio(aspect_ratio: str):
    """Parse an aspect ratio string like '16:9' into (w_parts, h_parts)."""
    parts = aspect_ratio.split(':')
    if len(parts) != 2:
        raise ValueError(f"aspect_ratio must be 'W:H', got '{aspect_ratio}'")
    return float(parts[0]), float(parts[1])


def _hex_to_rgb(hex_colour: str):
    """Convert a 6-character hex string (no # prefix) to an (R, G, B) tuple."""
    hex_colour = hex_colour.lstrip('#')
    if len(hex_colour) != 6:
        raise ValueError(f"hex_colour must be 6 characters, got '{hex_colour}'")
    r = int(hex_colour[0:2], 16)
    g = int(hex_colour[2:4], 16)
    b = int(hex_colour[4:6], 16)
    return r, g, b


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resize(image_path, width, height, output_path=None, method='lanczos'):
    """Resize an image to exact dimensions using Lanczos resampling.

    Args:
        image_path: Path to source image.
        width: Target width in pixels.
        height: Target height in pixels.
        output_path: Output path (default: overwrite source).
        method: Resampling method ('lanczos', 'bicubic', 'nearest').

    Returns:
        str: Path to the output file.
    """
    dest = output_path if output_path is not None else image_path
    resample = _resample_filter(method)

    with Image.open(image_path) as img:
        resized = img.resize((width, height), resample)
        resized.save(dest)

    return dest


def crop_to_aspect(image_path, aspect_ratio='16:9', output_path=None):
    """Centre-crop an image to a target aspect ratio.

    Args:
        image_path: Path to source image.
        aspect_ratio: Target ratio as string ('16:9', '4:3', '1:1').
        output_path: Output path (default: overwrite source).

    Returns:
        str: Path to the output file.
    """
    dest = output_path if output_path is not None else image_path
    target_w, target_h = _parse_aspect_ratio(aspect_ratio)
    target_ratio = target_w / target_h

    with Image.open(image_path) as img:
        src_w, src_h = img.size
        src_ratio = src_w / src_h

        if src_ratio > target_ratio:
            # Source is wider than target — crop width
            new_w = int(src_h * target_ratio)
            new_h = src_h
        else:
            # Source is taller than target — crop height
            new_w = src_w
            new_h = int(src_w / target_ratio)

        left = (src_w - new_w) // 2
        top = (src_h - new_h) // 2
        right = left + new_w
        bottom = top + new_h

        cropped = img.crop((left, top, right, bottom))
        cropped.save(dest)

    return dest


def get_dimensions(image_path):
    """Get image dimensions.

    Returns:
        tuple: (width, height) in pixels.
    """
    with Image.open(image_path) as img:
        return img.size  # (width, height)


def compute_content_hash(image_path):
    """Compute SHA-256 hex digest of image file contents.

    Returns:
        str: 64-character hex digest.
    """
    sha256 = hashlib.sha256()
    chunk_size = 8 * 1024  # 8 KB

    with open(image_path, 'rb') as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)

    return sha256.hexdigest()


def generate_placeholder(width, height, hex_colour, alt_text, output_path):
    """Generate a solid-colour placeholder image.

    Used when all image generation providers fail.
    Creates a solid rectangle with the given colour.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        hex_colour: 6-character hex colour (no # prefix), e.g. '1A365D'.
        alt_text: Alt text description (stored in PNG metadata if possible).
        output_path: Where to save the image.

    Returns:
        str: Path to the output file.
    """
    colour = _hex_to_rgb(hex_colour)
    img = Image.new('RGB', (width, height), colour)

    # Store alt_text in PNG metadata where possible
    png_info = {}
    try:
        from PIL.PngImagePlugin import PngInfo
        metadata = PngInfo()
        metadata.add_text('Description', alt_text)
        img.save(output_path, pnginfo=metadata)
    except Exception:
        img.save(output_path)

    return output_path


def optimize_png(image_path, output_path=None, quality=80):
    """Reduce PNG file size via Pillow quantization.

    Uses Pillow's quantize() for size reduction since pngquant
    may not be installed. Falls back to saving with optimize=True.

    Args:
        image_path: Path to source PNG.
        output_path: Output path (default: overwrite source).
        quality: Quality level 1-100 (lower = smaller file).

    Returns:
        dict: {path, original_size, optimized_size, savings_pct}
    """
    dest = output_path if output_path is not None else image_path
    original_size = os.path.getsize(image_path)

    # Number of colours scales with quality: quality=100 → 256, quality=1 → ~3
    num_colors = max(2, int(256 * quality / 100))

    try:
        with Image.open(image_path) as img:
            # quantize works on P-mode; convert back to RGB for broad compat
            quantized = img.quantize(colors=num_colors).convert('RGB')
            quantized.save(dest, format='PNG', optimize=True)
    except Exception:
        # Fallback: straight optimize save
        with Image.open(image_path) as img:
            img.save(dest, format='PNG', optimize=True)

    optimized_size = os.path.getsize(dest)
    savings_pct = round((1 - optimized_size / original_size) * 100, 2) if original_size else 0.0

    return {
        'path': dest,
        'original_size': original_size,
        'optimized_size': optimized_size,
        'savings_pct': savings_pct,
    }
