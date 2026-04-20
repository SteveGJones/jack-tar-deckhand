"""Render funnel — three-stage render orchestration for keynote slides.

Orchestrates the Ollama → cloud_low → cloud_full render stages for
full_render and backdrop_render slides. Logs every render attempt to
render-log.json for cost and convergence analysis.
"""

import hashlib
import json
import os

from datetime import datetime, timezone


def init_render_log(deck_dir):
    """Create an empty render-log.json in the deck directory.

    Args:
        deck_dir: Path to the deck working directory.
    """
    path = os.path.join(deck_dir, 'render-log.json')
    with open(path, 'w') as f:
        json.dump({'entries': []}, f, indent=2)
        f.write('\n')


def load_render_log(deck_dir):
    """Load render-log.json from the deck directory.

    Args:
        deck_dir: Path to the deck working directory.

    Returns:
        dict: The parsed render log.

    Raises:
        FileNotFoundError: If render-log.json does not exist.
    """
    path = os.path.join(deck_dir, 'render-log.json')
    if not os.path.exists(path):
        raise FileNotFoundError(f'No render-log.json in {deck_dir}')
    with open(path) as f:
        return json.load(f)


def append_render_entry(deck_dir, entry):
    """Append a render attempt entry to the render log.

    Args:
        deck_dir: Path to the deck working directory.
        entry: dict with render attempt data (must conform to RenderLog entry schema).
    """
    log = load_render_log(deck_dir)
    log['entries'].append(entry)
    path = os.path.join(deck_dir, 'render-log.json')
    tmp_path = path + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(log, f, indent=2)
        f.write('\n')
    os.replace(tmp_path, path)


def hash_prompt(prompt_text):
    """Compute a short hash of a prompt for log deduplication.

    Args:
        prompt_text: The prompt string.

    Returns:
        str: First 16 chars of SHA-256 hex digest.
    """
    return hashlib.sha256(prompt_text.encode('utf-8')).hexdigest()[:16]


import subprocess
import sys

from src.generate_cloud_image import generate_cloud_image as _generate_cloud_raw


# Resolution defaults per funnel stage
_OLLAMA_RESOLUTIONS = {
    'ollama': {'width': 1024, 'height': 576},
    'cloud_low': {'width': 1280, 'height': 720},
    'cloud_full': {'width': 1920, 'height': 1080},
}

# Cloud provider quality settings per stage
_CLOUD_STAGE_QUALITY = {
    'cloud_low': 'low',
    'cloud_full': 'medium',
}

_CLOUD_STAGE_SIZE = {
    'cloud_low': '1024x1024',
    'cloud_full': '1536x1024',
}


def _generate_cloud(prompt, provider, output_path, funnel_stage, model=None):
    """Wrapper for cloud generation with funnel-stage-appropriate settings."""
    quality = _CLOUD_STAGE_QUALITY.get(funnel_stage, 'medium')
    size = _CLOUD_STAGE_SIZE.get(funnel_stage, '1536x1024')
    kwargs = {'quality': quality, 'size': size}
    if model:
        kwargs['model'] = model
    return _generate_cloud_raw(
        prompt=prompt,
        provider=provider,
        output_path=output_path,
        **kwargs,
    )


def execute_funnel_stage(deck_dir, slide_number, strategy, prompt, funnel_stage,
                         model, output_path, provider=None, iteration=1):
    """Execute a single render funnel stage for one slide.

    Args:
        deck_dir: Path to the deck working directory.
        slide_number: Which slide this render is for.
        strategy: 'full_render' or 'backdrop_render'.
        prompt: The image generation prompt text.
        funnel_stage: 'ollama', 'cloud_low', or 'cloud_full'.
        model: Model identifier (e.g., 'x/z-image-turbo', 'imagen-4-fast').
        output_path: Where to save the generated image.
        provider: Cloud provider name (required for cloud stages).
        iteration: Iteration number for this stage (default 1).

    Returns:
        dict: {status, file_path, cost_usd, model, resolution, error?}
    """
    prompt_h = hash_prompt(prompt)
    dims = _OLLAMA_RESOLUTIONS.get(funnel_stage, {'width': 1920, 'height': 1080})
    resolution = f'{dims["width"]}x{dims["height"]}'
    cost = 0.0

    try:
        if funnel_stage == 'ollama':
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            subprocess.run(
                [sys.executable, 'src/generate_image.py',
                 '--prompt', prompt,
                 '--model', model,
                 '--output', output_path,
                 '--width', str(dims['width']),
                 '--height', str(dims['height'])],
                check=True, capture_output=True, text=True,
            )
        else:
            result = _generate_cloud(prompt, provider, output_path, funnel_stage, model=model)
            cost = result.get('cost_usd', 0.0)
            resolution = _CLOUD_STAGE_SIZE.get(funnel_stage, '1536x1024')

        # Log the attempt
        append_render_entry(deck_dir, {
            'slide_number': slide_number,
            'strategy': strategy,
            'funnel_stage': funnel_stage,
            'prompt_hash': prompt_h,
            'model': model,
            'resolution': resolution,
            'vision_score': None,
            'iteration': iteration,
            'cost_usd': cost,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })

        return {
            'status': 'generated',
            'file_path': output_path,
            'cost_usd': cost,
            'model': model,
            'resolution': resolution,
        }

    except Exception as e:
        # Log the failure too
        append_render_entry(deck_dir, {
            'slide_number': slide_number,
            'strategy': strategy,
            'funnel_stage': funnel_stage,
            'prompt_hash': prompt_h,
            'model': model,
            'resolution': resolution,
            'vision_score': None,
            'iteration': iteration,
            'cost_usd': 0.0,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })

        return {
            'status': 'failed',
            'file_path': output_path,
            'cost_usd': 0.0,
            'model': model,
            'resolution': resolution,
            'error': str(e),
        }
