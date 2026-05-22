import os
from pathlib import Path

from src.cloud_results import GenerationResult


def test_generation_result_path_is_fspath_compatible(tmp_path):
    f = tmp_path / "image.png"
    f.write_bytes(b"fake")
    result = GenerationResult(
        path=str(f),
        cost_estimated=0.067,
        cost_actual=0.040,
        usage_metadata={"prompt_token_count": 100, "candidates_token_count": 1290, "total_token_count": 1390},
        provider="google_nano_banana",
        model="gemini-3.1-flash-image-preview",
        resolution="1K",
    )
    # legacy callers reading the result as a path:
    assert Path(result).name == "image.png"
    assert os.fspath(result) == str(f)
    assert str(result) == str(f)


def test_generation_result_no_usage_keeps_actual_optional():
    result = GenerationResult(
        path="/tmp/x.png",
        cost_estimated=0.04,
        cost_actual=None,
        usage_metadata=None,
        provider="fal",
        model="flux-2-pro",
        resolution="1K",
    )
    assert result.cost_actual is None
    assert result.usage_metadata is None


def test_generation_result_path_passes_to_open(tmp_path):
    """Verify __fspath__ works with open()."""
    f = tmp_path / "x.txt"
    f.write_text("hello")
    result = GenerationResult(
        path=str(f),
        cost_estimated=0.0,
        cost_actual=None,
        usage_metadata=None,
        provider="fal",
        model="flux-2-pro",
        resolution="1K",
    )
    with open(result) as fh:
        assert fh.read() == "hello"
