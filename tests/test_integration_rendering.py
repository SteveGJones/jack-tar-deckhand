"""Integration tests for new rendering strategies. Require Ollama running.

Run with: pytest tests/test_integration_rendering.py -m ollama -v
Skip in CI with: pytest -m "not ollama"
"""

import json
import os
import shutil
import subprocess
import tempfile

import pytest
import requests

# Mark all tests in this module as requiring Ollama
pytestmark = pytest.mark.ollama


def ollama_available():
    try:
        resp = requests.get('http://localhost:11434/api/tags', timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


@pytest.fixture(autouse=True)
def skip_without_ollama():
    if not ollama_available():
        pytest.skip('Ollama not running')


@pytest.fixture
def integration_deck_dir():
    d = tempfile.mkdtemp(prefix='jtd-render-test-')
    # Copy minimal deck fixture
    fixture_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'minimal_deck')
    for fname in os.listdir(fixture_dir):
        src = os.path.join(fixture_dir, fname)
        dst = os.path.join(d, fname)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
    os.makedirs(os.path.join(d, 'output'), exist_ok=True)
    yield d
    shutil.rmtree(d)


def generate_test_image(prompt, output_path, w=512, h=288):
    """Generate a small test image via Ollama."""
    import base64
    resp = requests.post('http://localhost:11434/api/generate', json={
        'model': 'x/z-image-turbo:fp8',
        'prompt': prompt,
        'stream': False,
        'width': w,
        'height': h,
        'steps': 4,
    }, timeout=120)
    if resp.status_code == 200:
        data = resp.json()
        img_b64 = data.get('image')
        if img_b64:
            with open(output_path, 'wb') as f:
                f.write(base64.b64decode(img_b64))
            return True
    return False


def test_background_variant_full_pipeline(integration_deck_dir):
    """Generate background image + assemble with bottom_bar variant."""
    img_path = os.path.join(integration_deck_dir, 'images', 'slide-02-hero.png')
    assert generate_test_image('abstract teal geometric shapes', img_path)

    # Set up strategy map with background strategy
    sm = {
        'created_at': '2026-03-30T00:00:00Z', 'approval_mode': 'review',
        'slides': [
            {'slide_number': 1, 'strategy': 'full_render', 'rationale': '', 'render_funnel': ['ollama'], 'speaker_override': None},
            {'slide_number': 2, 'strategy': 'background', 'rationale': '', 'render_funnel': ['ollama'], 'speaker_override': None, 'backdrop_variant': 'bottom_bar'},
            {'slide_number': 3, 'strategy': 'composed', 'rationale': '', 'render_funnel': ['ollama'], 'speaker_override': None},
        ],
    }
    with open(os.path.join(integration_deck_dir, 'strategy-map.json'), 'w') as f:
        json.dump(sm, f)

    # Update image manifest
    im = {
        'images': [
            {'image_id': 'slide-01-hero', 'slide_number': 1, 'file_path': img_path, 'status': 'generated'},
            {'image_id': 'slide-02-hero', 'slide_number': 2, 'file_path': img_path, 'status': 'generated'},
        ],
    }
    with open(os.path.join(integration_deck_dir, 'image-manifest.json'), 'w') as f:
        json.dump(im, f)

    result = subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', integration_deck_dir],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"Assembly failed: {result.stderr}"
    assert os.path.exists(os.path.join(integration_deck_dir, 'output', 'presentation.pptx'))


def test_pragmatic_composition_full_pipeline(integration_deck_dir):
    """Generate bg + 2 elements + assemble with pragmatic_composition."""
    img_dir = os.path.join(integration_deck_dir, 'images')
    bg_path = os.path.join(img_dir, 'slide-02-bg.png')
    e1_path = os.path.join(img_dir, 'slide-02-elem-1.png')
    e2_path = os.path.join(img_dir, 'slide-02-elem-2.png')

    assert generate_test_image('subtle teal gradient background', bg_path)
    assert generate_test_image('flat illustration of a laptop computer', e1_path)
    assert generate_test_image('flat illustration of a server rack', e2_path)

    sm = {
        'created_at': '2026-03-30T00:00:00Z', 'approval_mode': 'review',
        'slides': [
            {'slide_number': 1, 'strategy': 'full_render', 'rationale': '', 'render_funnel': ['ollama'], 'speaker_override': None},
            {'slide_number': 2, 'strategy': 'pragmatic_composition', 'rationale': '', 'render_funnel': ['ollama'], 'speaker_override': None,
             'element_layout': {
                 'template': 'two_column',
                 'elements': [
                     {'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.05, 'y': 0.22, 'w': 0.42, 'h': 0.55},
                     {'id': 'elem_2', 'label_source': 'body_points[1]', 'x': 0.55, 'y': 0.22, 'w': 0.42, 'h': 0.55},
                 ],
                 'title_region': {'x': 0.05, 'y': 0.03, 'w': 0.90, 'h': 0.12},
             }},
            {'slide_number': 3, 'strategy': 'composed', 'rationale': '', 'render_funnel': ['ollama'], 'speaker_override': None},
        ],
    }
    with open(os.path.join(integration_deck_dir, 'strategy-map.json'), 'w') as f:
        json.dump(sm, f)

    im = {
        'images': [
            {'image_id': 'slide-01-hero', 'slide_number': 1, 'file_path': bg_path, 'status': 'generated'},
            {'image_id': 'slide-02-bg', 'slide_number': 2, 'file_path': bg_path, 'status': 'generated', 'placement_zone': 'background'},
            {'image_id': 'slide-02-elem-1', 'slide_number': 2, 'file_path': e1_path, 'status': 'generated', 'placement_zone': 'element', 'element_id': 'elem_1'},
            {'image_id': 'slide-02-elem-2', 'slide_number': 2, 'file_path': e2_path, 'status': 'generated', 'placement_zone': 'element', 'element_id': 'elem_2'},
        ],
    }
    with open(os.path.join(integration_deck_dir, 'image-manifest.json'), 'w') as f:
        json.dump(im, f)

    result = subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', integration_deck_dir],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"Assembly failed: {result.stderr}"
