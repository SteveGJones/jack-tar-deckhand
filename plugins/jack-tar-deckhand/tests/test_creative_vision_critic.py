"""Tests for the Director's Critic dispatch helper."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.critic import build_critic_input, parse_critic_output  # noqa: E402


def test_build_critic_input_includes_prose_image_intermediate():
    blob = build_critic_input(
        original_prose="Four warships.",
        image_path="/tmp/render.png",
        parsed_vision={"original_prose": "Four warships."},
        prior_scores_history=[],
        tier="flash_1k",
        iteration_index=1,
    )
    assert "Four warships." in blob
    assert "/tmp/render.png" in blob
    assert "flash_1k" in blob


def test_parse_critic_output_pass_verdict():
    response = '''```json
{
  "verdict": "pass",
  "per_axis_scores": {"entity_fidelity": 90, "spatial_fidelity": 90, "style_fidelity": 90, "quality": 90, "composition": 90},
  "issues": [],
  "gap_location": "unknown",
  "recommended_action": "ship it",
  "tier": "flash_1k",
  "iteration_index": 1,
  "plateau_signal": false
}
```'''
    verdict = parse_critic_output(response)
    assert verdict["verdict"] == "pass"
    assert verdict["per_axis_scores"]["entity_fidelity"] == 90


def test_parse_critic_output_validates_against_schema():
    response = '''```json
{"verdict": "invalid_value"}
```'''
    with pytest.raises(ValueError):
        parse_critic_output(response)
