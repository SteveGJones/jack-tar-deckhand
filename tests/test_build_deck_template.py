"""Tests for template-driven deck assembly via python-pptx."""

import json
import os
import pytest
from pptx import Presentation

from src.template_analyser import analyse_template
from src.assembler.build_deck_template import build_deck

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'templates', 'metamirror-template.pptx')


def _setup_deck_dir(tmp_path, outline_slides, image_manifest_images=None, speaker_notes=None):
    """Create a minimal DeckContext for testing."""
    deck_dir = str(tmp_path / 'deck')
    os.makedirs(os.path.join(deck_dir, 'images'), exist_ok=True)
    os.makedirs(os.path.join(deck_dir, 'output'), exist_ok=True)

    # Template profile
    profile = analyse_template(FIXTURE_PATH)
    with open(os.path.join(deck_dir, 'template-profile.json'), 'w') as f:
        json.dump(profile, f)

    # Outline
    outline = {
        'narrative_arc': 'test',
        'estimated_duration_minutes': 10,
        'slides': outline_slides,
    }
    with open(os.path.join(deck_dir, 'outline.json'), 'w') as f:
        json.dump(outline, f)

    # Image manifest
    manifest = {'images': image_manifest_images or []}
    with open(os.path.join(deck_dir, 'image-manifest.json'), 'w') as f:
        json.dump(manifest, f)

    # Speaker notes
    notes = speaker_notes or {'notes': []}
    with open(os.path.join(deck_dir, 'speaker-notes.json'), 'w') as f:
        json.dump(notes, f)

    return deck_dir, profile


class TestBuildDeckTemplate:
    def test_strips_example_slides(self, tmp_path):
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'content', 'headline': 'Real Slide'},
        ])
        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        prs = Presentation(output_path)
        # Should have exactly 1 slide (the one from our outline), not the template examples
        assert len(prs.slides) == 1

    def test_populates_title_placeholder(self, tmp_path):
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'content', 'headline': 'My Headline'},
        ])
        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        prs = Presentation(output_path)
        slide = prs.slides[0]
        texts = [shape.text for shape in slide.shapes if shape.has_text_frame]
        assert any('My Headline' in t for t in texts)

    def test_populates_body_points(self, tmp_path):
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'content', 'headline': 'Title',
             'body_points': ['Point one', 'Point two', 'Point three']},
        ])
        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        prs = Presentation(output_path)
        slide = prs.slides[0]
        all_text = ' '.join(shape.text for shape in slide.shapes if shape.has_text_frame)
        assert 'Point one' in all_text
        assert 'Point two' in all_text
        assert 'Point three' in all_text

    def test_output_path_correct(self, tmp_path):
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'content', 'headline': 'Test'},
        ])
        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        assert output_path.endswith('output/presentation.pptx')
        assert os.path.isfile(output_path)

    def test_multiple_slides(self, tmp_path):
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title Slide'},
            {'slide_number': 2, 'slide_type': 'content', 'headline': 'Content Slide'},
            {'slide_number': 3, 'slide_type': 'content', 'headline': 'Another Content'},
        ])
        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        prs = Presentation(output_path)
        assert len(prs.slides) == 3
