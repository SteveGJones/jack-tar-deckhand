"""Tests for the custom SVG engine — primitives, tokens, and constraint engine."""

import pytest


class TestSvgPrimitives:
    def test_svg_rect_basic(self):
        from src.smartart_svg.primitives import svg_rect
        result = svg_rect(10, 20, 100, 50, rx=5, fill="#FF0000", stroke="#000000")
        assert '<rect' in result
        assert 'x="10"' in result
        assert 'width="100"' in result
        assert 'fill="#FF0000"' in result
        assert 'rx="5"' in result

    def test_svg_text_basic(self):
        from src.smartart_svg.primitives import svg_text
        result = svg_text(50, 30, "Hello World", font_family="Inter", font_size=16, fill="#000")
        assert '<text' in result
        assert 'Hello World' in result
        assert 'font-family="Inter"' in result

    def test_svg_circle_basic(self):
        from src.smartart_svg.primitives import svg_circle
        result = svg_circle(100, 100, 50, fill="#0000FF", opacity=0.5)
        assert '<circle' in result
        assert 'cx="100"' in result
        assert 'r="50"' in result
        assert 'opacity="0.5"' in result

    def test_svg_document_has_accessibility(self):
        from src.smartart_svg.primitives import svg_document
        result = svg_document(1920, 1080, ["<rect/>"], title="Test Chart", desc="A test chart")
        assert '<title>Test Chart</title>' in result
        assert '<desc>A test chart</desc>' in result
        assert 'xmlns="http://www.w3.org/2000/svg"' in result

    def test_svg_group_has_aria(self):
        from src.smartart_svg.primitives import svg_group
        result = svg_group(["<rect/>"], role="img", aria_label="Process flow")
        assert '<g' in result
        assert 'role="img"' in result
        assert 'aria-label="Process flow"' in result

    def test_svg_arrow(self):
        from src.smartart_svg.primitives import svg_arrow
        result = svg_arrow(0, 0, 100, 100, stroke="#333")
        assert '<line' in result or '<path' in result

    def test_svg_text_escapes_html(self):
        from src.smartart_svg.primitives import svg_text
        result = svg_text(0, 0, "A < B & C > D", font_family="Arial", font_size=14, fill="#000")
        assert '&amp;' in result
        assert '&lt;' in result
        assert '&gt;' in result


class TestTokenMapping:
    def test_extract_style_tokens(self):
        from src.smartart_svg.tokens import extract_style_tokens
        style_guide = {
            'palette': {
                'primary': '1a73e8',
                'accent': 'e8710a',
                'background': 'ffffff',
                'text_primary': '1a1a1a',
                'chart_series': ['2B6CB0', 'ED8936', '38A169', 'E53E3E']
            },
            'typography': {
                'heading_font': 'Inter',
                'body_font': 'Inter'
            }
        }
        tokens = extract_style_tokens(style_guide)
        assert tokens['primary_color'] == '#1a73e8'
        assert tokens['font_family'] == 'Inter'
        assert len(tokens['chart_series']) == 4
        assert tokens['chart_series'][0] == '#2B6CB0'

    def test_extract_style_tokens_defaults(self):
        from src.smartart_svg.tokens import extract_style_tokens
        tokens = extract_style_tokens({})
        assert tokens['primary_color'] == '#1a73e8'
        assert tokens['font_family'] == 'sans-serif'

    def test_resolve_text_colour_good_contrast(self):
        from src.smartart_svg.tokens import resolve_text_colour
        # White text on dark background — good contrast
        result = resolve_text_colour('#1a1a1a', '#ffffff', None)
        assert result == '#ffffff'

    def test_resolve_text_colour_bad_contrast_fallback(self):
        from src.smartart_svg.tokens import resolve_text_colour
        # Similar colours — bad contrast, should fallback to white or black
        result = resolve_text_colour('#2B6CB0', '#3B7CC0', None)
        assert result in ('#ffffff', '#000000')

    def test_contrast_ratio_calculation(self):
        from src.smartart_svg.tokens import _contrast_ratio
        # Black on white should be ~21:1
        ratio = _contrast_ratio('#000000', '#ffffff')
        assert ratio > 20


class TestContainerEngine:
    def test_container_split_grid(self):
        from src.smartart_svg.engine import Container
        c = Container(0, 0, 1000, 800, padding=10)
        cells = c.split_grid(2, 2, gap=10)
        assert len(cells) == 4
        for cell in cells:
            assert cell.x >= 0
            assert cell.y >= 0
            assert cell.x + cell.width <= 1000
            assert cell.y + cell.height <= 800

    def test_container_split_horizontal(self):
        from src.smartart_svg.engine import Container
        c = Container(0, 0, 1000, 500, padding=0)
        parts = c.split_horizontal([1, 2, 1], gap=10)
        assert len(parts) == 3
        assert parts[1].width > parts[0].width

    def test_container_split_vertical(self):
        from src.smartart_svg.engine import Container
        c = Container(0, 0, 500, 1000, padding=0)
        parts = c.split_vertical([1, 4], gap=10)
        assert len(parts) == 2
        assert parts[1].height > parts[0].height

    def test_container_center_point(self):
        from src.smartart_svg.engine import Container
        c = Container(100, 200, 300, 400, padding=0)
        cx, cy = c.center_point()
        assert cx == 250  # 100 + 300/2
        assert cy == 400  # 200 + 400/2

    def test_fit_text_reduces_font_size(self):
        from src.smartart_svg.engine import Container
        c = Container(0, 0, 100, 30, padding=0)
        fitted = c.fit_text("A very long text that cannot fit at large size", font_size=48, max_lines=1)
        assert fitted.font_size < 48
        assert fitted.font_size >= 10  # minimum readable

    def test_fit_text_preserves_size_when_fits(self):
        from src.smartart_svg.engine import Container
        c = Container(0, 0, 500, 100, padding=0)
        fitted = c.fit_text("Short", font_size=16, max_lines=1)
        assert fitted.font_size == 16
        assert fitted.overflow is False

    def test_split_grid_single_cell(self):
        from src.smartart_svg.engine import Container
        c = Container(0, 0, 400, 400, padding=0)
        cells = c.split_grid(1, 1, gap=0)
        assert len(cells) == 1
        assert cells[0].width == 400
        assert cells[0].height == 400
