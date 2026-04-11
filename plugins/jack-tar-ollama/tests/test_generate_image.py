"""Tests for src/generate_image.py — all HTTP calls mocked."""

import base64
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

# Add src to path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import generate_image  # noqa: E402

FAKE_IMAGE_DATA = b"\x89PNG\r\n\x1a\nfake image data"
FAKE_IMAGE_B64 = base64.b64encode(FAKE_IMAGE_DATA).decode()


def mock_response(status_code=200, json_data=None, text=None):
    """Create a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text if text is not None else (json.dumps(json_data) if json_data else "")
    resp.json.return_value = json_data or {}
    return resp


def make_args(**overrides):
    """Create a Namespace with defaults, overriding as needed."""
    defaults = {
        "prompt": "a cat",
        "model": "x/z-image-turbo",
        "output": None,
        "width": 1024,
        "height": 1024,
        "steps": 8,
        "seed": None,
        "timeout": None,
    }
    defaults.update(overrides)
    import argparse
    return argparse.Namespace(**defaults)


class TestHappyPath:
    def test_generates_image_and_prints_path(self, tmp_path, capsys):
        output = tmp_path / "test.png"
        args = make_args(output=str(output))
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True, "image": FAKE_IMAGE_B64}
        )):
            generate_image.generate(args)

        captured = capsys.readouterr()
        assert str(output) in captured.out.strip()
        assert output.exists()
        assert output.read_bytes() == FAKE_IMAGE_DATA

    def test_creates_output_directory(self, tmp_path, capsys):
        output = tmp_path / "nested" / "dir" / "image.png"
        args = make_args(output=str(output))
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True, "image": FAKE_IMAGE_B64}
        )):
            generate_image.generate(args)

        assert output.exists()

    def test_default_output_path_uses_timestamp(self, tmp_path, capsys, monkeypatch):
        monkeypatch.chdir(tmp_path)
        args = make_args(output=None)
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True, "image": FAKE_IMAGE_B64}
        )):
            generate_image.generate(args)

        captured = capsys.readouterr()
        path = captured.out.strip()
        assert "output" in path
        assert path.endswith(".png")


class TestSeedHandling:
    def test_seed_included_in_request(self, tmp_path):
        output = tmp_path / "test.png"
        args = make_args(output=str(output), seed=42)
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True, "image": FAKE_IMAGE_B64}
        )) as mock_post:
            generate_image.generate(args)

        body = mock_post.call_args.kwargs["json"]
        assert body["seed"] == 42

    def test_seed_omitted_when_not_provided(self, tmp_path):
        output = tmp_path / "test.png"
        args = make_args(output=str(output), seed=None)
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True, "image": FAKE_IMAGE_B64}
        )) as mock_post:
            generate_image.generate(args)

        body = mock_post.call_args.kwargs["json"]
        assert "seed" not in body


class TestErrorHandling:
    def test_connection_refused(self, tmp_path):
        output = tmp_path / "test.png"
        args = make_args(output=str(output))
        with patch("generate_image.requests.post", side_effect=requests.ConnectionError("refused")):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1

    def test_model_not_found_404(self, tmp_path, capsys):
        output = tmp_path / "test.png"
        args = make_args(output=str(output), model="x/fake-model")
        with patch("generate_image.requests.post", return_value=mock_response(
            status_code=404, text="model 'x/fake-model' not found"
        )):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()
        assert "ollama pull" in captured.err

    def test_timeout(self, tmp_path):
        output = tmp_path / "test.png"
        args = make_args(output=str(output))
        with patch("generate_image.requests.post", side_effect=requests.Timeout("timed out")):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1

    def test_empty_image_data(self, tmp_path, capsys):
        output = tmp_path / "test.png"
        args = make_args(output=str(output))
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True}
        )):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "no image data" in captured.err.lower()

    def test_other_http_error(self, tmp_path, capsys):
        output = tmp_path / "test.png"
        args = make_args(output=str(output))
        with patch("generate_image.requests.post", return_value=mock_response(
            status_code=500, text="internal server error"
        )):
            with pytest.raises(SystemExit) as exc_info:
                generate_image.generate(args)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "500" in captured.err


class TestTimeoutResolution:
    def test_z_image_turbo_gets_120s(self):
        assert generate_image.resolve_timeout("x/z-image-turbo", None) == 120

    def test_z_image_turbo_with_tag_gets_120s(self):
        assert generate_image.resolve_timeout("x/z-image-turbo:fp8", None) == 120

    def test_flux_gets_600s(self):
        assert generate_image.resolve_timeout("x/flux2-klein", None) == 600

    def test_flux_with_tag_gets_600s(self):
        assert generate_image.resolve_timeout("x/flux2-klein:9b", None) == 600

    def test_unknown_model_gets_default_300s(self):
        assert generate_image.resolve_timeout("x/some-new-model", None) == 300

    def test_explicit_timeout_overrides_model_default(self):
        assert generate_image.resolve_timeout("x/z-image-turbo", 60) == 60


class TestArgumentParsing:
    def test_custom_dimensions_and_steps(self, tmp_path):
        output = tmp_path / "test.png"
        args = make_args(output=str(output), width=512, height=768, steps=20)
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True, "image": FAKE_IMAGE_B64}
        )) as mock_post:
            generate_image.generate(args)

        body = mock_post.call_args.kwargs["json"]
        assert body["width"] == 512
        assert body["height"] == 768
        assert body["steps"] == 20

    def test_model_passed_to_request(self, tmp_path):
        output = tmp_path / "test.png"
        args = make_args(output=str(output), model="x/flux2-klein")
        with patch("generate_image.requests.post", return_value=mock_response(
            json_data={"done": True, "image": FAKE_IMAGE_B64}
        )) as mock_post:
            generate_image.generate(args)

        body = mock_post.call_args.kwargs["json"]
        assert body["model"] == "x/flux2-klein"
