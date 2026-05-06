"""Integration: SKILL.md --resolution flag reaches generate_cloud_image kwargs.

Exec each cloud-image SKILL.md's Generate Python snippet with mocked
generate_cloud_image, verify the captured kwargs include the expected
resolution and any flag-specific translations (FAL --size -> image_size dict).
"""
import re
import sys
from pathlib import Path
from unittest import mock

import pytest

CLOUD_PLUGIN = Path(__file__).resolve().parent.parent / 'jack-tar-cloud'


def _exec_generate_block(skill_name, env_substitutions):
    """Extract and exec the Generate Python snippet from a SKILL.md file.

    Substitutes $PROMPT, $OUTPUT_PATH, etc. into the snippet, mocks
    generate_cloud_image to capture kwargs without making an API call,
    and returns the captured kwargs.
    """
    skill_text = (CLOUD_PLUGIN / 'skills' / skill_name / 'SKILL.md').read_text()
    # Find the Generate block -- first ```bash block containing "generate_cloud_image"
    blocks = re.findall(r'```bash\n(.*?)```', skill_text, re.DOTALL)
    gen_block = next((b for b in blocks if 'generate_cloud_image' in b), None)
    assert gen_block, f"{skill_name}: no generate_cloud_image bash block found"

    # Pull the python3 -c "..." body out of the bash heredoc
    py_match = re.search(r'python3 -c "(.+?)"\s*$', gen_block, re.DOTALL)
    assert py_match, f"{skill_name}: no python3 -c body found in generate block"
    py_body = py_match.group(1)

    # Substitute placeholders ($PROMPT, $OUTPUT_PATH, $RESOLUTION, etc.)
    for k, v in env_substitutions.items():
        py_body = py_body.replace(f'${k}', v)

    # Capture kwargs without making an API call
    captured = {}

    def fake_generate(**kwargs):
        captured.update(kwargs)
        return {'file_path': kwargs.get('output_path', '/tmp/x'), 'cost_usd': 0.0}

    sys.path.insert(0, str(CLOUD_PLUGIN))
    try:
        # Force a fresh import each call so mock.patch takes effect on the
        # 'from ... import generate_cloud_image' line inside py_body.
        sys.modules.pop('src.generate_cloud_image', None)
        with mock.patch('src.generate_cloud_image.generate_cloud_image', fake_generate):
            ns = {'__name__': '__main__'}
            exec(py_body, ns)
    finally:
        if str(CLOUD_PLUGIN) in sys.path:
            sys.path.remove(str(CLOUD_PLUGIN))
        sys.modules.pop('src.generate_cloud_image', None)
    return captured


def test_openai_skill_threads_resolution_and_model():
    captured = _exec_generate_block('openai-image', {
        'PROMPT': 'a lighthouse',
        'OUTPUT': '/tmp/o.png',
        'SIZE': '1024x1024',
        'QUALITY': 'medium',
        'BACKGROUND': 'auto',
        'MODEL': 'gpt-image-1.5',
        'RESOLUTION': '1K',
    })
    assert captured['provider'] == 'openai'
    assert captured['resolution'] == '1K'
    assert captured['model'] == 'gpt-image-1.5'
    assert captured['size'] == '1024x1024'


def test_google_skill_threads_resolution_4k():
    captured = _exec_generate_block('google-image', {
        'PROMPT': 'a lighthouse',
        'OUTPUT_PATH': '/tmp/g.png',
        'MODEL': 'gemini-3-pro-image-preview',
        'ASPECT_RATIO': '16:9',
        'RESOLUTION': '4K',
    })
    assert captured['provider'] == 'google'
    assert captured['resolution'] == '4K'
    assert captured['model'] == 'gemini-3-pro-image-preview'
    assert captured['aspect_ratio'] == '16:9'


def test_fal_skill_translates_size_and_threads_resolution_2k():
    captured = _exec_generate_block('fal-image', {
        'PROMPT': 'a lighthouse',
        'OUTPUT_PATH': '/tmp/f.png',
        'SIZE': '2048x2048',
        'MODEL': 'fal-ai/flux-2-pro',
        'RESOLUTION': '2K',
    })
    assert captured['provider'] == 'fal'
    assert captured['resolution'] == '2K'
    assert captured['model'] == 'fal-ai/flux-2-pro'
    assert captured.get('image_size') == {'width': 2048, 'height': 2048}, (
        f"fal --size should translate to image_size dict, got {captured.get('image_size')!r}"
    )


def test_fal_skill_omits_image_size_when_size_not_provided():
    """When --size is omitted, the SKILL.md should NOT pass image_size -- letting
    the underlying provider use the resolution-mapped default preset."""
    captured = _exec_generate_block('fal-image', {
        'PROMPT': 'a lighthouse',
        'OUTPUT_PATH': '/tmp/f.png',
        'SIZE': '',  # not provided
        'MODEL': 'fal-ai/flux-2-pro',
        'RESOLUTION': '1K',
    })
    assert 'image_size' not in captured, (
        f"image_size should not be set when --size is empty; got {captured.get('image_size')!r}"
    )
    assert captured['resolution'] == '1K'
