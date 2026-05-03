"""Tests for generate_cloud_image() resolution wiring + provider_discovery surface."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.generate_cloud_image import (
    generate_cloud_image,
    ProviderResolutionUnsupportedError,
)
from src.provider_discovery import discover_providers


class TestDispatch:
    def test_default_resolution_is_1k(self, monkeypatch, tmp_path):
        monkeypatch.setenv("FAL_KEY", "test")
        with patch("src.generate_cloud_image.fal_client.subscribe") as sub:
            sub.return_value = {"images": [{"url": "x"}]}
            with patch("src.generate_cloud_image.requests.get") as get:
                get.return_value.content = b"x"
                get.return_value.raise_for_status = MagicMock()
                result = generate_cloud_image(
                    prompt="test", provider="fal",
                    output_path=str(tmp_path / "out.png"),
                )
        assert result["resolution"] == "1K"

    def test_explicit_resolution_threads_through(self, monkeypatch, tmp_path):
        monkeypatch.setenv("FAL_KEY", "test")
        with patch("src.generate_cloud_image.fal_client.subscribe") as sub:
            sub.return_value = {"images": [{"url": "x"}]}
            with patch("src.generate_cloud_image.requests.get") as get:
                get.return_value.content = b"x"
                get.return_value.raise_for_status = MagicMock()
                result = generate_cloud_image(
                    prompt="test", provider="fal",
                    output_path=str(tmp_path / "out.png"),
                    resolution="2K",
                )
        assert result["resolution"] == "2K"

    def test_unsupported_resolution_propagates(self, monkeypatch, tmp_path):
        monkeypatch.setenv("FAL_KEY", "test")
        with pytest.raises(ProviderResolutionUnsupportedError):
            generate_cloud_image(
                prompt="test", provider="fal",
                output_path=str(tmp_path / "out.png"),
                resolution="4K",  # FLUX caps at 2K
            )


class TestProviderDiscoveryResolutions:
    def test_supported_resolutions_per_google_model(self):
        providers = discover_providers()
        google = providers.get("google", {})
        models = google.get("models", {})
        # Nano Banana Pro supports 1K/2K/4K (no 512)
        pro = models.get("gemini-3-pro-image-preview", {})
        assert pro.get("supported_resolutions") == ["1K", "2K", "4K"]
        # Nano Banana Flash supports the full ladder
        flash = models.get("gemini-3.1-flash-image-preview", {})
        assert flash.get("supported_resolutions") == ["512", "1K", "2K", "4K"]
        # Imagen Standard supports 1K/2K
        std = models.get("imagen-4.0-generate-001", {})
        assert std.get("supported_resolutions") == ["1K", "2K"]
        # Imagen Fast supports 1K only
        fast = models.get("imagen-4.0-fast-generate-001", {})
        assert fast.get("supported_resolutions") == ["1K"]

    def test_supported_resolutions_per_openai_model(self):
        providers = discover_providers()
        openai_p = providers.get("openai", {})
        models = openai_p.get("models", {})
        gpt = models.get("gpt-image-1.5", {})
        assert gpt.get("supported_resolutions") == ["1K"]

    def test_supported_resolutions_per_fal_model(self):
        providers = discover_providers()
        fal_p = providers.get("fal", {})
        models = fal_p.get("models", {})
        flux = models.get("fal-ai/flux-2-pro", {})
        assert flux.get("supported_resolutions") == ["1K", "2K"]
