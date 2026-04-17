"""Tests for external speaker notes parsing, matching, and timing."""

import os
import pytest

from src.notes_parser import parse_notes_file

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures', 'notes')


class TestParseNotesFile:
    def test_heading_based_parsing(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'heading-based.md'))
        assert len(blocks) == 3
        assert blocks[0]['slide_number'] == 1
        assert blocks[0]['headline_hint'] == 'Welcome to the Future'
        assert 'set the scene' in blocks[0]['text']

    def test_number_marker_parsing(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'number-markers.txt'))
        assert len(blocks) == 3
        assert blocks[0]['slide_number'] == 1
        assert blocks[1]['slide_number'] == 2
        assert 'debugging a deployment' in blocks[1]['text']

    def test_headline_only_parsing(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'headline-only.md'))
        assert len(blocks) == 3
        assert blocks[0]['slide_number'] is None
        assert blocks[0]['headline_hint'] == 'Welcome to the Future'

    def test_mixed_format_parsing(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'mixed-format.md'))
        assert len(blocks) == 4
        assert blocks[0]['slide_number'] == 1
        assert blocks[1]['slide_number'] == 2
        assert blocks[2]['slide_number'] is None
        assert blocks[2]['headline_hint'] == 'Our Solution'
        assert blocks[3]['slide_number'] == 4

    def test_empty_file(self, tmp_path):
        empty = tmp_path / 'empty.md'
        empty.write_text('')
        blocks = parse_notes_file(str(empty))
        assert blocks == []

    def test_no_delimiters_single_block(self, tmp_path):
        plain = tmp_path / 'plain.txt'
        plain.write_text('Just some unstructured speaker notes for the whole talk.')
        blocks = parse_notes_file(str(plain))
        assert len(blocks) == 1
        assert blocks[0]['slide_number'] == 1
        assert blocks[0]['headline_hint'] is None
        assert 'unstructured speaker notes' in blocks[0]['text']

    def test_preserves_paragraph_breaks(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'heading-based.md'))
        assert isinstance(blocks[0]['text'], str)
        assert len(blocks[0]['text']) > 10

    def test_strips_leading_trailing_whitespace(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'heading-based.md'))
        for block in blocks:
            assert block['text'] == block['text'].strip()

    def test_raw_label_preserved(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'heading-based.md'))
        assert 'Slide 1: Welcome to the Future' in blocks[0]['raw_label']

    def test_slide_number_extracted_from_bracket(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'number-markers.txt'))
        assert blocks[2]['slide_number'] == 3

    def test_slide_prefix_in_bracket(self, tmp_path):
        f = tmp_path / 'slide_prefix.txt'
        f.write_text('[Slide 5]\nNotes for slide five.')
        blocks = parse_notes_file(str(f))
        assert len(blocks) == 1
        assert blocks[0]['slide_number'] == 5

    def test_heading_level_ignored(self, tmp_path):
        f = tmp_path / 'h3.md'
        f.write_text('### Slide 1: Title\nSome notes.\n\n### Slide 2: Other\nMore notes.')
        blocks = parse_notes_file(str(f))
        assert len(blocks) == 2
        assert blocks[0]['slide_number'] == 1


from src.notes_parser import match_notes_to_outline

SAMPLE_OUTLINE = {
    'narrative_arc': 'test',
    'estimated_duration_minutes': 15,
    'slides': [
        {'slide_number': 1, 'slide_type': 'title', 'headline': 'Welcome to the Future'},
        {'slide_number': 2, 'slide_type': 'content', 'headline': 'The Problem'},
        {'slide_number': 3, 'slide_type': 'content', 'headline': 'Our Solution'},
        {'slide_number': 4, 'slide_type': 'closing', 'headline': 'Thank You'},
    ],
}


