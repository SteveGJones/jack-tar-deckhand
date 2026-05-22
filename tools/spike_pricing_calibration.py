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
import os
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


def providers_with_keys() -> set[str]:
    """Return the set of providers reachable in the current environment.

    'google_nano_banana' requires a Google credential — either GOOGLE_API_KEY
    (Developer API) or GOOGLE_CLOUD_PROJECT (Vertex with ADC).
    'openai' requires OPENAI_API_KEY.

    Imagen is intentionally absent — Phase 0 confirmed no usage_metadata field,
    so Imagen cells were dropped from ALL_CELLS in Task 10.
    """
    detected = set()
    if os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_CLOUD_PROJECT"):
        detected.add("google_nano_banana")
    if os.environ.get("OPENAI_API_KEY"):
        detected.add("openai")
    return detected


# ---------------------------------------------------------------------------
# Real SDK dispatch
# ---------------------------------------------------------------------------
import argparse  # noqa: E402 — after dataclass/helper definitions
import sys
from pathlib import Path as _Path
from typing import Optional

# Ensure the project root is on sys.path so 'src.*' imports resolve when the
# script is run directly (e.g. `python tools/spike_pricing_calibration.py`).
_PROJECT_ROOT = _Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import importlib.util as _ilu  # noqa: E402

_PLUGIN_CLOUD_SRC = Path(__file__).parent.parent / "plugins" / "jack-tar-cloud" / "src"
_PLUGIN_CLOUD = _PLUGIN_CLOUD_SRC / "generate_cloud_image.py"
if str(_PLUGIN_CLOUD_SRC) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_CLOUD_SRC))
_spec = _ilu.spec_from_file_location("jack_tar_cloud_generate_cloud_image", _PLUGIN_CLOUD)
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
estimate_google_cost = _mod.estimate_google_cost
estimate_openai_cost = _mod.estimate_openai_cost
from src.actual_cost_calculator import (  # noqa: E402
    compute_nano_banana_actual_cost,
    compute_openai_image_actual_cost,
)


def _call_nano_banana(model: str, resolution: str, prompt: str) -> tuple[dict, bytes]:
    """Call Nano Banana via google-genai. Return (usage_metadata_dict, image_bytes)."""
    from google import genai
    from google.genai import types
    client = genai.Client()
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(image_size=resolution),
    )
    response = client.models.generate_content(model=model, contents=[prompt], config=config)
    usage = {
        "prompt_token_count": response.usage_metadata.prompt_token_count,
        "candidates_token_count": response.usage_metadata.candidates_token_count,
        "total_token_count": response.usage_metadata.total_token_count,
    }
    image_bytes = b""
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            image_bytes = part.inline_data.data
            break
    return usage, image_bytes


def _call_openai(model: str, resolution: str, prompt: str) -> tuple[Optional[dict], bytes]:
    """Call OpenAI images.generate. Return (usage_or_None, image_bytes).

    response_format="b64_json" is specified explicitly — the default for
    gpt-image-1 is a URL, so without this the image bytes would be empty.
    """
    import base64
    from openai import OpenAI
    client = OpenAI()
    response = client.images.generate(
        model=model,
        prompt=prompt,
        size="1024x1024",
        quality="medium",
        n=1,
        response_format="b64_json",
    )
    usage = None
    if hasattr(response, "usage") and response.usage is not None:
        usage = {
            "input_tokens": getattr(response.usage, "input_tokens", 0),
            "output_tokens": getattr(response.usage, "output_tokens", 0),
            "total_tokens": getattr(response.usage, "total_tokens", 0),
        }
    image_bytes = (
        base64.b64decode(response.data[0].b64_json)
        if response.data and response.data[0].b64_json
        else b""
    )
    return usage, image_bytes


