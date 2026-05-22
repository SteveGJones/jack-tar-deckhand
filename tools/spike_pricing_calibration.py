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
from dataclasses import dataclass
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
