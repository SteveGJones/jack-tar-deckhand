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


from unittest.mock import patch, MagicMock
from PIL import Image


def _create_test_image(path, width=1024, height=576):
    """Helper to create a test image at the given path."""
    img = Image.new('RGB', (width, height), color=(0, 107, 94))
    img.save(path)
    return path


def test_execute_ollama_stage(deck_dir):
    from src.render_funnel import init_render_log, execute_funnel_stage
    init_render_log(deck_dir)
    output_path = os.path.join(deck_dir, 'images', 'slide-01-hero.png')

    with patch('src.render_funnel.subprocess.run') as mock_run:
        # Simulate generate_image.py writing a file
        def side_effect(*args, **kwargs):
            _create_test_image(output_path)
            result = MagicMock()
            result.stdout = output_path
            result.returncode = 0
            return result
        mock_run.side_effect = side_effect

        result = execute_funnel_stage(
            deck_dir=deck_dir,
            slide_number=1,
            strategy='full_render',
            prompt='Test prompt for slide 1',
            funnel_stage='ollama',
            model='x/z-image-turbo',
            output_path=output_path,
        )

    assert result['status'] == 'generated'
    assert result['file_path'] == output_path
    assert result['cost_usd'] == 0.0
    assert os.path.exists(output_path)


def test_execute_cloud_stage(deck_dir):
    from src.render_funnel import init_render_log, execute_funnel_stage
    init_render_log(deck_dir)
    output_path = os.path.join(deck_dir, 'images', 'slide-01-hero.png')

    with patch('src.render_funnel._generate_cloud') as mock_cloud:
        _create_test_image(output_path, 1280, 720)
        mock_cloud.return_value = {
            'file_path': output_path,
            'provider': 'google',
            'model_used': 'imagen-4-fast',
            'cost_usd': 0.02,
            'status': 'generated',
        }

        result = execute_funnel_stage(
            deck_dir=deck_dir,
            slide_number=1,
            strategy='full_render',
            prompt='Test prompt for slide 1',
            funnel_stage='cloud_low',
            model='imagen-4-fast',
            output_path=output_path,
            provider='google',
        )

    assert result['status'] == 'generated'
    assert result['cost_usd'] == 0.02


def test_execute_stage_logs_to_render_log(deck_dir):
    from src.render_funnel import init_render_log, execute_funnel_stage, load_render_log
    init_render_log(deck_dir)
    output_path = os.path.join(deck_dir, 'images', 'slide-01-hero.png')

    with patch('src.render_funnel.subprocess.run') as mock_run:
        def side_effect(*args, **kwargs):
            _create_test_image(output_path)
            result = MagicMock()
            result.stdout = output_path
            result.returncode = 0
            return result
        mock_run.side_effect = side_effect

        execute_funnel_stage(
            deck_dir=deck_dir,
            slide_number=1,
            strategy='full_render',
            prompt='Test prompt',
            funnel_stage='ollama',
            model='x/z-image-turbo',
            output_path=output_path,
        )

    log = load_render_log(deck_dir)
    assert len(log['entries']) == 1
    assert log['entries'][0]['funnel_stage'] == 'ollama'
    assert log['entries'][0]['slide_number'] == 1


def test_execute_stage_failed(deck_dir):
    from src.render_funnel import init_render_log, execute_funnel_stage
    init_render_log(deck_dir)
    output_path = os.path.join(deck_dir, 'images', 'slide-01-hero.png')

    with patch('src.render_funnel.subprocess.run') as mock_run:
        mock_run.side_effect = Exception('Ollama not running')

        result = execute_funnel_stage(
            deck_dir=deck_dir,
            slide_number=1,
            strategy='full_render',
            prompt='Test prompt',
            funnel_stage='ollama',
            model='x/z-image-turbo',
            output_path=output_path,
        )

    assert result['status'] == 'failed'
    assert 'error' in result


class TestCloudModelPassthrough:
    """_generate_cloud should pass model kwarg through to generate_cloud_image."""

    @pytest.fixture
    def deck_dir(self):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, 'images'), exist_ok=True)
        yield d
        shutil.rmtree(d)

    def test_model_passed_to_cloud_generator(self, deck_dir):
        from src.render_funnel import init_render_log, execute_funnel_stage
        init_render_log(deck_dir)

        mock_result = {
            'file_path': os.path.join(deck_dir, 'images', 'test.png'),
            'provider': 'google',
            'model_used': 'gemini-3.1-flash-image-preview',
            'cost_usd': 0.067,
            'status': 'generated',
        }
        output_path = os.path.join(deck_dir, 'images', 'test.png')

        with patch('src.render_funnel._generate_cloud_raw', return_value=mock_result) as mock_gen:
            execute_funnel_stage(
                deck_dir=deck_dir,
                slide_number=1,
                strategy='full_render',
                prompt='test prompt',
                funnel_stage='cloud_low',
                model='gemini-3.1-flash-image-preview',
                output_path=output_path,
                provider='google',
            )
            mock_gen.assert_called_once()
            _, kwargs = mock_gen.call_args
            assert kwargs.get('model') == 'gemini-3.1-flash-image-preview'

    def test_model_passed_for_openai_too(self, deck_dir):
        from src.render_funnel import init_render_log, execute_funnel_stage
        init_render_log(deck_dir)

        mock_result = {
            'file_path': os.path.join(deck_dir, 'images', 'test.png'),
            'provider': 'openai',
            'model_used': 'gpt-image-1.5',
            'cost_usd': 0.009,
            'status': 'generated',
        }
        output_path = os.path.join(deck_dir, 'images', 'test.png')

        with patch('src.render_funnel._generate_cloud_raw', return_value=mock_result) as mock_gen:
            execute_funnel_stage(
                deck_dir=deck_dir,
                slide_number=1,
                strategy='full_render',
                prompt='test prompt',
                funnel_stage='cloud_low',
                model='gpt-image-1.5',
                output_path=output_path,
                provider='openai',
            )
            mock_gen.assert_called_once()
            _, kwargs = mock_gen.call_args
            assert kwargs.get('model') == 'gpt-image-1.5'
