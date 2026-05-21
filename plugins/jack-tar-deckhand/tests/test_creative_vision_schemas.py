"""Schema validation tests for the creative_vision pipeline (issue #105)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

SCHEMA_DIR = PLUGIN_ROOT / "src" / "schemas"


def _load(name):
    with open(SCHEMA_DIR / name) as f:
        return json.load(f)


# --- parsed_vision -----------------------------------------------------------


def _valid_parsed_vision():
    return {
        "schema_version": "1.0",
        "original_prose": "Four warships on a lake.",
        "prose_version": 1,
        "subjects": [
            {"name": "SAP", "role": "named_entity", "spatial_slot": "ship_NE"}
        ],
        "spatial_directives": {
            "setting": "lake",
            "layout": "four-way",
            "containment": None,
            "named_relationships": [],
        },
        "style": {"explicit": None, "implied": "naval", "register_inherited_from": None},
        "composition": {
            "progression_axis": None,
            "primary_focus": "centre",
            "compositional_rules": [],
        },
        "delivery": {
            "scale": "screen_16x9",
            "aspect": "16:9",
            "viewing_context": "projection",
        },
        "text_density_warning": {
            "estimated_text_elements": 4,
            "threshold_breach": False,
        },
    }


def test_parsed_vision_minimal_valid():
    validate(instance=_valid_parsed_vision(), schema=_load("parsed_vision.schema.json"))


def test_parsed_vision_missing_required_rejected():
    bad = _valid_parsed_vision()
    del bad["original_prose"]
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("parsed_vision.schema.json"))


def test_parsed_vision_progression_axis_optional():
    pv = _valid_parsed_vision()
    pv["composition"]["progression_axis"] = "spatial_horizontal"
    validate(instance=pv, schema=_load("parsed_vision.schema.json"))


# --- directors_critic_verdict ------------------------------------------------


def _valid_verdict():
    return {
        "verdict": "refine_at_tier",
        "per_axis_scores": {
            "entity_fidelity": 65,
            "spatial_fidelity": 85,
            "style_fidelity": 90,
            "quality": 80,
            "composition": 75,
        },
        "issues": [
            {"axis": "entity_fidelity", "detail": "Databricks ship missing"}
        ],
        "gap_location": "prompt",
        "recommended_action": "Re-emphasise Databricks as labelled fourth ship",
        "tier": "flash_2k",
        "iteration_index": 2,
        "plateau_signal": False,
    }


def test_verdict_minimal_valid():
    validate(instance=_valid_verdict(), schema=_load("directors_critic_verdict.schema.json"))


def test_verdict_rejects_unknown_verdict_enum():
    bad = _valid_verdict()
    bad["verdict"] = "made_up"
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("directors_critic_verdict.schema.json"))


def test_verdict_rejects_score_out_of_range():
    bad = _valid_verdict()
    bad["per_axis_scores"]["quality"] = 150
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("directors_critic_verdict.schema.json"))


@pytest.mark.parametrize("verdict", ["pass", "refine_at_tier", "escalate_tier", "abort"])
def test_verdict_accepts_all_verdicts(verdict):
    v = _valid_verdict()
    v["verdict"] = verdict
    validate(instance=v, schema=_load("directors_critic_verdict.schema.json"))


@pytest.mark.parametrize("gap", ["prose", "prompt", "tier", "unknown"])
def test_verdict_accepts_all_gap_locations(gap):
    v = _valid_verdict()
    v["gap_location"] = gap
    validate(instance=v, schema=_load("directors_critic_verdict.schema.json"))
