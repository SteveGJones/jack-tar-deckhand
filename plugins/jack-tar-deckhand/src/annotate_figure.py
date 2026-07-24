"""Programmatic annotation overlay for diagram-class images (feature #142).

Draws leader lines, terminus dots, and typeset labels over an image whose
anchor coordinates were supplied by a vision pass (or by the caller
directly). Text is perfect by construction — labels come from a Python
string, never from a diffusion model — so this module only has to get the
POINTING right, not the spelling.

No model calls, no network access. Pure PIL imaging. This keeps the
overlay engine testable as a pure function of (image, anchors, labels).

See docs/feature-proposals/142-annotate-figure.md for the design.
"""

import os

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Drawing style constants
# ---------------------------------------------------------------------------

LEADER_LINE_WIDTH = 3
LEADER_LINE_COLOR = (20, 20, 20)
LEADER_CASING_EXTRA = 4   # casing line width = line_width + this
TERMINUS_DOT_RADIUS = 4
TERMINUS_DOT_COLOR = (20, 20, 20)
DOT_CASING_EXTRA = 3      # casing ring radius = dot_radius + this
LABEL_BOX_FILL = (255, 255, 255)
LABEL_BOX_BORDER = (20, 20, 20)
LABEL_BOX_BORDER_WIDTH = 2
LABEL_BOX_PADDING = 8
LABEL_TEXT_COLOR = (20, 20, 20)
DEFAULT_FONT_SIZE = 26

# Font fallback chain: Helvetica (macOS) -> DejaVu Sans (Linux/most systems) -> PIL default
_FONT_CANDIDATES = [
    '/System/Library/Fonts/Helvetica.ttc',
    '/System/Library/Fonts/Supplemental/Helvetica.ttc',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
]

DEFAULT_MARGIN_BAND = 0.12

_BANDS = ('top', 'bottom', 'left', 'right')

# ---------------------------------------------------------------------------
# Blank-zone variant (issue #142, final scope item)
# ---------------------------------------------------------------------------

#: Normalized (x, y, w, h) rects of the reserved region per zone name.
#: 0.33 / 0.25 are first-pass constants matching the vocabulary's literal
#: "third" / "strip" reading — the design doc's §8 dogfood is the
#: calibration mechanism for these fractions; treat them as tunable, not
#: as a load-bearing invariant of the vocabulary itself.
BLANK_ZONE_RECTS = {
    'left_third':   (0.0,  0.0,  0.33, 1.0),
    'right_third':  (0.67, 0.0,  0.33, 1.0),
    'top_strip':    (0.0,  0.0,  1.0,  0.25),
    'bottom_strip': (0.0,  0.75, 1.0,  0.25),
}

#: v1's estimated box pitch for vertically-stacked side-band labels
#: (place_labels' est_step), reused verbatim for the side-zone vertical
#: slot spacing and capacity count.
_ZONE_SLOT_PITCH_PX = 60.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_font(font_size):
    """Load a font via the fallback chain: Helvetica -> DejaVu -> PIL default.

    Returns a PIL ImageFont instance. Never raises — falls all the way
    back to ImageFont.load_default() if no TrueType font is found.
    """
    for candidate in _FONT_CANDIDATES:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, font_size)
            except Exception:
                continue
    try:
        # Pillow >= 9.2 supports a size arg on the default bitmap font
        return ImageFont.load_default(size=font_size)
    except TypeError:
        return ImageFont.load_default()


def _nearest_band(x, y):
    """Determine which margin band (top/bottom/left/right) an anchor is closest to.

    Distance to each of the four image edges is compared; the nearest edge
    wins. x, y are normalized 0-1 floats.
    """
    distances = {
        'top': y,
        'bottom': 1.0 - y,
        'left': x,
        'right': 1.0 - x,
    }
    return min(distances, key=distances.get)


