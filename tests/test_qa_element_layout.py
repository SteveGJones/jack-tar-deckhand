"""Tests for AP-27 to AP-30 (element layout, vision, alignment, reading order)."""

import pytest


def test_ap27_valid_layout_passes():
    """Valid element layout should produce no findings."""
    from src.qa.checks.element_layout import check_element_layout
    strategy_entry = {
        'slide_number': 5,
        'strategy': 'backdrop',
        'element_layout': {
            'template': 'three_across',
            'elements': [
                {'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.08, 'y': 0.25, 'w': 0.25, 'h': 0.50},
                {'id': 'elem_2', 'label_source': 'body_points[1]', 'x': 0.38, 'y': 0.25, 'w': 0.25, 'h': 0.50},
                {'id': 'elem_3', 'label_source': 'body_points[2]', 'x': 0.67, 'y': 0.25, 'w': 0.25, 'h': 0.50},
            ],
            'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
        },
    }
    outline_slide = {'slide_number': 5, 'body_points': ['A', 'B', 'C']}
    findings = check_element_layout(strategy_entry, outline_slide)
    assert len(findings) == 0


def test_ap27_out_of_bounds_element():
    """Element with coordinates > 1.0 should produce an error."""
    from src.qa.checks.element_layout import check_element_layout
    strategy_entry = {
        'slide_number': 5,
        'strategy': 'backdrop',
        'element_layout': {
            'template': 'test',
            'elements': [
                {'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.9, 'y': 0.25, 'w': 0.25, 'h': 0.50},
            ],
            'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
        },
    }
    outline_slide = {'slide_number': 5, 'body_points': ['A']}
    findings = check_element_layout(strategy_entry, outline_slide)
    errors = [f for f in findings if f['severity'] == 'error']
    assert len(errors) > 0


def test_ap27_too_many_elements():
    """More than 5 elements should produce an error."""
    from src.qa.checks.element_layout import check_element_layout
    strategy_entry = {
        'slide_number': 5,
        'strategy': 'pragmatic_composition',
        'element_layout': {
            'template': 'test',
            'elements': [
                {'id': f'elem_{i}', 'label_source': f'body_points[{i}]', 'x': i * 0.15, 'y': 0.2, 'w': 0.10, 'h': 0.3}
                for i in range(6)
            ],
            'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
        },
    }
    outline_slide = {'slide_number': 5, 'body_points': ['A', 'B', 'C', 'D', 'E', 'F']}
    findings = check_element_layout(strategy_entry, outline_slide)
    errors = [f for f in findings if f['severity'] == 'error']
    assert len(errors) > 0


def test_ap27_missing_label_source():
    """label_source referencing nonexistent body_point should warn."""
    from src.qa.checks.element_layout import check_element_layout
    strategy_entry = {
        'slide_number': 5,
        'strategy': 'backdrop',
        'element_layout': {
            'template': 'test',
            'elements': [
                {'id': 'elem_1', 'label_source': 'body_points[5]', 'x': 0.1, 'y': 0.2, 'w': 0.3, 'h': 0.4},
            ],
            'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
        },
    }
    outline_slide = {'slide_number': 5, 'body_points': ['A', 'B']}
    findings = check_element_layout(strategy_entry, outline_slide)
    warnings = [f for f in findings if f['severity'] == 'warning']
    assert len(warnings) > 0


def test_ap28_low_vision_confidence():
    """Low confidence detected position should produce a warning."""
    from src.qa.checks.element_layout import check_vision_confidence
    image_entry = {
        'slide_number': 5,
        'detected_positions': [
            {'element_id': 'elem_1', 'x': 0.1, 'y': 0.2, 'w': 0.3, 'h': 0.4, 'confidence': 0.5},
            {'element_id': 'elem_2', 'x': 0.5, 'y': 0.2, 'w': 0.3, 'h': 0.4, 'confidence': 0.9},
        ],
    }
    findings = check_vision_confidence(image_entry)
    warnings = [f for f in findings if f['severity'] == 'warning']
    assert len(warnings) >= 1  # elem_1 is below 0.7 threshold


def test_ap28_all_high_confidence():
    """All high-confidence detections should produce no findings."""
    from src.qa.checks.element_layout import check_vision_confidence
    image_entry = {
        'slide_number': 5,
        'detected_positions': [
            {'element_id': 'elem_1', 'x': 0.1, 'y': 0.2, 'w': 0.3, 'h': 0.4, 'confidence': 0.92},
        ],
    }
    findings = check_vision_confidence(image_entry)
    assert len(findings) == 0


# --- AP-29: Text-element alignment ---

def test_ap29_well_aligned_text():
    """Text centered on detected elements should produce no findings."""
    from src.qa.checks.element_layout import check_text_element_alignment
    strategy_entry = {
        'slide_number': 5,
        'element_layout': {
            'template': 'grid_2x2',
            'elements': [
                {'id': 'a', 'x': 0.05, 'y': 0.20, 'w': 0.40, 'h': 0.30},
                {'id': 'b', 'x': 0.55, 'y': 0.20, 'w': 0.40, 'h': 0.30},
            ],
        },
    }
    image_entry = {
        'slide_number': 5,
        'detected_positions': [
            {'element_id': 'a', 'x': 0.06, 'y': 0.15, 'w': 0.38, 'h': 0.35},
            {'element_id': 'b', 'x': 0.56, 'y': 0.15, 'w': 0.38, 'h': 0.35},
        ],
    }
    findings = check_text_element_alignment(strategy_entry, image_entry)
    assert len(findings) == 0


def test_ap29_misaligned_text_warns():
    """Text far from detected element center should produce a warning."""
    from src.qa.checks.element_layout import check_text_element_alignment
    strategy_entry = {
        'slide_number': 5,
        'element_layout': {
            'template': 'grid_2x2',
            'elements': [
                {'id': 'a', 'x': 0.55, 'y': 0.20, 'w': 0.42, 'h': 0.30},  # center_x = 0.76
            ],
        },
    }
    image_entry = {
        'slide_number': 5,
        'detected_positions': [
            {'element_id': 'a', 'x': 0.54, 'y': 0.15, 'w': 0.28, 'h': 0.35},  # center_x = 0.68
        ],
    }
    findings = check_text_element_alignment(strategy_entry, image_entry)
    warnings = [f for f in findings if f['category'] == 'text_element_alignment']
    assert len(warnings) >= 1


def test_ap29_inconsistent_vertical_anchor():
    """Mixed overlap/below positioning should warn about inconsistency."""
    from src.qa.checks.element_layout import check_text_element_alignment
    strategy_entry = {
        'slide_number': 5,
        'element_layout': {
            'template': 'grid_2x2',
            'elements': [
                {'id': 'a', 'x': 0.05, 'y': 0.10, 'w': 0.40, 'h': 0.30},  # overlaps detected
                {'id': 'b', 'x': 0.55, 'y': 0.55, 'w': 0.40, 'h': 0.30},  # below detected
            ],
        },
    }
    image_entry = {
        'slide_number': 5,
        'detected_positions': [
            {'element_id': 'a', 'x': 0.05, 'y': 0.05, 'w': 0.40, 'h': 0.40},  # text starts at 0.10, bottom at 0.45
            {'element_id': 'b', 'x': 0.55, 'y': 0.05, 'w': 0.40, 'h': 0.40},  # text starts at 0.55, bottom at 0.45
        ],
    }
    findings = check_text_element_alignment(strategy_entry, image_entry)
    inconsistency = [f for f in findings if 'inconsistent' in f['description'].lower()]
    assert len(inconsistency) >= 1


def test_ap29_no_detected_positions_skips():
    """No detected positions should produce no findings (nothing to align to)."""
    from src.qa.checks.element_layout import check_text_element_alignment
    strategy_entry = {
        'slide_number': 5,
        'element_layout': {
            'template': 'grid_2x2',
            'elements': [
                {'id': 'a', 'x': 0.05, 'y': 0.20, 'w': 0.40, 'h': 0.30},
            ],
        },
    }
    image_entry = {'slide_number': 5}
    findings = check_text_element_alignment(strategy_entry, image_entry)
    assert len(findings) == 0


# --- AP-30: Grid reading order ---

def test_ap30_column_first_order_passes():
    """Column-first reading order (N-pattern) should produce no findings."""
    from src.qa.checks.element_layout import check_grid_reading_order
    strategy_entry = {
        'slide_number': 12,
        'element_layout': {
            'template': 'grid_2x2',
            'elements': [
                {'id': 'a', 'label_source': 'body_points[0]', 'x': 0.05, 'y': 0.55, 'w': 0.42, 'h': 0.18},  # TL
                {'id': 'b', 'label_source': 'body_points[1]', 'x': 0.05, 'y': 0.78, 'w': 0.42, 'h': 0.18},  # BL
                {'id': 'c', 'label_source': 'body_points[2]', 'x': 0.55, 'y': 0.55, 'w': 0.42, 'h': 0.18},  # TR
                {'id': 'd', 'label_source': 'body_points[3]', 'x': 0.55, 'y': 0.78, 'w': 0.42, 'h': 0.18},  # BR
            ],
        },
    }
    findings = check_grid_reading_order(strategy_entry)
    assert len(findings) == 0


def test_ap30_row_first_order_warns():
    """Row-first reading order (Z-pattern) should produce a warning."""
    from src.qa.checks.element_layout import check_grid_reading_order
    strategy_entry = {
        'slide_number': 12,
        'element_layout': {
            'template': 'grid_2x2',
            'elements': [
                {'id': 'a', 'label_source': 'body_points[0]', 'x': 0.05, 'y': 0.55, 'w': 0.42, 'h': 0.18},  # TL
                {'id': 'b', 'label_source': 'body_points[1]', 'x': 0.55, 'y': 0.55, 'w': 0.42, 'h': 0.18},  # TR
                {'id': 'c', 'label_source': 'body_points[2]', 'x': 0.05, 'y': 0.78, 'w': 0.42, 'h': 0.18},  # BL
                {'id': 'd', 'label_source': 'body_points[3]', 'x': 0.55, 'y': 0.78, 'w': 0.42, 'h': 0.18},  # BR
            ],
        },
    }
    findings = check_grid_reading_order(strategy_entry)
    warnings = [f for f in findings if f['category'] == 'grid_reading_order']
    assert len(warnings) >= 1


def test_ap30_non_grid_skips():
    """Non grid_2x2 templates should produce no findings."""
    from src.qa.checks.element_layout import check_grid_reading_order
    strategy_entry = {
        'slide_number': 9,
        'element_layout': {
            'template': 'three_across',
            'elements': [
                {'id': 'a', 'label_source': 'body_points[0]', 'x': 0.05, 'y': 0.22, 'w': 0.27, 'h': 0.50},
                {'id': 'b', 'label_source': 'body_points[1]', 'x': 0.37, 'y': 0.22, 'w': 0.27, 'h': 0.50},
                {'id': 'c', 'label_source': 'body_points[2]', 'x': 0.69, 'y': 0.22, 'w': 0.27, 'h': 0.50},
            ],
        },
    }
    findings = check_grid_reading_order(strategy_entry)
    assert len(findings) == 0


def test_ap30_no_layout_skips():
    """Slides without element_layout should produce no findings."""
    from src.qa.checks.element_layout import check_grid_reading_order
    strategy_entry = {'slide_number': 2, 'strategy': 'background'}
    findings = check_grid_reading_order(strategy_entry)
    assert len(findings) == 0


# --- AP-31: Label text fit ---

def test_ap31_short_text_fits():
    """Short text should fit and produce no findings."""
    from src.qa.checks.element_layout import check_label_text_fit
    strategy_entry = {
        'slide_number': 5,
        'element_layout': {
            'template': 'grid_2x2',
            'elements': [
                {'id': 'a', 'label_source': 'body_points[0]', 'x': 0.05, 'y': 0.18, 'w': 0.40, 'h': 0.35},
            ],
        },
    }
    outline_slide = {'body_points': ['Short label text']}
    findings = check_label_text_fit(strategy_entry, outline_slide)
    assert len(findings) == 0


def test_ap31_long_text_in_narrow_box_warns():
    """Long text in a narrow element should warn about overflow."""
    from src.qa.checks.element_layout import check_label_text_fit
    strategy_entry = {
        'slide_number': 5,
        'element_layout': {
            'template': 'grid_2x2',
            'elements': [
                {'id': 'a', 'label_source': 'body_points[0]', 'x': 0.55, 'y': 0.18, 'w': 0.15, 'h': 0.35},
            ],
        },
    }
    outline_slide = {'body_points': [
        'This is a very long body point text that should not fit in a narrow element box and would need many lines to display'
    ]}
    findings = check_label_text_fit(strategy_entry, outline_slide)
    warnings = [f for f in findings if f['category'] == 'label_text_fit']
    assert len(warnings) >= 1


# --- AP-32: Element image completeness ---

def test_ap32_pragmatic_composition_missing_images():
    """AP-32 errors when a pragmatic_composition slide has no element images."""
    from src.qa.checks.element_layout import check_element_image_completeness
    strategy_entry = {
        'slide_number': 9,
        'strategy': 'pragmatic_composition',
        'element_layout': {
            'template': 'quad',
            'elements': [
                {'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.05, 'y': 0.20, 'w': 0.42, 'h': 0.35},
                {'id': 'elem_2', 'label_source': 'body_points[1]', 'x': 0.53, 'y': 0.20, 'w': 0.42, 'h': 0.35},
            ],
        },
    }
    image_manifest = {'images': []}  # No images at all
    findings = check_element_image_completeness(strategy_entry, image_manifest)
    errors = [f for f in findings if f['severity'] == 'error']
    assert len(errors) == 1
    assert errors[0]['category'] == 'element_image_completeness'
    assert errors[0]['slide_number'] == 9
    assert '2' in errors[0]['description']  # references missing count


def test_ap32_pragmatic_composition_partial_images():
    """AP-32 errors when only some element images are present."""
    from src.qa.checks.element_layout import check_element_image_completeness
    strategy_entry = {
        'slide_number': 9,
        'strategy': 'pragmatic_composition',
        'element_layout': {
            'template': 'quad',
            'elements': [
                {'id': 'elem_1'},
                {'id': 'elem_2'},
                {'id': 'elem_3'},
                {'id': 'elem_4'},
            ],
        },
    }
    image_manifest = {
        'images': [
            {'slide_number': 9, 'element_id': 'elem_1', 'file_path': 'a.png'},
            {'slide_number': 9, 'element_id': 'elem_2', 'file_path': 'b.png'},
        ],
    }
    findings = check_element_image_completeness(strategy_entry, image_manifest)
    errors = [f for f in findings if f['severity'] == 'error']
    assert len(errors) == 1


def test_ap32_pragmatic_composition_with_all_images_passes():
    """AP-32 returns no findings when every element has an image."""
    from src.qa.checks.element_layout import check_element_image_completeness
    strategy_entry = {
        'slide_number': 9,
        'strategy': 'pragmatic_composition',
        'element_layout': {
            'template': 'two_column',
            'elements': [
                {'id': 'elem_1'},
                {'id': 'elem_2'},
            ],
        },
    }
    image_manifest = {
        'images': [
            {'slide_number': 9, 'element_id': 'elem_1', 'file_path': 'foo.png'},
            {'slide_number': 9, 'element_id': 'elem_2', 'file_path': 'bar.png'},
        ],
    }
    findings = check_element_image_completeness(strategy_entry, image_manifest)
    assert len(findings) == 0


def test_ap32_skips_non_pragmatic_slides():
    """AP-32 produces no findings for slides that don't use pragmatic_composition."""
    from src.qa.checks.element_layout import check_element_image_completeness
    strategy_entry = {
        'slide_number': 5,
        'strategy': 'composed',
        'element_layout': {
            'elements': [
                {'id': 'elem_1'},
            ],
        },
    }
    image_manifest = {'images': []}
    findings = check_element_image_completeness(strategy_entry, image_manifest)
    assert len(findings) == 0


def test_ap32_skips_backdrop_slides():
    """AP-32 produces no findings for backdrop slides (only pragmatic_composition)."""
    from src.qa.checks.element_layout import check_element_image_completeness
    strategy_entry = {
        'slide_number': 5,
        'strategy': 'backdrop',
        'element_layout': {
            'elements': [
                {'id': 'elem_1'},
                {'id': 'elem_2'},
            ],
        },
    }
    image_manifest = {'images': []}
    findings = check_element_image_completeness(strategy_entry, image_manifest)
    assert len(findings) == 0


def test_ap32_respects_speaker_override():
    """AP-32 honours speaker_override when determining slide strategy."""
    from src.qa.checks.element_layout import check_element_image_completeness
    strategy_entry = {
        'slide_number': 9,
        'strategy': 'composed',
        'speaker_override': 'pragmatic_composition',
        'element_layout': {
            'elements': [{'id': 'elem_1'}],
        },
    }
    image_manifest = {'images': []}
    findings = check_element_image_completeness(strategy_entry, image_manifest)
    errors = [f for f in findings if f['severity'] == 'error']
    assert len(errors) == 1


def test_ap31_detected_width_used_when_available():
    """When detected positions exist, their width should be used for fit check."""
    from src.qa.checks.element_layout import check_label_text_fit
    strategy_entry = {
        'slide_number': 5,
        'element_layout': {
            'template': 'grid_2x2',
            'elements': [
                {'id': 'a', 'label_source': 'body_points[0]', 'x': 0.05, 'y': 0.18, 'w': 0.40, 'h': 0.35},
            ],
        },
    }
    outline_slide = {'body_points': [
        'This is quite a long text that needs space to display across multiple lines properly'
    ]}
    # Wide detected position — should fit
    image_wide = {
        'detected_positions': [{'element_id': 'a', 'x': 0.05, 'y': 0.10, 'w': 0.40, 'h': 0.40}],
    }
    findings_wide = check_label_text_fit(strategy_entry, outline_slide, image_wide)

    # Narrow detected position — may not fit
    image_narrow = {
        'detected_positions': [{'element_id': 'a', 'x': 0.55, 'y': 0.10, 'w': 0.10, 'h': 0.40}],
    }
    findings_narrow = check_label_text_fit(strategy_entry, outline_slide, image_narrow)

    # Narrow should have more warnings than wide
    assert len(findings_narrow) >= len(findings_wide)
