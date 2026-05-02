"""Tests for Google Imagen + Nano Banana resolution and pricing."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.generate_cloud_image import (
    generate_google,
    estimate_google_cost,
    ProviderResolutionUnsupportedError,
)


@pytest.fixture
def mock_google_client(monkeypatch):
    """Mock the google.genai client so no live API call is made."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    fake_image = MagicMock()
    fake_image.image.image_bytes = b"\x89PNG\r\n\x1a\n" + b"x" * 100
    fake_imagen_response = MagicMock()
    fake_imagen_response.generated_images = [fake_image]
    fake_part = MagicMock()
    fake_part.inline_data.mime_type = "image/png"
    fake_part.inline_data.data = b"\x89PNG\r\n\x1a\n" + b"x" * 100
    fake_nano_response = MagicMock()
    fake_nano_response.candidates = [MagicMock()]
    fake_nano_response.candidates[0].content.parts = [fake_part]
    with patch("src.generate_cloud_image.genai.Client") as mock_class:
        instance = mock_class.return_value
        instance.models.generate_images.return_value = fake_imagen_response
        instance.models.generate_content.return_value = fake_nano_response
        yield instance


class TestImagenResolution:
    def test_imagen_standard_1k_default(self, mock_google_client, tmp_path):
        out = tmp_path / "out.png"
        result = generate_google(
            prompt="test", output_path=str(out),
            model="imagen-4.0-generate-001",
            resolution="1K",
        )
        call_kwargs = mock_google_client.models.generate_images.call_args.kwargs
        config = call_kwargs["config"]
        assert config.image_size == "1K"
        # ALSO assert return dict has resolution key set
        assert result["resolution"] == "1K"

    def test_imagen_standard_2k(self, mock_google_client, tmp_path):
        out = tmp_path / "out.png"
        result = generate_google(
            prompt="test", output_path=str(out),
            model="imagen-4.0-generate-001",
            resolution="2K",
        )
        call_kwargs = mock_google_client.models.generate_images.call_args.kwargs
        assert call_kwargs["config"].image_size == "2K"
        assert result["resolution"] == "2K"

    def test_imagen_standard_4k_raises(self, mock_google_client, tmp_path):
        out = tmp_path / "out.png"
        with pytest.raises(ProviderResolutionUnsupportedError) as excinfo:
            generate_google(
                prompt="test", output_path=str(out),
                model="imagen-4.0-generate-001",
                resolution="4K",
            )
        assert excinfo.value.supported == ["1K", "2K"]

    def test_imagen_fast_1k_only(self, mock_google_client, tmp_path):
        out = tmp_path / "out.png"
        # Fast supports 1K
        generate_google(
            prompt="test", output_path=str(out),
            model="imagen-4.0-fast-generate-001",
            resolution="1K",
        )
        # Fast does NOT support 2K
        with pytest.raises(ProviderResolutionUnsupportedError) as excinfo:
            generate_google(
                prompt="test", output_path=str(out),
                model="imagen-4.0-fast-generate-001",
                resolution="2K",
            )
        assert excinfo.value.supported == ["1K"]


class TestImagenCostDualPricing:
    def test_vertex_flat_pricing_when_adc_set(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/fake/path.json")
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        # Vertex flat: 2K is uniform within Standard tier ($0.04)
        cost = estimate_google_cost(
            model="imagen-4.0-generate-001", resolution="2K",
        )
        assert cost == 0.04

    def test_developer_api_token_pricing_when_only_api_key_set(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test")
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        # Developer API token-based: 2K Standard = ~$0.101
        cost = estimate_google_cost(
            model="imagen-4.0-generate-001", resolution="2K",
        )
        assert cost == 0.101

    def test_imagen_1k_same_across_backends(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test")
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        cost_dev = estimate_google_cost(
            model="imagen-4.0-generate-001", resolution="1K",
        )
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/fake/path.json")
        cost_vertex = estimate_google_cost(
            model="imagen-4.0-generate-001", resolution="1K",
        )
        assert cost_dev == cost_vertex == 0.04

    def test_imagen_ultra_2k(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/fake/path.json")
        cost = estimate_google_cost(
            model="imagen-4.0-ultra-generate-001", resolution="2K",
        )
        assert cost == 0.06

    def test_nano_banana_cost_unchanged_across_backends(self, monkeypatch):
        # Nano Banana bills identically on either backend.
        monkeypatch.setenv("GOOGLE_API_KEY", "test")
        cost_dev = estimate_google_cost(
            model="gemini-3-pro-image-preview", resolution="4K",
        )
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/fake/path.json")
        cost_vertex = estimate_google_cost(
            model="gemini-3-pro-image-preview", resolution="4K",
        )
        assert cost_dev == cost_vertex == 0.24
