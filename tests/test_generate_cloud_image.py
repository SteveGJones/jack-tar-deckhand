"""Tests for cloud image generation — OpenAI (mocked), Google (mocked), stubs for unconfigured providers."""

import base64
import os
from unittest.mock import MagicMock, patch

import pytest


# --- Helpers ---

def _fake_png_b64():
    """Return base64-encoded 1x1 red PNG for mocking API responses."""
    # Minimal valid PNG: 1x1 pixel, red
    import struct
    import zlib

    def _chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = _chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
    raw = b'\x00\xff\x00\x00'  # filter byte + RGB
    idat = _chunk(b'IDAT', zlib.compress(raw))
    iend = _chunk(b'IEND', b'')
    png_bytes = sig + ihdr + idat + iend
    return base64.b64encode(png_bytes).decode('ascii'), png_bytes


def _fake_png_bytes():
    """Return raw bytes for a minimal valid PNG (1x1 red pixel)."""
    _, raw = _fake_png_b64()
    return raw


# --- OpenAI generation ---

class TestGenerateOpenAI:
    def test_generates_image_and_saves_to_path(self, tmp_path):
        from src.generate_cloud_image import generate_openai

        b64_data, raw_bytes = _fake_png_b64()
        mock_image = MagicMock()
        mock_image.b64_json = b64_data
        mock_response = MagicMock()
        mock_response.data = [mock_image]

        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch('src.generate_cloud_image.OpenAI', return_value=mock_client):
            result = generate_openai(
                prompt='A futuristic cityscape',
                output_path=str(output),
            )

        assert output.exists()
        assert output.read_bytes() == raw_bytes
        assert result['file_path'] == str(output)
        assert result['provider'] == 'openai'
        assert result['model_used'] == 'gpt-image-1.5'
        assert result['status'] == 'generated'

    def test_uses_medium_quality_by_default(self, tmp_path):
        from src.generate_cloud_image import generate_openai

        b64_data, _ = _fake_png_b64()
        mock_image = MagicMock()
        mock_image.b64_json = b64_data
        mock_response = MagicMock()
        mock_response.data = [mock_image]

        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch('src.generate_cloud_image.OpenAI', return_value=mock_client):
            generate_openai(prompt='test', output_path=str(output))

        call_kwargs = mock_client.images.generate.call_args[1]
        assert call_kwargs['quality'] == 'medium'

    def test_uses_landscape_size_by_default(self, tmp_path):
        from src.generate_cloud_image import generate_openai

        b64_data, _ = _fake_png_b64()
        mock_image = MagicMock()
        mock_image.b64_json = b64_data
        mock_response = MagicMock()
        mock_response.data = [mock_image]

        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch('src.generate_cloud_image.OpenAI', return_value=mock_client):
            generate_openai(prompt='test', output_path=str(output))

        call_kwargs = mock_client.images.generate.call_args[1]
        assert call_kwargs['size'] == '1536x1024'

    def test_supports_transparent_background(self, tmp_path):
        from src.generate_cloud_image import generate_openai

        b64_data, _ = _fake_png_b64()
        mock_image = MagicMock()
        mock_image.b64_json = b64_data
        mock_response = MagicMock()
        mock_response.data = [mock_image]

        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch('src.generate_cloud_image.OpenAI', return_value=mock_client):
            generate_openai(
                prompt='test',
                output_path=str(output),
                background='transparent',
            )

        call_kwargs = mock_client.images.generate.call_args[1]
        assert call_kwargs['background'] == 'transparent'
        assert call_kwargs['output_format'] == 'png'

    def test_overrides_quality_and_size(self, tmp_path):
        from src.generate_cloud_image import generate_openai

        b64_data, _ = _fake_png_b64()
        mock_image = MagicMock()
        mock_image.b64_json = b64_data
        mock_response = MagicMock()
        mock_response.data = [mock_image]

        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch('src.generate_cloud_image.OpenAI', return_value=mock_client):
            generate_openai(
                prompt='test',
                output_path=str(output),
                quality='high',
                size='1024x1024',
            )

        call_kwargs = mock_client.images.generate.call_args[1]
        assert call_kwargs['quality'] == 'high'
        assert call_kwargs['size'] == '1024x1024'

    def test_returns_cost_estimate(self, tmp_path):
        from src.generate_cloud_image import generate_openai

        b64_data, _ = _fake_png_b64()
        mock_image = MagicMock()
        mock_image.b64_json = b64_data
        mock_response = MagicMock()
        mock_response.data = [mock_image]

        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch('src.generate_cloud_image.OpenAI', return_value=mock_client):
            result = generate_openai(prompt='test', output_path=str(output))

        assert 'cost_usd' in result
        assert isinstance(result['cost_usd'], float)
        assert result['cost_usd'] > 0

    def test_raises_on_missing_api_key(self, tmp_path):
        from src.generate_cloud_image import generate_openai, ProviderNotConfiguredError

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {'PATH': '/usr/bin'}):
                with pytest.raises(ProviderNotConfiguredError, match='OPENAI_API_KEY'):
                    generate_openai(prompt='test', output_path=str(output))


