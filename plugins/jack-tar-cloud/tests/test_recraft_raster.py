"""Tests for Recraft V4 raster provider — cost helpers, dual-path generation,
4K via Creative Upscale chain."""
import os
import sys
from pathlib import Path
from unittest import mock

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


def test_generate_recraft_fal_1k_calls_text_to_image(monkeypatch, tmp_path):
    monkeypatch.setenv('FAL_KEY', 'test-fal')

    fake_subscribe = mock.Mock(return_value={
        'images': [{'url': 'https://example.com/img.png'}]
    })
    fake_get = mock.Mock(return_value=mock.Mock(content=b'PNG'))

    with mock.patch('src.generate_cloud_image.fal_client.subscribe', fake_subscribe), \
         mock.patch('src.generate_cloud_image.requests.get', fake_get):
        from src.generate_cloud_image import generate_recraft_fal
        result = generate_recraft_fal(
            prompt='a brand badge',
            output_path=str(tmp_path / 'out.png'),
            tier='standard',
            resolution='1K',
        )

    assert result['status'] == 'generated'
    assert result['provider'] == 'fal-recraft'
    fake_subscribe.assert_called_once()
    args = fake_subscribe.call_args
    assert args[0][0] == 'fal-ai/recraft/v4/text-to-image'


def test_generate_recraft_fal_2k_calls_pro_endpoint(monkeypatch, tmp_path):
    monkeypatch.setenv('FAL_KEY', 'test-fal')

    fake_subscribe = mock.Mock(return_value={
        'images': [{'url': 'https://example.com/img.png'}]
    })
    fake_get = mock.Mock(return_value=mock.Mock(content=b'PNG'))

    with mock.patch('src.generate_cloud_image.fal_client.subscribe', fake_subscribe), \
         mock.patch('src.generate_cloud_image.requests.get', fake_get):
        from src.generate_cloud_image import generate_recraft_fal
        generate_recraft_fal(
            prompt='x',
            output_path=str(tmp_path / 'out.png'),
            tier='pro',
            resolution='2K',
        )

    args = fake_subscribe.call_args
    assert args[0][0] == 'fal-ai/recraft/v4/pro/text-to-image'


def test_generate_recraft_fal_4k_chains_through_upscale(monkeypatch, tmp_path):
    """4K = 2K Pro generation followed by fal-ai/recraft/upscale/creative."""
    monkeypatch.setenv('FAL_KEY', 'test-fal')

    fake_subscribe = mock.Mock(side_effect=[
        {'images': [{'url': 'https://example.com/2k.png'}]},
        {'image': {'url': 'https://example.com/4k.png'}},
    ])
    fake_get = mock.Mock(return_value=mock.Mock(content=b'PNG'))

    with mock.patch('src.generate_cloud_image.fal_client.subscribe', fake_subscribe), \
         mock.patch('src.generate_cloud_image.requests.get', fake_get):
        from src.generate_cloud_image import generate_recraft_fal
        result = generate_recraft_fal(
            prompt='x',
            output_path=str(tmp_path / 'out.png'),
            tier='pro',
            resolution='4K',
        )

    assert result['resolution'] == '4K'
    second_call_args = fake_subscribe.call_args_list[1]
    assert second_call_args[0][0] == 'fal-ai/recraft/upscale/creative'
    # Second call should pass the 2K url as image_url
    second_kwargs = second_call_args.kwargs
    assert second_kwargs.get('arguments', {}).get('image_url') == 'https://example.com/2k.png'


def test_dispatch_recognises_recraft_provider(monkeypatch, tmp_path):
    """generate_cloud_image(provider='recraft', ...) routes to the new func."""
    # Ensure RECRAFT keys are NOT set so dispatch picks FAL
    for key in ['RECRAFT_API_KEY', 'RECRAFT_API']:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv('FAL_KEY', 'test-fal')

    fake_subscribe = mock.Mock(return_value={
        'images': [{'url': 'https://example.com/img.png'}]
    })
    fake_get = mock.Mock(return_value=mock.Mock(content=b'PNG'))

    with mock.patch('src.generate_cloud_image.fal_client.subscribe', fake_subscribe), \
         mock.patch('src.generate_cloud_image.requests.get', fake_get):
        from src.generate_cloud_image import generate_cloud_image
        result = generate_cloud_image(
            prompt='x',
            provider='recraft',
            output_path=str(tmp_path / 'out.png'),
            resolution='1K',
            tier='standard',
        )

    assert result['provider'] == 'fal-recraft'


