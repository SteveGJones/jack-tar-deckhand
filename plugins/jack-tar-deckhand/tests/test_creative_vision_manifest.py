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
