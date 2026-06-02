"""Tests for iterate-slide's creative_vision branch."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.manifest import initialise_manifest, save_manifest  # noqa: E402
from src.iterate_slide_dispatch import (  # noqa: E402
    available_channels_for_creative_vision,
    is_creative_vision_slide,
    revise_prose_action,
)


def test_is_creative_vision_slide_true_when_manifest_present(tmp_path):
    manifest = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=1.0)
    save_manifest(str(tmp_path), manifest)
    assert is_creative_vision_slide(str(tmp_path), slide_number=3) is True


def test_is_creative_vision_slide_false_when_no_manifest(tmp_path):
    assert is_creative_vision_slide(str(tmp_path), slide_number=99) is False


def test_available_channels_returns_all_three_when_budget_remains(tmp_path):
    manifest = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=1.0)
    manifest["iterate_slide_hooks"]["remaining_budget_usd"] = 0.5
    save_manifest(str(tmp_path), manifest)
    channels = available_channels_for_creative_vision(str(tmp_path), slide_number=3)
    assert set(channels) == {"revise_prose", "refine_prompt", "escalate_tier"}


def test_available_channels_excludes_escalate_tier_when_budget_out(tmp_path):
    manifest = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=1.0)
    manifest["iterate_slide_hooks"]["remaining_budget_usd"] = 0.0
    manifest["iterate_slide_hooks"]["can_escalate_tier"] = False
    save_manifest(str(tmp_path), manifest)
    channels = available_channels_for_creative_vision(str(tmp_path), slide_number=3)
    assert "escalate_tier" not in channels
    assert "revise_prose" in channels
    assert "refine_prompt" in channels


def test_revise_prose_action_bumps_version(tmp_path):
    manifest = initialise_manifest(slide_number=3, vision_prose="v1", budget_usd=1.0)
    save_manifest(str(tmp_path), manifest)
    revise_prose_action(str(tmp_path), slide_number=3, new_prose="v2", reason="too vague")
    with open(tmp_path / "creative-vision" / "3" / "manifest.json") as f:
        m = json.load(f)
    assert len(m["prose_history"]) == 2
    assert m["prose_history"][-1]["prose"] == "v2"