# --- Google (Gemini Developer API / Vertex AI) ---

class TestGenerateGoogle:
    """Tests for Google image generation via Nano Banana and Imagen 4 models."""

    def test_raises_not_configured_when_no_google_env(self, tmp_path):
        from src.generate_cloud_image import generate_google, ProviderNotConfiguredError

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {'PATH': '/usr/bin'}):
                with pytest.raises(ProviderNotConfiguredError, match='GOOGLE_API_KEY'):
                    generate_google(prompt='test', output_path=str(output))

    def test_default_model_is_nano_banana_flash(self, tmp_path):
        """Default model should be gemini-3.1-flash-image-preview (cheapest, fastest)."""
        from src.generate_cloud_image import generate_google

        png_bytes = _fake_png_bytes()

        mock_part = MagicMock()
        mock_part.inline_data.mime_type = 'image/png'
        mock_part.inline_data.data = png_bytes

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            with patch('src.generate_cloud_image.genai.Client', return_value=mock_client):
                result = generate_google(prompt='A futuristic city', output_path=str(output))

        assert result['model_used'] == 'gemini-3.1-flash-image-preview'
        mock_client.models.generate_content.assert_called_once()

    def test_nano_banana_flash_generates_and_saves(self, tmp_path):
        """Nano Banana Flash model should use generate_content and save the image."""
        from src.generate_cloud_image import generate_google

        png_bytes = _fake_png_bytes()

        mock_part = MagicMock()
        mock_part.inline_data.mime_type = 'image/png'
        mock_part.inline_data.data = png_bytes

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            with patch('src.generate_cloud_image.genai.Client', return_value=mock_client):
                result = generate_google(
                    prompt='A mountain landscape',
                    output_path=str(output),
                    model='gemini-3.1-flash-image-preview',
                )

        assert output.exists()
        assert output.read_bytes() == png_bytes
        assert result['file_path'] == str(output)
        assert result['provider'] == 'google'
        assert result['model_used'] == 'gemini-3.1-flash-image-preview'
        assert result['status'] == 'generated'

    def test_nano_banana_pro_routes_to_generate_content(self, tmp_path):
        """Nano Banana Pro model should also use generate_content API."""
        from src.generate_cloud_image import generate_google

        png_bytes = _fake_png_bytes()

        mock_part = MagicMock()
        mock_part.inline_data.mime_type = 'image/png'
        mock_part.inline_data.data = png_bytes

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            with patch('src.generate_cloud_image.genai.Client', return_value=mock_client):
                result = generate_google(
                    prompt='A sunset',
                    output_path=str(output),
                    model='gemini-3-pro-image-preview',
                )

        assert result['model_used'] == 'gemini-3-pro-image-preview'
        mock_client.models.generate_content.assert_called_once()
        mock_client.models.generate_images.assert_not_called()

    def test_imagen4_standard_routes_to_generate_images(self, tmp_path):
        """Imagen 4 standard model should use generate_images API."""
        from src.generate_cloud_image import generate_google

        png_bytes = _fake_png_bytes()

        mock_image = MagicMock()
        mock_image.image.image_bytes = png_bytes

        mock_response = MagicMock()
        mock_response.generated_images = [mock_image]

        mock_client = MagicMock()
        mock_client.models.generate_images.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            with patch('src.generate_cloud_image.genai.Client', return_value=mock_client):
                result = generate_google(
                    prompt='A dog playing fetch',
                    output_path=str(output),
                    model='imagen-4.0-generate-001',
                )

        assert output.exists()
        assert output.read_bytes() == png_bytes
        assert result['model_used'] == 'imagen-4.0-generate-001'
        assert result['provider'] == 'google'
        assert result['status'] == 'generated'
        mock_client.models.generate_images.assert_called_once()
        mock_client.models.generate_content.assert_not_called()

    def test_imagen4_fast_routes_to_generate_images(self, tmp_path):
        """Imagen 4 Fast model should also use generate_images API."""
        from src.generate_cloud_image import generate_google

        png_bytes = _fake_png_bytes()

        mock_image = MagicMock()
        mock_image.image.image_bytes = png_bytes

        mock_response = MagicMock()
        mock_response.generated_images = [mock_image]

        mock_client = MagicMock()
        mock_client.models.generate_images.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            with patch('src.generate_cloud_image.genai.Client', return_value=mock_client):
                result = generate_google(
                    prompt='An abstract pattern',
                    output_path=str(output),
                    model='imagen-4.0-fast-generate-001',
                )

        assert result['model_used'] == 'imagen-4.0-fast-generate-001'
        mock_client.models.generate_images.assert_called_once()
        mock_client.models.generate_content.assert_not_called()

    def test_imagen4_passes_aspect_ratio(self, tmp_path):
        """Imagen 4 should forward aspect_ratio kwarg to GenerateImagesConfig."""
        from src.generate_cloud_image import generate_google

        png_bytes = _fake_png_bytes()

        mock_image = MagicMock()
        mock_image.image.image_bytes = png_bytes

        mock_response = MagicMock()
        mock_response.generated_images = [mock_image]

        mock_client = MagicMock()
        mock_client.models.generate_images.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            with patch('src.generate_cloud_image.genai.Client', return_value=mock_client):
                with patch('src.generate_cloud_image.GenerateImagesConfig') as mock_config_cls:
                    mock_config_cls.return_value = MagicMock()
                    generate_google(
                        prompt='Wide landscape',
                        output_path=str(output),
                        model='imagen-4.0-generate-001',
                        aspect_ratio='16:9',
                    )

        mock_config_cls.assert_called_once()
        call_kwargs = mock_config_cls.call_args[1]
        assert call_kwargs['aspect_ratio'] == '16:9'

    def test_result_has_required_fields(self, tmp_path):
        """Result dict must have file_path, provider, model_used, cost_usd, status."""
        from src.generate_cloud_image import generate_google

        png_bytes = _fake_png_bytes()

        mock_part = MagicMock()
        mock_part.inline_data.mime_type = 'image/png'
        mock_part.inline_data.data = png_bytes

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            with patch('src.generate_cloud_image.genai.Client', return_value=mock_client):
                result = generate_google(prompt='test', output_path=str(output))

        required_fields = {'file_path', 'provider', 'model_used', 'cost_usd', 'status'}
        assert required_fields.issubset(result.keys())
        assert isinstance(result['cost_usd'], float)
        assert result['cost_usd'] > 0

    def test_nano_banana_content_config_has_image_modality(self, tmp_path):
        """Nano Banana calls should specify response_modalities=['IMAGE', 'TEXT']."""
        from src.generate_cloud_image import generate_google

        png_bytes = _fake_png_bytes()

        mock_part = MagicMock()
        mock_part.inline_data.mime_type = 'image/png'
        mock_part.inline_data.data = png_bytes

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            with patch('src.generate_cloud_image.genai.Client', return_value=mock_client):
                with patch('src.generate_cloud_image.GenerateContentConfig') as mock_config_cls:
                    mock_config_cls.return_value = MagicMock()
                    generate_google(prompt='test image', output_path=str(output))

        mock_config_cls.assert_called_once()
        call_kwargs = mock_config_cls.call_args[1]
        assert 'IMAGE' in call_kwargs['response_modalities']
        assert 'TEXT' in call_kwargs['response_modalities']

    def test_creates_parent_directories(self, tmp_path):
        """Should create parent directories if they don't exist."""
        from src.generate_cloud_image import generate_google

        png_bytes = _fake_png_bytes()

        mock_part = MagicMock()
        mock_part.inline_data.mime_type = 'image/png'
        mock_part.inline_data.data = png_bytes

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        output = tmp_path / 'sub' / 'dir' / 'hero.png'
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            with patch('src.generate_cloud_image.genai.Client', return_value=mock_client):
                generate_google(prompt='test', output_path=str(output))

        assert output.exists()

    def test_works_with_adc_credentials(self, tmp_path):
        """Should work with GOOGLE_APPLICATION_CREDENTIALS (no GOOGLE_API_KEY)."""
        from src.generate_cloud_image import generate_google

        png_bytes = _fake_png_bytes()

        mock_part = MagicMock()
        mock_part.inline_data.mime_type = 'image/png'
        mock_part.inline_data.data = png_bytes

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'GOOGLE_APPLICATION_CREDENTIALS': '/path/key.json'}, clear=True):
            with patch.dict(os.environ, {'PATH': '/usr/bin'}):
                with patch('src.generate_cloud_image.genai.Client', return_value=mock_client):
                    result = generate_google(prompt='test', output_path=str(output))

        assert result['provider'] == 'google'
        assert output.exists()


