"""Spike: actual-token pricing calibration.

Runs a calibration matrix of real API calls against in-scope providers,
captures usage metadata, computes actual cost via src.actual_cost_calculator,
and emits a delta report. Idempotent: skips cells already in results.json.

Usage:
    .venv/bin/python tools/spike_pricing_calibration.py \\
        --max-spend-usd 5.0 \\
        --results docs/spikes/2026-05-21-actual-token-pricing/calibration-results.json \\
        --prompts docs/spikes/2026-05-21-actual-token-pricing/prompts \\
        --dry-run    # print matrix without calling APIs
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class PromptSet:
    short_a: str
    short_b: str
    medium_a: str
    medium_b: str
    long_a: str
    long_b: str


def load_prompts(prompts_dir: Path) -> PromptSet:
    """Load the six calibration prompts from a directory.

    Raises:
        FileNotFoundError: if any required prompt file is missing.
    """
    required = ("short_a", "short_b", "medium_a", "medium_b", "long_a", "long_b")
    bodies = {}
    for name in required:
        path = prompts_dir / f"{name}.txt"
        if not path.is_file():
            raise FileNotFoundError(f"Missing prompt file: {path}")
        bodies[name] = path.read_text().strip()
    return PromptSet(**bodies)


@dataclass(frozen=True)
class MatrixCell:
    """A single calibration matrix cell: provider × model × resolution × prompt."""

    provider: str  # 'google_nano_banana' | 'openai'
    model: str
    resolution: str  # '1K' | '2K' | '4K'
    prompt_key: str  # 'short_a' | 'medium_a' | 'long_a' (use _b on re-runs)


# Matrix: 16 cells total (Imagen excluded per Phase 0 — no usage_metadata).
# Estimated spend ~$1.77; well under the $5 cap.
ALL_CELLS: tuple[MatrixCell, ...] = (
    # Nano Banana Flash 1K (3 prompts)
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "1K", "short_a"),
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "1K", "medium_a"),
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "1K", "long_a"),
    # Nano Banana Flash 2K (3 prompts)
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "2K", "short_a"),
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "2K", "medium_a"),
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "2K", "long_a"),
    # Nano Banana Flash 4K (3 prompts)
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "4K", "short_a"),
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "4K", "medium_a"),
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "4K", "long_a"),
    # Nano Banana Pro 1K (3 prompts)
    MatrixCell("google_nano_banana", "gemini-3-pro-image-preview", "1K", "short_a"),
    MatrixCell("google_nano_banana", "gemini-3-pro-image-preview", "1K", "medium_a"),
    MatrixCell("google_nano_banana", "gemini-3-pro-image-preview", "1K", "long_a"),
    # Nano Banana Pro 4K (long only — single expensive shot)
    MatrixCell("google_nano_banana", "gemini-3-pro-image-preview", "4K", "long_a"),
    # OpenAI GPT Image (3 prompts, single resolution 1K medium quality)
    MatrixCell("openai", "gpt-image-1", "1K", "short_a"),
    MatrixCell("openai", "gpt-image-1", "1K", "medium_a"),
    MatrixCell("openai", "gpt-image-1", "1K", "long_a"),
)


class SpendCapExceeded(Exception):
    """Raised when the next API call would push cumulative spend past the cap."""


def check_spend_cap(*, spent: float, next_estimate: float, cap: float) -> None:
    """Raise SpendCapExceeded if spent + next_estimate would exceed cap.

    Keyword-only args to prevent argument-order confusion at call sites.
    """
    if spent + next_estimate > cap:
        raise SpendCapExceeded(
            f"Spend ${spent:.3f} + next ${next_estimate:.3f} > cap ${cap:.3f}"
        )


def load_results(results_path: Path) -> list[dict]:
    """Read the calibration-results.json file if it exists; return empty list otherwise."""
    if not results_path.is_file():
        return []
    return json.loads(results_path.read_text())


def missing_cells(results_path: Path) -> list[MatrixCell]:
    """Return cells from ALL_CELLS that don't yet have a row in results.json."""
    done = load_results(results_path)
    done_keys = {
        (r["provider"], r["model"], r["resolution"], r["prompt_key"]) for r in done
    }
    return [
        c
        for c in ALL_CELLS
        if (c.provider, c.model, c.resolution, c.prompt_key) not in done_keys
    ]