def _estimate_for_cell(cell: MatrixCell) -> float:
    if cell.provider == "google_nano_banana":
        return estimate_google_cost(model=cell.model, resolution=cell.resolution)
    if cell.provider == "openai":
        return estimate_openai_cost(size="1024x1024", quality="medium")
    raise ValueError(f"Unknown provider: {cell.provider}")


def _actual_for_cell(cell: MatrixCell, usage: Optional[dict], estimated: float) -> float:
    if usage is None:
        return estimated
    if cell.provider == "google_nano_banana":
        return compute_nano_banana_actual_cost(cell.model, usage)
    if cell.provider == "openai":
        return compute_openai_image_actual_cost(cell.model, usage)
    raise ValueError(f"Unknown provider: {cell.provider}")


def run_cell(cell: MatrixCell, prompts: PromptSet) -> dict:
    """Call the API for one cell, return the result row dict (no file writes)."""
    prompt = getattr(prompts, cell.prompt_key)
    estimated = _estimate_for_cell(cell)
    if cell.provider == "google_nano_banana":
        usage, _img = _call_nano_banana(cell.model, cell.resolution, prompt)
    elif cell.provider == "openai":
        usage, _img = _call_openai(cell.model, cell.resolution, prompt)
    else:
        raise ValueError(f"Unknown provider: {cell.provider}")
    actual = _actual_for_cell(cell, usage, estimated)
    return {
        "provider": cell.provider,
        "model": cell.model,
        "resolution": cell.resolution,
        "prompt_key": cell.prompt_key,
        "prompt_chars": len(prompt),
        "prompt_words": len(prompt.split()),
        "catalog_estimate_usd": estimated,
        "raw_usage": usage,
        "computed_actual_usd": actual,
        "delta_usd": estimated - actual,
        "delta_pct": (estimated - actual) / estimated * 100 if estimated else 0.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def append_result(results_path: Path, row: dict) -> None:
    """Append a row to results.json, creating the file if needed."""
    existing = load_results(results_path)
    existing.append(row)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(existing, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-spend-usd", type=float, default=5.0)
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("docs/spikes/2026-05-21-actual-token-pricing/calibration-results.json"),
    )
    parser.add_argument(
        "--prompts",
        type=Path,
        default=Path("docs/spikes/2026-05-21-actual-token-pricing/prompts"),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    prompts = load_prompts(args.prompts)
    detected = providers_with_keys()
    pending = missing_cells(args.results)
    cells = [c for c in pending if c.provider in detected]
    skipped = [c for c in pending if c.provider not in detected]
    if skipped:
        print(
            f"SKIPPED {len(skipped)} cells — missing API keys for: "
            f"{sorted({c.provider for c in skipped})}"
        )
    spent = sum(r["computed_actual_usd"] for r in load_results(args.results))
    print(f"Spent so far: ${spent:.3f}; cap ${args.max_spend_usd:.3f}; {len(cells)} cells pending")

    if args.dry_run:
        print("--- DRY RUN — matrix preview ---")
        for c in cells:
            est = _estimate_for_cell(c)
            print(f"  {c.provider}/{c.model}/{c.resolution}/{c.prompt_key} ~${est:.3f}")
        print(f"Total estimated: ${sum(_estimate_for_cell(c) for c in cells):.3f}")
        return 0

    for cell in cells:
        est = _estimate_for_cell(cell)
        try:
            check_spend_cap(spent=spent, next_estimate=est, cap=args.max_spend_usd)
        except SpendCapExceeded as exc:
            print(f"HALT: {exc}")
            return 1
        print(
            f"Calling {cell.provider}/{cell.model}/{cell.resolution}/{cell.prompt_key}"
            f" (est ${est:.3f})..."
        )
        row = run_cell(cell, prompts)
        append_result(args.results, row)
        spent += row["computed_actual_usd"]
        print(
            f"  actual ${row['computed_actual_usd']:.3f}"
            f"  delta {row['delta_pct']:+.1f}%"
            f"  cumulative ${spent:.3f}"
        )

    print(f"Done. Cumulative actual: ${spent:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
