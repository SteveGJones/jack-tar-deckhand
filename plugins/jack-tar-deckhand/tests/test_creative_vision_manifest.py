"""Tests for the CreativeVisionManifest persistence module."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.manifest import (  # noqa: E402
    create_run_id,
    initialise_manifest,
    load_manifest,
    save_manifest,
)


def test_create_run_id_format():
    rid = create_run_id(slide_number=3)
    # cv-YYYY-MM-DD-HHMMSS-<rand>-slide-N
    assert rid.startswith("cv-")
    assert rid.endswith("-slide-3")
    assert len(rid) > 20


def test_create_run_id_uniqueness_between_calls():
    # Even at the same second-precision timestamp, calls must produce distinct ids
    rid1 = create_run_id(slide_number=3)
    rid2 = create_run_id(slide_number=3)
    assert rid1 != rid2


def test_initialise_manifest_minimum_shape():
    m = initialise_manifest(slide_number=3, vision_prose="Four ships.", budget_usd=1.0)
    assert m["slide_number"] == 3
    assert m["strategy"] == "creative_vision"
    assert len(m["prose_history"]) == 1
    assert m["prose_history"][0]["version"] == 1
    assert m["prose_history"][0]["prose"] == "Four ships."
    assert m["attempts"] == []
    assert m["final"] is None
    assert m["iterate_slide_hooks"]["remaining_budget_usd"] == 1.0
    # Task 6 addendum: _initial_budget_usd is stashed for later use by append_attempt
    assert m["_initial_budget_usd"] == 1.0


def test_save_and_load_roundtrip(tmp_path):
    deck_dir = tmp_path / "deck"
    deck_dir.mkdir()
    m = initialise_manifest(slide_number=3, vision_prose="Four ships.", budget_usd=1.0)
    save_manifest(str(deck_dir), m)
    loaded = load_manifest(str(deck_dir), slide_number=3)
    assert loaded == m


def test_save_creates_directory_structure(tmp_path):
    deck_dir = tmp_path / "deck"
    deck_dir.mkdir()
    m = initialise_manifest(slide_number=7, vision_prose="X", budget_usd=0.5)
    save_manifest(str(deck_dir), m)
    expected = deck_dir / "creative-vision" / "7" / "manifest.json"
    assert expected.is_file()
    # also creates runs/ subdir
    assert (deck_dir / "creative-vision" / "7" / "runs").is_dir()


def test_load_raises_when_missing(tmp_path):
    deck_dir = tmp_path / "deck"
    deck_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        load_manifest(str(deck_dir), slide_number=3)


from src.creative_vision.manifest import revise_prose  # noqa: E402


def test_revise_prose_bumps_version():
    m = initialise_manifest(slide_number=3, vision_prose="v1 prose", budget_usd=1.0)
    revise_prose(m, new_prose="v2 prose", revised_by="operator", reason="too vague")
    assert len(m["prose_history"]) == 2
    assert m["prose_history"][1]["version"] == 2
    assert m["prose_history"][1]["prose"] == "v2 prose"
    assert m["prose_history"][1]["revised_by"] == "operator"
    assert m["prose_history"][1]["reason"] == "too vague"


def test_revise_prose_preserves_history():
    m = initialise_manifest(slide_number=3, vision_prose="v1", budget_usd=1.0)
    revise_prose(m, new_prose="v2", revised_by="operator", reason="x")
    revise_prose(m, new_prose="v3", revised_by="operator", reason="y")
    assert [h["version"] for h in m["prose_history"]] == [1, 2, 3]
    assert [h["prose"] for h in m["prose_history"]] == ["v1", "v2", "v3"]


def test_revise_prose_rejects_empty_string():
    m = initialise_manifest(slide_number=3, vision_prose="v1", budget_usd=1.0)
    with pytest.raises(ValueError):
        revise_prose(m, new_prose="", revised_by="operator", reason="x")


from src.creative_vision.manifest import append_attempt, finalise_manifest  # noqa: E402


def _valid_verdict_inline():
    return {
        "verdict": "refine_at_tier",
        "per_axis_scores": {"entity_fidelity": 80, "spatial_fidelity": 80, "style_fidelity": 80, "quality": 80, "composition": 80},
        "issues": [],
        "gap_location": "prompt",
        "recommended_action": "x",
        "tier": "ollama",
        "iteration_index": 1,
        "plateau_signal": False,
    }


def _sample_attempt(idx=1, tier="ollama", cost=0.0, cumulative=0.0):
    return {
        "attempt_index": idx,
        "prose_version": 1,
        "tier": tier,
        "text_iterations": [{"prompt_draft": "p", "reviewer_verdict": "pass"}],
        "render": {
            "model": "flux-schnell",
            "resolution": "1024x576",
            "cost_usd": cost,
            "output_path": f"runs/{idx:02d}-{tier}.png",
        },
        "image_reviewer_verdict": "pass",
        "directors_critic_verdict": _valid_verdict_inline(),
        "cumulative_cost_usd": cumulative,
    }


_LADDER_FIXTURE = ["ollama", "flash_1k", "flash_2k", "flash_4k", "pro_1k", "pro_2k", "pro_4k"]


def test_append_attempt_updates_iterate_slide_hooks():
    m = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=1.0)
    append_attempt(m, _sample_attempt(idx=1, tier="flash_1k", cost=0.067, cumulative=0.067), ladder=_LADDER_FIXTURE)
    assert m["iterate_slide_hooks"]["current_tier"] == "flash_1k"
    assert m["iterate_slide_hooks"]["next_tier_available"] == "flash_2k"
    assert m["iterate_slide_hooks"]["remaining_budget_usd"] == pytest.approx(0.933)
    assert len(m["attempts"]) == 1


def test_append_attempt_preserves_ordering():
    m = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=1.0)
    append_attempt(m, _sample_attempt(idx=1, tier="ollama", cost=0.0, cumulative=0.0), ladder=_LADDER_FIXTURE)
    append_attempt(m, _sample_attempt(idx=2, tier="flash_1k", cost=0.067, cumulative=0.067), ladder=_LADDER_FIXTURE)
    assert [a["attempt_index"] for a in m["attempts"]] == [1, 2]


def test_append_attempt_at_top_of_ladder_clears_next_tier():
    m = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=5.0)
    append_attempt(m, _sample_attempt(idx=1, tier="pro_4k", cost=0.24, cumulative=0.24), ladder=_LADDER_FIXTURE)
    assert m["iterate_slide_hooks"]["next_tier_available"] is None


def test_finalise_manifest_sets_final_block():
    m = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=1.0)
    append_attempt(m, _sample_attempt(idx=1, tier="flash_1k", cost=0.067, cumulative=0.067), ladder=_LADDER_FIXTURE)
    final_verdict = _valid_verdict_inline()
    final_verdict["verdict"] = "pass"
    finalise_manifest(m, image_path="runs/01-flash-1k.png", final_verdict=final_verdict)
    assert m["final"] is not None
    assert m["final"]["image_path"] == "runs/01-flash-1k.png"
    assert m["final"]["accepted_at_tier"] == "flash_1k"
    assert m["final"]["total_cost_usd"] == pytest.approx(0.067)
    assert m["final"]["total_iterations"] == 1
    assert m["final"]["final_verdict"]["verdict"] == "pass"
