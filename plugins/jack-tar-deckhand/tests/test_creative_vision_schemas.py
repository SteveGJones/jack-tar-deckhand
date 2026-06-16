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


# --- iteration_caps_override schema constraints (#113 polish) ----------------


def test_strategy_map_iteration_caps_override_accepts_valid_tier_keys():
    """Valid cascade tier names as keys + positive ints as values pass."""
    m = _valid_strategy_map_entry_creative_vision()
    m["slides"][0]["creative_vision"]["iteration_caps_override"] = {
        "flash_1k": 1,
        "pro_1k": 2,
    }
    validate(instance=m, schema=_load("strategy_map.schema.json"))


def test_strategy_map_iteration_caps_override_accepts_null():
    """Null is explicitly permitted — schema-level "no override"."""
    m = _valid_strategy_map_entry_creative_vision()
    m["slides"][0]["creative_vision"]["iteration_caps_override"] = None
    validate(instance=m, schema=_load("strategy_map.schema.json"))


def test_strategy_map_iteration_caps_override_accepts_empty_object():
    """Empty object is permitted — degenerate case, same as null."""
    m = _valid_strategy_map_entry_creative_vision()
    m["slides"][0]["creative_vision"]["iteration_caps_override"] = {}
    validate(instance=m, schema=_load("strategy_map.schema.json"))


def test_strategy_map_iteration_caps_override_rejects_typoed_tier_name():
    """A typo on a tier name (e.g. 'flsh_1k') is the exact footgun this
    schema constraint exists to catch — silently ignored, would leave the
    cap inactive.

    Before this constraint landed, 'flsh_1k' passed schema validation and
    was silently dropped by the cost estimator (which only reads canonical
    tier names from the cascade ladder). The propertyNames enum catches it.
    """
    m = _valid_strategy_map_entry_creative_vision()
    m["slides"][0]["creative_vision"]["iteration_caps_override"] = {"flsh_1k": 1}
    with pytest.raises(ValidationError):
        validate(instance=m, schema=_load("strategy_map.schema.json"))


def test_strategy_map_iteration_caps_override_rejects_unknown_tier_name():
    """Any string that isn't a canonical cascade tier name is rejected."""
    m = _valid_strategy_map_entry_creative_vision()
    m["slides"][0]["creative_vision"]["iteration_caps_override"] = {
        "ultra_premium_8k": 1
    }
    with pytest.raises(ValidationError):
        validate(instance=m, schema=_load("strategy_map.schema.json"))


def test_strategy_map_iteration_caps_override_rejects_non_integer_value():
    """Tier names map to iteration counts — strings, floats, negatives are out."""
    m = _valid_strategy_map_entry_creative_vision()
    m["slides"][0]["creative_vision"]["iteration_caps_override"] = {"flash_1k": "3"}
    with pytest.raises(ValidationError):
        validate(instance=m, schema=_load("strategy_map.schema.json"))


def test_strategy_map_iteration_caps_override_rejects_zero_iterations():
    """Iteration cap must be positive — zero means 'never iterate', which
    is what allowed_ceiling already expresses by ladder truncation."""
    m = _valid_strategy_map_entry_creative_vision()
    m["slides"][0]["creative_vision"]["iteration_caps_override"] = {"flash_1k": 0}
    with pytest.raises(ValidationError):
        validate(instance=m, schema=_load("strategy_map.schema.json"))


def test_strategy_map_iteration_caps_override_accepts_all_canonical_tiers():
    """Pin the complete tier name list — if a new tier lands on the cascade
    (e.g. a hypothetical ultra-pro), the schema must be updated in lockstep."""
    m = _valid_strategy_map_entry_creative_vision()
    m["slides"][0]["creative_vision"]["iteration_caps_override"] = {
        "ollama": 5,
        "flash_1k": 3, "flash_2k": 3, "flash_4k": 3,
        "pro_1k": 2, "pro_2k": 2, "pro_4k": 1,
        "recraft_standard_1k": 3, "recraft_pro_2k": 2, "recraft_pro_4k": 1,
    }
    validate(instance=m, schema=_load("strategy_map.schema.json"))


# --- academic_figure block schema (#113 Path B) -----------------------------


def _valid_strategy_map_entry_academic_figure(*, with_block=False, block=None):
    """Build a minimal valid strategy map with one academic_figure slide.

    When ``with_block`` is False, the slide omits the academic_figure block
    (legacy paperbanana-loop default). When True, attaches ``block`` (or
    the canonical claude-critic example).
    """
    slide = {
        "slide_number": 1,
        "strategy": "academic_figure",
        "rationale": "operator-directed",
        "render_funnel": ["ollama"],
    }
    if with_block:
        slide["academic_figure"] = block if block is not None else {
            "critic": "claude",
            "figure_type": "architecture_diagram",
            "iteration_cap": 4,
            "log_paperbanana_verdict_for_comparison": False,
        }
    return {"approval_mode": "review", "slides": [slide]}


