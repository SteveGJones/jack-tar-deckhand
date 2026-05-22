import json
from pathlib import Path
import pytest
from tools.spike_pricing_calibration import (
    load_prompts,
    PromptSet,
    load_results,
    missing_cells,
    check_spend_cap,
    SpendCapExceeded,
    MatrixCell,
    ALL_CELLS,
)


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
    with pytest.raises(FileNotFoundError):
        load_prompts(prompts_dir)


def test_all_cells_excludes_imagen():
    """Phase 0 found Imagen has no usage_metadata — Imagen cells must be excluded."""
    providers = {cell.provider for cell in ALL_CELLS}
    assert "google_imagen" not in providers


def test_all_cells_count():
    """The matrix should have 16 cells after Imagen exclusion."""
    assert len(ALL_CELLS) == 16


def test_missing_cells_returns_all_when_no_prior_results(tmp_path):
    results_path = tmp_path / "results.json"
    cells = missing_cells(results_path)
    assert set(cells) == set(ALL_CELLS)


def test_missing_cells_skips_completed(tmp_path):
    results_path = tmp_path / "results.json"
    completed = ALL_CELLS[0]
    results_path.write_text(
        json.dumps(
            [
                {
                    "provider": completed.provider,
                    "model": completed.model,
                    "resolution": completed.resolution,
                    "prompt_key": completed.prompt_key,
                    "catalog_estimate_usd": 0.067,
                    "computed_actual_usd": 0.040,
                    "raw_usage": {},
                    "timestamp": "2026-05-21T10:00:00Z",
                }
            ]
        )
    )
    cells = missing_cells(results_path)
    assert completed not in cells


def test_load_results_returns_empty_when_file_absent(tmp_path):
    assert load_results(tmp_path / "noexist.json") == []


def test_spend_cap_exceeded_raises():
    with pytest.raises(SpendCapExceeded):
        check_spend_cap(spent=4.95, next_estimate=0.10, cap=5.0)


def test_spend_cap_allows_under_cap():
    # Should not raise
    check_spend_cap(spent=4.85, next_estimate=0.10, cap=5.0)
