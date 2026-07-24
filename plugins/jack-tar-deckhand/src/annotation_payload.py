"""Annotation payload builder for deck-native annotations (issue #142 v2).

Bridges v1's pure-PIL overlay engine (src/annotate_figure.py) to the
deck-native assembly path: resolves label positions server-side via
place_labels, serialises them — with a content hash of the exact base
image the anchors were derived from (F4) and a fully-explicit style
block (F9) — into a per-slide payload the assemblers consume as pure
resolved coordinates.

Design: docs/superpowers/plans/2026-07-17-annotate-figure-v2.md §2.3.

No model calls, no network access. The only I/O is reading the base
image (hash + dimensions) and the atomic payload write.
"""

import json
import os

import jsonschema

from src.annotate_figure import _segment_box_entry, place_labels
from src.process_image import compute_content_hash, get_dimensions
from src.qa.config import QA_CONFIG

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), 'schemas')

# Fallback label font when no style guide is supplied. The design intent
# (§2.2) is "font_face from the style guide's body font"; the fallback
# only applies when the bridge has no style guide in hand.
DEFAULT_FONT_FACE = 'Calibri'

# Formula reference point for estimate_label_box (F13): 7 characters per
# inch at 18pt, scaled linearly by font size. This 18.0 is the formula's
# calibration constant, NOT the default label font size (which is the
# AP-02 floor, read from QA_CONFIG below).
_ESTIMATOR_REF_CPI = 7.0
_ESTIMATOR_REF_PT = 18.0


def _style_defaults(style_guide=None):
    """Code-level style defaults (F9 — the schema has NO defaults).

    The default label font size is the deck-qa AP-02 body-font floor,
    read from QA_CONFIG so the two stay aligned by construction (design
    §13 F3d note — the intent is "default = the AP-02 floor", not a
    hardcoded 18).
    """
    font_face = DEFAULT_FONT_FACE
    if style_guide:
        font_face = (style_guide.get('typography', {}) or {}).get(
            'body_font') or DEFAULT_FONT_FACE
    return {
        'leader_width_pt': 1.5,
        'casing_width_pt': 3.5,
        'casing_color': 'FFFFFF',
        'leader_color': '141414',
        'dot_radius_pt': 3.0,
        'box_fill': 'FFFFFF',
        'box_border': '141414',
        'box_border_width_pt': 1.0,
        'text_color': '141414',
        'font_face': font_face,
        'font_size_pt': QA_CONFIG['min_font_size_body_pt'],
    }


def _load_annotations_schema():
    with open(os.path.join(SCHEMA_DIR, 'annotations.schema.json')) as f:
        return json.load(f)


def build_annotation_payload(slide_number, source, base_image_path,
                             image_dimensions, placement_zone, anchors,
                             *, style_overrides=None, style_guide=None):
    """Build a schema-valid, fully-explicit SlideAnnotations payload dict.

    Reuses annotate_figure.place_labels verbatim to resolve collision-free
    label positions (the load-bearing v1 reuse), computes the base image's
    sha256 content hash (F4 invalidation contract), and fills every style
    field in code (F9) so on-disk payloads never rely on schema defaults.

    Args:
        slide_number: 1-based slide number.
        source: 'external' or 'generated'.
        base_image_path: Path to the UNLABELLED base image. Must exist —
            it is read for its content hash (and dimensions when
            image_dimensions is None).
        image_dimensions: {"width": int, "height": int} in pixels, or
            None to read them from the image via process_image.
            get_dimensions.
        placement_zone: 'annotated_full_slide' or 'annotated_image_zone'.
        anchors: VALIDATED {label: [x, y]} dict (normalized 0-1), from
            annotate_figure.validate_anchors().
        style_overrides: Optional dict of style fields that win over the
            code-level defaults (e.g. {'font_size_pt': 14}).
        style_guide: Optional StyleGuide dict — its typography.body_font
            becomes the default font_face.

    Returns:
        dict: payload validated against annotations.schema.json.

    Raises:
        FileNotFoundError: base_image_path does not exist.
        ValueError: anchors empty / image dimensions non-positive.
        jsonschema.ValidationError: the assembled payload (e.g. a bad
            source or placement_zone argument) violates the schema.
    """
    if not os.path.exists(base_image_path):
        raise FileNotFoundError(f'Base image not found: {base_image_path}')
    if not anchors:
        raise ValueError('anchors dict is empty — at least one anchor is required')

    if image_dimensions is None:
        width, height = get_dimensions(base_image_path)
        image_dimensions = {'width': width, 'height': height}

    placements = place_labels(
        anchors,
        (image_dimensions['width'], image_dimensions['height']),
    )

    labels = [
        {
            'text': name,
            'anchor': list(placements[name]['anchor']),
            'label_pos': list(placements[name]['label_pos']),
        }
        for name in anchors
    ]

    style = _style_defaults(style_guide)
    if style_overrides:
        style.update(style_overrides)

    payload = {
        'slide_number': slide_number,
        'source': source,
        'base_image_path': base_image_path,
        'base_image_hash': compute_content_hash(base_image_path),
        'image_dimensions': dict(image_dimensions),
        'placement_zone': placement_zone,
        'fit': 'contain',
        'labels': labels,
        'style': style,
    }

    jsonschema.Draft202012Validator(_load_annotations_schema()).validate(payload)
    return payload


