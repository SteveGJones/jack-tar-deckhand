"""AP-27: Element layout validation and AP-28: Vision confidence checks."""

_VISION_CONFIDENCE_THRESHOLD = 0.7
_MAX_ELEMENTS = 5


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
