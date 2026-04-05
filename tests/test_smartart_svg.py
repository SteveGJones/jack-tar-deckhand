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
        assert fitted.font_size >= 12  # minimum readable

    def test_fit_text_preserves_size_when_fits(self):
        from src.smartart_svg.engine import Container
        c = Container(0, 0, 500, 100, padding=0)
        fitted = c.fit_text("Short", font_size=16, max_lines=1)
        assert fitted.font_size == 16
        assert fitted.overflow is False

    def test_fit_text_never_below_12px(self):
        from src.smartart_svg.engine import Container
        c = Container(0, 0, 50, 20, padding=0)
        fitted = c.fit_text("This text absolutely cannot fit", font_size=24, max_lines=1)
        assert fitted.font_size >= 12
        assert fitted.overflow is True

    def test_fit_text_recommended_min(self):
        from src.smartart_svg.engine import Container
        c = Container(0, 0, 200, 30, padding=0)
        fitted = c.fit_text("Medium length text here", font_size=16, max_lines=1, recommended_min=14)
        assert fitted.font_size >= 12

    def test_split_grid_single_cell(self):
        from src.smartart_svg.engine import Container
        c = Container(0, 0, 400, 400, padding=0)
        cells = c.split_grid(1, 1, gap=0)
        assert len(cells) == 1
        assert cells[0].width == 400
        assert cells[0].height == 400


class TestSwotLayout:
    def test_renders_4_quadrants(self):
        from src.smartart_svg.layouts.swot import render_swot
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "quadrants": [
                {"label": "Strengths", "position": "top_left", "items": ["Brand", "Team"]},
                {"label": "Weaknesses", "position": "top_right", "items": ["Scale"]},
                {"label": "Opportunities", "position": "bottom_left", "items": ["AI"]},
                {"label": "Threats", "position": "bottom_right", "items": ["Regulation"]}
            ]
        }
        style = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a', 'chart_series': ['2B6CB0', 'ED8936', '38A169', 'E53E3E']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 1920, 1080, padding=40)
        svg = render_swot(data, c, tokens)
        assert '<svg' not in svg  # layout returns fragment, not full doc
        assert 'Strengths' in svg
        assert 'Weaknesses' in svg
        assert 'Brand' in svg


class TestFeatureMatrixLayout:
    def test_renders_grid(self):
        from src.smartart_svg.layouts.feature_matrix import render_feature_matrix
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "columns": ["Feature A", "Feature B"],
            "rows": [
                {"label": "Product 1", "values": [True, False]},
                {"label": "Product 2", "values": [True, True]}
            ]
        }
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 1920, 1080, padding=40)
        svg = render_feature_matrix(data, c, tokens)
        assert 'Feature A' in svg
        assert 'Product 1' in svg


class TestVennLayout:
    def test_renders_2_circles(self):
        from src.smartart_svg.layouts.venn import render_venn
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "sets": [
                {"label": "Set A", "items": ["Only A"]},
                {"label": "Set B", "items": ["Only B"]}
            ],
            "intersection": {"items": ["Shared"]}
        }
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0', 'ED8936']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 1920, 1080, padding=40)
        svg = render_venn(data, c, tokens)
        assert '<circle' in svg
        assert 'Set A' in svg
        assert 'Shared' in svg


class TestTimelineLayout:
    def test_renders_stages(self):
        from src.smartart_svg.layouts.timeline import render_timeline
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "stages": [
                {"label": "Q1 2025", "description": "Research"},
                {"label": "Q2 2025", "description": "Design"},
                {"label": "Q3 2025", "description": "Build"}
            ]
        }
        style = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a', 'chart_series': ['2B6CB0']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 1920, 1080, padding=40)
        svg = render_timeline(data, c, tokens)
        assert 'Q1 2025' in svg
        assert 'Research' in svg


class TestPipelineFunnelLayout:
    def test_renders_stages(self):
        from src.smartart_svg.layouts.pipeline_funnel import render_pipeline_funnel
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "stages": [
                {"label": "Leads", "value": 1000},
                {"label": "Qualified", "value": 500},
                {"label": "Proposals", "value": 200},
                {"label": "Closed", "value": 50}
            ]
        }
        style = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a', 'chart_series': ['2B6CB0']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 1920, 1080, padding=40)
        svg = render_pipeline_funnel(data, c, tokens)
        assert 'Leads' in svg
        assert 'Closed' in svg


