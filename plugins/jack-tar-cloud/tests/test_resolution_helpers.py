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
