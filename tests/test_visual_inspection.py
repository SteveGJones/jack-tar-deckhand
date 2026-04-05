"""Tests for post-assembly visual inspection — blank detection and brand colour checks."""

import os
import tempfile

import pytest
from PIL import Image


class TestBlankDetection:
    def test_detects_blank_white_slide(self):
        from src.qa.checks.visual_inspection import inspect_slide
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (1920, 1080), (255, 255, 255))
            img.save(f.name)
            findings = inspect_slide(f.name, slide_number=1, outline_slide={}, style_guide={})
        errors = [f for f in findings if f['severity'] == 'error']
        assert any('blank' in f['description'].lower() for f in errors)
        os.unlink(f.name)

    def test_accepts_slide_with_content(self):
        from src.qa.checks.visual_inspection import inspect_slide
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (1920, 1080), (245, 240, 232))
            for x in range(100, 800):
                for y in range(100, 400):
                    img.putpixel((x, y), (27, 58, 75))
            img.save(f.name)
            findings = inspect_slide(f.name, slide_number=1, outline_slide={}, style_guide={})
        errors = [f for f in findings if f['severity'] == 'error' and 'blank' in f['description'].lower()]
        assert len(errors) == 0
        os.unlink(f.name)


class TestColourCheck:
    def test_detects_off_brand_colours(self):
        from src.qa.checks.visual_inspection import inspect_slide
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (1920, 1080), (255, 0, 0))
            img.save(f.name)
            style_guide = {
                'palette': {
                    'primary': '1B3A4B', 'background': 'F5F0E8',
                    'accent': 'C67B2F', 'text_primary': '1A1A1A'
                }
            }
            findings = inspect_slide(f.name, slide_number=1, outline_slide={}, style_guide=style_guide)
        warnings = [f for f in findings if f['severity'] == 'warning' and 'brand' in f['description'].lower()]
        assert len(warnings) > 0
        os.unlink(f.name)

    def test_accepts_brand_coloured_slide(self):
        from src.qa.checks.visual_inspection import inspect_slide
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (1920, 1080), (245, 240, 232))  # F5F0E8 parchment
            img.save(f.name)
            style_guide = {
                'palette': {
                    'primary': '1B3A4B', 'background': 'F5F0E8',
                    'accent': 'C67B2F', 'text_primary': '1A1A1A'
                }
            }
            findings = inspect_slide(f.name, slide_number=1, outline_slide={}, style_guide=style_guide)
        warnings = [f for f in findings if f['severity'] == 'warning' and 'brand' in f['description'].lower()]
        assert len(warnings) == 0
        os.unlink(f.name)


class TestRunVisualInspection:
    def test_returns_empty_for_missing_pptx(self):
        from src.qa.checks.visual_inspection import run_visual_inspection
        findings = run_visual_inspection(
            pptx_path=None, outline={'slides': []},
            style_guide={}, output_dir=tempfile.mkdtemp()
        )
        assert isinstance(findings, list)
        assert len(findings) == 0
