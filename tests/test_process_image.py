"""Tests for image processing utilities."""

import hashlib
import os
import shutil
import tempfile
import pytest
from PIL import Image


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


@pytest.fixture
def test_image(tmp_dir):
    """Create a 200x100 red test image."""
    path = os.path.join(tmp_dir, 'test.png')
    img = Image.new('RGB', (200, 100), color=(255, 0, 0))
    img.save(path)
    return path


@pytest.fixture
def test_image_square(tmp_dir):
    """Create a 100x100 blue test image."""
    path = os.path.join(tmp_dir, 'square.png')
    img = Image.new('RGB', (100, 100), color=(0, 0, 255))
    img.save(path)
    return path


class TestResize:
    def test_resize_to_larger(self, test_image, tmp_dir):
        from src.process_image import resize
        out = os.path.join(tmp_dir, 'resized.png')
        result = resize(test_image, 400, 200, output_path=out)
        assert result == out
        img = Image.open(out)
        assert img.size == (400, 200)

    def test_resize_to_smaller(self, test_image, tmp_dir):
        from src.process_image import resize
        out = os.path.join(tmp_dir, 'small.png')
        result = resize(test_image, 50, 25, output_path=out)
        img = Image.open(result)
        assert img.size == (50, 25)

    def test_resize_in_place(self, test_image):
        from src.process_image import resize
        result = resize(test_image, 150, 75)
        assert result == test_image
        img = Image.open(result)
        assert img.size == (150, 75)

    def test_resize_preserves_format(self, test_image, tmp_dir):
        from src.process_image import resize
        out = os.path.join(tmp_dir, 'resized.png')
        resize(test_image, 100, 50, output_path=out)
        img = Image.open(out)
        assert img.format == 'PNG'


class TestCropToAspect:
    def test_crop_wide_to_16_9(self, tmp_dir):
        from src.process_image import crop_to_aspect
        # Create a 1920x1200 image (16:10)
        path = os.path.join(tmp_dir, 'wide.png')
        Image.new('RGB', (1920, 1200), color=(0, 255, 0)).save(path)
        out = os.path.join(tmp_dir, 'cropped.png')
        result = crop_to_aspect(path, '16:9', output_path=out)
        img = Image.open(result)
        w, h = img.size
        ratio = w / h
        assert abs(ratio - 16/9) < 0.02

    def test_crop_square_to_16_9(self, test_image_square, tmp_dir):
        from src.process_image import crop_to_aspect
        out = os.path.join(tmp_dir, 'cropped.png')
        result = crop_to_aspect(test_image_square, '16:9', output_path=out)
        img = Image.open(result)
        w, h = img.size
        ratio = w / h
        assert abs(ratio - 16/9) < 0.02

    def test_crop_to_1_1(self, test_image, tmp_dir):
        from src.process_image import crop_to_aspect
        out = os.path.join(tmp_dir, 'square.png')
        result = crop_to_aspect(test_image, '1:1', output_path=out)
        img = Image.open(result)
        assert img.size[0] == img.size[1]

    def test_crop_in_place(self, test_image):
        from src.process_image import crop_to_aspect
        result = crop_to_aspect(test_image, '16:9')
        assert result == test_image


class TestGetDimensions:
    def test_returns_correct_size(self, test_image):
        from src.process_image import get_dimensions
        w, h = get_dimensions(test_image)
        assert w == 200
        assert h == 100

    def test_square_image(self, test_image_square):
        from src.process_image import get_dimensions
        w, h = get_dimensions(test_image_square)
        assert w == 100
        assert h == 100


class TestComputeContentHash:
    def test_returns_64_char_hex(self, test_image):
        from src.process_image import compute_content_hash
        h = compute_content_hash(test_image)
        assert len(h) == 64
        assert all(c in '0123456789abcdef' for c in h)

    def test_same_file_same_hash(self, test_image):
        from src.process_image import compute_content_hash
        h1 = compute_content_hash(test_image)
        h2 = compute_content_hash(test_image)
        assert h1 == h2

    def test_different_files_different_hash(self, test_image, test_image_square):
        from src.process_image import compute_content_hash
        h1 = compute_content_hash(test_image)
        h2 = compute_content_hash(test_image_square)
        assert h1 != h2


