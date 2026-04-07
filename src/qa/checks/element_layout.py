"""AP-27 to AP-32: Element layout, vision confidence, alignment, reading order, text-fit, and element image completeness checks."""

_VISION_CONFIDENCE_THRESHOLD = 0.7
_MAX_ELEMENTS = 5
_ALIGNMENT_TOLERANCE = 0.06  # 6% of slide dimension
_CHARS_PER_INCH = 7  # conservative estimate at 18pt font


def check_element_layout(strategy_entry, outline_slide):
    """AP-27: Validate element layout for backdrop and pragmatic_composition slides.

    Args:
        strategy_entry: Dict from StrategyMap.slides with element_layout.
        outline_slide: Dict from SlideOutline.slides (for body_points reference).

    Returns:
        list of finding dicts.
    """
    findings = []
    slide_number = strategy_entry.get('slide_number', 0)
    layout = strategy_entry.get('element_layout')
    if not layout:
        return findings

    elements = layout.get('elements', [])
    body_points = outline_slide.get('body_points', [])

    # Check element count
    if len(elements) > _MAX_ELEMENTS:
        findings.append({
            'slide_number': slide_number,
            'severity': 'error',
            'category': 'element_layout',
            'description': f'Element count {len(elements)} exceeds maximum of {_MAX_ELEMENTS}',
            'suggested_fix': f'Reduce to {_MAX_ELEMENTS} or fewer elements, or use background strategy.',
            'affected_element': 'element_layout',
            'auto_fixable': False,
        })

    # Check each element
    for elem in elements:
        eid = elem.get('id', 'unknown')
        x, y, w, h = elem.get('x', 0), elem.get('y', 0), elem.get('w', 0), elem.get('h', 0)

        # Bounds check (x+w and y+h must be <= 1.0)
        if x + w > 1.0 or y + h > 1.0 or x < 0 or y < 0:
            findings.append({
                'slide_number': slide_number,
                'severity': 'error',
                'category': 'element_layout',
                'description': f'Element {eid} extends outside slide bounds (x={x}, y={y}, w={w}, h={h})',
                'suggested_fix': 'Adjust element coordinates to stay within 0.0-1.0 range.',
                'affected_element': eid,
                'auto_fixable': False,
            })

        # Check label_source reference
        label_source = elem.get('label_source', '')
        try:
            if 'body_points[' in label_source:
                idx = int(label_source.split('[')[1].rstrip(']'))
                if idx >= len(body_points):
                    findings.append({
                        'slide_number': slide_number,
                        'severity': 'warning',
                        'category': 'element_layout',
                        'description': f'Element {eid} label_source {label_source} references nonexistent body_point (only {len(body_points)} exist)',
                        'suggested_fix': 'Update label_source to reference an existing body_point index.',
                        'affected_element': eid,
                        'auto_fixable': False,
                    })
        except (ValueError, IndexError):
            pass

    return findings


def check_text_element_alignment(strategy_entry, image_entry):
    """AP-29: Verify text boxes are horizontally centered on detected visual elements.

    For backdrop and pragmatic_composition slides, the text labels should be
    aligned to the visual elements detected by the vision analyst. This check
    compares the horizontal center of each layout element with the horizontal
    center of its corresponding detected position.

    Args:
        strategy_entry: Dict from StrategyMap.slides with element_layout.
        image_entry: Dict from ImageManifest.images with detected_positions.

    Returns:
        list of finding dicts.
    """
    findings = []
    slide_number = strategy_entry.get('slide_number', 0)
    layout = strategy_entry.get('element_layout')
    if not layout:
        return findings

    detected = image_entry.get('detected_positions', [])
    if not detected:
        return findings

    elements = layout.get('elements', [])
    # Build lookup from element_id to detected position
    detected_by_id = {d['element_id']: d for d in detected}

    for elem in elements:
        eid = elem.get('id', 'unknown')
        det = detected_by_id.get(eid)
        if not det:
            continue

        # Compare horizontal centers
        layout_cx = elem.get('x', 0) + elem.get('w', 0) / 2
        detected_cx = det.get('x', 0) + det.get('w', 0) / 2
        h_offset = abs(layout_cx - detected_cx)

        if h_offset > _ALIGNMENT_TOLERANCE:
            findings.append({
                'slide_number': slide_number,
                'severity': 'warning',
                'category': 'text_element_alignment',
                'description': (
                    f'Element {eid} text center ({layout_cx:.2f}) is {h_offset:.2f} '
                    f'from detected visual center ({detected_cx:.2f}), '
                    f'exceeds {_ALIGNMENT_TOLERANCE} tolerance'
                ),
                'suggested_fix': (
                    f'Update element_layout x/w for {eid} so text is horizontally '
                    f'centered on the detected visual element.'
                ),
                'affected_element': eid,
                'auto_fixable': True,
            })

        # Check vertical consistency: text should be anchored consistently
        # (all at bottom of element, or all below element)
        layout_bottom = elem.get('y', 0) + elem.get('h', 0)
        detected_bottom = det.get('y', 0) + det.get('h', 0)
        # Text below detected element (gap > 0) vs overlapping (gap <= 0)
        vertical_gap = elem.get('y', 0) - detected_bottom
        elem['_vertical_gap'] = vertical_gap  # stash for cross-element check

    # Check vertical anchor consistency across all elements
    gaps = [e.get('_vertical_gap') for e in elements if '_vertical_gap' in e]
    if len(gaps) >= 2:
        all_below = all(g > 0 for g in gaps)
        all_overlapping = all(g <= 0 for g in gaps)
        if not all_below and not all_overlapping:
            findings.append({
                'slide_number': slide_number,
                'severity': 'warning',
                'category': 'text_element_alignment',
                'description': (
                    'Text vertical anchoring is inconsistent: some labels overlap '
                    'their visual elements while others sit below.'
                ),
                'suggested_fix': (
                    'Choose one vertical anchor strategy: all text labels either '
                    'bottom-aligned within element bounds, or top-aligned below elements.'
                ),
                'affected_element': 'all_elements',
                'auto_fixable': False,
            })

    # Clean up stashed values
    for elem in elements:
        elem.pop('_vertical_gap', None)

    return findings