class TestRenderCustomSvgPublicAPI:
    def test_renders_swot_as_full_document(self):
        from src.smartart_svg import render_custom_svg
        spec = {
            'graphic_type': 'swot',
            'data': {
                'quadrants': [
                    {'label': 'S', 'position': 'top_left', 'items': ['a']},
                    {'label': 'W', 'position': 'top_right', 'items': ['b']},
                    {'label': 'O', 'position': 'bottom_left', 'items': ['c']},
                    {'label': 'T', 'position': 'bottom_right', 'items': ['d']}
                ]
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a', 'chart_series': ['2B6CB0', 'ED8936', '38A169', 'E53E3E']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        result = render_custom_svg(spec, style_guide)
        assert '<svg' in result
        assert '<title>' in result
        assert '</svg>' in result

    def test_raises_for_unsupported_type(self):
        from src.smartart_svg import render_custom_svg
        spec = {'graphic_type': 'unsupported', 'data': {}}
        with pytest.raises(ValueError, match="Unsupported graphic type"):
            render_custom_svg(spec, {})


class TestGanttLayout:
    def test_renders_gantt_chart(self):
        from src.smartart_svg.layouts.gantt import render_gantt
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "tasks": [
                {"label": "Research", "start": "2026-01-01", "end": "2026-02-15"},
                {"label": "Design", "start": "2026-02-01", "end": "2026-03-15"},
                {"label": "Build", "start": "2026-03-01", "end": "2026-05-01"},
            ]
        }
        style = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a', 'chart_series': ['2B6CB0', 'ED8936', '38A169']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_gantt(data, c, tokens)
        assert 'Research' in svg
        assert 'Design' in svg
        assert 'Build' in svg
        assert '<rect' in svg

    def test_gantt_single_task(self):
        from src.smartart_svg.layouts.gantt import render_gantt
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "tasks": [{"label": "Solo Task", "start": "2026-01-01", "end": "2026-06-01"}]
        }
        style = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a'},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_gantt(data, c, tokens)
        assert 'Solo Task' in svg

    def test_gantt_empty(self):
        from src.smartart_svg.layouts.gantt import render_gantt
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {"tasks": []}
        style = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a'},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_gantt(data, c, tokens)
        assert 'Empty Gantt chart' in svg


class TestVennOverlap:
    def test_exclusive_regions_visible(self):
        """Each set's exclusive region should be clearly visible."""
        from src.smartart_svg.layouts.venn import render_venn
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        import re
        data = {
            "sets": [
                {"label": "Set A", "items": ["Only A1", "Only A2", "Only A3"]},
                {"label": "Set B", "items": ["Only B1", "Only B2"]}
            ],
            "intersection": {"items": ["Shared"]}
        }
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0', 'ED8936']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_venn(data, c, tokens)
        circles = re.findall(r'<circle cx="([\d.]+)"', svg)
        assert len(circles) >= 2
        left_cx = float(circles[0])
        right_cx = float(circles[1])
        radii = re.findall(r'r="([\d.]+)"', svg)
        r = float(radii[0])
        separation = right_cx - left_cx
        overlap = 2 * r - separation
        assert overlap < r * 1.4, f"Overlap {overlap:.1f} too large for radius {r:.1f}"
        assert overlap > 0, "Circles should overlap"

    def test_no_intersection_minimal_overlap(self):
        """With no shared items, circles should barely overlap."""
        from src.smartart_svg.layouts.venn import render_venn
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        import re
        data = {
            "sets": [
                {"label": "A", "items": ["A1", "A2"]},
                {"label": "B", "items": ["B1", "B2"]}
            ],
            "intersection": {"items": []}
        }
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0', 'ED8936']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_venn(data, c, tokens)
        circles = re.findall(r'<circle cx="([\d.]+)"', svg)
        radii = re.findall(r'r="([\d.]+)"', svg)
        r = float(radii[0])
        separation = float(circles[1]) - float(circles[0])
        overlap = 2 * r - separation
        assert overlap < r * 0.5, f"Should have minimal overlap with no shared items"

    def test_all_labels_present(self):
        from src.smartart_svg.layouts.venn import render_venn
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "sets": [
                {"label": "Alpha", "items": ["Exclusive1"]},
                {"label": "Beta", "items": ["Exclusive2"]}
            ],
            "intersection": {"items": ["Common"]}
        }
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0', 'ED8936']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_venn(data, c, tokens)
        assert 'Alpha' in svg
        assert 'Beta' in svg
        assert 'Exclusive1' in svg
        assert 'Exclusive2' in svg
        assert 'Common' in svg


class TestFeatureMatrixOverflow:
    def test_many_columns_truncated(self):
        from src.smartart_svg.layouts.feature_matrix import render_feature_matrix
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        columns = [f"Feature {chr(65+i)}" for i in range(10)]
        rows = [{"label": "Product 1", "values": [True] * 10}]
        data = {"columns": columns, "rows": rows}
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_feature_matrix(data, c, tokens)
        assert 'Feature A' in svg
        assert '...' in svg or '+' in svg

    def test_few_columns_all_shown(self):
        from src.smartart_svg.layouts.feature_matrix import render_feature_matrix
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "columns": ["Speed", "Cost"],
            "rows": [{"label": "Option A", "values": [True, False]}]
        }
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_feature_matrix(data, c, tokens)
        assert 'Speed' in svg
        assert 'Cost' in svg
        assert '...' not in svg