class TestGeneratePlaceholder:
    def test_creates_image_at_path(self, tmp_dir):
        from src.process_image import generate_placeholder
        out = os.path.join(tmp_dir, 'placeholder.png')
        result = generate_placeholder(1920, 1080, '1A365D', 'Test placeholder', out)
        assert result == out
        assert os.path.isfile(out)

    def test_correct_dimensions(self, tmp_dir):
        from src.process_image import generate_placeholder
        out = os.path.join(tmp_dir, 'placeholder.png')
        generate_placeholder(800, 600, 'FF0000', 'Red box', out)
        img = Image.open(out)
        assert img.size == (800, 600)

    def test_correct_colour(self, tmp_dir):
        from src.process_image import generate_placeholder
        out = os.path.join(tmp_dir, 'placeholder.png')
        generate_placeholder(100, 100, 'FF0000', 'Red', out)
        img = Image.open(out)
        # Check centre pixel is red
        pixel = img.getpixel((50, 50))
        assert pixel == (255, 0, 0)

    def test_hex_without_hash(self, tmp_dir):
        from src.process_image import generate_placeholder
        out = os.path.join(tmp_dir, 'placeholder.png')
        generate_placeholder(100, 100, '00FF00', 'Green', out)
        img = Image.open(out)
        pixel = img.getpixel((50, 50))
        assert pixel == (0, 255, 0)


class TestOptimizePng:
    def test_reduces_file_size(self, tmp_dir):
        from src.process_image import optimize_png
        # Create a large-ish image with some content
        path = os.path.join(tmp_dir, 'large.png')
        img = Image.new('RGB', (500, 500), color=(128, 64, 32))
        # Add some variation so compression has something to work with
        for x in range(0, 500, 10):
            for y in range(0, 500, 10):
                img.putpixel((x, y), (x % 256, y % 256, (x+y) % 256))
        img.save(path)
        original_size = os.path.getsize(path)

        out = os.path.join(tmp_dir, 'optimized.png')
        result = optimize_png(path, output_path=out)
        assert 'path' in result
        assert 'original_size' in result
        assert 'optimized_size' in result
        assert 'savings_pct' in result
        assert os.path.isfile(result['path'])

    def test_output_is_valid_image(self, test_image, tmp_dir):
        from src.process_image import optimize_png
        out = os.path.join(tmp_dir, 'opt.png')
        result = optimize_png(test_image, output_path=out)
        img = Image.open(result['path'])
        assert img.size[0] > 0
        assert img.size[1] > 0


@pytest.fixture
def test_svg(tmp_dir):
    """Create a minimal valid SVG file."""
    path = os.path.join(tmp_dir, 'test.svg')
    with open(path, 'w') as f:
        f.write(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">'
            '<rect width="400" height="300" fill="#006B5E"/>'
            '</svg>'
        )
    return path


def test_rasterize_svg_basic(tmp_dir, test_svg):
    from src.process_image import rasterize_svg
    output = os.path.join(tmp_dir, 'output.png')
    result = rasterize_svg(test_svg, output, width=800)
    assert result['path'] == output
    assert os.path.exists(output)
    assert result['width'] == 800
    assert result['height'] == 600  # maintains 4:3 aspect
    assert len(result['content_hash']) == 64


def test_rasterize_svg_explicit_height(tmp_dir, test_svg):
    from src.process_image import rasterize_svg
    output = os.path.join(tmp_dir, 'output.png')
    result = rasterize_svg(test_svg, output, width=800, height=800, keep_aspect=False)
    assert result['width'] == 800
    assert result['height'] == 800


def test_rasterize_svg_missing_file(tmp_dir):
    from src.process_image import rasterize_svg
    with pytest.raises(FileNotFoundError):
        rasterize_svg('/no/such/file.svg', os.path.join(tmp_dir, 'out.png'))


def test_rasterize_svg_no_rsvg(tmp_dir, test_svg, monkeypatch):
    from src import process_image
    monkeypatch.setattr(process_image, '_RSVG_CONVERT_PATH', None)
    output = os.path.join(tmp_dir, 'output.png')
    with pytest.raises(RuntimeError, match='rsvg-convert'):
        process_image.rasterize_svg(test_svg, output)
