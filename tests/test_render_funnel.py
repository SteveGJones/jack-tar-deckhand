"""Tests for render funnel orchestration."""

import hashlib
import json
import os
import shutil
import tempfile

import pytest


@pytest.fixture
def deck_dir():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, 'images'), exist_ok=True)
    yield d
    shutil.rmtree(d)


def test_init_render_log(deck_dir):
    from src.render_funnel import init_render_log, load_render_log
    init_render_log(deck_dir)
    log = load_render_log(deck_dir)
    assert log['entries'] == []


def test_append_render_entry(deck_dir):
    from src.render_funnel import init_render_log, append_render_entry, load_render_log
    init_render_log(deck_dir)
    append_render_entry(deck_dir, {
        'slide_number': 1,
        'strategy': 'full_render',
        'funnel_stage': 'ollama',
        'prompt_hash': 'abc123',
        'model': 'x/z-image-turbo',
        'resolution': '1024x576',
        'vision_score': 6.5,
        'iteration': 1,
        'cost_usd': 0.0,
        'timestamp': '2026-03-29T12:00:00Z',
    })
    log = load_render_log(deck_dir)
    assert len(log['entries']) == 1
    assert log['entries'][0]['slide_number'] == 1


def test_append_multiple_entries(deck_dir):
    from src.render_funnel import init_render_log, append_render_entry, load_render_log
    init_render_log(deck_dir)
    for i in range(3):
        append_render_entry(deck_dir, {
            'slide_number': 1,
            'strategy': 'full_render',
            'funnel_stage': 'ollama',
            'prompt_hash': f'hash_{i}',
            'model': 'x/z-image-turbo',
            'resolution': '1024x576',
            'vision_score': 5.0 + i,
            'iteration': i + 1,
            'cost_usd': 0.0,
            'timestamp': f'2026-03-29T12:0{i}:00Z',
        })
    log = load_render_log(deck_dir)
    assert len(log['entries']) == 3


def test_load_render_log_missing(deck_dir):
    from src.render_funnel import load_render_log
    with pytest.raises(FileNotFoundError):
        load_render_log(deck_dir)
