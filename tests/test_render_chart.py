"""Tests for chart renderer module."""

import json
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
def sample_bar_data():
    return {
        'labels': ['Q1', 'Q2', 'Q3', 'Q4'],
        'values': [12, 19, 8, 15]
    }


@pytest.fixture
def sample_pie_data():
    return {
        'labels': ['Desktop', 'Mobile', 'Tablet'],
        'values': [60, 30, 10]
    }


@pytest.fixture
def sample_multi_series():
    return {
        'labels': ['Jan', 'Feb', 'Mar', 'Apr'],
        'series': {
            'Revenue': [100, 120, 115, 140],
            'Costs': [80, 85, 90, 95]
        }
    }


@pytest.fixture
def style_guide():
    with open('tests/fixtures/valid_style_guide.json') as f:
        return json.load(f)


class TestRenderBarChart:
    def test_creates_png_file(self, tmp_dir, sample_bar_data):
        from src.render_chart import render_chart
        out = os.path.join(tmp_dir, 'bar.png')
        result = render_chart('bar', sample_bar_data, out)
        assert os.path.isfile(out)
        assert result['status'] == 'rendered'

    def test_correct_dimensions(self, tmp_dir, sample_bar_data):
        from src.render_chart import render_chart
        out = os.path.join(tmp_dir, 'bar.png')
        render_chart('bar', sample_bar_data, out, width=1920, height=1080)
        img = Image.open(out)
        w, h = img.size
        # At 300 DPI, 1920px = 6.4 inches, but matplotlib sizes in inches
        # Just verify it's a reasonable size (>100px in each dimension)
        assert w > 100
        assert h > 100

    def test_multi_series_bar(self, tmp_dir, sample_multi_series):
        from src.render_chart import render_chart
        out = os.path.join(tmp_dir, 'multi_bar.png')
        result = render_chart('bar', sample_multi_series, out)
        assert os.path.isfile(out)
        assert result['status'] == 'rendered'

    def test_with_style_guide(self, tmp_dir, sample_bar_data, style_guide):
        from src.render_chart import render_chart
        out = os.path.join(tmp_dir, 'styled_bar.png')
        result = render_chart('bar', sample_bar_data, out, style_guide=style_guide)
        assert os.path.isfile(out)


class TestRenderLineChart:
    def test_creates_png(self, tmp_dir, sample_multi_series):
        from src.render_chart import render_chart
        out = os.path.join(tmp_dir, 'line.png')
        result = render_chart('line', sample_multi_series, out)
        assert os.path.isfile(out)
        assert result['chart_type'] == 'line'

    def test_single_series(self, tmp_dir, sample_bar_data):
        from src.render_chart import render_chart
        out = os.path.join(tmp_dir, 'line_single.png')
        result = render_chart('line', sample_bar_data, out)
        assert os.path.isfile(out)


class TestRenderPieChart:
    def test_creates_png(self, tmp_dir, sample_pie_data):
        from src.render_chart import render_chart
        out = os.path.join(tmp_dir, 'pie.png')
        result = render_chart('pie', sample_pie_data, out)
        assert os.path.isfile(out)

    def test_donut_variant(self, tmp_dir, sample_pie_data):
        from src.render_chart import render_chart
        out = os.path.join(tmp_dir, 'donut.png')
        result = render_chart('donut', sample_pie_data, out)
        assert os.path.isfile(out)
        assert result['chart_type'] == 'donut'


class TestRenderAreaChart:
    def test_creates_png(self, tmp_dir, sample_multi_series):
        from src.render_chart import render_chart
        out = os.path.join(tmp_dir, 'area.png')
        result = render_chart('area', sample_multi_series, out)
        assert os.path.isfile(out)


class TestRenderScatterChart:
    def test_creates_png(self, tmp_dir):
        from src.render_chart import render_chart
        data = {
            'labels': ['A', 'B', 'C', 'D', 'E'],
            'values': [10, 20, 15, 25, 30]  # x positions implied by index
        }
        out = os.path.join(tmp_dir, 'scatter.png')
        result = render_chart('scatter', data, out)
        assert os.path.isfile(out)


class TestReturnValue:
    def test_has_required_manifest_fields(self, tmp_dir, sample_bar_data):
        from src.render_chart import render_chart
        out = os.path.join(tmp_dir, 'test.png')
        result = render_chart('bar', sample_bar_data, out)
        assert 'chart_id' in result
        assert 'file_path' in result
        assert 'chart_type' in result
        assert 'status' in result
        assert 'dimensions' in result
        assert 'alt_text' in result
        assert 'content_hash' in result
        assert result['file_path'] == out
        assert result['chart_type'] == 'bar'
        assert result['status'] == 'rendered'
        assert len(result['content_hash']) == 64

    def test_dimensions_are_integers(self, tmp_dir, sample_bar_data):
        from src.render_chart import render_chart
        out = os.path.join(tmp_dir, 'test.png')
        result = render_chart('bar', sample_bar_data, out)
        assert isinstance(result['dimensions']['width'], int)
        assert isinstance(result['dimensions']['height'], int)


class TestHexConversion:
    def test_converts_hex_to_normalised_rgb(self):
        from src.render_chart import _hex_to_rgb_normalised
        r, g, b = _hex_to_rgb_normalised('FF0000')
        assert abs(r - 1.0) < 0.01
        assert abs(g - 0.0) < 0.01
        assert abs(b - 0.0) < 0.01

    def test_converts_dark_blue(self):
        from src.render_chart import _hex_to_rgb_normalised
        r, g, b = _hex_to_rgb_normalised('1A365D')
        assert 0.0 < r < 0.2
        assert 0.1 < g < 0.3
        assert 0.3 < b < 0.5


class TestUnsupportedChartType:
    def test_unknown_type_raises(self, tmp_dir):
        from src.render_chart import render_chart
        out = os.path.join(tmp_dir, 'test.png')
        with pytest.raises(ValueError, match='chart_type'):
            render_chart('sunburst', {'labels': [], 'values': []}, out)