def _segment_box_entry(p0, p1, box):
    """Point where the segment p0 -> p1 first enters an axis-aligned box.

    Used to terminate a leader line at the edge of its own label box
    nearest the anchor, instead of drawing into the box interior.
    Slab-method clip: p1 is expected to be inside the box (the label
    centre); if the segment never reaches the box (degenerate input),
    p1 is returned unchanged as a safe fallback.

    Args:
        p0: (x, y) segment start in pixels (the anchor).
        p1: (x, y) segment end in pixels (the label box centre).
        box: (left, top, right, bottom) rect in pixels.

    Returns:
        (x, y) tuple: the entry point on the box perimeter (or p0 if the
        anchor is already inside the box).
    """
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    t_min, t_max = 0.0, 1.0

    for delta, lo, hi, origin in ((dx, box[0], box[2], x0),
                                  (dy, box[1], box[3], y0)):
        if delta == 0:
            if origin < lo or origin > hi:
                return p1  # parallel and outside the slab — degenerate
        else:
            t_a = (lo - origin) / delta
            t_b = (hi - origin) / delta
            if t_a > t_b:
                t_a, t_b = t_b, t_a
            t_min = max(t_min, t_a)
            t_max = min(t_max, t_b)

    if t_min > t_max:
        return p1  # segment never enters the box — degenerate

    t = max(0.0, t_min)  # anchor inside box -> zero-length leader
    return (x0 + t * dx, y0 + t * dy)


def _draw_leader(draw, p0, p1, color, width):
    """Draw a leader line twice with a 1px offset to mitigate aliasing.

    Near-horizontal (and near-vertical) lines render visually fainter in
    PIL's non-anti-aliased line rasteriser; the second pass, offset 1px
    along the line's minor axis, thickens the perceived stroke evenly.
    """
    draw.line([p0, p1], fill=color, width=width)
    if abs(p1[0] - p0[0]) >= abs(p1[1] - p0[1]):
        off_x, off_y = 0, 1  # near-horizontal: offset vertically
    else:
        off_x, off_y = 1, 0  # near-vertical: offset horizontally
    draw.line(
        [(p0[0] + off_x, p0[1] + off_y), (p1[0] + off_x, p1[1] + off_y)],
        fill=color, width=width,
    )


def _band_target_point(band, x, y, margin_band):
    """Project an anchor's (x, y) onto its band's placement line.

    The label is pushed to the middle of the outer margin_band fraction on
    the chosen side, preserving the anchor's position along the
    perpendicular axis (e.g. for the top band, x is preserved and y is
    pushed to the vertical midpoint of the top margin strip).
    """
    half_band = margin_band / 2.0
    if band == 'top':
        return x, half_band
    if band == 'bottom':
        return x, 1.0 - half_band
    if band == 'left':
        return half_band, y
    # band == 'right'
    return 1.0 - half_band, y


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_anchors(payload):
    """Validate the vision pass's anchor JSON contract.

    Expected shape: {"anchors": {label_name: [x, y], ...}, ...extra keys
    are passed through untouched}. Coordinates must be normalized floats
    in [0, 1]. Labels must be non-empty, unique strings.

    Args:
        payload: dict from the vision pass (or hand-authored).

    Returns:
        dict: the validated payload (same object, not a copy).

    Raises:
        ValueError: with an actionable message identifying exactly what
            is wrong (missing key, wrong type, out-of-range coordinate,
            duplicate/empty label name).
    """
    if not isinstance(payload, dict):
        raise ValueError(
            f"Anchor payload must be a dict, got {type(payload).__name__}"
        )

    if 'anchors' not in payload:
        raise ValueError(
            "Anchor payload missing required 'anchors' key. "
            "Expected shape: {\"anchors\": {label: [x, y], ...}}"
        )

    anchors = payload['anchors']
    if not isinstance(anchors, dict):
        raise ValueError(
            f"'anchors' must be a dict of {{label: [x, y]}}, got {type(anchors).__name__}"
        )

    if not anchors:
        raise ValueError("'anchors' dict is empty — at least one anchor is required")

    seen_labels = set()
    for label, coord in anchors.items():
        if not isinstance(label, str) or not label.strip():
            raise ValueError(
                f"Anchor label must be a non-empty string, got {label!r}"
            )
        # Case-sensitive exact-match duplicate check: dict keys are already
        # unique by construction, but guard against caller-constructed
        # payloads built by hand (e.g. list-of-tuples coerced to dict) where
        # whitespace-only variants could otherwise slip through as distinct.
        normalized = label.strip()
        if normalized in seen_labels:
            raise ValueError(f"Duplicate anchor label: '{label}'")
        seen_labels.add(normalized)

        if not isinstance(coord, (list, tuple)) or len(coord) != 2:
            raise ValueError(
                f"Anchor '{label}' coordinate must be a 2-element [x, y] list, got {coord!r}"
            )

        x, y = coord
        for axis_name, axis_val in (('x', x), ('y', y)):
            if not isinstance(axis_val, (int, float)) or isinstance(axis_val, bool):
                raise ValueError(
                    f"Anchor '{label}' {axis_name} coordinate must be a number, got {axis_val!r}"
                )
            if not (0.0 <= axis_val <= 1.0):
                raise ValueError(
                    f"Anchor '{label}' {axis_name} coordinate must be normalized in [0, 1], "
                    f"got {axis_val}. Coordinates must be fractions of image width/height, "
                    f"not pixels."
                )

    return payload


