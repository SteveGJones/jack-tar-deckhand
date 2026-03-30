"""Manifest utilities for surgical image-manifest.json updates.

Provides functions to load, update individual entries, and save
the image manifest without requiring a full pipeline re-run.
Uses process_image.py primitives for dimension/hash computation.
"""

import json
import os


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