def check_grid_reading_order(strategy_entry):
    """AP-30: Verify grid layouts use column-first reading order.

    For 2x2 grids, the natural presentation reading order is column-first
    (N-pattern): TL → BL → TR → BR. This check verifies that body_points
    mapped to spatial positions follow this pattern — sequential content
    should read down the left column first, then the right column.

    Args:
        strategy_entry: Dict from StrategyMap.slides with element_layout.

    Returns:
        list of finding dicts.
    """
    findings = []
    slide_number = strategy_entry.get('slide_number', 0)
    layout = strategy_entry.get('element_layout')
    if not layout:
        return findings

    template = layout.get('template', '')
    if template != 'grid_2x2':
        return findings

    elements = layout.get('elements', [])
    if len(elements) != 4:
        return findings

    # Extract body_point indices in spatial order
    indexed = []
    for elem in elements:
        label_source = elem.get('label_source', '')
        try:
            if 'body_points[' in label_source:
                idx = int(label_source.split('[')[1].rstrip(']'))
                cx = elem.get('x', 0) + elem.get('w', 0) / 2
                cy = elem.get('y', 0) + elem.get('h', 0) / 2
                indexed.append((idx, cx, cy))
        except (ValueError, IndexError):
            pass

    if len(indexed) != 4:
        return findings

    # Sort by column-first order: left column (small x) top-to-bottom,
    # then right column top-to-bottom
    mid_x = sum(i[1] for i in indexed) / len(indexed)
    left_col = sorted([i for i in indexed if i[1] < mid_x], key=lambda i: i[2])
    right_col = sorted([i for i in indexed if i[1] >= mid_x], key=lambda i: i[2])
    spatial_order = [i[0] for i in left_col + right_col]

    # Check if the body_point indices increase in column-first order
    expected = sorted(spatial_order)
    if spatial_order != expected:
        findings.append({
            'slide_number': slide_number,
            'severity': 'warning',
            'category': 'grid_reading_order',
            'description': (
                f'Grid reading order is row-first (Z-pattern). '
                f'Body points map spatially as {spatial_order} but '
                f'column-first (N-pattern) order would be {expected}. '
                f'Audiences read down the left column before moving right.'
            ),
            'suggested_fix': (
                'Remap body_points to column-first order: '
                'TL=body_points[0], BL=body_points[1], '
                'TR=body_points[2], BR=body_points[3].'
            ),
            'affected_element': 'element_layout',
            'auto_fixable': True,
        })

    return findings


