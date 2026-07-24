"""Tests for the annotate-figure v2 payload contract
(issue #142, design doc docs/superpowers/plans/2026-07-17-annotate-figure-v2.md).

T1 scope: schema-shape tests from design-doc §8.1 that exercise
`annotations.schema.json` directly, plus the F8 image-manifest extension test.

T2 scope: the remaining §8.1 cases — test_build_payload_* /
test_write_payload_* / test_estimate_label_box_formula — exercising
`src/annotation_payload.py` (build_annotation_payload /
write_annotation_payload / estimate_label_box). Synthetic base images are
created via PIL in tmp_path; no image is ever Read into context.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate
from PIL import Image

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.annotate_figure import place_labels  # noqa: E402
from src.annotation_payload import (  # noqa: E402
    build_annotation_payload,
    estimate_label_box,
    write_annotation_payload,
)
from src.qa.config import QA_CONFIG  # noqa: E402

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


# --- blank_zone audit block (issue #142, final scope item) -----------------


def test_schema_accepts_payload_without_blank_zone():
    """v2/v2.1 payloads on disk (no blank_zone key at all) stay valid."""
    payload = _valid_payload()
    assert "blank_zone" not in payload
    validate(instance=payload, schema=_annotations_schema())


def test_schema_rejects_bad_blank_zone_placement_value():
    payload = _valid_payload()
    payload["blank_zone"] = {
        "requested": "right_third",
        "resolved": "right_third",
        "verified_clear": True,
        "placement": "zone_partial",  # not in the enum
    }
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


# ===========================================================================
# T2 — build_annotation_payload / write_annotation_payload / estimate_label_box
# ===========================================================================

AP02_FLOOR = QA_CONFIG["min_font_size_body_pt"]

ANCHORS = {
    "Rudder": [0.82, 0.71],
    "Mainsail": [0.45, 0.2],
}


def _make_base_image(tmp_path, size=(800, 600), color=(30, 30, 30),
                     name="base.png"):
    """Synthesize a solid-colour base image on disk (never Read back)."""
    img = Image.new("RGB", size, color)
    path = tmp_path / name
    img.save(path)
    return str(path)


def _build(tmp_path, **overrides):
    base = overrides.pop("base_image_path", None) or _make_base_image(tmp_path)
    kwargs = {
        "slide_number": 3,
        "source": "generated",
        "base_image_path": base,
        "image_dimensions": {"width": 800, "height": 600},
        "placement_zone": "annotated_full_slide",
        "anchors": dict(ANCHORS),
    }
    kwargs.update(overrides)
    return build_annotation_payload(**kwargs)


# --- build_annotation_payload ----------------------------------------------


def test_build_payload_resolves_label_pos_via_place_labels(tmp_path):
    """The load-bearing reuse assertion: label_pos comes verbatim from
    annotate_figure.place_labels — the assembler never re-runs placement."""
    payload = _build(tmp_path)
    expected = place_labels(ANCHORS, (800, 600))
    by_text = {lbl["text"]: lbl for lbl in payload["labels"]}
    assert set(by_text) == set(ANCHORS)
    for name in ANCHORS:
        assert by_text[name]["anchor"] == list(expected[name]["anchor"])
        assert by_text[name]["label_pos"] == list(expected[name]["label_pos"])


def test_build_payload_is_deterministic(tmp_path):
    base = _make_base_image(tmp_path)
    p1 = _build(tmp_path, base_image_path=base)
    p2 = _build(tmp_path, base_image_path=base)
    assert p1 == p2


def test_build_payload_preserves_label_text_verbatim(tmp_path):
    anchors = {
        "Bow thruster (fwd)": [0.1, 0.5],
        "Mizzen — aft mast": [0.9, 0.5],
    }
    payload = _build(tmp_path, anchors=anchors)
    assert sorted(lbl["text"] for lbl in payload["labels"]) == sorted(anchors)


def test_build_payload_computes_content_hash_of_base_image(tmp_path):
    """F4: base_image_hash is the sha256 of the file bytes, and changing
    the file changes the hash."""
    base = _make_base_image(tmp_path)
    payload = _build(tmp_path, base_image_path=base)
    with open(base, "rb") as fh:
        expected = hashlib.sha256(fh.read()).hexdigest()
    assert payload["base_image_hash"] == expected

    # Regenerate the image with different content -> hash must change.
    Image.new("RGB", (800, 600), (200, 10, 10)).save(base)
    payload2 = _build(tmp_path, base_image_path=base)
    assert payload2["base_image_hash"] != payload["base_image_hash"]


def test_build_payload_fills_all_style_fields_in_code(tmp_path):
    """F9: NO schema defaults — the CODE fills every style field, so the
    on-disk payload is fully explicit. Default font size is the AP-02
    body floor read from QA_CONFIG (parametric, not a hardcoded 18)."""
    payload = _build(tmp_path)
    style = payload["style"]
    schema_style = _annotations_schema()["$defs"]["style"]
    assert set(style) == set(schema_style["required"])
    assert style["font_size_pt"] == AP02_FLOOR
    assert style["leader_width_pt"] == 1.5
    assert style["casing_width_pt"] == 3.5
    assert style["casing_color"] == "FFFFFF"
    assert style["leader_color"] == "141414"
    assert style["dot_radius_pt"] == 3.0
    assert style["box_fill"] == "FFFFFF"
    assert style["box_border"] == "141414"
    assert style["box_border_width_pt"] == 1.0
    assert style["text_color"] == "141414"
    assert isinstance(style["font_face"], str) and style["font_face"]


def test_build_payload_style_override_wins(tmp_path):
    payload = _build(tmp_path, style_overrides={"font_size_pt": 14})
    assert payload["style"]["font_size_pt"] == 14
    # Non-overridden fields keep their defaults.
    assert payload["style"]["leader_width_pt"] == 1.5


def test_build_payload_font_face_from_style_guide(tmp_path):
    style_guide = {"typography": {"body_font": "Avenir Next",
                                  "heading_font": "Avenir Next Bold"}}
    payload = _build(tmp_path, style_guide=style_guide)
    assert payload["style"]["font_face"] == "Avenir Next"


def test_build_payload_reads_dimensions_when_omitted(tmp_path):
    """image_dimensions=None -> read from the image via
    process_image.get_dimensions."""
    base = _make_base_image(tmp_path, size=(1024, 576))
    payload = _build(tmp_path, base_image_path=base, image_dimensions=None)
    assert payload["image_dimensions"] == {"width": 1024, "height": 576}


def test_build_payload_result_is_schema_valid(tmp_path):
    payload = _build(tmp_path)
    validate(instance=payload, schema=_annotations_schema())
    assert payload["fit"] == "contain"


def test_build_payload_missing_base_image_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        _build(tmp_path, base_image_path=str(tmp_path / "nope.png"))


def test_build_payload_empty_anchors_raises(tmp_path):
    with pytest.raises(ValueError):
        _build(tmp_path, anchors={})


def test_build_payload_invalid_placement_zone_raises(tmp_path):
    with pytest.raises(ValidationError):
        _build(tmp_path, placement_zone="full_bleed")


def test_build_payload_invalid_source_raises(tmp_path):
    with pytest.raises(ValidationError):
        _build(tmp_path, source="conjured")


# --- write_annotation_payload ----------------------------------------------


def test_write_payload_atomic_and_roundtrips(tmp_path):
    payload = _build(tmp_path)
    deck_dir = tmp_path / "deck"
    deck_dir.mkdir()
    path = write_annotation_payload(str(deck_dir), 3, payload)

    assert path == str(deck_dir / "annotations" / "slide-03-annotations.json")
    assert Path(path).exists()
    # No leftover tmp file (os.replace atomicity convention).
    assert not Path(path + ".tmp").exists()

    with open(path) as fh:
        reloaded = json.load(fh)
    assert reloaded == payload
    validate(instance=reloaded, schema=_annotations_schema())


def test_write_payload_zero_pads_slide_number(tmp_path):
    payload = _build(tmp_path, slide_number=12)
    deck_dir = tmp_path / "deck"
    deck_dir.mkdir()
    path = write_annotation_payload(str(deck_dir), 12, payload)
    assert path.endswith("slide-12-annotations.json")
    path9 = write_annotation_payload(str(deck_dir), 9, payload)
    assert path9.endswith("slide-09-annotations.json")


# --- estimate_label_box (F13) ----------------------------------------------


def test_estimate_label_box_formula():
    """Pins the exact F13 formula: 7 cpi at 18pt scaled linearly by font
    size, plus fixed 0.06in padding per side; height = line height 1.4x
    of the font's inch size plus the same padding."""
    # 18pt reference point: cpi = 7.0
    w, h = estimate_label_box("Rudder", 18)  # 6 chars
    assert w == pytest.approx(6 / 7.0 + 0.12)
    assert h == pytest.approx((18 / 72.0) * 1.4 + 0.12)

    # 12pt: cpi = 7.0 * 18/12 = 10.5
    w, h = estimate_label_box("Mizzenmast", 12)  # 10 chars
    assert w == pytest.approx(10 / 10.5 + 0.12)
    assert h == pytest.approx((12 / 72.0) * 1.4 + 0.12)

    # 36pt: cpi = 3.5 — larger text, wider boxes
    w, h = estimate_label_box("Keel", 36)  # 4 chars
    assert w == pytest.approx(4 / 3.5 + 0.12)
    assert h == pytest.approx((36 / 72.0) * 1.4 + 0.12)


def test_estimate_label_box_pad_override():
    w, h = estimate_label_box("ab", 18, pad_in=0.1)
    assert w == pytest.approx(2 / 7.0 + 0.2)
    assert h == pytest.approx((18 / 72.0) * 1.4 + 0.2)


def test_estimate_label_box_rejects_non_positive_font_size():
    with pytest.raises(ValueError):
        estimate_label_box("x", 0)
