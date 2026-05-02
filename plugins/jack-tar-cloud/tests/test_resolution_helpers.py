"""Tests for resolution normalisation and ProviderResolutionUnsupportedError."""
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.generate_cloud_image import (
    _normalise_resolution,
    ProviderResolutionUnsupportedError,
)


class TestNormaliseResolution:
    def test_uppercase_already(self):
        assert _normalise_resolution("1K") == "1K"
        assert _normalise_resolution("2K") == "2K"
        assert _normalise_resolution("4K") == "4K"

    def test_lowercase_normalised(self):
        assert _normalise_resolution("1k") == "1K"
        assert _normalise_resolution("2k") == "2K"
        assert _normalise_resolution("4k") == "4K"

    def test_512_passes_through(self):
        assert _normalise_resolution("512") == "512"

    def test_whitespace_stripped(self):
        assert _normalise_resolution("  1K  ") == "1K"

    def test_unknown_value_raises(self):
        with pytest.raises(ValueError, match="not recognised"):
            _normalise_resolution("8K")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            _normalise_resolution("")

    def test_non_string_raises(self):
        with pytest.raises(TypeError, match="must be str"):
            _normalise_resolution(1024)

    def test_none_raises(self):
        with pytest.raises(TypeError):
            _normalise_resolution(None)

    def test_whitespace_stripped_512(self):
        assert _normalise_resolution("  512  ") == "512"

    def test_lowercase_with_whitespace(self):
        assert _normalise_resolution("  2k  ") == "2K"


class TestProviderResolutionUnsupportedError:
    def test_carries_attributes(self):
        err = ProviderResolutionUnsupportedError(
            provider="openai",
            model="gpt-image-1.5",
            requested="4K",
            supported=["1K"],
        )
        assert err.provider == "openai"
        assert err.model == "gpt-image-1.5"
        assert err.requested == "4K"
        assert err.supported == ["1K"]

    def test_message_includes_supported(self):
        err = ProviderResolutionUnsupportedError(
            provider="google",
            model="gemini-3.1-flash-image-preview",
            requested="8K",
            supported=["512", "1K", "2K", "4K"],
        )
        msg = str(err)
        assert "google" in msg
        assert "8K" in msg
        assert "512" in msg
        assert "4K" in msg
        assert "Retry with one of those" in msg

    def test_is_value_error_subclass(self):
        # So callers can `except ValueError` if they want generic handling.
        err = ProviderResolutionUnsupportedError("p", "m", "4K", ["1K"])
        assert isinstance(err, ValueError)

    def test_positional_args_carry_attributes(self):
        err = ProviderResolutionUnsupportedError("fal", "fal-ai/flux-2-pro", "4K", ["1K", "2K"])
        assert err.provider == "fal"
        assert err.model == "fal-ai/flux-2-pro"
        assert err.requested == "4K"
        assert err.supported == ["1K", "2K"]
