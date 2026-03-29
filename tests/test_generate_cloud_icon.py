"""Tests for cloud icon generation — Recraft V4 SVG + FAL fallback."""

import os
from unittest.mock import MagicMock, patch

import pytest


# --- Helpers ---

FAKE_SVG = b'<svg xmlns="http://www.w3.org/2000/svg"><circle r="10"/></svg>'


def _mock_recraft_response(url='https://recraft.example.com/icon.svg'):
    """Build a mock OpenAI-compatible response with a URL."""
    mock_image = MagicMock()
    mock_image.url = url
    mock_response = MagicMock()
    mock_response.data = [mock_image]
    return mock_response


def _mock_requests_get(content=FAKE_SVG, status_code=200):
    """Build a mock requests.get response."""
    mock_resp = MagicMock()
    mock_resp.content = content
    mock_resp.status_code = status_code
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# --- Recraft direct API ---

class TestGenerateRecraftDirect:
    def test_raises_not_configured_when_env_missing(self, tmp_path):
        from src.generate_cloud_icon import generate_recraft_direct, ProviderNotConfiguredError

        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {'PATH': '/usr/bin'}):
                with pytest.raises(ProviderNotConfiguredError, match='RECRAFT_API_KEY'):
                    generate_recraft_direct(
                        prompt='A handshake icon',
                        output_path=str(output),
                    )

    def test_generates_svg_and_saves_to_path(self, tmp_path):
        from src.generate_cloud_icon import generate_recraft_direct

        mock_response = _mock_recraft_response()
        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'RECRAFT_API_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.OpenAI', return_value=mock_client):
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    result = generate_recraft_direct(
                        prompt='A simple anchor icon',
                        output_path=str(output),
                    )

        assert output.exists()
        assert output.read_bytes() == FAKE_SVG
        assert result['file_path'] == str(output)
        assert result['provider'] == 'recraft'
        assert result['model_used'] == 'recraftv4'
        assert result['status'] == 'generated'
        assert result['output_format'] == 'svg'

    def test_passes_brand_colors_to_api(self, tmp_path):
        from src.generate_cloud_icon import generate_recraft_direct

        mock_response = _mock_recraft_response()
        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        colors = [
            {'rgb': [0, 51, 102]},
            {'rgb': [255, 204, 0]},
        ]
        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'RECRAFT_API_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.OpenAI', return_value=mock_client):
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    generate_recraft_direct(
                        prompt='A compass icon',
                        output_path=str(output),
                        colors=colors,
                    )

        call_kwargs = mock_client.images.generate.call_args[1]
        controls = call_kwargs['extra_body']['controls']
        assert controls['colors'] == colors

    def test_returns_correct_cost_standard(self, tmp_path):
        from src.generate_cloud_icon import generate_recraft_direct

        mock_response = _mock_recraft_response()
        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'RECRAFT_API_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.OpenAI', return_value=mock_client):
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    result = generate_recraft_direct(
                        prompt='test',
                        output_path=str(output),
                        tier='standard',
                    )

        assert result['cost_usd'] == 0.08

    def test_returns_correct_cost_pro(self, tmp_path):
        from src.generate_cloud_icon import generate_recraft_direct

        mock_response = _mock_recraft_response()
        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'RECRAFT_API_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.OpenAI', return_value=mock_client):
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    result = generate_recraft_direct(
                        prompt='test',
                        output_path=str(output),
                        tier='pro',
                    )

        assert result['cost_usd'] == 0.30

    def test_uses_vector_illustration_style_by_default(self, tmp_path):
        from src.generate_cloud_icon import generate_recraft_direct

        mock_response = _mock_recraft_response()
        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'RECRAFT_API_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.OpenAI', return_value=mock_client):
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    generate_recraft_direct(
                        prompt='test',
                        output_path=str(output),
                    )

        call_kwargs = mock_client.images.generate.call_args[1]
        assert call_kwargs['style'] == 'vector_illustration'

    def test_connects_to_recraft_endpoint(self, tmp_path):
        from src.generate_cloud_icon import generate_recraft_direct

        mock_response = _mock_recraft_response()
        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'RECRAFT_API_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.OpenAI', return_value=mock_client) as mock_openai_cls:
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    generate_recraft_direct(
                        prompt='test',
                        output_path=str(output),
                    )

        mock_openai_cls.assert_called_once_with(
            base_url='https://external.api.recraft.ai/v1',
            api_key='fake-key',
        )

    def test_accepts_recraft_api_env_as_fallback(self, tmp_path):
        """RECRAFT_API env var should work when RECRAFT_API_KEY is not set."""
        from src.generate_cloud_icon import generate_recraft_direct

        mock_response = _mock_recraft_response()
        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'RECRAFT_API': 'alt-key'}, clear=True):
            with patch.dict(os.environ, {'PATH': '/usr/bin'}):
                with patch('src.generate_cloud_icon.OpenAI', return_value=mock_client) as mock_openai_cls:
                    with patch('src.generate_cloud_icon.requests') as mock_requests:
                        mock_requests.get.return_value = _mock_requests_get()
                        generate_recraft_direct(
                            prompt='test',
                            output_path=str(output),
                        )

        mock_openai_cls.assert_called_once_with(
            base_url='https://external.api.recraft.ai/v1',
            api_key='alt-key',
        )

    def test_downloads_svg_from_url(self, tmp_path):
        from src.generate_cloud_icon import generate_recraft_direct

        svg_url = 'https://recraft.example.com/output/icon123.svg'
        mock_response = _mock_recraft_response(url=svg_url)
        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'RECRAFT_API_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.OpenAI', return_value=mock_client):
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    generate_recraft_direct(
                        prompt='test',
                        output_path=str(output),
                    )

        mock_requests.get.assert_called_once_with(svg_url, timeout=30)

    def test_creates_parent_directories(self, tmp_path):
        from src.generate_cloud_icon import generate_recraft_direct

        mock_response = _mock_recraft_response()
        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'deep' / 'nested' / 'icon.svg'
        with patch.dict(os.environ, {'RECRAFT_API_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.OpenAI', return_value=mock_client):
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    generate_recraft_direct(
                        prompt='test',
                        output_path=str(output),
                    )

        assert output.exists()


# --- FAL.ai Recraft V4 ---

class TestGenerateFalRecraft:
    def test_raises_not_configured_when_env_missing(self, tmp_path):
        from src.generate_cloud_icon import generate_fal_recraft, ProviderNotConfiguredError

        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {'PATH': '/usr/bin'}):
                with pytest.raises(ProviderNotConfiguredError, match='FAL_KEY'):
                    generate_fal_recraft(
                        prompt='A database icon',
                        output_path=str(output),
                    )

    def test_generates_svg_and_saves_to_path(self, tmp_path):
        from src.generate_cloud_icon import generate_fal_recraft

        fal_result = {
            'images': [{'url': 'https://fal.example.com/icon.svg'}],
        }
        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.fal_client') as mock_fal:
                mock_fal.subscribe.return_value = fal_result
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    result = generate_fal_recraft(
                        prompt='A minimalist handshake icon',
                        output_path=str(output),
                    )

        assert output.exists()
        assert output.read_bytes() == FAKE_SVG
        assert result['file_path'] == str(output)
        assert result['provider'] == 'fal'
        assert result['model_used'] == 'recraft-v4'
        assert result['status'] == 'generated'
        assert result['output_format'] == 'svg'

    def test_passes_colors_to_fal(self, tmp_path):
        from src.generate_cloud_icon import generate_fal_recraft

        fal_result = {
            'images': [{'url': 'https://fal.example.com/icon.svg'}],
        }
        colors = [
            {'r': 0, 'g': 102, 'b': 204},
            {'r': 255, 'g': 255, 'b': 255},
        ]
        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.fal_client') as mock_fal:
                mock_fal.subscribe.return_value = fal_result
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    generate_fal_recraft(
                        prompt='test',
                        output_path=str(output),
                        colors=colors,
                    )

        call_args = mock_fal.subscribe.call_args
        arguments = call_args[1]['arguments'] if 'arguments' in (call_args[1] or {}) else call_args[0][1]
        assert arguments['colors'] == colors

    def test_returns_correct_cost_standard(self, tmp_path):
        from src.generate_cloud_icon import generate_fal_recraft

        fal_result = {
            'images': [{'url': 'https://fal.example.com/icon.svg'}],
        }
        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.fal_client') as mock_fal:
                mock_fal.subscribe.return_value = fal_result
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    result = generate_fal_recraft(
                        prompt='test',
                        output_path=str(output),
                        tier='standard',
                    )

        assert result['cost_usd'] == 0.08

    def test_returns_correct_cost_pro(self, tmp_path):
        from src.generate_cloud_icon import generate_fal_recraft

        fal_result = {
            'images': [{'url': 'https://fal.example.com/icon.svg'}],
        }
        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.fal_client') as mock_fal:
                mock_fal.subscribe.return_value = fal_result
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    result = generate_fal_recraft(
                        prompt='test',
                        output_path=str(output),
                        tier='pro',
                    )

        assert result['cost_usd'] == 0.30

    def test_calls_correct_fal_endpoint(self, tmp_path):
        from src.generate_cloud_icon import generate_fal_recraft

        fal_result = {
            'images': [{'url': 'https://fal.example.com/icon.svg'}],
        }
        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.fal_client') as mock_fal:
                mock_fal.subscribe.return_value = fal_result
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    generate_fal_recraft(
                        prompt='test',
                        output_path=str(output),
                    )

        call_args = mock_fal.subscribe.call_args
        assert call_args[0][0] == 'fal-ai/recraft/v4/text-to-vector'

    def test_downloads_svg_from_url(self, tmp_path):
        from src.generate_cloud_icon import generate_fal_recraft

        svg_url = 'https://fal.example.com/output/icon456.svg'
        fal_result = {
            'images': [{'url': svg_url}],
        }
        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.fal_client') as mock_fal:
                mock_fal.subscribe.return_value = fal_result
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    generate_fal_recraft(
                        prompt='test',
                        output_path=str(output),
                    )

        mock_requests.get.assert_called_once_with(svg_url, timeout=30)

    def test_creates_parent_directories(self, tmp_path):
        from src.generate_cloud_icon import generate_fal_recraft

        fal_result = {
            'images': [{'url': 'https://fal.example.com/icon.svg'}],
        }
        output = tmp_path / 'deep' / 'nested' / 'icon.svg'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.fal_client') as mock_fal:
                mock_fal.subscribe.return_value = fal_result
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    generate_fal_recraft(
                        prompt='test',
                        output_path=str(output),
                    )

        assert output.exists()