def write_annotation_payload(deck_dir, slide_number, payload):
    """Atomically write the payload to annotations/slide-NN-annotations.json.

    Creates <deck_dir>/annotations/ if needed, writes to a .tmp sibling,
    then os.replace()s into place (mirroring manifest_utils.save_manifest).

    Args:
        deck_dir: Path to the deck working directory.
        slide_number: 1-based slide number (used for the NN filename).
        payload: The payload dict (from build_annotation_payload).

    Returns:
        str: absolute-or-as-given path of the written payload file.
    """
    annotations_dir = os.path.join(deck_dir, 'annotations')
    os.makedirs(annotations_dir, exist_ok=True)

    path = os.path.join(
        annotations_dir, f'slide-{slide_number:02d}-annotations.json')
    tmp_path = path + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(payload, f, indent=2)
        f.write('\n')
    os.replace(tmp_path, path)
    return path


def segment_box_entry(p0, p1, box):
    """Shared geometry helper (§4.6): where segment p0 -> p1 first enters
    an axis-aligned box.

    `annotation_payload` is the single import surface for the shared
    geometry helpers used by both assembler paths (§2.3, §4.6) — this is
    a thin re-export of `annotate_figure._segment_box_entry`, the exact
    slab-clip v1 uses to terminate a leader line at its own label box's
    edge nearest the anchor rather than drawing into the box interior.
    The python-pptx template path (T5) calls this directly; the JS
    assembler (T6) ports the same ~15-line algorithm verbatim as
    `segmentBoxEntry` in `assembler/annotation_geometry.js`. Parity
    between the two is pinned by `test_annotation_geometry_parity.py`
    (§8.3, F13).

    Args:
        p0: (x, y) segment start (the anchor), in any consistent unit
            (pixels for v1's raster path, inches/EMU for the assemblers).
        p1: (x, y) segment end (the label box centre), same unit as p0.
        box: (left, top, right, bottom) rect, same unit as p0/p1.

    Returns:
        (x, y) tuple: the entry point on the box perimeter, or p0 when the
        anchor already lies inside the box (zero-length leader), or p1
        unchanged for the degenerate case where the segment never enters
        the box at all.
    """
    return _segment_box_entry(p0, p1, box)


def estimate_label_box(text, font_size_pt, *, pad_in=0.06):
    """THE single shared label-box estimator (F13).

    Both assembler paths use this exact formula (the JS assembler ports
    it verbatim), so label boxes agree across paths:

        chars_per_inch = 7.0 * (18.0 / font_size_pt)   # 7 cpi at 18pt, linear
        text_w_in = len(text) / chars_per_inch
        box_w_in  = text_w_in + 2 * pad_in
        box_h_in  = (font_size_pt / 72.0) * 1.4 + 2 * pad_in

    Args:
        text: The label string.
        font_size_pt: Label font size in points.
        pad_in: Fixed padding in inches on each side (default 0.06).

    Returns:
        (box_w_in, box_h_in) tuple of floats, in inches.
    """
    if font_size_pt <= 0:
        raise ValueError(f'font_size_pt must be positive, got {font_size_pt}')
    chars_per_inch = _ESTIMATOR_REF_CPI * (_ESTIMATOR_REF_PT / font_size_pt)
    text_w_in = len(text) / chars_per_inch
    box_w_in = text_w_in + 2 * pad_in
    box_h_in = (font_size_pt / 72.0) * 1.4 + 2 * pad_in
    return (box_w_in, box_h_in)
