"""Tests for AP-27 (element layout validation) and AP-28 (vision confidence)."""

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
