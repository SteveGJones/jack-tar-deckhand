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
