"""Tests for keynote-specific QA checks."""

import io
import os
import shutil
import tempfile

import pytest
from PIL import Image
from pptx import Presentation
from pptx.util import Inches


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


def _make_pptx_with_image(tmp_dir, image_color, filename='test.pptx'):
    """Create a minimal pptx with a single full-bleed image of the given RGB colour."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout

    # Create image in memory
    img = Image.new('RGB', (1920, 1080), color=image_color)
    img_path = os.path.join(tmp_dir, 'test_img.png')
    img.save(img_path)
    slide.shapes.add_picture(img_path, 0, 0, Inches(13.333), Inches(7.5))

    pptx_path = os.path.join(tmp_dir, filename)
    prs.save(pptx_path)
    return pptx_path


def test_palette_drift_within_tolerance(tmp_dir):
    from src.qa.checks.keynote_checks import check_palette_drift
    # Image is exact brand teal — no drift
    pptx_path = _make_pptx_with_image(tmp_dir, (0, 107, 94))  # #006B5E
    prs = Presentation(pptx_path)
    slide = prs.slides[0]
    brand_palette = ['006B5E', '5CDBC0', '4B635B', 'F5FBF7']
    issues = check_palette_drift(slide, 1, brand_palette=brand_palette)
    assert len(issues) == 0


def test_palette_drift_detected(tmp_dir):
    from src.qa.checks.keynote_checks import check_palette_drift
    # Image is bright red — completely off-brand
    pptx_path = _make_pptx_with_image(tmp_dir, (255, 0, 0))
    prs = Presentation(pptx_path)
    slide = prs.slides[0]
    brand_palette = ['006B5E', '5CDBC0', '4B635B', 'F5FBF7']
    issues = check_palette_drift(slide, 1, brand_palette=brand_palette)
    assert len(issues) >= 1
    assert issues[0]['category'] == 'palette_drift'
    assert issues[0]['severity'] == 'warning'


def test_palette_drift_no_images_no_issues(tmp_dir):
    from src.qa.checks.keynote_checks import check_palette_drift
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    brand_palette = ['006B5E']
    issues = check_palette_drift(slide, 1, brand_palette=brand_palette)
    assert len(issues) == 0
