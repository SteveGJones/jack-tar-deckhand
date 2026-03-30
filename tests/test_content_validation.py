"""Tests for content validation utilities — timing arithmetic and reference integrity."""

import json
import os
import pytest

from src.content_validation import (
    validate_outline_schema,
    validate_notes_schema,
    check_timing_total,
    check_notes_slide_references,
    check_outline_layout_references,
)

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def _load_fixture(name):
    with open(os.path.join(FIXTURE_DIR, name)) as f:
        return json.load(f)


class TestValidateOutlineSchema:
    def test_valid_outline_passes(self):
        outline = _load_fixture('valid_slide_outline.json')
        errors = validate_outline_schema(outline)
        assert len(errors) == 0

    def test_missing_slides_fails(self):
        outline = {"narrative_arc": "test", "estimated_duration_minutes": 10}
        errors = validate_outline_schema(outline)
        assert len(errors) > 0


class TestValidateNotesSchema:
    def test_valid_notes_passes(self):
        notes = _load_fixture('valid_speaker_notes.json')
        errors = validate_notes_schema(notes)
        assert len(errors) == 0

    def test_missing_notes_array_fails(self):
        notes = {"target_pace_wpm": 130}
        errors = validate_notes_schema(notes)
        assert len(errors) > 0


class TestTimingTotal:
    def test_timing_within_tolerance(self):
        notes = {
            "total_estimated_minutes": 10,
            "notes": [
                {"slide_number": 1, "text": "Hello", "estimated_seconds": 300},
                {"slide_number": 2, "text": "World", "estimated_seconds": 300},
            ]
        }
        issues = check_timing_total(notes, duration_minutes=10)
        assert len(issues) == 0

    def test_timing_too_long(self):
        notes = {
            "total_estimated_minutes": 30,
            "notes": [
                {"slide_number": 1, "text": "Hello", "estimated_seconds": 600},
                {"slide_number": 2, "text": "World", "estimated_seconds": 600},
                {"slide_number": 3, "text": "Extra", "estimated_seconds": 600},
            ]
        }
        issues = check_timing_total(notes, duration_minutes=10)
        assert len(issues) > 0
        assert any('exceeds' in i.lower() or 'over' in i.lower() for i in issues)

    def test_timing_without_seconds_skips(self):
        notes = {
            "notes": [
                {"slide_number": 1, "text": "Hello"},
            ]
        }
        issues = check_timing_total(notes, duration_minutes=10)
        assert len(issues) == 0


class TestNotesSlideReferences:
    def test_valid_references(self):
        outline = {
            "slides": [
                {"slide_number": 1, "slide_type": "title", "headline": "Hi"},
                {"slide_number": 2, "slide_type": "content", "headline": "Body"},
            ]
        }
        notes = {
            "notes": [
                {"slide_number": 1, "text": "Hello"},
                {"slide_number": 2, "text": "World"},
            ]
        }
        issues = check_notes_slide_references(notes, outline)
        assert len(issues) == 0

    def test_orphan_note_detected(self):
        outline = {
            "slides": [
                {"slide_number": 1, "slide_type": "title", "headline": "Hi"},
            ]
        }
        notes = {
            "notes": [
                {"slide_number": 1, "text": "Hello"},
                {"slide_number": 99, "text": "Orphan"},
            ]
        }
        issues = check_notes_slide_references(notes, outline)
        assert len(issues) > 0
        assert any('99' in i for i in issues)


class TestOutlineLayoutReferences:
    def test_valid_layout_references(self):
        outline = {
            "slides": [
                {"slide_number": 1, "slide_type": "title", "headline": "Hi", "layout_template": "title"},
                {"slide_number": 2, "slide_type": "content", "headline": "Body", "layout_template": "content"},
            ]
        }
        style_guide = {
            "layout": {
                "templates": {"title": {}, "content": {}}
            }
        }
        issues = check_outline_layout_references(outline, style_guide)
        assert len(issues) == 0

    def test_missing_template_detected(self):
        outline = {
            "slides": [
                {"slide_number": 1, "slide_type": "title", "headline": "Hi", "layout_template": "nonexistent"},
            ]
        }
        style_guide = {
            "layout": {
                "templates": {"title": {}, "content": {}}
            }
        }
        issues = check_outline_layout_references(outline, style_guide)
        assert len(issues) > 0

    def test_no_layout_template_skips(self):
        outline = {
            "slides": [
                {"slide_number": 1, "slide_type": "title", "headline": "Hi"},
            ]
        }
        style_guide = {"layout": {"templates": {}}}
        issues = check_outline_layout_references(outline, style_guide)
        assert len(issues) == 0
