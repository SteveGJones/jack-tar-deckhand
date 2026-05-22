"""End-to-end smoke test for the GenerationResult + BudgetTracker plumbing.

Runs ONE real Nano Banana Flash 1K image generation, logs the call to a
BudgetTracker, and emits a cost summary markdown to disk for the spike report.

Cost: ~$0.07-$0.10 per run.

Usage:
    .venv/bin/python tools/spike_dogfood_smoke.py
"""
from __future__ import annotations
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Use the plugin's resolution-aware version
import importlib.util as _ilu

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PLUGIN_GEN = _PROJECT_ROOT / "plugins" / "jack-tar-cloud" / "src" / "generate_cloud_image.py"
_PLUGIN_SRC = _PROJECT_ROOT / "plugins" / "jack-tar-cloud" / "src"

# Add plugin's src/ to sys.path so the sibling-module imports inside generate_cloud_image
# (safety_filter_vocab, etc.) work.
sys.path.insert(0, str(_PLUGIN_SRC))

_spec = _ilu.spec_from_file_location("_dogfood_gen_cloud", _PLUGIN_GEN)
_gen = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_gen)

sys.path.insert(0, str(_PROJECT_ROOT))
from src.budget_tracker import BudgetTracker

# Import GenerationResult from the *same* module the plugin loaded into sys.modules
# to avoid the two-class identity problem (plugin uses bare 'cloud_results' import).
import cloud_results as _cr
GenerationResult = _cr.GenerationResult


def main() -> int:
    output_md = (
        _PROJECT_ROOT
        / "docs"
        / "spikes"
        / "2026-05-21-actual-token-pricing"
        / "dogfood-cost-summary.md"
    )

    tracker = BudgetTracker(total_budget_usd=1.0)

    with TemporaryDirectory() as tmp:
        image_path = Path(tmp) / "smoke.png"
        prompt = (
            "A minimal abstract lighthouse beam, navy blue and gold palette, "
            "vector-clean composition, centered."
        )
        result = _gen.generate_cloud_image(
            prompt=prompt,
            provider="google",
            output_path=str(image_path),
            model="gemini-3.1-flash-image-preview",
            resolution="1K",
        )

    # Verify return shape
    assert isinstance(result, GenerationResult), (
        f"Expected GenerationResult, got {type(result)}"
    )
    assert result.cost_estimated > 0
    assert result.usage_metadata is not None, "Expected usage_metadata for Nano Banana"
    assert result.cost_actual is not None, "Expected cost_actual for Nano Banana"

    print(f"Generated: {result.path}")
    print(f"Estimated: ${result.cost_estimated:.4f}")
    print(f"Actual:    ${result.cost_actual:.4f}")
    delta_pct = (result.cost_estimated - result.cost_actual) / result.cost_estimated * 100
    print(f"Delta:     {delta_pct:+.1f}%")
    print(f"Usage:     {result.usage_metadata}")

    # Log to BudgetTracker
    tracker.log_api_call(
        model_key=f"{result.model}-{result.resolution}",
        cost_estimated=result.cost_estimated,
        image_id="smoke-test-1",
        cost_actual=result.cost_actual,
        usage_metadata=result.usage_metadata,
    )

    md = tracker.cost_summary_markdown()
    print("\n--- BudgetTracker.cost_summary_markdown() ---")
    print(md)

    # Verify both columns present
    assert "Estimated $" in md, "Missing 'Estimated $' column"
    assert "Actual $" in md, "Missing 'Actual $' column"

    # Verify actual differs from estimated (sanity: plumbing carries actual value)
    assert result.cost_actual != result.cost_estimated, (
        "cost_actual == cost_estimated — the actual value may not have been captured"
    )

    # Save artefact
    artefact_lines = [
        "# Phase 2 dogfood — cost summary output",
        "",
        "**Date:** 2026-05-21",
        "**Brief:** single-image smoke test (Nano Banana Flash 1K)",
        f"**Cost estimated:** ${result.cost_estimated:.4f}",
        f"**Cost actual:**    ${result.cost_actual:.4f}",
        f"**Delta:**          {delta_pct:+.1f}%",
        f"**Usage metadata:** {result.usage_metadata}",
        "",
        "## BudgetTracker.cost_summary_markdown() output",
        "",
        md,
    ]
    output_md.write_text("\n".join(artefact_lines))
    print(f"\nWrote {output_md}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
