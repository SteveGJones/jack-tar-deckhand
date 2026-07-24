"""Tests for the annotation-overlay module (feature #142).

Covers: anchor payload validation, deterministic auto-placement,
collision resolution, band selection, end-to-end drawing, explicit
label_pos override, and missing-file handling. All images are
synthesized in tmp_path — none are committed to the repo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.annotate_figure import (  # noqa: E402
    BLANK_ZONE_RECTS,
    DEFAULT_MARGIN_BAND,
    LABEL_BOX_PADDING,
    LEADER_LINE_WIDTH,
    annotate,
    parse_blank_zone_verdict,
    place_labels,
    place_labels_in_zone,
    validate_anchors,
    _load_font,
    _segment_box_entry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_image(tmp_path, size=(800, 600), color=(30, 30, 30)):
    """Create a synthetic solid-colour PIL image on disk and return its path."""
    img = Image.new('RGB', size, color)
    path = tmp_path / 'source.png'
    img.save(path)
    return str(path)


def _box_for(label_pos_norm, image_size, text, font_size=26, padding=LABEL_BOX_PADDING):
    """Independently recompute a label's box rect the same way annotate() does.

    Used by tests to assert non-overlap without reaching into annotate()'s
    internals — this mirrors the textbbox-based sizing logic in the module.
    """
    width, height = image_size
    draw = ImageDraw.Draw(Image.new('RGB', image_size))
    font = _load_font(font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    lx = label_pos_norm[0] * width
    ly = label_pos_norm[1] * height
    return (
        lx - text_w / 2 - padding,
        ly - text_h / 2 - padding,
        lx + text_w / 2 + padding,
        ly + text_h / 2 + padding,
    )


def _boxes_intersect(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def _segment_intersects_rect(p0, p1, rect):
    """Liang-Barsky clip: does the segment p0->p1 pass through the rect?"""
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    t_min, t_max = 0.0, 1.0
    for p, q in ((-dx, x0 - rect[0]), (dx, rect[2] - x0),
                 (-dy, y0 - rect[1]), (dy, rect[3] - y0)):
        if p == 0:
            if q < 0:
                return False  # parallel and outside this boundary
        else:
            r = q / p
            if p < 0:
                t_min = max(t_min, r)
            else:
                t_max = min(t_max, r)
    return t_min <= t_max


def _leader_segments_and_boxes(anchors, image_size):
    """Mirror annotate()'s geometry: placements, box rects, leader segments."""
    placements = place_labels(anchors, image_size)
    width, height = image_size
    boxes = {}
    leaders = {}
    for name, spec in placements.items():
        anchor_px = (spec['anchor'][0] * width, spec['anchor'][1] * height)
        label_px = (spec['label_pos'][0] * width, spec['label_pos'][1] * height)
        box = _box_for(spec['label_pos'], image_size, name)
        boxes[name] = box
        leaders[name] = (anchor_px, _segment_box_entry(anchor_px, label_px, box))
    return leaders, boxes


def _assert_no_leader_crosses_other_box(anchors, image_size):
    leaders, boxes = _leader_segments_and_boxes(anchors, image_size)
    for leader_name, (p0, p1) in leaders.items():
        for box_name, rect in boxes.items():
            if box_name == leader_name:
                continue
            assert not _segment_intersects_rect(p0, p1, rect), (
                f"Leader for '{leader_name}' passes through '{box_name}' label box"
            )


# ---------------------------------------------------------------------------
# validate_anchors — valid payloads
# ---------------------------------------------------------------------------

def test_validate_anchors_valid_payload_passes():
    payload = {"anchors": {"Bow": [0.1, 0.2], "Stern": [0.9, 0.8]}}
    result = validate_anchors(payload)
    assert result == payload


def test_validate_anchors_valid_payload_with_extra_keys_passthrough():
    payload = {"anchors": {"Bow": [0.1, 0.2]}, "model": "vision-check"}
    result = validate_anchors(payload)
    assert result["model"] == "vision-check"


