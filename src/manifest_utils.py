"""Manifest utilities for surgical image-manifest.json updates.

Provides functions to load, update individual entries, and save
the image manifest without requiring a full pipeline re-run.
Uses process_image.py primitives for dimension/hash computation.
"""

import json
import os

from src.process_image import get_dimensions, compute_content_hash


def load_manifest(deck_dir):
    """Load image-manifest.json from a deck directory.

    Args:
        deck_dir: Path to the deck working directory.

    Returns:
        dict: The parsed manifest.

    Raises:
        FileNotFoundError: If manifest does not exist.
    """
    path = os.path.join(deck_dir, 'image-manifest.json')
    if not os.path.exists(path):
        raise FileNotFoundError(f'No image-manifest.json in {deck_dir}')
    with open(path) as f:
        return json.load(f)


def save_manifest(deck_dir, manifest):
    """Write image-manifest.json atomically.

    Args:
        deck_dir: Path to the deck working directory.
        manifest: The manifest dict to write.
    """
    path = os.path.join(deck_dir, 'image-manifest.json')
    tmp_path = path + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(manifest, f, indent=2)
        f.write('\n')
    os.replace(tmp_path, path)


def _find_entry(manifest, *, image_id=None, slide_number=None):
    """Find an entry in the manifest by image_id or slide_number."""
    for entry in manifest.get('images', []):
        if image_id and entry.get('image_id') == image_id:
            return entry
        if slide_number is not None and entry.get('slide_number') == slide_number:
            return entry
    key = image_id if image_id else f'slide {slide_number}'
    raise KeyError(f'No manifest entry for {key}')


def update_manifest_entry(deck_dir, image_id, model_used=None, alt_text=None):
    """Update a single entry in the manifest by image_id.

    Recomputes dimensions and content_hash from the file on disk.
    Only updates model_used and alt_text if provided.

    Args:
        deck_dir: Path to the deck working directory.
        image_id: The image_id to update.
        model_used: Optional new model attribution.
        alt_text: Optional new alt text.

    Returns:
        dict: The updated entry.

    Raises:
        KeyError: If image_id not found.
    """
    manifest = load_manifest(deck_dir)
    entry = _find_entry(manifest, image_id=image_id)

    file_path = entry['file_path']
    w, h = get_dimensions(file_path)
    entry['dimensions'] = {'width': w, 'height': h}
    entry['content_hash'] = compute_content_hash(file_path)

    if model_used is not None:
        entry['model_used'] = model_used
    if alt_text is not None:
        entry['alt_text'] = alt_text

    save_manifest(deck_dir, manifest)
    return entry


def replace_image_in_manifest(deck_dir, slide_number, new_file_path, model_used, alt_text=None):
    """Replace an image entry by slide_number with a new file.

    Args:
        deck_dir: Path to the deck working directory.
        slide_number: Slide number to update.
        new_file_path: Path to the replacement image.
        model_used: Model/tool attribution string.
        alt_text: Optional new alt text.

    Returns:
        dict: The updated entry.

    Raises:
        KeyError: If slide_number not found.
    """
    manifest = load_manifest(deck_dir)
    entry = _find_entry(manifest, slide_number=slide_number)

    entry['file_path'] = new_file_path
    w, h = get_dimensions(new_file_path)
    entry['dimensions'] = {'width': w, 'height': h}
    entry['content_hash'] = compute_content_hash(new_file_path)
    entry['model_used'] = model_used

    if alt_text is not None:
        entry['alt_text'] = alt_text

    save_manifest(deck_dir, manifest)
    return entry