# --- Dispatch function ---

class TestGenerateCloudIcon:
    def test_raises_for_unknown_provider(self, tmp_path):
        from src.generate_cloud_icon import generate_cloud_icon

        output = tmp_path / 'icon.svg'
        with pytest.raises(ValueError, match='bogus'):
            generate_cloud_icon(
                prompt='test',
                provider='bogus',
                output_path=str(output),
            )

    def test_dispatches_to_recraft(self, tmp_path):
        from src.generate_cloud_icon import generate_cloud_icon

        mock_response = _mock_recraft_response()
        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'RECRAFT_API_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.OpenAI', return_value=mock_client):
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    result = generate_cloud_icon(
                        prompt='test',
                        provider='recraft',
                        output_path=str(output),
                    )

        assert result['provider'] == 'recraft'
        assert output.exists()

    def test_dispatches_to_fal(self, tmp_path):
        from src.generate_cloud_icon import generate_cloud_icon

        fal_result = {
            'images': [{'url': 'https://fal.example.com/icon.svg'}],
        }
        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.fal_client') as mock_fal:
                mock_fal.subscribe.return_value = fal_result
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    result = generate_cloud_icon(
                        prompt='test',
                        provider='fal',
                        output_path=str(output),
                    )

        assert result['provider'] == 'fal'
        assert output.exists()

    def test_passes_colors_through_to_provider(self, tmp_path):
        from src.generate_cloud_icon import generate_cloud_icon

        mock_response = _mock_recraft_response()
        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        colors = [{'rgb': [0, 102, 204]}]
        output = tmp_path / 'icon.svg'
        with patch.dict(os.environ, {'RECRAFT_API_KEY': 'fake-key'}):
            with patch('src.generate_cloud_icon.OpenAI', return_value=mock_client):
                with patch('src.generate_cloud_icon.requests') as mock_requests:
                    mock_requests.get.return_value = _mock_requests_get()
                    result = generate_cloud_icon(
                        prompt='test',
                        provider='recraft',
                        output_path=str(output),
                        colors=colors,
                    )

        assert result['status'] == 'generated'