def test_validate_anchors_accepts_integer_coordinates():
    # 0 and 1 are valid boundary values, and int is a valid numeric type.
    payload = {"anchors": {"Corner": [0, 1]}}
    result = validate_anchors(payload)
    assert result["anchors"]["Corner"] == [0, 1]


# ---------------------------------------------------------------------------
# validate_anchors — invalid payloads
# ---------------------------------------------------------------------------

def test_validate_anchors_rejects_non_dict_payload():
    with pytest.raises(ValueError, match='must be a dict'):
        validate_anchors(['not', 'a', 'dict'])


def test_validate_anchors_rejects_missing_anchors_key():
    with pytest.raises(ValueError, match="missing required 'anchors' key"):
        validate_anchors({"other": {}})


def test_validate_anchors_rejects_non_dict_anchors_value():
    with pytest.raises(ValueError, match="'anchors' must be a dict"):
        validate_anchors({"anchors": [["Bow", 0.1, 0.2]]})


def test_validate_anchors_rejects_empty_anchors_dict():
    with pytest.raises(ValueError, match="'anchors' dict is empty"):
        validate_anchors({"anchors": {}})


def test_validate_anchors_rejects_empty_label_name():
    with pytest.raises(ValueError, match='non-empty string'):
        validate_anchors({"anchors": {"": [0.1, 0.2]}})


def test_validate_anchors_rejects_whitespace_only_label_name():
    with pytest.raises(ValueError, match='non-empty string'):
        validate_anchors({"anchors": {"   ": [0.1, 0.2]}})


def test_validate_anchors_rejects_duplicate_label_after_normalization():
    # Distinct dict keys that normalize (strip) to the same label name.
    payload = {"anchors": {"Bow": [0.1, 0.2], " Bow ": [0.3, 0.4]}}
    with pytest.raises(ValueError, match='Duplicate anchor label'):
        validate_anchors(payload)


def test_validate_anchors_rejects_coordinate_not_two_elements():
    with pytest.raises(ValueError, match='2-element'):
        validate_anchors({"anchors": {"Bow": [0.1, 0.2, 0.3]}})


def test_validate_anchors_rejects_non_numeric_coordinate():
    with pytest.raises(ValueError, match='must be a number'):
        validate_anchors({"anchors": {"Bow": ["x", 0.2]}})


def test_validate_anchors_rejects_boolean_coordinate():
    # bool is a numbers.Number subclass in Python; explicitly rejected.
    with pytest.raises(ValueError, match='must be a number'):
        validate_anchors({"anchors": {"Bow": [True, 0.2]}})


def test_validate_anchors_rejects_out_of_range_low():
    with pytest.raises(ValueError, match='normalized in \\[0, 1\\]'):
        validate_anchors({"anchors": {"Bow": [-0.1, 0.2]}})


def test_validate_anchors_rejects_out_of_range_high():
    with pytest.raises(ValueError, match='normalized in \\[0, 1\\]'):
        validate_anchors({"anchors": {"Bow": [0.1, 1.5]}})


def test_validate_anchors_error_message_names_the_offending_label():
    with pytest.raises(ValueError, match="'Mast'"):
        validate_anchors({"anchors": {"Mast": [2.0, 0.2]}})


# ---------------------------------------------------------------------------
# place_labels — determinism
# ---------------------------------------------------------------------------

def test_place_labels_deterministic_same_input_same_output():
    anchors = {"Bow": [0.05, 0.5], "Stern": [0.95, 0.5], "Mast": [0.5, 0.05]}
    result1 = place_labels(anchors, (800, 600))
    result2 = place_labels(anchors, (800, 600))
    assert result1 == result2


def test_place_labels_deterministic_across_dict_ordering():
    # Same anchors, different insertion order -> same placement result.
    anchors_a = {"Bow": [0.05, 0.5], "Stern": [0.95, 0.5]}
    anchors_b = {"Stern": [0.95, 0.5], "Bow": [0.05, 0.5]}
    assert place_labels(anchors_a, (800, 600)) == place_labels(anchors_b, (800, 600))


def test_place_labels_rejects_non_positive_image_size():
    with pytest.raises(ValueError):
        place_labels({"Bow": [0.1, 0.1]}, (0, 600))