def test_dispatch_recraft_picks_standard_tier_for_1k(monkeypatch, tmp_path):
    """When caller doesn't specify tier but passes resolution='1K',
    dispatch should derive tier='standard' so the call succeeds."""
    for key in ['RECRAFT_API_KEY', 'RECRAFT_API']:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv('FAL_KEY', 'test-fal')

    fake_subscribe = mock.Mock(return_value={
        'images': [{'url': 'https://example.com/img.png'}]
    })
    fake_get = mock.Mock(return_value=mock.Mock(content=b'PNG'))

    with mock.patch('src.generate_cloud_image.fal_client.subscribe', fake_subscribe), \
         mock.patch('src.generate_cloud_image.requests.get', fake_get):
        from src.generate_cloud_image import generate_cloud_image
        # Caller passes resolution but NOT tier — dispatch must derive
        result = generate_cloud_image(
            prompt='x',
            provider='recraft',
            output_path=str(tmp_path / 'out.png'),
            resolution='1K',
        )

    assert result['tier'] == 'standard'
    assert result['resolution'] == '1K'
    # Confirm the standard endpoint was hit
    args = fake_subscribe.call_args
    assert args[0][0] == 'fal-ai/recraft/v4/text-to-image'


def test_dispatch_recraft_picks_pro_tier_for_4k(monkeypatch, tmp_path):
    """When caller passes resolution='4K' without tier, dispatch picks pro."""
    for key in ['RECRAFT_API_KEY', 'RECRAFT_API']:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv('FAL_KEY', 'test-fal')

    fake_subscribe = mock.Mock(side_effect=[
        {'images': [{'url': 'https://example.com/2k.png'}]},
        {'image': {'url': 'https://example.com/4k.png'}},
    ])
    fake_get = mock.Mock(return_value=mock.Mock(content=b'PNG'))

    with mock.patch('src.generate_cloud_image.fal_client.subscribe', fake_subscribe), \
         mock.patch('src.generate_cloud_image.requests.get', fake_get):
        from src.generate_cloud_image import generate_cloud_image
        result = generate_cloud_image(
            prompt='x',
            provider='recraft',
            output_path=str(tmp_path / 'out.png'),
            resolution='4K',
        )

    assert result['tier'] == 'pro'
    assert result['resolution'] == '4K'


def test_provider_discovery_includes_recraft_raster_models(monkeypatch):
    """Recraft entry must surface raster supported_resolutions for routing
    decisions and cross-plugin drift checks. Models surface is populated
    regardless of availability — the iteration over _PROVIDER_MODEL_RESOLUTIONS
    runs unconditionally, so the test should pass even when no Recraft env
    var is set (e.g. in CI)."""
    # Defensive: clear any inherited env so the test is hermetic
    for key in ['RECRAFT_API_KEY', 'RECRAFT_API', 'FAL_KEY']:
        monkeypatch.delenv(key, raising=False)
    from src.provider_discovery import discover_providers
    providers = discover_providers()
    recraft = providers.get('recraft')
    assert recraft is not None
    # Raster surface — new in #61. Populated by the post-probe loop over
    # _PROVIDER_MODEL_RESOLUTIONS regardless of availability state.
    models = recraft.get('models', {})
    assert 'recraft-v4-standard' in models, (
        f"recraft entry missing 'recraft-v4-standard' in models: {recraft!r}"
    )
    assert models['recraft-v4-standard']['supported_resolutions'] == ['1K']
    assert 'recraft-v4-pro' in models
    assert models['recraft-v4-pro']['supported_resolutions'] == ['2K', '4K']


def test_provider_discovery_recraft_available_when_recraft_api_set(monkeypatch):
    """When RECRAFT_API_KEY is set, the recraft entry is marked available."""
    for key in ['RECRAFT_API_KEY', 'RECRAFT_API', 'FAL_KEY']:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv('RECRAFT_API_KEY', 'test-key')
    from src.provider_discovery import discover_providers
    providers = discover_providers()
    assert providers['recraft']['available'] is True


# Issue #73 — V4 default style ----------------------------------------

def test_generate_recraft_direct_omits_style_by_default(monkeypatch, tmp_path):
    """Issue #73: the V4 API rejects the legacy default ``style='realistic_image'``
    with 400 invalid_image_type. With the default left to None, the call must
    not pass a ``style`` argument at all — Recraft V4 will pick a default
    server-side."""
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
        )

    call_kwargs = fake_openai.return_value.images.generate.call_args.kwargs
    assert 'style' not in call_kwargs, (
        f"V4 default invocation must not pass 'style'. Got kwargs: {call_kwargs!r}"
    )


def test_generate_recraft_direct_passes_explicit_style_when_supplied(monkeypatch, tmp_path):
    """Issue #73 (positive case): when the caller explicitly supplies a style
    that V4 accepts (e.g. ``digital_illustration_pixel_art``), it must be
    forwarded to the API call."""
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
            prompt='a pixel-art badge',
            output_path=str(tmp_path / 'out.png'),
            tier='standard',
            resolution='1K',
            style='digital_illustration_pixel_art',
        )

    call_kwargs = fake_openai.return_value.images.generate.call_args.kwargs
    assert call_kwargs.get('style') == 'digital_illustration_pixel_art'


