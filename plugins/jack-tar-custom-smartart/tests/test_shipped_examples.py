"""Render-guard: every shipped example spec must render cleanly.

Phase-D shipped example files that were never executed and whose data shapes
did not match the renderer contract. This guard renders each
`examples/*.json` through the real renderer and asserts the engine reports
`status == 'rendered'` — which also exercises the PA-03 / dimension / text
validators, so an example that fails the plugin's own QA fails the test.
"""
import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

EXAMPLES = sorted((PLUGIN_ROOT / "examples").glob("*.json"))


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.stem)
def test_shipped_example_renders(example, tmp_path):
    from src.smartart_renderer import render

    spec = json.loads(example.read_text())
    result = render(spec, {}, "production", str(tmp_path))

    assert result["status"] == "rendered", f"{example.name}: {result}"
    assert Path(result["file_path"]).exists(), f"{example.name} produced no file"