# ---------------------------------------------------------------------------
# place_labels — band selection
# ---------------------------------------------------------------------------

def test_place_labels_anchor_near_top_edge_goes_to_top_band():
    anchors = {"Mast": [0.5, 0.02]}
    result = place_labels(anchors, (800, 600))
    label_pos = result["Mast"]["label_pos"]
    # Top band: label pushed to the vertical midpoint of the top margin strip.
    assert label_pos[1] == pytest.approx(DEFAULT_MARGIN_BAND / 2)
    assert label_pos[0] == pytest.approx(0.5)


def test_place_labels_anchor_near_bottom_edge_goes_to_bottom_band():
    anchors = {"Keel": [0.5, 0.98]}
    result = place_labels(anchors, (800, 600))
    label_pos = result["Keel"]["label_pos"]
    assert label_pos[1] == pytest.approx(1.0 - DEFAULT_MARGIN_BAND / 2)


def test_place_labels_anchor_near_left_edge_goes_to_left_band():
    anchors = {"Bow": [0.02, 0.5]}
    result = place_labels(anchors, (800, 600))
    label_pos = result["Bow"]["label_pos"]
    assert label_pos[0] == pytest.approx(DEFAULT_MARGIN_BAND / 2)


def test_place_labels_anchor_near_right_edge_goes_to_right_band():
    anchors = {"Stern": [0.98, 0.5]}
    result = place_labels(anchors, (800, 600))
    label_pos = result["Stern"]["label_pos"]
    assert label_pos[0] == pytest.approx(1.0 - DEFAULT_MARGIN_BAND / 2)


def test_place_labels_anchor_at_dead_centre_picks_a_single_band():
    # Equidistant from all four edges — nearest_band must resolve to exactly
    # one band deterministically (min() with a dict picks the first tie).
    anchors = {"Middle": [0.5, 0.5]}
    result = place_labels(anchors, (800, 600))
    assert "label_pos" in result["Middle"]


# ---------------------------------------------------------------------------
# place_labels — collision handling
# ---------------------------------------------------------------------------

def test_place_labels_close_anchors_get_non_overlapping_boxes():
    # Two anchors close together on the left edge -> same band -> must stack.
    anchors = {"Bow": [0.02, 0.40], "BowLine": [0.02, 0.42]}
    image_size = (800, 600)
    result = place_labels(anchors, image_size)

    box_bow = _box_for(result["Bow"]["label_pos"], image_size, "Bow")
    box_bowline = _box_for(result["BowLine"]["label_pos"], image_size, "BowLine")

    assert not _boxes_intersect(box_bow, box_bowline)
    # And they must actually be different positions (proof stacking happened).
    assert result["Bow"]["label_pos"] != result["BowLine"]["label_pos"]


def test_place_labels_three_close_anchors_all_pairwise_non_overlapping():
    anchors = {
        "Mast1": [0.30, 0.02],
        "Mast2": [0.50, 0.02],
        "Mast3": [0.70, 0.02],
    }
    image_size = (1000, 700)
    result = place_labels(anchors, image_size)

    boxes = {
        name: _box_for(result[name]["label_pos"], image_size, name)
        for name in anchors
    }
    names = list(boxes)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            assert not _boxes_intersect(boxes[names[i]], boxes[names[j]]), (
                f'{names[i]} and {names[j]} label boxes overlap'
            )


# ---------------------------------------------------------------------------
# place_labels — perpendicular stagger + leader/box geometry
# ---------------------------------------------------------------------------

def test_place_labels_stacked_labels_stagger_along_perpendicular_axis():
    # Three labels in the top band: stacked along x AND staggered along y
    # (alternating offsets) so their y positions are not all identical.
    anchors = {
        "Mast1": [0.30, 0.02],
        "Mast2": [0.50, 0.02],
        "Mast3": [0.70, 0.02],
    }
    result = place_labels(anchors, (1000, 700))
    ys = {result[name]["label_pos"][1] for name in anchors}
    assert len(ys) >= 2, 'Stacked labels must alternate perpendicular offsets'
    # All staggered positions must remain inside the top band strip.
    assert all(0.0 <= y <= DEFAULT_MARGIN_BAND for y in ys)


