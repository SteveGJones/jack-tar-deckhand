"""Tests for SmartArt data extraction — content to engine-specific data."""

import pytest


class TestExtractGraphData:
    def test_extract_flowchart_from_sequential_points(self):
        from src.smartart_extractor import extract_graph_data
        body_points = ["Research the market", "Design the solution", "Build the product", "Launch to customers"]
        result = extract_graph_data(body_points, "flowchart")
        assert result['engine'] == 'mermaid'
        assert 'syntax' in result
        assert result['node_count'] == 4
        assert 'graph' in result['syntax']

    def test_extract_decision_tree(self):
        from src.smartart_extractor import extract_graph_data
        body_points = [
            "Is the talk persuasive? Yes: hook-body-callback-cta",
            "Is it problem-solving? Yes: situation-complication-resolution",
            "Is it historical? Yes: chronological",
        ]
        result = extract_graph_data(body_points, "decision_tree")
        assert result['engine'] == 'mermaid'
        syntax = result['syntax']
        # Top-down branching tree, not a sequential left-right flowchart
        assert syntax.startswith('graph TB')
        assert 'graph LR' not in syntax
        # Yes/No edge labels
        assert '-->|Yes|' in syntax
        assert '-->|No|' in syntax
        # Diamond question nodes and rectangle outcome leaves
        assert 'Q1{"Is the talk persuasive?"}' in syntax
        assert 'O1["hook-body-callback-cta"]' in syntax
        assert 'Q2{"Is it problem-solving?"}' in syntax
        assert 'O2["situation-complication-resolution"]' in syntax
        assert 'Q3{"Is it historical?"}' in syntax
        assert 'O3["chronological"]' in syntax
        # Yes branches go to outcomes; No branches cascade to the next question
        assert 'Q1 -->|Yes| O1' in syntax
        assert 'Q1 -->|No| Q2' in syntax
        assert 'Q2 -->|Yes| O2' in syntax
        assert 'Q2 -->|No| Q3' in syntax
        assert 'Q3 -->|Yes| O3' in syntax
        # Final question has no No branch (no further question to cascade to)
        assert 'Q3 -->|No|' not in syntax
        # node_count = questions + outcomes
        assert result['node_count'] == 6

    def test_extract_gantt_data(self):
        from src.smartart_extractor import extract_graph_data
        body_points = ["Research: Jan-Mar", "Design: Mar-May", "Build: May-Aug"]
        result = extract_graph_data(body_points, "gantt")
        assert result['engine'] == 'mermaid'
        assert 'gantt' in result['syntax']


class TestExtractSeriesData:
    def test_extract_bar_chart_vega_lite(self):
        from src.smartart_extractor import extract_series_data
        body_points = ["Q1: 120", "Q2: 150", "Q3: 180"]
        result = extract_series_data(body_points, "bar_chart")
        assert result['engine'] == 'vega_lite'
        assert '$schema' in result['spec']
        assert len(result['spec']['data']['values']) == 3

    def test_extract_bar_chart_matplotlib(self):
        from src.smartart_extractor import extract_series_data
        body_points = ["Q1: 120", "Q2: 150"]
        result = extract_series_data(body_points, "bar_chart", engine="matplotlib")
        assert result['engine'] == 'matplotlib'
        assert result['data']['labels'] == ['Q1', 'Q2']
        assert result['data']['values'] == [120, 150]

    def test_extract_line_chart(self):
        from src.smartart_extractor import extract_series_data
        body_points = ["Jan: 10", "Feb: 20", "Mar: 15"]
        result = extract_series_data(body_points, "line_chart")
        assert result['engine'] == 'vega_lite'
        assert result['spec']['mark'] in ('line', {'type': 'line'})


