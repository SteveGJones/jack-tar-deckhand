"""Tests for Recraft V4 raster provider — cost helpers, dual-path generation,
4K via Creative Upscale chain."""
import os
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.generate_cloud_image import (
    estimate_recraft_cost,
    ProviderResolutionUnsupportedError,
)


def test_recraft_cost_1k_standard():
    assert estimate_recraft_cost(tier='standard', resolution='1K') == 0.04


def test_recraft_cost_2k_pro():
    assert estimate_recraft_cost(tier='pro', resolution='2K') == 0.25


def test_recraft_cost_4k_chain():
    """4K = generate at 2K Pro ($0.25) + Creative Upscale (~$0.25) = $0.50."""
    assert estimate_recraft_cost(tier='pro', resolution='4K') == 0.50


def test_recraft_cost_standard_rejects_4k():
    """Standard tier doesn't support 4K — caller is expected to upgrade tier."""
    with pytest.raises(ValueError, match='standard.*4K'):
        estimate_recraft_cost(tier='standard', resolution='4K')


def test_recraft_cost_unknown_tier():
    with pytest.raises(ValueError, match='Unknown'):
        estimate_recraft_cost(tier='ultra', resolution='1K')


def test_recraft_upscale_cost_override_via_env(monkeypatch):
    """RECRAFT_UPSCALE_COST_USD env var overrides the assumed parity price.

    Used to hot-fix the 4K chain cost if the upscale price isn't the assumed
    $0.25. See spike report for context."""
    monkeypatch.setenv('RECRAFT_UPSCALE_COST_USD', '0.30')
    cost_4k = estimate_recraft_cost(tier='pro', resolution='4K')
    assert cost_4k == 0.55  # 0.25 (2K) + 0.30 (override upscale)


from unittest import mock
import os


def test_generate_recraft_direct_1k_calls_recraft_api(monkeypatch, tmp_path):
    """Direct API path: 1K standard tier hits Recraft generation endpoint."""
    monkeypatch.setenv('RECRAFT_API_KEY', 'test-key')

    fake_response = mock.Mock()
    fake_response.data = [mock.Mock(url='https://example.com/img.png')]

    fake_get = mock.Mock(return_value=mock.Mock(content=b'PNG_BYTES'))
    fake_openai = mock.Mock()
    fake_openai.return_value.images.generate.return_value = fake_response

    out = tmp_path / 'out.png'
    with mock.patch('src.generate_cloud_image.OpenAI', fake_openai), \
         mock.patch('src.generate_cloud_image.requests.get', fake_get):
        from src.generate_cloud_image import generate_recraft_direct
        result = generate_recraft_direct(
            prompt='a brand badge',
            output_path=str(out),
            tier='standard',
            resolution='1K',
        )

    assert result['status'] == 'generated'
    assert result['provider'] == 'recraft'
    assert result['tier'] == 'standard'
    assert result['resolution'] == '1K'
    assert out.read_bytes() == b'PNG_BYTES'
    fake_openai.assert_called_with(
        base_url='https://external.api.recraft.ai/v1',
        api_key='test-key',
    )


def test_generate_recraft_direct_brand_colors_passed(monkeypatch, tmp_path):
    """Brand colors must be forwarded as Recraft `controls.colors` rgb dicts."""
    monkeypatch.setenv('RECRAFT_API_KEY', 'test-key')

    fake_response = mock.Mock()
    fake_response.data = [mock.Mock(url='https://example.com/img.png')]
    fake_get = mock.Mock(return_value=mock.Mock(content=b'PNG'))
    fake_openai = mock.Mock()
    fake_openai.return_value.images.generate.return_value = fake_response

    with mock.patch('src.generate_cloud_image.OpenAI', fake_openai), \
         mock.patch('src.generate_cloud_image.requests.get', fake_get):
        from src.generate_cloud_image import generate_recraft_direct
        generate_recraft_direct(
            prompt='a brand badge',
            output_path=str(tmp_path / 'out.png'),
            tier='standard',
            resolution='1K',
            colors=[
                {'rgb': [0, 51, 102]},
                {'rgb': [255, 204, 0]},
            ],
        )

    call_kwargs = fake_openai.return_value.images.generate.call_args.kwargs
    extra_body = call_kwargs['extra_body']
    assert extra_body['controls']['colors'] == [
        {'rgb': [0, 51, 102]},
        {'rgb': [255, 204, 0]},
    ]


def test_generate_recraft_direct_unsupported_resolution_raises(monkeypatch, tmp_path):
    """Standard tier doesn't support 2K/4K — must raise without making API call."""
    monkeypatch.setenv('RECRAFT_API_KEY', 'test-key')

    with pytest.raises(ProviderResolutionUnsupportedError) as exc:
        from src.generate_cloud_image import generate_recraft_direct
        generate_recraft_direct(
            prompt='x',
            output_path=str(tmp_path / 'out.png'),
            tier='standard',
            resolution='2K',
        )
    assert exc.value.requested == '2K'
    assert '1K' in exc.value.supported


def test_generate_recraft_direct_no_api_key():
    from src.generate_cloud_image import (
        generate_recraft_direct,
        ProviderNotConfiguredError,
    )
    with mock.patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ProviderNotConfiguredError, match='RECRAFT_API_KEY'):
            generate_recraft_direct(
                prompt='x',
                output_path='/tmp/x.png',
                tier='standard',
                resolution='1K',
            )