def test_segment_box_entry_terminates_on_box_edge():
    # Horizontal approach from the left: entry is on the box's left edge.
    entry = _segment_box_entry((0, 50), (50, 50), (40, 40, 60, 60))
    assert entry == (40, 50)


def test_segment_box_entry_anchor_inside_box_is_zero_length():
    # Anchor already inside the box -> leader collapses to the anchor.
    entry = _segment_box_entry((45, 50), (50, 50), (40, 40, 60, 60))
    assert entry == (45, 50)


def test_no_leader_intersects_other_label_box_top_band():
    # Clustered anchors near the top edge fan out to spread slots — no
    # leader may pass through a sibling label's box.
    anchors = {
        "Foremast": [0.45, 0.03],
        "Mainmast": [0.50, 0.03],
        "Mizzenmast": [0.55, 0.03],
    }
    _assert_no_leader_crosses_other_box(anchors, (1000, 700))


def test_no_leader_intersects_other_label_box_left_band():
    anchors = {
        "Bow": [0.02, 0.40],
        "BowLine": [0.02, 0.42],
        "Keel": [0.02, 0.44],
    }
    _assert_no_leader_crosses_other_box(anchors, (800, 600))


def test_default_leader_line_width_is_3():
    assert LEADER_LINE_WIDTH == 3


# ---------------------------------------------------------------------------
# annotate — end to end
# ---------------------------------------------------------------------------

def test_annotate_end_to_end_creates_output_file(tmp_path):
    src = _make_image(tmp_path)
    out = tmp_path / 'annotated.png'

    result_path = annotate(src, {"Bow": [0.1, 0.5]}, str(out))

    assert result_path == str(out)
    assert out.exists()


def test_annotate_output_differs_from_input(tmp_path):
    src = _make_image(tmp_path, color=(30, 30, 30))
    out = tmp_path / 'annotated.png'
    annotate(src, {"Bow": [0.1, 0.5]}, str(out))

    with Image.open(src) as src_img, Image.open(out) as out_img:
        assert src_img.tobytes() != out_img.convert('RGB').tobytes()


def test_annotate_label_box_location_is_white_ish(tmp_path):
    src = _make_image(tmp_path, size=(800, 600), color=(30, 30, 30))
    out = tmp_path / 'annotated.png'

    # Explicit override so the label box position is exactly known.
    labels = {"Bow": {"anchor": [0.1, 0.5], "label_pos": [0.5, 0.5]}}
    annotate(src, labels, str(out))

    with Image.open(out) as img:
        img = img.convert('RGB')
        width, height = img.size
        # Sample near the top-left corner of the label box (inside the
        # padding, away from the glyph strokes and the border line).
        box = _box_for([0.5, 0.5], (width, height), 'Bow')
        sample_x = int(box[0] + 3)
        sample_y = int(box[1] + 3)
        pixel = img.getpixel((sample_x, sample_y))

    assert all(channel > 230 for channel in pixel), f'Expected white-ish pixel, got {pixel}'


def test_annotate_explicit_label_pos_override_respected(tmp_path):
    src = _make_image(tmp_path, size=(800, 600), color=(30, 30, 30))
    out = tmp_path / 'annotated.png'

    # An explicit label_pos far from where auto-placement (nearest margin
    # band) would ever put it -- if the override is honoured, the box shows
    # up dead centre; if auto-placement ran instead, it would be pushed to
    # a margin band near the anchor at (0.1, 0.5), i.e. the left edge.
    explicit_pos = [0.5, 0.5]
    labels = {"Bow": {"anchor": [0.1, 0.5], "label_pos": explicit_pos}}
    annotate(src, labels, str(out))

    with Image.open(out) as img:
        img = img.convert('RGB')
        width, height = img.size
        box = _box_for(explicit_pos, (width, height), 'Bow')
        centre_pixel = img.getpixel((int((box[0] + box[2]) / 2), int(box[1] + 3)))
        # Left-margin-band placement would leave the image centre untouched
        # (still the solid source colour); the override must have painted
        # a white-ish box there instead.
        assert all(channel > 230 for channel in centre_pixel)