def place_labels(anchors, image_size, *, margin_band=DEFAULT_MARGIN_BAND):
    """Automatically place labels in the nearest margin band, avoiding collisions.

    Each anchor is assigned to the margin band (top/bottom/left/right) it
    is nearest to, then pushed outward to that band at the anchor's
    projected position. Labels landing in the same band are stacked along
    the band (vertically for left/right bands, horizontally for top/bottom
    bands) to avoid overlapping label boxes, AND staggered along the
    perpendicular axis (alternating offsets within the band strip) so that
    leader lines from stacked labels do not overlap each other's boxes.
    Stacking order follows the anchors' positions along the band's run
    axis, tie-broken by label name — deterministic: the same input always
    produces the same output.

    Args:
        anchors: dict of {label: [x, y]} normalized coordinates (already
            validated by validate_anchors).
        image_size: (width, height) in pixels — used to convert the
            normalized stacking offsets into a genuinely non-overlapping
            spread regardless of aspect ratio.
        margin_band: fraction of image extent reserved as the outer margin
            strip on each side (default 0.12 — matches the proposal).

    Returns:
        dict: {label: {"anchor": [x, y], "label_pos": [x, y]}} — both
        normalized 0-1 floats, ready for annotate(). Deterministic: the
        same anchors + image_size always produce the same label_pos.
    """
    width, height = image_size
    if width <= 0 or height <= 0:
        raise ValueError(f"image_size must be positive, got {image_size}")

    # Assign each label to its nearest band.
    by_band = {band: [] for band in _BANDS}
    for label, (x, y) in anchors.items():
        band = _nearest_band(x, y)
        by_band[band].append(label)

    placements = {}
    for band, labels in by_band.items():
        # Deterministic stacking order: by anchor position along the band's
        # run axis (x for top/bottom, y for left/right), tie-broken by
        # label name. Spatial ordering keeps each leader short and stops
        # leaders crossing sibling slots; the name tie-break keeps the
        # result independent of dict insertion order.
        run_axis = 0 if band in ('top', 'bottom') else 1
        labels_sorted = sorted(labels, key=lambda lbl: (anchors[lbl][run_axis], lbl))
        n = len(labels_sorted)
        for i, label in enumerate(labels_sorted):
            x, y = anchors[label]
            target_x, target_y = _band_target_point(band, x, y, margin_band)

            # Stack labels sharing a band along the band's run direction so
            # their boxes don't collide, AND stagger them along the
            # perpendicular axis (alternating a near-edge offset with the
            # band's inner boundary) so leaders from stacked labels do not
            # overlap each other's boxes.
            #
            # Top/bottom bands spread across the central run span (boxes
            # are wide, so generous horizontal separation is needed);
            # left/right bands instead stack in a narrow window centred on
            # the anchors' centroid, spaced by an estimated box height —
            # this keeps each leader short so it cannot travel past a
            # sibling's (horizontally wide) box.
            if n > 1:
                if band in ('top', 'bottom'):
                    span_lo, span_hi = margin_band, 1.0 - margin_band
                    step = (span_hi - span_lo) / (n + 1)
                    slot = span_lo + step * (i + 1)
                else:
                    est_step = 60.0 / height  # est. box height + gap, normalized
                    centroid = sum(anchors[lbl][1] for lbl in labels_sorted) / n
                    half_window = (n - 1) / 2.0 * est_step
                    win_lo = margin_band + half_window
                    win_hi = 1.0 - margin_band - half_window
                    if win_lo <= win_hi:
                        centroid = min(max(centroid, win_lo), win_hi)
                        slot = centroid + (i - (n - 1) / 2.0) * est_step
                    else:
                        # Too many labels for a centred window — fall back
                        # to an even spread across the run span.
                        step = (1.0 - 2 * margin_band) / (n + 1)
                        slot = margin_band + step * (i + 1)

                # Perpendicular stagger: even slots near the edge, odd
                # slots at the band's inner boundary.
                perp = margin_band / 4.0 if i % 2 == 0 else margin_band
                if band == 'top':
                    target_x, target_y = slot, perp
                elif band == 'bottom':
                    target_x, target_y = slot, 1.0 - perp
                elif band == 'left':
                    target_x, target_y = perp, slot
                else:  # right
                    target_x, target_y = 1.0 - perp, slot

            placements[label] = {
                'anchor': [x, y],
                'label_pos': [target_x, target_y],
            }

    return placements