# --- FAL.ai ---

class TestGenerateFal:
    """Tests for FAL.ai image generation (FLUX.2 Pro and other models)."""

    def test_raises_not_configured_when_env_missing(self, tmp_path):
        from src.generate_cloud_image import generate_fal, ProviderNotConfiguredError

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {'PATH': '/usr/bin'}):
                with pytest.raises(ProviderNotConfiguredError, match='FAL_KEY'):
                    generate_fal(prompt='test', output_path=str(output))

    def test_generates_image_and_saves_to_path(self, tmp_path):
        from src.generate_cloud_image import generate_fal

        fake_png = _fake_png_bytes()
        mock_fal_client = MagicMock()
        mock_fal_client.subscribe.return_value = {
            'images': [{'url': 'https://fake.fal.ai/image.png'}],
        }
        mock_response = MagicMock()
        mock_response.content = fake_png
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_image.fal_client', mock_fal_client):
                with patch('src.generate_cloud_image.requests') as mock_requests:
                    mock_requests.get.return_value = mock_response
                    result = generate_fal(
                        prompt='A futuristic cityscape',
                        output_path=str(output),
                    )

        assert output.exists()
        assert output.read_bytes() == fake_png
        assert result['file_path'] == str(output)
        assert result['provider'] == 'fal'
        assert result['status'] == 'generated'

    def test_default_model_is_flux_2_pro(self, tmp_path):
        from src.generate_cloud_image import generate_fal

        fake_png = _fake_png_bytes()
        mock_fal_client = MagicMock()
        mock_fal_client.subscribe.return_value = {
            'images': [{'url': 'https://fake.fal.ai/image.png'}],
        }
        mock_response = MagicMock()
        mock_response.content = fake_png
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_image.fal_client', mock_fal_client):
                with patch('src.generate_cloud_image.requests') as mock_requests:
                    mock_requests.get.return_value = mock_response
                    result = generate_fal(prompt='test', output_path=str(output))

        # Verify fal_client.subscribe was called with the default model
        call_args = mock_fal_client.subscribe.call_args
        assert call_args[0][0] == 'fal-ai/flux-2-pro'
        assert result['model_used'] == 'fal-ai/flux-2-pro'

    def test_default_image_size_is_landscape_16_9(self, tmp_path):
        from src.generate_cloud_image import generate_fal

        fake_png = _fake_png_bytes()
        mock_fal_client = MagicMock()
        mock_fal_client.subscribe.return_value = {
            'images': [{'url': 'https://fake.fal.ai/image.png'}],
        }
        mock_response = MagicMock()
        mock_response.content = fake_png
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_image.fal_client', mock_fal_client):
                with patch('src.generate_cloud_image.requests') as mock_requests:
                    mock_requests.get.return_value = mock_response
                    generate_fal(prompt='test', output_path=str(output))

        call_kwargs = mock_fal_client.subscribe.call_args[1]
        assert call_kwargs['arguments']['image_size'] == 'landscape_16_9'

    def test_result_has_required_fields(self, tmp_path):
        from src.generate_cloud_image import generate_fal

        fake_png = _fake_png_bytes()
        mock_fal_client = MagicMock()
        mock_fal_client.subscribe.return_value = {
            'images': [{'url': 'https://fake.fal.ai/image.png'}],
        }
        mock_response = MagicMock()
        mock_response.content = fake_png
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_image.fal_client', mock_fal_client):
                with patch('src.generate_cloud_image.requests') as mock_requests:
                    mock_requests.get.return_value = mock_response
                    result = generate_fal(prompt='test', output_path=str(output))

        required_fields = {'file_path', 'provider', 'model_used', 'cost_usd', 'status'}
        assert required_fields.issubset(result.keys())
        assert result['provider'] == 'fal'
        assert isinstance(result['cost_usd'], float)
        assert result['cost_usd'] > 0
        assert result['status'] == 'generated'

    def test_cost_estimation_flux_2_pro(self, tmp_path):
        from src.generate_cloud_image import generate_fal

        fake_png = _fake_png_bytes()
        mock_fal_client = MagicMock()
        mock_fal_client.subscribe.return_value = {
            'images': [{'url': 'https://fake.fal.ai/image.png'}],
        }
        mock_response = MagicMock()
        mock_response.content = fake_png
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_image.fal_client', mock_fal_client):
                with patch('src.generate_cloud_image.requests') as mock_requests:
                    mock_requests.get.return_value = mock_response
                    result = generate_fal(prompt='test', output_path=str(output))

        # FLUX.2 Pro default landscape_16_9 (~1920x1080) costs ~$0.045
        assert result['cost_usd'] == pytest.approx(0.045, abs=0.005)

    def test_cost_estimation_flux_2_klein(self, tmp_path):
        from src.generate_cloud_image import generate_fal

        fake_png = _fake_png_bytes()
        mock_fal_client = MagicMock()
        mock_fal_client.subscribe.return_value = {
            'images': [{'url': 'https://fake.fal.ai/image.png'}],
        }
        mock_response = MagicMock()
        mock_response.content = fake_png
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_image.fal_client', mock_fal_client):
                with patch('src.generate_cloud_image.requests') as mock_requests:
                    mock_requests.get.return_value = mock_response
                    result = generate_fal(
                        prompt='test',
                        output_path=str(output),
                        model='fal-ai/flux-2-klein',
                    )

        # FLUX.2 Klein has a flat rate of $0.014/image
        assert result['cost_usd'] == 0.014
        assert result['model_used'] == 'fal-ai/flux-2-klein'

    def test_custom_model_override(self, tmp_path):
        from src.generate_cloud_image import generate_fal

        fake_png = _fake_png_bytes()
        mock_fal_client = MagicMock()
        mock_fal_client.subscribe.return_value = {
            'images': [{'url': 'https://fake.fal.ai/image.png'}],
        }
        mock_response = MagicMock()
        mock_response.content = fake_png
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_image.fal_client', mock_fal_client):
                with patch('src.generate_cloud_image.requests') as mock_requests:
                    mock_requests.get.return_value = mock_response
                    result = generate_fal(
                        prompt='test',
                        output_path=str(output),
                        model='fal-ai/ideogram/v3',
                    )

        call_args = mock_fal_client.subscribe.call_args
        assert call_args[0][0] == 'fal-ai/ideogram/v3'
        assert result['model_used'] == 'fal-ai/ideogram/v3'

    def test_custom_image_size_override(self, tmp_path):
        from src.generate_cloud_image import generate_fal

        fake_png = _fake_png_bytes()
        mock_fal_client = MagicMock()
        mock_fal_client.subscribe.return_value = {
            'images': [{'url': 'https://fake.fal.ai/image.png'}],
        }
        mock_response = MagicMock()
        mock_response.content = fake_png
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_image.fal_client', mock_fal_client):
                with patch('src.generate_cloud_image.requests') as mock_requests:
                    mock_requests.get.return_value = mock_response
                    generate_fal(
                        prompt='test',
                        output_path=str(output),
                        image_size='square_hd',
                    )

        call_kwargs = mock_fal_client.subscribe.call_args[1]
        assert call_kwargs['arguments']['image_size'] == 'square_hd'

    def test_output_format_is_png(self, tmp_path):
        from src.generate_cloud_image import generate_fal

        fake_png = _fake_png_bytes()
        mock_fal_client = MagicMock()
        mock_fal_client.subscribe.return_value = {
            'images': [{'url': 'https://fake.fal.ai/image.png'}],
        }
        mock_response = MagicMock()
        mock_response.content = fake_png
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_image.fal_client', mock_fal_client):
                with patch('src.generate_cloud_image.requests') as mock_requests:
                    mock_requests.get.return_value = mock_response
                    generate_fal(prompt='test', output_path=str(output))

        call_kwargs = mock_fal_client.subscribe.call_args[1]
        assert call_kwargs['arguments']['output_format'] == 'png'

    def test_creates_parent_directories(self, tmp_path):
        from src.generate_cloud_image import generate_fal

        fake_png = _fake_png_bytes()
        mock_fal_client = MagicMock()
        mock_fal_client.subscribe.return_value = {
            'images': [{'url': 'https://fake.fal.ai/image.png'}],
        }
        mock_response = MagicMock()
        mock_response.content = fake_png
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        output = tmp_path / 'nested' / 'deep' / 'hero.png'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_image.fal_client', mock_fal_client):
                with patch('src.generate_cloud_image.requests') as mock_requests:
                    mock_requests.get.return_value = mock_response
                    generate_fal(prompt='test', output_path=str(output))

        assert output.exists()

    def test_downloads_from_returned_url(self, tmp_path):
        from src.generate_cloud_image import generate_fal

        fake_png = _fake_png_bytes()
        image_url = 'https://fal.media/files/unique-id/image.png'
        mock_fal_client = MagicMock()
        mock_fal_client.subscribe.return_value = {
            'images': [{'url': image_url}],
        }
        mock_response = MagicMock()
        mock_response.content = fake_png
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {'FAL_KEY': 'fake-key'}):
            with patch('src.generate_cloud_image.fal_client', mock_fal_client):
                with patch('src.generate_cloud_image.requests') as mock_requests:
                    mock_requests.get.return_value = mock_response
                    generate_fal(prompt='test', output_path=str(output))

        mock_requests.get.assert_called_once_with(image_url, timeout=30)