def test_dispatch_recraft_falls_back_to_fal_on_v4_style_error(monkeypatch, tmp_path):
    """Issue #73 (defensive fall-through): if the direct API still rejects a
    style preset (e.g. the API changes its accepted styles in the future),
    and FAL_KEY is also configured, fall through to the FAL route which
    accepts no style parameter. The user is unblocked."""
    import openai

    monkeypatch.setenv('RECRAFT_API_KEY', 'test-key')
    monkeypatch.setenv('FAL_KEY', 'fal-key')

    request = mock.Mock()
    body = {'code': 'invalid_image_type',
            'message': "Recraft V4 doesn't support style 'whatever'"}
    bad_request = openai.BadRequestError(
        message="Recraft V4 doesn't support style 'whatever'",
        response=mock.Mock(status_code=400, request=request),
        body=body,
    )

    direct_called = []
    fal_called = []

    def fake_direct(prompt, output_path, **kwargs):
        direct_called.append((prompt, kwargs))
        raise bad_request

    def fake_fal(prompt, output_path, **kwargs):
        fal_called.append((prompt, kwargs))
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b'PNG_FROM_FAL')
        return {
            'file_path': str(output_path),
            'provider': 'fal-recraft',
            'tier': kwargs.get('tier', 'standard'),
            'resolution': kwargs.get('resolution', '1K'),
            'model_used': f"recraft-v4-{kwargs.get('tier', 'standard')}",
            'cost_usd': 0.04,
            'status': 'generated',
        }

    out = tmp_path / 'out.png'
    with mock.patch('src.generate_cloud_image.generate_recraft_direct', side_effect=fake_direct), \
         mock.patch('src.generate_cloud_image.generate_recraft_fal', side_effect=fake_fal):
        from src.generate_cloud_image import _dispatch_recraft
        result = _dispatch_recraft(
            prompt='a brand badge',
            output_path=str(out),
            resolution='1K',
            style='whatever-the-api-now-rejects',
        )

    assert direct_called, "direct path should have been attempted"
    assert fal_called, "FAL fall-through must fire on V4-style 400"
    assert result['provider'] == 'fal-recraft'
    assert out.read_bytes() == b'PNG_FROM_FAL'


def test_dispatch_recraft_does_not_fall_back_on_unrelated_400(monkeypatch, tmp_path):
    """Issue #73: only V4-style errors trigger the fall-through. Other 400s
    (rate-limit, content-policy, malformed request) must propagate so the
    operator sees the real cause."""
    import openai

    monkeypatch.setenv('RECRAFT_API_KEY', 'test-key')
    monkeypatch.setenv('FAL_KEY', 'fal-key')

    request = mock.Mock()
    body = {'code': 'content_policy_violation',
            'message': 'Prompt rejected by content policy'}
    bad_request = openai.BadRequestError(
        message='Prompt rejected by content policy',
        response=mock.Mock(status_code=400, request=request),
        body=body,
    )

    fal_called = []

    def fake_direct(prompt, output_path, **kwargs):
        raise bad_request

    def fake_fal(prompt, output_path, **kwargs):
        fal_called.append((prompt, kwargs))

    with mock.patch('src.generate_cloud_image.generate_recraft_direct', side_effect=fake_direct), \
         mock.patch('src.generate_cloud_image.generate_recraft_fal', side_effect=fake_fal):
        from src.generate_cloud_image import _dispatch_recraft
        with pytest.raises(openai.BadRequestError):
            _dispatch_recraft(
                prompt='a brand badge',
                output_path=str(tmp_path / 'out.png'),
                resolution='1K',
            )

    assert not fal_called, "FAL fall-through must NOT fire on non-style 400s"


def test_dispatch_recraft_does_not_fall_back_when_fal_unconfigured(monkeypatch, tmp_path):
    """Issue #73: if FAL_KEY is not set, even a V4-style 400 must propagate —
    we cannot silently succeed when the only working route is unavailable."""
    import openai

    monkeypatch.setenv('RECRAFT_API_KEY', 'test-key')
    monkeypatch.delenv('FAL_KEY', raising=False)

    request = mock.Mock()
    body = {'code': 'invalid_image_type',
            'message': "Recraft V4 doesn't support style 'realistic_image'"}
    bad_request = openai.BadRequestError(
        message="Recraft V4 doesn't support style 'realistic_image'",
        response=mock.Mock(status_code=400, request=request),
        body=body,
    )

    def fake_direct(prompt, output_path, **kwargs):
        raise bad_request

    with mock.patch('src.generate_cloud_image.generate_recraft_direct', side_effect=fake_direct):
        from src.generate_cloud_image import _dispatch_recraft
        with pytest.raises(openai.BadRequestError):
            _dispatch_recraft(
                prompt='a brand badge',
                output_path=str(tmp_path / 'out.png'),
                resolution='1K',
            )
