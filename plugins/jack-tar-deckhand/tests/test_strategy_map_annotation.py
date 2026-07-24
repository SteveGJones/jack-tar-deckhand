"""Schema surfacing tests for annotate-figure v2 (issue #142).

Covers the `annotation_mode` / `annotation` properties and the F1-fixed
`allOf` conditional added to strategy_map.schema.json (design doc
docs/superpowers/plans/2026-07-17-annotate-figure-v2.md, §6.1 / §8.2).

The load-bearing regression is `test_schema_accepts_entry_without_annotation_mode_key`:
before the F1 fix, the conditional's `if` matched vacuously against any
slide lacking the `annotation_mode` key (JSON Schema's `properties` keyword
does not imply presence), so EVERY legacy strategy-map document — none of
which carry `annotation_mode` — would have been forced into the `then`
branch and rejected for missing `annotation`. The fix adds
`"required": ["annotation_mode"]` to the `if`, making the conditional only
fire when the key is actually present.
"""
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


def _schema():
    return _load("strategy_map.schema.json")


def _base_slide(**overrides):
    slide = {
        "slide_number": 1,
        "strategy": "full_bleed",
        "rationale": "hero figure",
        "render_funnel": ["ollama", "cloud_low", "cloud_full"],
    }
    slide.update(overrides)
    return slide


def _base_map(slide):
    return {
        "approval_mode": "review",
        "slides": [slide],
    }


def _valid_annotation():
    return {
        "labels": [
            {"text": "SAP", "target": "leftmost ship"},
            {"text": "Databricks", "target": "second ship from left"},
        ]
    }


# --- F1 regression pin --------------------------------------------------


def test_schema_accepts_entry_without_annotation_mode_key():
    """Legacy strategy-map documents with NO annotation_mode key on any
    slide must validate unchanged. This is the F1 blocker regression pin."""
    slide = _base_slide()
    assert "annotation_mode" not in slide
    assert "annotation" not in slide
    validate(instance=_base_map(slide), schema=_schema())


# --- none / absent behaviour ---------------------------------------------


def test_schema_accepts_annotation_mode_none_without_annotation():
    slide = _base_slide(annotation_mode="none")
    validate(instance=_base_map(slide), schema=_schema())


# --- positive native / raster cases --------------------------------------


def test_schema_accepts_native_with_annotation_on_full_bleed():
    slide = _base_slide(
        strategy="full_bleed",
        annotation_mode="native",
        annotation=_valid_annotation(),
    )
    validate(instance=_base_map(slide), schema=_schema())


def test_schema_accepts_raster_with_annotation_on_academic_figure():
    slide = _base_slide(
        strategy="academic_figure",
        annotation_mode="raster",
        annotation=_valid_annotation(),
    )
    validate(instance=_base_map(slide), schema=_schema())


# --- negative conditional cases ------------------------------------------


def test_schema_rejects_native_without_annotation():
    slide = _base_slide(strategy="full_bleed", annotation_mode="native")
    with pytest.raises(ValidationError):
        validate(instance=_base_map(slide), schema=_schema())


def test_schema_rejects_annotation_without_mode():
    slide = _base_slide(annotation=_valid_annotation())
    assert "annotation_mode" not in slide
    with pytest.raises(ValidationError):
        validate(instance=_base_map(slide), schema=_schema())


def test_schema_rejects_annotation_with_mode_none():
    slide = _base_slide(annotation_mode="none", annotation=_valid_annotation())
    with pytest.raises(ValidationError):
        validate(instance=_base_map(slide), schema=_schema())


def test_schema_rejects_native_on_creative_vision():
    slide = _base_slide(
        strategy="creative_vision",
        annotation_mode="native",
        annotation=_valid_annotation(),
        creative_vision={"vision_prose": "Four warships on a lake."},
    )
    with pytest.raises(ValidationError):
        validate(instance=_base_map(slide), schema=_schema())


def test_schema_rejects_native_on_smartart():
    slide = _base_slide(
        strategy="smartart",
        annotation_mode="native",
        annotation=_valid_annotation(),
    )
    with pytest.raises(ValidationError):
        validate(instance=_base_map(slide), schema=_schema())


def test_schema_rejects_label_missing_target():
    annotation = _valid_annotation()
    del annotation["labels"][0]["target"]
    slide = _base_slide(
        strategy="full_bleed",
        annotation_mode="native",
        annotation=annotation,
    )
    with pytest.raises(ValidationError):
        validate(instance=_base_map(slide), schema=_schema())


# --- v2.1: show_headline (issue #142 v2.1) --------------------------------


def test_schema_accepts_native_with_show_headline_true():
    annotation = _valid_annotation()
    annotation["show_headline"] = True
    slide = _base_slide(
        strategy="full_bleed",
        annotation_mode="native",
        annotation=annotation,
    )
    validate(instance=_base_map(slide), schema=_schema())


def test_schema_accepts_annotation_without_show_headline():
    """Omitted show_headline is valid (default false); backward-compat pin."""
    slide = _base_slide(
        strategy="full_bleed",
        annotation_mode="native",
        annotation=_valid_annotation(),
    )
    assert "show_headline" not in slide["annotation"]
    validate(instance=_base_map(slide), schema=_schema())


def test_schema_rejects_non_boolean_show_headline():
    annotation = _valid_annotation()
    annotation["show_headline"] = "yes"
    slide = _base_slide(
        strategy="full_bleed",
        annotation_mode="native",
        annotation=annotation,
    )
    with pytest.raises(ValidationError):
        validate(instance=_base_map(slide), schema=_schema())


def test_schema_accepts_native_on_composed_with_annotation():
    """Regression pin: composed remains a legal strategy for native annotation."""
    slide = _base_slide(
        strategy="composed",
        annotation_mode="native",
        annotation=_valid_annotation(),
    )
    validate(instance=_base_map(slide), schema=_schema())


# --- blank_zone variant (issue #142, final scope item) --------------------


def test_schema_accepts_annotation_blank_zone_all_values():
    for mode in ("native", "raster"):
        for zone in ("left_third", "right_third", "top_strip", "bottom_strip", "auto"):
            annotation = _valid_annotation()
            annotation["blank_zone"] = zone
            slide = _base_slide(
                strategy="full_bleed",
                annotation_mode=mode,
                annotation=annotation,
            )
            validate(instance=_base_map(slide), schema=_schema())


def test_schema_rejects_unknown_blank_zone_value():
    """'top_band' is the F8-rejected collision value (§2.2) — deliberately
    used as the fixture here to also pin the vocabulary decision."""
    annotation = _valid_annotation()
    annotation["blank_zone"] = "top_band"
    slide = _base_slide(
        strategy="full_bleed",
        annotation_mode="native",
        annotation=annotation,
    )
    with pytest.raises(ValidationError):
        validate(instance=_base_map(slide), schema=_schema())


def test_schema_accepts_annotation_without_blank_zone():
    """Backward-compat pin: omitted blank_zone is valid, v2/v2.1 shape."""
    slide = _base_slide(
        strategy="full_bleed",
        annotation_mode="native",
        annotation=_valid_annotation(),
    )
    assert "blank_zone" not in slide["annotation"]
    validate(instance=_base_map(slide), schema=_schema())
