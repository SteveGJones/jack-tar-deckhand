from pathlib import Path
from tools.spike_pricing_calibration import load_prompts, PromptSet


def test_load_prompts_returns_six_buckets(tmp_path):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    for name in ("short_a", "short_b", "medium_a", "medium_b", "long_a", "long_b"):
        (prompts_dir / f"{name}.txt").write_text(f"prompt body {name}")
    result = load_prompts(prompts_dir)
    assert isinstance(result, PromptSet)
    assert result.short_a == "prompt body short_a"
    assert result.medium_a == "prompt body medium_a"
    assert result.long_a == "prompt body long_a"


def test_load_prompts_missing_file_raises(tmp_path):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "short_a.txt").write_text("only one")
    import pytest
    with pytest.raises(FileNotFoundError):
        load_prompts(prompts_dir)
