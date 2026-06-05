"""Render-guard: every shipped example spec must render to a valid carrier.

Phase-D shipped example files that were never executed and whose data shapes
did not match the real builder contract. This guard renders each
`examples/*.json` through the real engine so the examples cannot silently drift
out of sync with the builders again.
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
    from src.engine import render

    spec = json.loads(example.read_text())
    result = render(spec, str(tmp_path))

    assert Path(result.output_path).exists(), f"{example.name} produced no carrier"
    assert result.node_count > 0, f"{example.name} rendered zero nodes"
