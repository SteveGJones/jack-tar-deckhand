"""Resolution-aware funnel stages: cloud_2k and cloud_4k."""
import sys
import types
from pathlib import Path
from unittest import mock

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

# render_funnel imports `src.generate_cloud_image` at module load time. The
# plugin's src/ does not vendor that module (it lives in plugins/jack-tar-cloud
# and in the legacy worktree-root src/). For a focused unit test of the funnel
# stage logic, stub the dependency before importing.
if 'src.generate_cloud_image' not in sys.modules:
    _stub = types.ModuleType('src.generate_cloud_image')

    def _stub_generate_cloud_image(*args, **kwargs):  # pragma: no cover
        raise NotImplementedError('stub — patch src.render_funnel._generate_cloud_raw instead')

    _stub.generate_cloud_image = _stub_generate_cloud_image
    sys.modules['src.generate_cloud_image'] = _stub

from src import render_funnel  # noqa: E402


def test_cloud_2k_stage_calls_generate_with_resolution_2k(tmp_path):
    render_funnel.init_render_log(str(tmp_path))
    fake = mock.Mock(return_value={
        'file_path': str(tmp_path / 'out.png'),
        'cost_usd': 0.101,
    })
    with mock.patch('src.render_funnel._generate_cloud_raw', fake):
        result = render_funnel.execute_funnel_stage(
            deck_dir=str(tmp_path),
            slide_number=1,
            strategy='full_render',
            prompt='a lighthouse',
            funnel_stage='cloud_2k',
            model='gemini-3.1-flash-image-preview',
            output_path=str(tmp_path / 'out.png'),
            provider='google',
        )
    assert result['status'] == 'generated'
    call_kwargs = fake.call_args.kwargs
    assert call_kwargs['resolution'] == '2K'
    assert call_kwargs['provider'] == 'google'


def test_cloud_4k_stage_calls_generate_with_resolution_4k(tmp_path):
    render_funnel.init_render_log(str(tmp_path))
    fake = mock.Mock(return_value={
        'file_path': str(tmp_path / 'out.png'),
        'cost_usd': 0.240,
    })
    with mock.patch('src.render_funnel._generate_cloud_raw', fake):
        result = render_funnel.execute_funnel_stage(
            deck_dir=str(tmp_path),
            slide_number=1,
            strategy='full_render',
            prompt='a lighthouse',
            funnel_stage='cloud_4k',
            model='gemini-3-pro-image-preview',
            output_path=str(tmp_path / 'out.png'),
            provider='google',
        )
    assert result['status'] == 'generated'
    assert fake.call_args.kwargs['resolution'] == '4K'


def test_cloud_full_default_passes_1k(tmp_path):
    """Default cloud_full stage preserves prior behaviour: resolution='1K'."""
    render_funnel.init_render_log(str(tmp_path))
    fake = mock.Mock(return_value={'file_path': str(tmp_path / 'out.png'), 'cost_usd': 0.05})
    with mock.patch('src.render_funnel._generate_cloud_raw', fake):
        render_funnel.execute_funnel_stage(
            deck_dir=str(tmp_path),
            slide_number=1,
            strategy='full_render',
            prompt='x',
            funnel_stage='cloud_full',
            model='gemini-3.1-flash-image-preview',
            output_path=str(tmp_path / 'out.png'),
            provider='google',
        )
    assert fake.call_args.kwargs['resolution'] == '1K'


# --- Schema conformance ----------------------------------------------------

import json  # noqa: E402

import jsonschema  # noqa: E402

_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / 'src' / 'schemas' / 'render_log.schema.json'
)


def test_render_log_schema_accepts_cloud_2k_and_cloud_4k():
    """The render-log schema must accept entries for the new funnel stages
    so downstream validators don't reject logs from cloud_2k/cloud_4k slides."""
    schema = json.loads(_SCHEMA_PATH.read_text())
    log = {
        'entries': [
            {
                'slide_number': 1,
                'strategy': 'full_render',
                'funnel_stage': 'cloud_2k',
                'prompt_hash': 'abc123',
                'model': 'gemini-3.1-flash-image-preview',
                'resolution': '2K',
                'iteration': 1,
                'cost_usd': 0.101,
                'timestamp': '2026-05-06T12:00:00Z',
            },
            {
                'slide_number': 2,
                'strategy': 'full_render',
                'funnel_stage': 'cloud_4k',
                'prompt_hash': 'def456',
                'model': 'gemini-3-pro-image-preview',
                'resolution': '4K',
                'iteration': 1,
                'cost_usd': 0.240,
                'timestamp': '2026-05-06T12:00:01Z',
            },
        ],
    }
    jsonschema.validate(log, schema)  # raises on mismatch