# --- Dispatch function ---

class TestGenerateCloudImage:
    def test_dispatches_to_openai(self, tmp_path):
        from src.generate_cloud_image import generate_cloud_image

        b64_data, _ = _fake_png_b64()
        mock_image = MagicMock()
        mock_image.b64_json = b64_data
        mock_response = MagicMock()
        mock_response.data = [mock_image]

        mock_client = MagicMock()
        mock_client.images.generate.return_value = mock_response

        output = tmp_path / 'hero.png'
        with patch('src.generate_cloud_image.OpenAI', return_value=mock_client):
            result = generate_cloud_image(
                prompt='A cityscape',
                provider='openai',
                output_path=str(output),
            )

        assert result['provider'] == 'openai'
        assert output.exists()

    def test_raises_for_unknown_provider(self, tmp_path):
        from src.generate_cloud_image import generate_cloud_image

        output = tmp_path / 'hero.png'
        with pytest.raises(ValueError, match='unknown_provider'):
            generate_cloud_image(
                prompt='test',
                provider='unknown_provider',
                output_path=str(output),
            )

    def test_dispatches_to_google(self, tmp_path):
        from src.generate_cloud_image import generate_cloud_image, ProviderNotConfiguredError

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {'PATH': '/usr/bin'}):
                with pytest.raises(ProviderNotConfiguredError):
                    generate_cloud_image(
                        prompt='test',
                        provider='google',
                        output_path=str(output),
                    )

    def test_dispatches_to_fal(self, tmp_path):
        from src.generate_cloud_image import generate_cloud_image, ProviderNotConfiguredError

        output = tmp_path / 'hero.png'
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {'PATH': '/usr/bin'}):
                with pytest.raises(ProviderNotConfiguredError):
                    generate_cloud_image(
                        prompt='test',
                        provider='fal',
                        output_path=str(output),
                    )


