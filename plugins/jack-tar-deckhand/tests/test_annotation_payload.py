"""Schema validation tests for the annotate-figure v2 payload contract
(issue #142, design doc docs/superpowers/plans/2026-07-17-annotate-figure-v2.md).

T1 scope only: schema-shape tests from design-doc §8.1 that exercise
`annotations.schema.json` directly, plus the F8 image-manifest extension test.
The remaining §8.1 cases (test_build_payload_*, test_write_payload_*,
test_estimate_label_box_formula) depend on `src/annotation_payload.py`
(build_annotation_payload / write_annotation_payload / estimate_label_box),
which is T2 scope and does not exist yet — they are intentionally NOT included
here and belong in a follow-up addition to this same file once T2 lands.
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


def _annotations_schema():
    return _load("annotations.schema.json")


def _image_manifest_schema():
    return _load("image_manifest.schema.json")


def _valid_payload():
    return {
        "slide_number": 3,
        "source": "generated",
        "base_image_path": "images/slide-03-base.png",
        "base_image_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "image_dimensions": {"width": 1920, "height": 1080},
        "placement_zone": "annotated_full_slide",
        "fit": "contain",
        "labels": [
            {"text": "Rudder", "anchor": [0.82, 0.71], "label_pos": [0.92, 0.71]},
            {"text": "Mainsail", "anchor": [0.45, 0.2], "label_pos": [0.45, 0.05]},
        ],
        "style": {
            "leader_width_pt": 1.5,
            "casing_width_pt": 3.5,
            "casing_color": "FFFFFF",
            "leader_color": "141414",
            "dot_radius_pt": 3.0,
            "box_fill": "FFFFFF",
            "box_border": "141414",
            "box_border_width_pt": 1.0,
            "text_color": "141414",
            "font_face": "Calibri",
            "font_size_pt": 18,
        },
    }


# --- annotations.schema.json ------------------------------------------------


def test_schema_valid_payload_passes():
    validate(instance=_valid_payload(), schema=_annotations_schema())


def test_schema_rejects_out_of_range_norm_point():
    payload = _valid_payload()
    payload["labels"][0]["anchor"] = [1.4, 0.2]
    with pytest.raises(ValidationError):
        validate(instance=payload, schema=_annotations_schema())


def test_schema_rejects_empty_labels():
    payload = _valid_payload()
    payload["labels"] = []
    with pytest.raises(ValidationError):
        validate(instance=payload, schema=_annotations_schema())


def test_schema_rejects_zero_image_dimension():
    payload = _valid_payload()
    payload["image_dimensions"]["width"] = 0
    with pytest.raises(ValidationError):
        validate(instance=payload, schema=_annotations_schema())


def test_schema_requires_contain_fit():
    payload = _valid_payload()
    payload["fit"] = "cover"
    with pytest.raises(ValidationError):
        validate(instance=payload, schema=_annotations_schema())


def test_schema_requires_base_image_hash():
    payload = _valid_payload()
    del payload["base_image_hash"]
    with pytest.raises(ValidationError):
        validate(instance=payload, schema=_annotations_schema())


def test_schema_accepts_annotated_image_zone_placement():
    """placement_zone enum's second value (composed path, deferred per F2
    but schema-allowed) — sanity check on the full enum, not just the
    full_bleed value exercised by _valid_payload()."""
    payload = _valid_payload()
    payload["placement_zone"] = "annotated_image_zone"
    validate(instance=payload, schema=_annotations_schema())


def test_schema_rejects_unknown_placement_zone():
    payload = _valid_payload()
    payload["placement_zone"] = "full_bleed"
    with pytest.raises(ValidationError):
        validate(instance=payload, schema=_annotations_schema())


def test_schema_rejects_style_missing_required_field():
    """F9: style has NO defaults — every field is required so on-disk
    payloads are always fully explicit."""
    payload = _valid_payload()
    del payload["style"]["font_size_pt"]
    with pytest.raises(ValidationError):
        validate(instance=payload, schema=_annotations_schema())


def test_schema_rejects_label_missing_text():
    payload = _valid_payload()
    del payload["labels"][0]["text"]
    with pytest.raises(ValidationError):
        validate(instance=payload, schema=_annotations_schema())


# --- image_manifest.schema.json (F8) ----------------------------------------


def _valid_image_manifest_entry(**overrides):
    entry = {
        "image_id": "img-slide-03",
        "slide_number": 3,
        "file_path": "images/slide-03-base.png",
        "status": "generated",
    }
    entry.update(overrides)
    return entry


def test_image_manifest_schema_accepts_annotations_path_and_zones():
    for zone in ("annotated_full_slide", "annotated_image_zone"):
        manifest = {
            "images": [
                _valid_image_manifest_entry(
                    placement_zone=zone,
                    annotations_path="annotations/slide-03-annotations.json",
                )
            ]
        }
        validate(instance=manifest, schema=_image_manifest_schema())


def test_image_manifest_schema_still_accepts_legacy_zones_without_annotations_path():
    """Regression pin: existing zone vocabulary ('full_bleed', 'background')
    and entries with no annotations_path at all still validate — the F8
    extension is additive."""
    manifest = {
        "images": [
            _valid_image_manifest_entry(placement_zone="full_bleed"),
            _valid_image_manifest_entry(placement_zone="background"),
        ]
    }
    validate(instance=manifest, schema=_image_manifest_schema())
