"""Tests for manifest utilities."""

import json
import os
import shutil
import tempfile

import pytest
from PIL import Image


@pytest.fixture
def deck_dir():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, 'images'), exist_ok=True)
    yield d
    shutil.rmtree(d)


@pytest.fixture
def sample_image(deck_dir):
    """Create a 200x100 red PNG in the deck images dir."""
    path = os.path.join(deck_dir, 'images', 'slide-01-hero.png')
    img = Image.new('RGB', (200, 100), color=(255, 0, 0))
    img.save(path)
    return path


@pytest.fixture
def sample_manifest(deck_dir, sample_image):
    """Write a minimal valid image-manifest.json."""
    manifest = {
        'images': [
            {
                'image_id': 'slide-01-hero_image',
                'slide_number': 1,
                'file_path': sample_image,
                'status': 'generated',
                'dimensions': {'width': 200, 'height': 100},
                'model_used': 'x/z-image-turbo',
                'alt_text': 'Test image',
                'content_hash': 'abc123',
            }
        ],
        'summary': {
            'total_images': 1,
            'generated_count': 1,
            'cached_count': 0,
            'placeholder_count': 0,
            'failed_count': 0,
            'total_generation_seconds': 0.0,
        },
    }
    manifest_path = os.path.join(deck_dir, 'image-manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)
    return manifest_path


def test_load_manifest(deck_dir, sample_manifest):
    from src.manifest_utils import load_manifest
    manifest = load_manifest(deck_dir)
    assert len(manifest['images']) == 1
    assert manifest['images'][0]['image_id'] == 'slide-01-hero_image'


def test_load_manifest_missing_file(deck_dir):
    from src.manifest_utils import load_manifest
    with pytest.raises(FileNotFoundError):
        load_manifest(deck_dir)