# --- Cost estimation ---

class TestCostEstimate:
    def test_landscape_medium_cost(self):
        from src.generate_cloud_image import estimate_openai_cost

        cost = estimate_openai_cost(size='1536x1024', quality='medium')
        assert cost == 0.051

    def test_square_low_cost(self):
        from src.generate_cloud_image import estimate_openai_cost

        cost = estimate_openai_cost(size='1024x1024', quality='low')
        assert cost == 0.009

    def test_square_high_cost(self):
        from src.generate_cloud_image import estimate_openai_cost

        cost = estimate_openai_cost(size='1024x1024', quality='high')
        assert cost == 0.133

    def test_landscape_high_cost(self):
        from src.generate_cloud_image import estimate_openai_cost

        cost = estimate_openai_cost(size='1536x1024', quality='high')
        assert cost == 0.200

    def test_unknown_combo_raises(self):
        from src.generate_cloud_image import estimate_openai_cost

        with pytest.raises(ValueError):
            estimate_openai_cost(size='999x999', quality='medium')


class TestGoogleCostEstimate:
    def test_imagen4_fast_cost(self):
        from src.generate_cloud_image import estimate_google_cost

        cost = estimate_google_cost(model='imagen-4.0-fast-generate-001')
        assert cost == 0.020

    def test_imagen4_standard_cost(self):
        from src.generate_cloud_image import estimate_google_cost

        cost = estimate_google_cost(model='imagen-4.0-generate-001')
        assert cost == 0.040

    def test_nano_banana_flash_cost(self):
        from src.generate_cloud_image import estimate_google_cost

        cost = estimate_google_cost(model='gemini-3.1-flash-image-preview')
        assert cost == 0.067

    def test_nano_banana_pro_cost(self):
        from src.generate_cloud_image import estimate_google_cost

        cost = estimate_google_cost(model='gemini-3-pro-image-preview')
        assert cost == 0.134

    def test_unknown_model_raises(self):
        from src.generate_cloud_image import estimate_google_cost

        with pytest.raises(ValueError, match='Unknown Google model'):
            estimate_google_cost(model='nonexistent-model')