# --- Cost estimation ---

class TestIconCostEstimate:
    def test_recraft_svg_cost(self):
        from src.generate_cloud_icon import estimate_icon_cost

        cost = estimate_icon_cost(provider='recraft', tier='standard')
        assert cost == 0.08

    def test_recraft_pro_svg_cost(self):
        from src.generate_cloud_icon import estimate_icon_cost

        cost = estimate_icon_cost(provider='recraft', tier='pro')
        assert cost == 0.30

    def test_fal_recraft_svg_cost(self):
        from src.generate_cloud_icon import estimate_icon_cost

        cost = estimate_icon_cost(provider='fal', tier='standard')
        assert cost == 0.08

    def test_fal_recraft_pro_svg_cost(self):
        from src.generate_cloud_icon import estimate_icon_cost

        cost = estimate_icon_cost(provider='fal', tier='pro')
        assert cost == 0.30

    def test_unknown_provider_raises(self):
        from src.generate_cloud_icon import estimate_icon_cost

        with pytest.raises(ValueError):
            estimate_icon_cost(provider='dall-e', tier='standard')

    def test_unknown_tier_raises(self):
        from src.generate_cloud_icon import estimate_icon_cost

        with pytest.raises(ValueError):
            estimate_icon_cost(provider='recraft', tier='ultra')
