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
        # 1-3 node flowcharts use Mermaid LR (which fits a wide horizontal zone)
        from src.smartart_extractor import extract
        slide = {
            'slide_number': 5,
            'headline': 'Our Process',
            'body_points': ['Research', 'Design', 'Build']
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

    def test_extract_routes_4plus_flowcharts_to_custom_svg(self):
        # 4+ node flowcharts get re-routed to custom_svg for a better aspect ratio
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
        assert result['engine'] == 'custom_svg'
        assert result['graphic_type'] == 'flowchart'
        assert 'nodes' in result['data']
        assert len(result['data']['nodes']) == 4

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

    def test_extract_vega_lite_prefers_inline_data_over_body_points(self):
        """Issue #20 — when slide.data.inline_data is present, the dispatcher
        must use it and IGNORE body_points for vega_lite. This guards the
        refactor at smartart_extractor.py:843 against future regressions."""
        from src.smartart_extractor import extract
        # body_points would parse to 3 categories via extract_series_data
        body_points = ['Phase 1: 100', 'Phase 2: 200', 'Phase 3: 300']
        # inline_data has DIFFERENT data — 5 categories with different values
        inline_data = {
            'series': [
                {'label': 'Q1', 'value': 50},
                {'label': 'Q2', 'value': 75},
                {'label': 'Q3', 'value': 110},
                {'label': 'Q4', 'value': 160},
                {'label': 'Q5', 'value': 220},
            ]
        }
        slide = {
            'slide_number': 7,
            'headline': 'Revenue by Quarter',
            'body_points': body_points,
            'data': {'inline_data': inline_data},
        }
        selection = {
            'slide_number': 7,
            'graphic_type': 'bar_chart',
            'enrichment_tier': 'pure_programmatic',
            'engine': 'vega_lite',
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'text_primary': '1a1a1a', 'chart_series': []},
            'typography': {'body_font': 'Inter', 'heading_font': 'Inter'},
        }
        result = extract(slide, selection, style_guide)
        assert result['engine'] == 'vega_lite'
        assert result['validation_status'] == 'valid'
        # inline_data won — result reflects Q1-Q5, not Phase 1-3
        vega_values = result['data']['spec']['data']['values']
        labels_in_result = [v['label'] for v in vega_values]
        assert 'Q1' in labels_in_result
        assert 'Phase 1' not in labels_in_result
        assert len(vega_values) == 5  # not 3 from body_points

    def test_extract_matplotlib_prefers_inline_data_over_body_points(self):
        """Issue #20 — when slide.data.inline_data is present, the dispatcher
        must use it and IGNORE body_points for matplotlib. This guards the
        refactor at smartart_extractor.py:846 against future regressions."""
        from src.smartart_extractor import extract
        # body_points would parse to 2 labels/values via extract_series_data
        body_points = ['Alpha: 10', 'Beta: 20']
        # inline_data has DIFFERENT data — 4 entries with different labels
        inline_data = {
            'series': [
                {'label': 'Jan', 'value': 500},
                {'label': 'Feb', 'value': 600},
                {'label': 'Mar', 'value': 700},
                {'label': 'Apr', 'value': 800},
            ]
        }
        slide = {
            'slide_number': 8,
            'headline': 'Monthly Spend',
            'body_points': body_points,
            'data': {'inline_data': inline_data},
        }
        selection = {
            'slide_number': 8,
            'graphic_type': 'bar_chart',
            'enrichment_tier': 'pure_programmatic',
            'engine': 'matplotlib',
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'text_primary': '1a1a1a', 'chart_series': []},
            'typography': {'body_font': 'Inter', 'heading_font': 'Inter'},
        }
        result = extract(slide, selection, style_guide)
        assert result['engine'] == 'matplotlib'
        assert result['validation_status'] == 'valid'
        # inline_data won — result reflects Jan-Apr, not Alpha/Beta
        labels = result['data']['data']['labels']
        assert 'Jan' in labels
        assert 'Alpha' not in labels
        assert len(labels) == 4  # not 2 from body_points

    def test_extract_custom_svg_prefers_inline_data_over_body_points(self):
        """Issue #20 — when slide.data.inline_data is present, the dispatcher
        must use it and IGNORE body_points for custom_svg. This guards the
        refactor at smartart_extractor.py:841 against future regressions."""
        from src.smartart_extractor import extract
        # body_points would parse to a SWOT with the standard four quadrant labels
        body_points = [
            'Strengths: Brand, Team',
            'Weaknesses: Scale',
            'Opportunities: AI growth',
            'Threats: Regulation',
        ]
        # inline_data has DIFFERENT quadrant labels — custom labels, not SWOT defaults
        inline_data = {
            'quadrants': [
                {'label': 'Pillar A', 'items': ['Item1', 'Item2']},
                {'label': 'Pillar B', 'items': ['Item3']},
                {'label': 'Pillar C', 'items': ['Item4']},
                {'label': 'Pillar D', 'items': ['Item5', 'Item6']},
            ]
        }
        slide = {
            'slide_number': 9,
            'headline': 'Strategic Pillars',
            'body_points': body_points,
            'data': {'inline_data': inline_data},
        }
        selection = {
            'slide_number': 9,
            'graphic_type': 'swot',
            'enrichment_tier': 'pure_programmatic',
            'engine': 'custom_svg',
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0', 'ED8936', '38A169', 'E53E3E']},
            'typography': {'body_font': 'Inter', 'heading_font': 'Inter'},
        }
        result = extract(slide, selection, style_guide)
        assert result['engine'] == 'custom_svg'
        assert result['validation_status'] == 'valid'
        # inline_data won — quadrant labels are Pillar A-D, not Strengths/Weaknesses etc.
        quadrant_labels = [q['label'] for q in result['data']['quadrants']]
        assert 'Pillar A' in quadrant_labels
        assert 'Strengths' not in quadrant_labels
        assert len(quadrant_labels) == 4


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


class TestTimelineExtractorIssue49:
    """Issue #49 Defect 3: _extract_timeline must preserve the 'date' key from dict inputs."""

    def test_preserves_date_key_from_dict_input(self):
        """When body_points contains dicts with a 'date' key, the key must reach the stage."""
        from src.smartart_extractor import _extract_timeline  # type: ignore[attr-defined]
        body_points = [
            {'date': 'Q1 2026', 'label': 'Kickoff', 'description': 'Project starts'},
            {'date': 'Q2 2026', 'label': 'Design', 'description': 'Architecture'},
            {'label': 'Launch', 'description': 'No date'},
        ]
        result = _extract_timeline(body_points)
        stages = result['stages']
        assert stages[0]['date'] == 'Q1 2026'
        assert stages[1]['date'] == 'Q2 2026'
        # Stage without 'date' key must not have a 'date' key injected
        assert 'date' not in stages[2]

    def test_string_input_still_works(self):
        """Colon-split string format must still produce valid stages (no regression)."""
        from src.smartart_extractor import _extract_timeline  # type: ignore[attr-defined]
        body_points = [
            'Q1 2026: Research phase',
            'Q2 2026: Design phase',
        ]
        result = _extract_timeline(body_points)
        stages = result['stages']
        assert stages[0]['label'] == 'Q1 2026'
        assert stages[0]['description'] == 'Research phase'
        assert stages[1]['label'] == 'Q2 2026'
        assert stages[1]['description'] == 'Design phase'
        # No 'date' key in string-input output (date is folded into label)
        assert 'date' not in stages[0]