def test_annotate_mixed_auto_and_explicit_labels(tmp_path):
    src = _make_image(tmp_path)
    out = tmp_path / 'annotated.png'

    labels = {
        "Bow": [0.05, 0.5],  # auto placement
        "Stern": {"anchor": [0.95, 0.5], "label_pos": [0.5, 0.5]},  # explicit
    }
    result_path = annotate(src, labels, str(out))
    assert Path(result_path).exists()


def test_annotate_raises_on_missing_image(tmp_path):
    missing = tmp_path / 'does-not-exist.png'
    out = tmp_path / 'annotated.png'
    with pytest.raises(FileNotFoundError, match='Image not found'):
        annotate(str(missing), {"Bow": [0.1, 0.5]}, str(out))


def test_annotate_raises_on_empty_labels(tmp_path):
    src = _make_image(tmp_path)
    out = tmp_path / 'annotated.png'
    with pytest.raises(ValueError, match='non-empty dict'):
        annotate(src, {}, str(out))


def test_annotate_raises_on_malformed_label_spec(tmp_path):
    src = _make_image(tmp_path)
    out = tmp_path / 'annotated.png'
    with pytest.raises(ValueError, match='auto placement.*explicit override'):
        annotate(src, {"Bow": "not a valid spec"}, str(out))


def test_annotate_raises_on_incomplete_explicit_spec(tmp_path):
    src = _make_image(tmp_path)
    out = tmp_path / 'annotated.png'
    with pytest.raises(ValueError, match="'anchor' and 'label_pos'"):
        annotate(src, {"Bow": {"anchor": [0.1, 0.5]}}, str(out))