def check_label_text_fit(strategy_entry, outline_slide, image_entry=None):
    """AP-31: Verify text labels fit within their element bounding boxes.

    For backdrop and pragmatic_composition slides, estimate whether each
    body_point text will fit within its allocated label area (derived from
    the detected or prescribed element dimensions). Flags when text would
    overflow, indicating the box is too narrow or too short.

    Args:
        strategy_entry: Dict from StrategyMap.slides with element_layout.
        outline_slide: Dict from SlideOutline.slides (for body_points).
        image_entry: Optional dict from ImageManifest.images with detected_positions.

    Returns:
        list of finding dicts.
    """
    findings = []
    slide_number = strategy_entry.get('slide_number', 0)
    layout = strategy_entry.get('element_layout')
    if not layout:
        return findings

    elements = layout.get('elements', [])
    body_points = outline_slide.get('body_points', [])

    # Use detected positions if available for width estimation
    detected = {}
    if image_entry:
        for d in image_entry.get('detected_positions', []):
            detected[d['element_id']] = d

    for elem in elements:
        eid = elem.get('id', 'unknown')
        label_source = elem.get('label_source', '')
        try:
            if 'body_points[' in label_source:
                idx = int(label_source.split('[')[1].rstrip(']'))
                if idx < len(body_points):
                    text = body_points[idx]
                else:
                    continue
            else:
                continue
        except (ValueError, IndexError):
            continue

        # Use detected width if available, otherwise prescribed
        det = detected.get(eid)
        elem_w = det['w'] if det else elem.get('w', 0)

        # Estimate: label width is max(element_width, min_width) in normalised coords
        # At 13.333" slide width, convert to inches
        label_w_inches = max(elem_w * 13.333, 3.5)
        chars_per_line = label_w_inches * _CHARS_PER_INCH
        estimated_lines = len(text) / chars_per_line if chars_per_line > 0 else 999

        if estimated_lines > 3:
            findings.append({
                'slide_number': slide_number,
                'severity': 'warning',
                'category': 'label_text_fit',
                'description': (
                    f'Element {eid} text ({len(text)} chars) would need '
                    f'~{estimated_lines:.1f} lines at {label_w_inches:.1f}" width. '
                    f'Text may overflow or be truncated.'
                ),
                'suggested_fix': (
                    f'Shorten the body_point text, widen the element layout, '
                    f'or use a smaller font size for this slide.'
                ),
                'affected_element': eid,
                'auto_fixable': False,
            })

    return findings


def check_element_image_completeness(strategy_entry, image_manifest):
    """AP-32: Verify pragmatic_composition slides have an image for every element_layout element.

    A pragmatic_composition slide that lacks element images silently degrades to
    a text-label-only layout — visually identical to a broken render. This check
    flags slides where the element_layout declares N elements but the image
    manifest contains fewer than N element images for that slide.

    Args:
        strategy_entry: Dict from StrategyMap.slides with element_layout.
        image_manifest: Dict matching ImageManifest schema (with 'images' list).

    Returns:
        list of finding dicts (empty if all elements are accounted for, or if
        the slide does not use pragmatic_composition).
    """
    findings = []
    slide_number = strategy_entry.get('slide_number', 0)
    strategy = strategy_entry.get('speaker_override') or strategy_entry.get('strategy')
    if strategy != 'pragmatic_composition':
        return findings

    elements = strategy_entry.get('element_layout', {}).get('elements', [])
    if not elements:
        return findings

    images = [
        i for i in (image_manifest or {}).get('images', [])
        if i.get('slide_number') == slide_number and i.get('element_id')
    ]

    expected = len(elements)
    actual = len(images)
    if actual < expected:
        missing = expected - actual
        findings.append({
            'slide_number': slide_number,
            'severity': 'error',
            'category': 'element_image_completeness',
            'description': (
                f'pragmatic_composition slide declares {expected} element(s) '
                f'but image manifest contains only {actual} element image(s) '
                f'({missing} missing). Slide will render as text labels only.'
            ),
            'suggested_fix': (
                'Generate the missing element images via the imagegen-bridge, '
                'or change the slide strategy to composed/background.'
            ),
            'affected_element': 'element_layout',
            'auto_fixable': False,
        })

    return findings


def check_vision_confidence(image_entry):
    """AP-28: Check vision detection confidence for backdrop slides.

    Args:
        image_entry: Dict from ImageManifest.images with detected_positions.

    Returns:
        list of finding dicts.
    """
    findings = []
    slide_number = image_entry.get('slide_number', 0)
    detected = image_entry.get('detected_positions', [])

    for pos in detected:
        confidence = pos.get('confidence', 0)
        eid = pos.get('element_id', 'unknown')
        if confidence < _VISION_CONFIDENCE_THRESHOLD:
            findings.append({
                'slide_number': slide_number,
                'severity': 'warning',
                'category': 'vision_confidence',
                'description': f'Element {eid} detected with low confidence {confidence:.2f} (threshold {_VISION_CONFIDENCE_THRESHOLD})',
                'suggested_fix': 'Re-generate the image or use prescribed fallback positions.',
                'affected_element': eid,
                'auto_fixable': False,
            })

    return findings
