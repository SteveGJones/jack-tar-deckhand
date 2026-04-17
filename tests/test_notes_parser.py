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