class TestExtractSpatialData:
    def test_extract_swot(self):
        from src.smartart_extractor import extract_spatial_data
        body_points = [
            "Strengths: Brand recognition, Strong team",
            "Weaknesses: Limited scale",
            "Opportunities: AI market growth",
            "Threats: Regulatory changes"
        ]
        result = extract_spatial_data(body_points, "swot")
        assert result['engine'] == 'custom_svg'
        assert len(result['data']['quadrants']) == 4
        assert result['data']['quadrants'][0]['label'] == 'Strengths'
        assert 'Brand recognition' in result['data']['quadrants'][0]['items']

    def test_extract_timeline(self):
        from src.smartart_extractor import extract_spatial_data
        body_points = ["Q1 2025: Research phase", "Q2 2025: Design phase", "Q3 2025: Build phase"]
        result = extract_spatial_data(body_points, "timeline")
        assert result['engine'] == 'custom_svg'
        assert len(result['data']['stages']) == 3
        assert result['data']['stages'][0]['label'] == 'Q1 2025'

    def test_extract_pipeline_funnel(self):
        from src.smartart_extractor import extract_spatial_data
        body_points = ["Leads: 1000", "Qualified: 500", "Proposals: 200", "Closed: 50"]
        result = extract_spatial_data(body_points, "pipeline_funnel")
        assert result['engine'] == 'custom_svg'
        assert len(result['data']['stages']) == 4
        assert result['data']['stages'][0]['value'] == 1000

    def test_extract_venn(self):
        from src.smartart_extractor import extract_spatial_data
        body_points = ["Set A: Design, Research", "Set B: Engineering, Research", "Shared: Research"]
        result = extract_spatial_data(body_points, "venn")
        assert result['engine'] == 'custom_svg'
        assert len(result['data']['sets']) >= 2

    def test_extract_feature_matrix(self):
        from src.smartart_extractor import extract_spatial_data
        body_points = ["Features: Speed, Cost, Quality", "Product A: Yes, No, Yes", "Product B: Yes, Yes, No"]
        result = extract_spatial_data(body_points, "feature_matrix")
        assert result['engine'] == 'custom_svg'
        assert 'columns' in result['data']
        assert 'rows' in result['data']


class TestExtractFunction:
    def test_extract_dispatches_to_mermaid(self):
        from src.smartart_extractor import extract
        slide = {
            'slide_number': 5,
            'headline': 'Our Process',
            'body_points': ['Research', 'Design', 'Build', 'Launch']
        }
        selection = {
            'slide_number': 5,
            'graphic_type': 'flowchart',
            'enrichment_tier': 'pure_programmatic',
            'engine': 'mermaid'
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'text_primary': '1a1a1a', 'chart_series': []},
            'typography': {'body_font': 'Inter', 'heading_font': 'Inter'}
        }
        result = extract(slide, selection, style_guide)
        assert result['slide_number'] == 5
        assert result['graphic_type'] == 'flowchart'
        assert result['engine'] == 'mermaid'
        assert result['validation_status'] == 'valid'
        assert 'graph' in result['data']['syntax']

    def test_extract_dispatches_to_custom_svg(self):
        from src.smartart_extractor import extract
        slide = {
            'slide_number': 3,
            'headline': 'SWOT Analysis',
            'body_points': [
                'Strengths: Brand', 'Weaknesses: Scale',
                'Opportunities: AI', 'Threats: Risk'
            ]
        }
        selection = {
            'slide_number': 3,
            'graphic_type': 'swot',
            'enrichment_tier': 'pure_programmatic',
            'engine': 'custom_svg'
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0', 'ED8936', '38A169', 'E53E3E']},
            'typography': {'body_font': 'Inter', 'heading_font': 'Inter'}
        }
        result = extract(slide, selection, style_guide)
        assert result['graphic_type'] == 'swot'
        assert result['engine'] == 'custom_svg'
        assert len(result['data']['quadrants']) == 4


class TestValidateSpec:
    def test_valid_mermaid_spec(self):
        from src.smartart_extractor import validate_spec
        spec = {
            'engine': 'mermaid',
            'data': {'syntax': 'graph TD\n  A --> B', 'node_count': 2},
            'graphic_type': 'flowchart'
        }
        valid, errors = validate_spec(spec)
        assert valid is True
        assert errors == []

    def test_missing_syntax_fails(self):
        from src.smartart_extractor import validate_spec
        spec = {
            'engine': 'mermaid',
            'data': {'node_count': 2},
            'graphic_type': 'flowchart'
        }
        valid, errors = validate_spec(spec)
        assert valid is False

    def test_valid_custom_svg_spec(self):
        from src.smartart_extractor import validate_spec
        spec = {
            'engine': 'custom_svg',
            'data': {'quadrants': [{'label': 'S', 'items': []}]},
            'graphic_type': 'swot'
        }
        valid, errors = validate_spec(spec)
        assert valid is True


class TestOverflow:
    def test_swot_truncates_long_items(self):
        from src.smartart_extractor import extract_spatial_data
        items = [f"Item {i}" for i in range(10)]
        body_points = [
            f"Strengths: {', '.join(items)}",
            "Weaknesses: One",
            "Opportunities: One",
            "Threats: One"
        ]
        result = extract_spatial_data(body_points, "swot")
        strengths = result['data']['quadrants'][0]
        assert len(strengths['items']) <= 5