def place_labels_in_zone(anchors, image_size, zone, *,
                         font_size_pt, displayed_width_in, pad=0.03):
    """Stack ALL labels inside a reserved blank zone (§4.1, issue #142).

    Preference placement used only when the zone verifiably came back
    clear (§5) AND has capacity for the whole label set — this is
    all-or-nothing (§4.2): no per-label nearest-zone mixing. Returns the
    same {label: {"anchor": [...], "label_pos": [...]}} shape as
    place_labels, or None when the zone lacks capacity (caller falls
    back to place_labels for the whole set).

    font_size_pt / displayed_width_in (BZ-3, BZ-6): the capacity checks
    need real label-box extents via estimate_label_box at the RESOLVED
    style font size (operator-variable, e.g. style.font_size_pt: 14 —
    not derivable from anchors), converted to a normalized fraction of
    the image via the zone-dependent effective displayed width in
    inches. Both are required kwargs; the caller (build_annotation_payload
    for native, the annotate-figure flow for raster) always has them.
    A lazy import of annotation_payload.estimate_label_box is used here
    to avoid a module-load-time circular import (annotation_payload
    already imports place_labels / _segment_box_entry from this module
    at import time; by the time this function actually runs,
    annotation_payload is fully loaded regardless of which module
    called first).

    Side zones (left_third, right_third): labels stack VERTICALLY, x
    centred in the zone, sorted by anchor y (tie-break label name) so
    leaders fan out monotonically — crossings are MINIMISED, not
    eliminated (BZ-5): a far-side anchor whose y-order differs from its
    slot's neighbours can produce a crossing; this is an accepted trade
    of the all-labels-to-one-zone design. Slots spaced by the v1
    estimated box pitch (60px / image height, normalized), centred on
    the anchors' y-centroid, clamped to
    [zone_y + pad, zone_y + zone_h - pad].

    Top/bottom strips: labels spread HORIZONTALLY, y centred in the
    strip, sorted by anchor x (tie-break name), evenly slotted across
    [pad, 1 - pad] as v1's top/bottom spread does.

    All labels go to the zone, not just nearby ones [FIRM] — that is the
    point of a reserved region: guaranteed-empty space. A far-side
    anchor gets a long leader crossing the subject; leaders are drawn
    with a white casing halo and this is the standard cartographic
    trade.

    Capacity gates (§4.2) — ANY of these failing returns None:
      - Side zones: count `floor(usable_h / slot_pitch)` with
        `slot_pitch = 60px / image_height` normalized, `usable_h =
        zone_h - 2*pad`; AND width — the WIDEST label's normalized
        `estimate_label_box` width must fit `zone_w - 2*pad` (BZ-2),
        otherwise the box spills out of the reserved region.
      - Strips: `floor(usable_w / max_slot_w)` where `max_slot_w` is the
        widest label's normalized estimated width plus a fixed gap
        (`pad`, reused as the inter-box gap) — height fits by
        construction (one box row in a 0.25 strip).

    Args:
        anchors: dict of {label: [x, y]} normalized coordinates
            (already validated by validate_anchors).
        image_size: (width, height) in pixels.
        zone: one of BLANK_ZONE_RECTS's keys (never 'auto' here — the
            caller resolves 'auto' before calling).
        font_size_pt: the RESOLVED (merged) style font size in points.
        displayed_width_in: effective displayed width of the image, in
            inches, for the inches->normalized-fraction conversion
            (BZ-6 — a per-placement-zone conservative constant, NOT a
            flat 96-dpi assumption).
        pad: normalized padding from the zone's own edges (default
            0.03), also reused as the strip inter-box gap.

    Returns:
        dict, or None when any capacity gate fails.

    Raises:
        KeyError: zone is not one of BLANK_ZONE_RECTS's keys.
        ValueError: image_size is not positive.
    """
    from src.annotation_payload import estimate_label_box  # lazy: avoid circular import

    width, height = image_size
    if width <= 0 or height <= 0:
        raise ValueError(f"image_size must be positive, got {image_size}")

    zone_x, zone_y, zone_w, zone_h = BLANK_ZONE_RECTS[zone]

    labels_sorted_by_name = sorted(anchors)
    box_w_fracs = {}
    for label in labels_sorted_by_name:
        box_w_in, _box_h_in = estimate_label_box(label, font_size_pt)
        box_w_fracs[label] = box_w_in / displayed_width_in
    max_box_w_frac = max(box_w_fracs.values())

    n = len(anchors)
    placements = {}

    if zone in ('left_third', 'right_third'):
        slot_pitch = _ZONE_SLOT_PITCH_PX / height
        usable_h = zone_h - 2 * pad
        count_capacity = int(usable_h // slot_pitch) if slot_pitch > 0 else 0
        if n > count_capacity:
            return None
        if max_box_w_frac > zone_w - 2 * pad:
            return None

        cx = zone_x + zone_w / 2.0
        labels_sorted = sorted(anchors, key=lambda lbl: (anchors[lbl][1], lbl))
        centroid = sum(anchors[lbl][1] for lbl in labels_sorted) / n
        half_window = (n - 1) / 2.0 * slot_pitch
        win_lo = zone_y + pad + half_window
        win_hi = zone_y + zone_h - pad - half_window
        if win_lo <= win_hi:
            centred = min(max(centroid, win_lo), win_hi)
            for i, label in enumerate(labels_sorted):
                slot_y = centred + (i - (n - 1) / 2.0) * slot_pitch
                placements[label] = {
                    'anchor': list(anchors[label]),
                    'label_pos': [cx, slot_y],
                }
        else:
            # Defensive fallback (capacity gate above should prevent this):
            # even spread across the usable span.
            span_lo, span_hi = zone_y + pad, zone_y + zone_h - pad
            step = (span_hi - span_lo) / (n + 1)
            for i, label in enumerate(labels_sorted):
                slot_y = span_lo + step * (i + 1)
                placements[label] = {
                    'anchor': list(anchors[label]),
                    'label_pos': [cx, slot_y],
                }
        return placements

    if zone in ('top_strip', 'bottom_strip'):
        usable_w = zone_w - 2 * pad
        max_slot_w = max_box_w_frac + pad
        count_capacity = int(usable_w // max_slot_w) if max_slot_w > 0 else 0
        if n > count_capacity:
            return None

        cy = zone_y + zone_h / 2.0
        labels_sorted = sorted(anchors, key=lambda lbl: (anchors[lbl][0], lbl))
        span_lo, span_hi = zone_x + pad, zone_x + zone_w - pad
        step = (span_hi - span_lo) / (n + 1)
        for i, label in enumerate(labels_sorted):
            slot_x = span_lo + step * (i + 1)
            placements[label] = {
                'anchor': list(anchors[label]),
                'label_pos': [slot_x, cy],
            }
        return placements

    raise KeyError(
        f"Unknown blank zone {zone!r}; expected one of {sorted(BLANK_ZONE_RECTS)}"
    )


def parse_blank_zone_verdict(payload):
    """Tolerant parse of the anchor-pass's blank_zone verdict (§5.2).

    Args:
        payload: the parsed anchor-pass JSON dict.

    Returns:
        True, False, or None — None when the 'blank_zone' key is absent,
        the value is not a dict, or 'clear' is missing / non-boolean.
        NEVER raises. Absent/malformed is treated by the caller exactly
        like False: fall back to margin-band placement (the conservative
        default).
    """
    if not isinstance(payload, dict):
        return None
    blank_zone = payload.get('blank_zone')
    if not isinstance(blank_zone, dict):
        return None
    clear = blank_zone.get('clear')
    if isinstance(clear, bool):
        return clear
    return None


def annotate(image_path, labels, out_path, *, font_size=DEFAULT_FONT_SIZE,
             line_width=LEADER_LINE_WIDTH, line_color=LEADER_LINE_COLOR,
             dot_radius=TERMINUS_DOT_RADIUS, box_fill=LABEL_BOX_FILL,
             box_border=LABEL_BOX_BORDER, box_border_width=LABEL_BOX_BORDER_WIDTH,
             box_padding=LABEL_BOX_PADDING, text_color=LABEL_TEXT_COLOR,
             casing_color=None, casing_width=None):
    """Draw leader lines, terminus dots, and boxed labels onto an image.

    For each label, draws: a small filled dot at the anchor point, a
    straight leader line from the anchor towards the label position —
    terminating at the edge of its OWN label box nearest the anchor
    (never drawn into the box interior) — and a white box with a dark
    border containing the typeset label text centred at the label
    position. All leader lines are drawn BEFORE any label boxes/text, so
    boxes always sit on top of any leader that passes beneath them.

    Leaders and dots are drawn with cartographic CASING: a light underlay
    line (line_width + 4 wide) beneath each dark leader, and a light ring
    (dot_radius + 3) beneath each terminus dot, so lines and dots stay
    readable against dark image regions. All casing underlays are drawn
    before any dark cores, so one leader's casing never cuts another's
    core line.

    Args:
        image_path: Path to the source image (diagram, generated or
            external). Must exist.
        labels: dict, either
            {name: [x, y]} — auto placement (fed through place_labels()
                using the image's own dimensions), or
            {name: {"anchor": [x, y], "label_pos": [x, y]}} — explicit
                override, e.g. from a prior place_labels() call or a
                caller-specified position.
            Both forms use normalized 0-1 coordinates. Mixing forms
            within a single dict is allowed per-key.
        out_path: Where to save the annotated PNG.
        font_size: Point size for label text (default 26, per the PoC).
        line_width: Leader line stroke width in pixels (default 3).
        line_color: RGB tuple for the leader line and terminus dot.
        dot_radius: Terminus dot radius in pixels (default 4).
        box_fill: RGB tuple for the label box background (default white).
        box_border: RGB tuple for the label box border (default dark).
        box_border_width: Label box border stroke width in pixels.
        box_padding: Padding in pixels between label text and its box edge.
        text_color: RGB tuple for the label text.
        casing_color: RGB tuple for the leader/dot casing underlay.
            Default None -> uses box_fill (white), matching the label
            boxes so all overlay furniture reads as one system.
        casing_width: Casing line width in pixels. Default None ->
            line_width + 4. Pass 0 to disable casing entirely (dots then
            also lose their rings).

    Returns:
        str: out_path, the path to the annotated PNG.

    Raises:
        FileNotFoundError: If image_path does not exist.
        ValueError: If labels is empty or malformed.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f'Image not found: {image_path}')

    if not labels:
        raise ValueError("'labels' must be a non-empty dict")

    with Image.open(image_path) as src:
        img = src.convert('RGB')

    width, height = img.size

    # Split labels into those needing auto-placement vs. explicit override.
    explicit = {}
    auto_anchors = {}
    for name, spec in labels.items():
        if isinstance(spec, dict):
            if 'anchor' not in spec or 'label_pos' not in spec:
                raise ValueError(
                    f"Label '{name}' explicit spec must have both 'anchor' and "
                    f"'label_pos' keys, got {list(spec.keys())}"
                )
            explicit[name] = spec
        elif isinstance(spec, (list, tuple)) and len(spec) == 2:
            auto_anchors[name] = spec
        else:
            raise ValueError(
                f"Label '{name}' must be either [x, y] (auto placement) or "
                f"{{'anchor': [x, y], 'label_pos': [x, y]}} (explicit override), "
                f"got {spec!r}"
            )

    resolved = dict(explicit)
    if auto_anchors:
        resolved.update(place_labels(auto_anchors, (width, height)))

    font = _load_font(font_size)
    draw = ImageDraw.Draw(img)

    # Precompute all geometry first: box rects, text metrics, and the
    # leader's termination point on its own box edge nearest the anchor.
    geometry = []
    for name in sorted(resolved):
        spec = resolved[name]
        ax, ay = spec['anchor']
        lx, ly = spec['label_pos']

        anchor_px = (ax * width, ay * height)
        label_px = (lx * width, ly * height)

        text_bbox = draw.textbbox((0, 0), name, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]

        lx_px, ly_px = label_px
        box_rect = (
            lx_px - text_w / 2 - box_padding,
            ly_px - text_h / 2 - box_padding,
            lx_px + text_w / 2 + box_padding,
            ly_px + text_h / 2 + box_padding,
        )
        leader_end = _segment_box_entry(anchor_px, label_px, box_rect)
        geometry.append((name, anchor_px, label_px, box_rect, text_bbox, leader_end))

    resolved_casing_color = casing_color if casing_color is not None else box_fill
    resolved_casing_width = (casing_width if casing_width is not None
                             else line_width + LEADER_CASING_EXTRA)

    # Pass 1a: ALL casing underlays (light lines + dot rings) first, so
    # one leader's casing never cuts another leader's dark core.
    if resolved_casing_width > 0:
        ring_radius = dot_radius + DOT_CASING_EXTRA
        for name, anchor_px, label_px, box_rect, text_bbox, leader_end in geometry:
            _draw_leader(draw, anchor_px, leader_end,
                         resolved_casing_color, resolved_casing_width)

            ax_px, ay_px = anchor_px
            draw.ellipse(
                [ax_px - ring_radius, ay_px - ring_radius,
                 ax_px + ring_radius, ay_px + ring_radius],
                fill=resolved_casing_color,
            )

    # Pass 1b: ALL dark leader cores + terminus dots, over the casing
    # layer but still before every label box drawn in pass 2, so boxes
    # sit on top of any leader that passes beneath them.
    for name, anchor_px, label_px, box_rect, text_bbox, leader_end in geometry:
        _draw_leader(draw, anchor_px, leader_end, line_color, line_width)

        ax_px, ay_px = anchor_px
        draw.ellipse(
            [ax_px - dot_radius, ay_px - dot_radius,
             ax_px + dot_radius, ay_px + dot_radius],
            fill=TERMINUS_DOT_COLOR,
        )

    # Pass 2: ALL label boxes + text, painted over the leader layer.
    for name, anchor_px, label_px, box_rect, text_bbox, leader_end in geometry:
        draw.rectangle(
            list(box_rect),
            fill=box_fill,
            outline=box_border,
            width=box_border_width,
        )

        # Centre text within the box, accounting for textbbox's own offset.
        lx_px, ly_px = label_px
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        text_x = lx_px - text_w / 2 - text_bbox[0]
        text_y = ly_px - text_h / 2 - text_bbox[1]
        draw.text((text_x, text_y), name, font=font, fill=text_color)

    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    img.save(out_path, format='PNG')

    return out_path