class TestFalCostEstimate:
    def test_flux_2_pro_landscape_cost(self):
        from src.generate_cloud_image import estimate_fal_cost

        # landscape_16_9 ~ 1920x1080 = 2.07 MP, at $0.030/MP = ~$0.045
        cost = estimate_fal_cost(model='fal-ai/flux-2-pro', image_size='landscape_16_9')
        assert cost == pytest.approx(0.045, abs=0.005)

    def test_flux_2_pro_square_cost(self):
        from src.generate_cloud_image import estimate_fal_cost

        # square = 1024x1024 = 1.048 MP, at $0.030/MP = ~$0.031
        cost = estimate_fal_cost(model='fal-ai/flux-2-pro', image_size='square')
        assert cost == pytest.approx(0.031, abs=0.002)

    def test_flux_2_klein_flat_rate(self):
        from src.generate_cloud_image import estimate_fal_cost

        cost = estimate_fal_cost(model='fal-ai/flux-2-klein')
        assert cost == 0.014

    def test_ideogram_default_cost(self):
        from src.generate_cloud_image import estimate_fal_cost

        cost = estimate_fal_cost(model='fal-ai/ideogram/v3')
        assert cost == 0.060

    def test_unknown_model_uses_fallback(self):
        from src.generate_cloud_image import estimate_fal_cost

        # Unknown models should use a reasonable fallback, not crash
        cost = estimate_fal_cost(model='fal-ai/some-new-model')
        assert isinstance(cost, float)
        assert cost > 0
