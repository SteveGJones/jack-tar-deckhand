"""Tests for OpenAI resolution mapping in generate_openai."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import os

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.generate_cloud_image import (
    generate_openai,
    ProviderResolutionUnsupportedError,
)


@pytest.fixture
def mock_openai_client(tmp_path, monkeypatch):
    """Mock the OpenAI client so no live API call is made."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    fake_response = MagicMock()
    fake_response.data = [MagicMock(b64_json="aGVsbG8=")]  # base64 for 'hello'
    with patch("src.generate_cloud_image.OpenAI") as mock_class:
        instance = mock_class.return_value
        instance.images.generate.return_value = fake_response
        yield instance


class TestOpenAIResolution:
    def test_default_1k_maps_to_1024_when_size_unset(self, mock_openai_client, tmp_path):
        out = tmp_path / "out.png"
        generate_openai(
            prompt="test", output_path=str(out), resolution="1K", size=None,
        )
        call_kwargs = mock_openai_client.images.generate.call_args.kwargs
        assert call_kwargs["size"] == "1024x1024"

    def test_explicit_size_wins_over_resolution(self, mock_openai_client, tmp_path):
        out = tmp_path / "out.png"
        generate_openai(
            prompt="test", output_path=str(out),
            resolution="1K", size="1536x1024",
        )
        call_kwargs = mock_openai_client.images.generate.call_args.kwargs
        assert call_kwargs["size"] == "1536x1024"

    def test_2k_raises_unsupported(self, mock_openai_client, tmp_path):
        out = tmp_path / "out.png"
        with pytest.raises(ProviderResolutionUnsupportedError) as excinfo:
            generate_openai(
                prompt="test", output_path=str(out), resolution="2K", size=None,
            )
        assert excinfo.value.provider == "openai"
        assert excinfo.value.requested == "2K"
        assert excinfo.value.supported == ["1K"]

    def test_4k_raises_unsupported(self, mock_openai_client, tmp_path):
        out = tmp_path / "out.png"
        with pytest.raises(ProviderResolutionUnsupportedError):
            generate_openai(
                prompt="test", output_path=str(out), resolution="4K", size=None,
            )

    def test_512_raises_unsupported(self, mock_openai_client, tmp_path):
        out = tmp_path / "out.png"
        with pytest.raises(ProviderResolutionUnsupportedError):
            generate_openai(
                prompt="test", output_path=str(out), resolution="512", size=None,
            )

    def test_lowercase_resolution_normalised(self, mock_openai_client, tmp_path):
        out = tmp_path / "out.png"
        generate_openai(
            prompt="test", output_path=str(out), resolution="1k", size=None,
        )
        call_kwargs = mock_openai_client.images.generate.call_args.kwargs
        assert call_kwargs["size"] == "1024x1024"

    def test_explicit_size_with_unsupported_resolution_warns_not_raises(
        self, mock_openai_client, tmp_path, caplog
    ):
        # Explicit size= wins; resolution=2K is unsupported on OpenAI but
        # since size= is given, we don't raise — we use the size and warn.
        out = tmp_path / "out.png"
        generate_openai(
            prompt="test", output_path=str(out),
            resolution="2K", size="1024x1024",
        )
        call_kwargs = mock_openai_client.images.generate.call_args.kwargs
        assert call_kwargs["size"] == "1024x1024"
