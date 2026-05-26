"""Tests for the top-level creative_vision dispatch entry."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision_dispatch import (  # noqa: E402
    DispatchRequest,
    initialise_dispatch,
)


def test_dispatch_request_minimum_fields():
    req = DispatchRequest(
        deck_dir="/tmp/deck",
        slide_number=3,
        vision_prose="Four ships.",
        budget_usd=1.0,
        allowed_ceiling="pro_4k",
        brand_fidelity="none",
    )
    assert req.deck_dir == "/tmp/deck"
    assert req.slide_number == 3


def test_initialise_dispatch_creates_manifest_on_disk(tmp_path):
    req = DispatchRequest(
        deck_dir=str(tmp_path),
        slide_number=3,
        vision_prose="Four ships.",
        budget_usd=1.0,
        allowed_ceiling="pro_4k",
        brand_fidelity="none",
    )
    manifest = initialise_dispatch(req)
    assert manifest["slide_number"] == 3
    assert (tmp_path / "creative-vision" / "3" / "manifest.json").is_file()


def test_initialise_dispatch_picks_recraft_ladder_when_brand_fidelity_exact(tmp_path):
    req = DispatchRequest(
        deck_dir=str(tmp_path),
        slide_number=3,
        vision_prose="x",
        budget_usd=1.0,
        allowed_ceiling="recraft_pro_4k",
        brand_fidelity="exact",
    )
    manifest = initialise_dispatch(req)
    # next_tier_available should be recraft_standard_1k (next after ollama in the recraft ladder)
    assert manifest["iterate_slide_hooks"]["next_tier_available"] == "recraft_standard_1k"