def test_annotate_boxes_drawn_over_leader_lines(tmp_path):
    # X's leader runs horizontally across the image centre and passes
    # beneath Y's box. Because all leaders are drawn before any boxes,
    # Y's box must paint OVER the leader — the sampled pixel inside Y's
    # box padding (on the leader's path) must be white, not line-dark.
    src = _make_image(tmp_path, size=(800, 600), color=(30, 30, 30))
    out = tmp_path / 'annotated.png'
    labels = {
        "X": {"anchor": [0.05, 0.5], "label_pos": [0.9, 0.5]},
        "Y": {"anchor": [0.5, 0.1], "label_pos": [0.5, 0.5]},
    }
    annotate(src, labels, str(out))

    with Image.open(out) as img:
        img = img.convert('RGB')
        width, height = img.size
        y_box = _box_for([0.5, 0.5], (width, height), 'Y')
        # Sample in Y's left padding strip at the leader's row (y = centre).
        sample = img.getpixel((int(y_box[0]) + 4, height // 2))

    assert all(channel > 230 for channel in sample), (
        f'Expected white-ish pixel (box over leader), got {sample}'
    )


def test_annotate_leader_stops_at_own_box_edge(tmp_path):
    # A horizontal leader approaching its own box from the left must stop
    # at the box's left edge: pixels INSIDE the box on the approach row
    # (past the border, before the glyph) stay white; a pixel just OUTSIDE
    # the box on the same row is line-dark.
    src = _make_image(tmp_path, size=(800, 600), color=(200, 200, 200))
    out = tmp_path / 'annotated.png'
    labels = {"Bow": {"anchor": [0.1, 0.5], "label_pos": [0.6, 0.5]}}
    annotate(src, labels, str(out))

    with Image.open(out) as img:
        img = img.convert('RGB')
        width, height = img.size
        box = _box_for([0.6, 0.5], (width, height), 'Bow')
        row = height // 2
        inside = img.getpixel((int(box[0]) + 4, row))
        outside = img.getpixel((int(box[0]) - 6, row))

    assert all(channel > 230 for channel in inside), (
        f'Leader drawn into box interior: {inside}'
    )
    assert all(channel < 100 for channel in outside), (
        f'Expected leader line just outside the box, got {outside}'
    )


def test_annotate_leader_casing_visible_on_black_background(tmp_path):
    # On a solid-black image, the dark leader core must be flanked by
    # white casing rows so the line reads against the dark region.
    src = _make_image(tmp_path, size=(800, 600), color=(0, 0, 0))
    out = tmp_path / 'annotated.png'
    labels = {"Bow": {"anchor": [0.1, 0.5], "label_pos": [0.7, 0.5]}}
    annotate(src, labels, str(out))

    with Image.open(out) as img:
        img = img.convert('RGB')
        # Horizontal leader along y=300 (rows 299-302 core, 297-304 casing).
        mid_x = 300  # well inside the leader's run, away from dot and box
        core = img.getpixel((mid_x, 300))
        casing_above = img.getpixel((mid_x, 298))
        casing_below = img.getpixel((mid_x, 303))
        background = img.getpixel((mid_x, 290))

    assert all(c < 100 for c in core), f'Expected dark leader core, got {core}'
    assert all(c > 230 for c in casing_above), (
        f'Expected white casing above the leader, got {casing_above}'
    )
    assert all(c > 230 for c in casing_below), (
        f'Expected white casing below the leader, got {casing_below}'
    )
    assert all(c < 50 for c in background), (
        f'Casing must not flood beyond its width, got {background}'
    )


def test_annotate_terminus_dot_has_casing_ring_on_black(tmp_path):
    # The terminus dot must sit inside a white ring so it reads on dark
    # regions: dark at the dot centre, white in the ring annulus, black
    # background beyond the ring.
    src = _make_image(tmp_path, size=(800, 600), color=(0, 0, 0))
    out = tmp_path / 'annotated.png'
    labels = {"Bow": {"anchor": [0.1, 0.5], "label_pos": [0.7, 0.5]}}
    annotate(src, labels, str(out))

    with Image.open(out) as img:
        img = img.convert('RGB')
        # Anchor at (80, 300): dot r=4 dark, ring r=7 white.
        dot_centre = img.getpixel((80, 300))
        ring = img.getpixel((80, 294))        # distance 6: in ring, above line casing
        beyond = img.getpixel((80, 290))      # distance 10: untouched background

    assert all(c < 100 for c in dot_centre), f'Expected dark dot, got {dot_centre}'
    assert all(c > 230 for c in ring), f'Expected white casing ring, got {ring}'
    assert all(c < 50 for c in beyond), f'Expected untouched background, got {beyond}'


def test_annotate_casing_can_be_disabled(tmp_path):
    src = _make_image(tmp_path, size=(800, 600), color=(0, 0, 0))
    out = tmp_path / 'annotated.png'
    labels = {"Bow": {"anchor": [0.1, 0.5], "label_pos": [0.7, 0.5]}}
    annotate(src, labels, str(out), casing_width=0)

    with Image.open(out) as img:
        img = img.convert('RGB')
        core = img.getpixel((300, 300))
        would_be_casing = img.getpixel((300, 298))

    assert all(c < 100 for c in core), f'Expected dark leader core, got {core}'
    assert all(c < 50 for c in would_be_casing), (
        f'Casing disabled — expected black background, got {would_be_casing}'
    )


def test_annotate_custom_casing_color_respected(tmp_path):
    src = _make_image(tmp_path, size=(800, 600), color=(0, 0, 0))
    out = tmp_path / 'annotated.png'
    labels = {"Bow": {"anchor": [0.1, 0.5], "label_pos": [0.7, 0.5]}}
    annotate(src, labels, str(out), casing_color=(255, 255, 0))

    with Image.open(out) as img:
        img = img.convert('RGB')
        casing = img.getpixel((300, 298))

    assert casing[0] > 230 and casing[1] > 230 and casing[2] < 50, (
        f'Expected yellow casing, got {casing}'
    )


def test_annotate_creates_output_directory_if_missing(tmp_path):
    src = _make_image(tmp_path)
    out = tmp_path / 'nested' / 'dir' / 'annotated.png'
    annotate(src, {"Bow": [0.1, 0.5]}, str(out))
    assert out.exists()


# ---------------------------------------------------------------------------
# place_labels regression pin (issue #142 blank-zone variant, §10.1)
# ---------------------------------------------------------------------------

def test_place_labels_unchanged():
    """Regression pin: place_labels_in_zone is a NEW sibling function,
    v1's place_labels is untouched — fixed fixture, fixed expected output."""
    anchors = {"Bow": [0.05, 0.5], "Stern": [0.95, 0.5], "Mast": [0.5, 0.05]}
    result = place_labels(anchors, (800, 600))
    assert result == {
        "Bow": {"anchor": [0.05, 0.5], "label_pos": [0.06, 0.5]},
        "Stern": {"anchor": [0.95, 0.5], "label_pos": [0.94, 0.5]},
        "Mast": {"anchor": [0.5, 0.05], "label_pos": [0.5, 0.06]},
    }


# ---------------------------------------------------------------------------
# place_labels_in_zone — blank-zone variant (issue #142, final scope item)
# ---------------------------------------------------------------------------

_FULL_SLIDE_WIDTH_IN = 12.0
_IMAGE_ZONE_WIDTH_IN = 4.8


def test_place_labels_in_zone_side_zone_stacks_vertically_sorted_by_anchor_y():
    anchors = {"C": [0.9, 0.8], "A": [0.9, 0.1], "B": [0.9, 0.5]}
    result = place_labels_in_zone(
        anchors, (800, 600), "right_third",
        font_size_pt=18, displayed_width_in=_FULL_SLIDE_WIDTH_IN,
    )
    assert result is not None
    zone_x, _zone_y, zone_w, _zone_h = BLANK_ZONE_RECTS["right_third"]
    cx = zone_x + zone_w / 2.0
    xs = {name: spec["label_pos"][0] for name, spec in result.items()}
    assert all(x == pytest.approx(cx) for x in xs.values())
    ys = {name: spec["label_pos"][1] for name, spec in result.items()}
    assert ys["A"] < ys["B"] < ys["C"]


def test_place_labels_in_zone_strip_spreads_horizontally_sorted_by_anchor_x():
    anchors = {"C": [0.8, 0.1], "A": [0.1, 0.1], "B": [0.5, 0.1]}
    result = place_labels_in_zone(
        anchors, (800, 600), "top_strip",
        font_size_pt=18, displayed_width_in=_FULL_SLIDE_WIDTH_IN,
    )
    assert result is not None
    _zone_x, zone_y, _zone_w, zone_h = BLANK_ZONE_RECTS["top_strip"]
    cy = zone_y + zone_h / 2.0
    ys = {name: spec["label_pos"][1] for name, spec in result.items()}
    assert all(y == pytest.approx(cy) for y in ys.values())
    xs = {name: spec["label_pos"][0] for name, spec in result.items()}
    assert xs["A"] < xs["B"] < xs["C"]


def test_place_labels_in_zone_positions_inside_zone_rect():
    anchors = {"A": [0.5, 0.5], "B": [0.4, 0.6]}
    pad = 0.03
    for zone in BLANK_ZONE_RECTS:
        result = place_labels_in_zone(
            anchors, (800, 600), zone,
            font_size_pt=18, displayed_width_in=_FULL_SLIDE_WIDTH_IN, pad=pad,
        )
        assert result is not None, zone
        zone_x, zone_y, zone_w, zone_h = BLANK_ZONE_RECTS[zone]
        for name, spec in result.items():
            x, y = spec["label_pos"]
            assert zone_x - pad <= x <= zone_x + zone_w + pad, (zone, name, x)
            assert zone_y - pad <= y <= zone_y + zone_h + pad, (zone, name, y)


def test_place_labels_in_zone_is_deterministic():
    anchors_a = {"Bow": [0.9, 0.2], "Stern": [0.9, 0.8]}
    anchors_b = {"Stern": [0.9, 0.8], "Bow": [0.9, 0.2]}
    kwargs = dict(font_size_pt=18, displayed_width_in=_FULL_SLIDE_WIDTH_IN)
    r1 = place_labels_in_zone(anchors_a, (800, 600), "right_third", **kwargs)
    r2 = place_labels_in_zone(anchors_a, (800, 600), "right_third", **kwargs)
    r3 = place_labels_in_zone(anchors_b, (800, 600), "right_third", **kwargs)
    assert r1 == r2 == r3


def test_place_labels_in_zone_returns_none_over_capacity():
    # slot_pitch = 60/200 = 0.3, usable_h = 1.0 - 2*0.03 = 0.94 ->
    # count_capacity = 3; 5 labels overflows.
    anchors = {f"L{i}": [0.9, i / 5.0] for i in range(5)}
    result = place_labels_in_zone(
        anchors, (800, 200), "right_third",
        font_size_pt=18, displayed_width_in=_FULL_SLIDE_WIDTH_IN,
    )
    assert result is None


def test_place_labels_in_zone_returns_none_when_widest_label_exceeds_side_zone_width():
    # "Orchestration Bus" at 18pt against the (stricter) image-zone
    # displayed width (BZ-2's own illustrative example) spills past the
    # 0.33-wide side zone -> capacity gate rejects rather than a silent
    # spill.
    anchors = {"Orchestration Bus": [0.9, 0.5]}
    result = place_labels_in_zone(
        anchors, (1024, 576), "right_third",
        font_size_pt=18, displayed_width_in=_IMAGE_ZONE_WIDTH_IN,
    )
    assert result is None


def test_place_labels_in_zone_capacity_scales_with_displayed_width():
    """BZ-6: same labels, smaller displayed_width_in -> lower capacity;
    the image-zone constant is stricter than the full-slide constant."""
    anchors = {
        "Alpha": [0.1, 0.1], "Beta": [0.3, 0.1], "Gamma": [0.5, 0.1],
        "Delta": [0.7, 0.1], "Epsilon": [0.9, 0.1],
    }
    wide = place_labels_in_zone(
        anchors, (1024, 576), "top_strip",
        font_size_pt=18, displayed_width_in=_FULL_SLIDE_WIDTH_IN,
    )
    narrow = place_labels_in_zone(
        anchors, (1024, 576), "top_strip",
        font_size_pt=18, displayed_width_in=_IMAGE_ZONE_WIDTH_IN,
    )
    assert wide is not None
    assert narrow is None


def test_place_labels_in_zone_far_anchor_keeps_anchor_verbatim():
    anchors = {"Far": [0.05, 0.9]}  # far side of the frame from right_third
    result = place_labels_in_zone(
        anchors, (800, 600), "right_third",
        font_size_pt=18, displayed_width_in=_FULL_SLIDE_WIDTH_IN,
    )
    assert result is not None
    assert result["Far"]["anchor"] == [0.05, 0.9]
    assert result["Far"]["label_pos"][0] != 0.05


def test_place_labels_in_zone_unknown_zone_raises():
    with pytest.raises(KeyError):
        place_labels_in_zone(
            {"A": [0.5, 0.5]}, (800, 600), "top_band",
            font_size_pt=18, displayed_width_in=_FULL_SLIDE_WIDTH_IN,
        )


# ---------------------------------------------------------------------------
# parse_blank_zone_verdict (§5.2)
# ---------------------------------------------------------------------------

def test_parse_blank_zone_verdict_true_false_absent_malformed():
    assert parse_blank_zone_verdict({"blank_zone": {"clear": True}}) is True
    assert parse_blank_zone_verdict({"blank_zone": {"clear": False}}) is False
    assert parse_blank_zone_verdict({"description": "x", "anchors": {}}) is None
    assert parse_blank_zone_verdict({"blank_zone": {"clear": "yes"}}) is None
    assert parse_blank_zone_verdict({"blank_zone": "not-a-dict"}) is None
    assert parse_blank_zone_verdict("not-a-dict") is None
    assert parse_blank_zone_verdict({"blank_zone": {}}) is None


# ---------------------------------------------------------------------------
# validate_anchors tolerance pin (BZ-7 — already holds, no relaxation)
# ---------------------------------------------------------------------------

def test_validate_anchors_tolerates_blank_zone_key():
    payload = {
        "description": "test",
        "anchors": {"Bow": [0.1, 0.5]},
        "blank_zone": {"clear": True, "notes": "sky is empty"},
    }
    result = validate_anchors(payload)
    assert result is payload
