"""Tests for FAL FLUX 2 Pro resolution mapping in generate_fal."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.generate_cloud_image import (
    generate_fal,
    ProviderResolutionUnsupportedError,
)


@pytest.fixture
def mock_fal(monkeypatch):
    monkeypatch.setenv("FAL_KEY", "test-key")
    fake_result = {"images": [{"url": "https://fake.example/img.png"}]}
    fake_response = MagicMock()
    fake_response.content = b"\x89PNG\r\n\x1a\n" + b"x" * 100
    fake_response.raise_for_status = MagicMock()
    with patch("src.generate_cloud_image.fal_client.subscribe") as mock_subscribe:
        with patch("src.generate_cloud_image.requests.get") as mock_get:
            mock_subscribe.return_value = fake_result
            mock_get.return_value = fake_response
            yield mock_subscribe


class TestFALResolution:
    def test_1k_uses_existing_preset_when_no_image_size(self, mock_fal, tmp_path):
        out = tmp_path / "out.png"
        result = generate_fal(
            prompt="test", output_path=str(out),
            model="fal-ai/flux-2-pro",
            resolution="1K",
        )
        args = mock_fal.call_args.kwargs["arguments"]
        assert args["image_size"] == "landscape_16_9"  # default preset
        assert result["resolution"] == "1K"

    def test_2k_maps_to_2048_dict(self, mock_fal, tmp_path):
        out = tmp_path / "out.png"
        result = generate_fal(
            prompt="test", output_path=str(out),
            model="fal-ai/flux-2-pro",
            resolution="2K",
        )
        args = mock_fal.call_args.kwargs["arguments"]
        assert args["image_size"] == {"width": 2048, "height": 2048}
        assert result["resolution"] == "2K"

    def test_4k_raises_unsupported(self, mock_fal, tmp_path):
        out = tmp_path / "out.png"
        with pytest.raises(ProviderResolutionUnsupportedError) as excinfo:
            generate_fal(
                prompt="test", output_path=str(out),
                model="fal-ai/flux-2-pro",
                resolution="4K",
            )
        assert excinfo.value.supported == ["1K", "2K"]

    def test_512_raises_unsupported(self, mock_fal, tmp_path):
        out = tmp_path / "out.png"
        with pytest.raises(ProviderResolutionUnsupportedError):
            generate_fal(
                prompt="test", output_path=str(out),
                model="fal-ai/flux-2-pro",
                resolution="512",
            )

    def test_explicit_image_size_wins(self, mock_fal, tmp_path):
        out = tmp_path / "out.png"
        custom = {"width": 1024, "height": 768}
        generate_fal(
            prompt="test", output_path=str(out),
            model="fal-ai/flux-2-pro",
            resolution="2K",
            image_size=custom,
        )
        args = mock_fal.call_args.kwargs["arguments"]
        assert args["image_size"] == custom
