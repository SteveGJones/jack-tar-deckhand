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


# --- creative_vision_manifest -----------------------------------------------


def _valid_manifest():
    return {
        "run_id": "cv-2026-05-21-093142-slide-3",
        "slide_number": 3,
        "strategy": "creative_vision",
        "prose_history": [
            {"version": 1, "timestamp": "2026-05-21T09:31:42Z", "prose": "Four ships..."}
        ],
        "attempts": [],
        "final": None,
        "iterate_slide_hooks": {
            "can_revise_prose": True,
            "can_refine_prompt": True,
            "can_escalate_tier": True,
            "current_tier": "ollama",
            "next_tier_available": "flash_1k",
            "remaining_budget_usd": 1.0,
        },
    }


def test_manifest_minimal_valid():
    validate(instance=_valid_manifest(), schema=_load("creative_vision_manifest.schema.json"))


def test_manifest_prose_revision_appended():
    m = _valid_manifest()
    m["prose_history"].append({
        "version": 2,
        "timestamp": "2026-05-21T10:00:00Z",
        "prose": "Four 1980s Cold-War warships...",
        "revised_by": "operator",
        "reason": "fishing-boat look in v1",
    })
    validate(instance=m, schema=_load("creative_vision_manifest.schema.json"))


def test_manifest_with_final_block():
    m = _valid_manifest()
    m["final"] = {
        "image_path": "runs/07-flash-4k.png",
        "accepted_at_tier": "flash_4k",
        "total_cost_usd": 0.43,
        "total_iterations": 7,
        "final_verdict": _valid_verdict(),
    }
    m["final"]["final_verdict"]["verdict"] = "pass"
    validate(instance=m, schema=_load("creative_vision_manifest.schema.json"))


def test_manifest_strategy_must_be_creative_vision():
    bad = _valid_manifest()
    bad["strategy"] = "full_bleed"
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("creative_vision_manifest.schema.json"))


# --- strategy_map.creative_vision integration -------------------------------


def _valid_strategy_map_entry_creative_vision():
    return {
        "approval_mode": "review",
        "slides": [
            {
                "slide_number": 1,
                "strategy": "creative_vision",
                "rationale": "operator-directed",
                "render_funnel": ["ollama", "cloud_low", "cloud_full"],
                "creative_vision": {
                    "vision_prose": "Four warships on a lake.",
                    "budget_usd": 1.0,
                    "allowed_ceiling": "pro_4k",
                    "iteration_caps_override": None,
                },
            }
        ],
    }


def test_strategy_map_accepts_creative_vision_strategy():
    validate(
        instance=_valid_strategy_map_entry_creative_vision(),
        schema=_load("strategy_map.schema.json"),
    )


def test_strategy_map_creative_vision_block_required_when_strategy_set():
    bad = _valid_strategy_map_entry_creative_vision()
    del bad["slides"][0]["creative_vision"]
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("strategy_map.schema.json"))


def test_strategy_map_creative_vision_block_forbidden_when_strategy_other():
    bad = _valid_strategy_map_entry_creative_vision()
    bad["slides"][0]["strategy"] = "composed"
    # creative_vision block still present - must reject
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("strategy_map.schema.json"))


def test_strategy_map_vision_prose_required_inside_block():
    bad = _valid_strategy_map_entry_creative_vision()
    del bad["slides"][0]["creative_vision"]["vision_prose"]
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("strategy_map.schema.json"))