def test_strategy_map_accepts_academic_figure_without_block():
    """Legacy behaviour: academic_figure slide with no academic_figure block
    is valid (paperbanana-loop default)."""
    validate(
        instance=_valid_strategy_map_entry_academic_figure(with_block=False),
        schema=_load("strategy_map.schema.json"),
    )


def test_strategy_map_accepts_academic_figure_with_claude_critic_block():
    """Opt-in claude-critic block is valid."""
    validate(
        instance=_valid_strategy_map_entry_academic_figure(with_block=True),
        schema=_load("strategy_map.schema.json"),
    )


def test_strategy_map_rejects_academic_figure_block_on_non_academic_figure_slide():
    """Conditional: academic_figure block forbidden when strategy is something else."""
    bad = _valid_strategy_map_entry_academic_figure(with_block=True)
    bad["slides"][0]["strategy"] = "composed"
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("strategy_map.schema.json"))


def test_strategy_map_academic_figure_block_critic_enum():
    """critic must be paperbanana or claude — typo rejected."""
    bad = _valid_strategy_map_entry_academic_figure(with_block=True)
    bad["slides"][0]["academic_figure"]["critic"] = "anthropic"
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("strategy_map.schema.json"))


def test_strategy_map_academic_figure_block_figure_type_enum():
    """figure_type must be a canonical value."""
    bad = _valid_strategy_map_entry_academic_figure(with_block=True)
    bad["slides"][0]["academic_figure"]["figure_type"] = "schematic_blueprint"
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("strategy_map.schema.json"))


def test_strategy_map_academic_figure_iteration_cap_bounds():
    """iteration_cap must be in [1, 10]."""
    m = _valid_strategy_map_entry_academic_figure(with_block=True)
    m["slides"][0]["academic_figure"]["iteration_cap"] = 0
    with pytest.raises(ValidationError):
        validate(instance=m, schema=_load("strategy_map.schema.json"))
    m["slides"][0]["academic_figure"]["iteration_cap"] = 11
    with pytest.raises(ValidationError):
        validate(instance=m, schema=_load("strategy_map.schema.json"))
    m["slides"][0]["academic_figure"]["iteration_cap"] = 5
    validate(instance=m, schema=_load("strategy_map.schema.json"))


def test_strategy_map_academic_figure_additional_properties_rejected():
    """additionalProperties: false — typoed fields fail loud."""
    bad = _valid_strategy_map_entry_academic_figure(with_block=True)
    bad["slides"][0]["academic_figure"]["critique_mode"] = "claude"  # typo
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("strategy_map.schema.json"))


# --- figure_critic_verdict schema -------------------------------------------


def _valid_figure_critic_verdict():
    return {
        "verdict": "pass",
        "per_axis_scores": {
            "methodology_fidelity": 85,
            "caption_alignment": 88,
            "legibility": 82,
            "figure_type_correctness": 90,
            "aesthetic_quality": 84,
        },
        "issues": [],
        "refinement_feedback": "",
        "iteration_index": 1,
        "plateau_signal": False,
        "agrees_with_paperbanana_verdict": True,
    }


def test_figure_critic_verdict_happy_path():
    validate(
        instance=_valid_figure_critic_verdict(),
        schema=_load("figure_critic_verdict.schema.json"),
    )


def test_figure_critic_verdict_rejects_unknown_verdict():
    bad = _valid_figure_critic_verdict()
    bad["verdict"] = "needs_work"
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("figure_critic_verdict.schema.json"))


def test_figure_critic_verdict_rejects_out_of_range_score():
    bad = _valid_figure_critic_verdict()
    bad["per_axis_scores"]["legibility"] = 150
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("figure_critic_verdict.schema.json"))


def test_figure_critic_verdict_rejects_extra_axis():
    """additionalProperties: false on per_axis_scores."""
    bad = _valid_figure_critic_verdict()
    bad["per_axis_scores"]["narrative_arc"] = 80  # not a real axis
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("figure_critic_verdict.schema.json"))


def test_figure_critic_verdict_accepts_null_agreement():
    """agrees_with_paperbanana_verdict is nullable when no side-by-side was provided."""
    payload = _valid_figure_critic_verdict()
    payload["agrees_with_paperbanana_verdict"] = None
    validate(instance=payload, schema=_load("figure_critic_verdict.schema.json"))