class TestMatchNotesToOutline:
    def test_exact_number_match(self):
        blocks = [
            {'raw_label': 'Slide 1', 'slide_number': 1, 'headline_hint': 'Welcome', 'text': 'Notes for slide 1'},
            {'raw_label': 'Slide 2', 'slide_number': 2, 'headline_hint': 'Problem', 'text': 'Notes for slide 2'},
        ]
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert matched[1] == 'Notes for slide 1'
        assert matched[2] == 'Notes for slide 2'
        assert warnings == []

    def test_headline_fuzzy_match(self):
        blocks = [
            {'raw_label': 'Welcome to the Future', 'slide_number': None, 'headline_hint': 'Welcome to the Future', 'text': 'Opening notes'},
            {'raw_label': 'The Problem', 'slide_number': None, 'headline_hint': 'The Problem', 'text': 'Problem notes'},
        ]
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert matched[1] == 'Opening notes'
        assert matched[2] == 'Problem notes'
        assert warnings == []

    def test_substring_match(self):
        blocks = [
            {'raw_label': 'Solution', 'slide_number': None, 'headline_hint': 'Solution', 'text': 'Solution notes'},
        ]
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert matched[3] == 'Solution notes'

    def test_unmatched_produces_warning(self):
        blocks = [
            {'raw_label': 'Nonexistent Slide', 'slide_number': None, 'headline_hint': 'Nonexistent Slide', 'text': 'Orphan notes'},
        ]
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert len(matched) == 0
        assert len(warnings) == 1
        assert 'Nonexistent Slide' in warnings[0]

    def test_number_out_of_range_warns(self):
        blocks = [
            {'raw_label': 'Slide 99', 'slide_number': 99, 'headline_hint': None, 'text': 'Bad ref'},
        ]
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert len(matched) == 0
        assert len(warnings) == 1

    def test_partial_coverage(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'partial-coverage.md'))
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert 2 in matched
        assert 3 in matched
        assert 1 not in matched
        assert warnings == []

    def test_unmatched_fixture(self):
        blocks = parse_notes_file(os.path.join(FIXTURES_DIR, 'unmatched.md'))
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert 1 in matched
        assert 3 in matched
        assert len(warnings) == 1
        assert 'Deleted Slide' in warnings[0]

    def test_duplicate_slide_number_last_wins(self):
        blocks = [
            {'raw_label': 'Slide 1', 'slide_number': 1, 'headline_hint': None, 'text': 'First version'},
            {'raw_label': 'Slide 1', 'slide_number': 1, 'headline_hint': None, 'text': 'Updated version'},
        ]
        matched, warnings = match_notes_to_outline(blocks, SAMPLE_OUTLINE)
        assert matched[1] == 'Updated version'


from src.notes_parser import estimate_timing, build_timing_markers


class TestTiming:
    def test_estimate_timing_basic(self):
        # 130 words at 130 WPM = 60 seconds
        text = ' '.join(['word'] * 130)
        assert estimate_timing(text) == 60

    def test_estimate_timing_custom_wpm(self):
        text = ' '.join(['word'] * 100)
        # 100 words at 100 WPM = 60 seconds
        assert estimate_timing(text, wpm=100) == 60

    def test_estimate_timing_empty_text(self):
        assert estimate_timing('') == 0

    def test_estimate_timing_rounds_to_int(self):
        # 10 words at 130 WPM = ~4.6 seconds -> 5
        text = ' '.join(['word'] * 10)
        result = estimate_timing(text)
        assert isinstance(result, int)
        assert result == 5

    def test_build_timing_markers(self):
        notes_dict = {
            1: 'First slide with some notes here for timing.',
            2: 'Second slide also has notes that take some time to deliver to the audience.',
            3: 'Third slide wraps up.',
        }
        markers = build_timing_markers(notes_dict)
        assert 1 in markers
        assert 2 in markers
        assert 3 in markers
        assert 'estimated_seconds' in markers[1]
        assert 'timing_marker' in markers[1]
        assert markers[1]['timing_marker'].startswith('~')

    def test_build_timing_markers_cumulative(self):
        notes_dict = {
            1: ' '.join(['word'] * 130),  # 60 seconds
            2: ' '.join(['word'] * 130),  # 60 seconds
        }
        markers = build_timing_markers(notes_dict)
        assert markers[1]['timing_marker'] == '~1:00'
        assert markers[2]['timing_marker'] == '~2:00'

    def test_build_timing_markers_empty(self):
        markers = build_timing_markers({})
        assert markers == {}
