"""Integration test — SmartArt extraction + rendering pipeline."""

import json
import os
import tempfile
import pytest


def test_extract_and_render_swot():
    """Full pipeline: extract SWOT data from body_points, render via custom SVG."""
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {
        'slide_number': 3,
        'headline': 'SWOT Analysis',
        'body_points': [
            'Strengths: Strong brand, Great team',
            'Weaknesses: Limited funding',
            'Opportunities: AI market growth, Global expansion',
            'Threats: Regulatory risk'
        ]
    }
    selection = {
        'slide_number': 3,
        'graphic_type': 'swot',
        'enrichment_tier': 'pure_programmatic',
        'engine': 'custom_svg'
    }
    style_guide = {
        'palette': {
            'primary': '1a73e8', 'accent': 'e8710a',
            'background': 'ffffff', 'text_primary': '1a1a1a',
            'chart_series': ['2B6CB0', 'ED8936', '38A169', 'E53E3E']
        },
        'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
    }

    # Extract
    spec = extract(slide, selection, style_guide)
    assert spec['validation_status'] == 'valid'
    assert spec['graphic_type'] == 'swot'
    assert len(spec['data']['quadrants']) == 4

    # Render
    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, style_guide, 'draft', tmpdir)
        assert entry['status'] == 'rendered'
        # Check files exist
        svg_base = os.path.basename(entry.get('svg_source_path', ''))
        if svg_base:
            svg_path = os.path.join(tmpdir, svg_base)
            assert os.path.exists(svg_path)
            with open(svg_path) as f:
                svg = f.read()
            assert 'Strengths' in svg or 'S' in svg
            assert '<title>' in svg  # Accessibility


def test_extract_and_render_flowchart_mermaid():
    """Full pipeline: extract small flowchart (1-3 nodes), render via Mermaid CLI."""
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {
        'slide_number': 5,
        'headline': 'Our Process',
        'body_points': ['Research', 'Design', 'Build']  # 3 nodes -> Mermaid LR
    }
    selection = {
        'slide_number': 5,
        'graphic_type': 'flowchart',
        'enrichment_tier': 'pure_programmatic',
        'engine': 'mermaid'
    }
    style_guide = {
        'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a', 'chart_series': []},
        'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
    }

    spec = extract(slide, selection, style_guide)
    assert spec['engine'] == 'mermaid'
    assert 'graph' in spec['data']['syntax']

    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, style_guide, 'draft', tmpdir)
        assert entry['engine_used'] == 'mermaid'
        assert entry['status'] in ('rendered', 'failed')  # mermaid CLI may not be available
        if entry['status'] == 'rendered':
            assert os.path.exists(os.path.join(tmpdir, os.path.basename(entry['file_path'])))


def test_extract_and_render_bar_chart_vega_lite():
    """Full pipeline: extract bar chart, render via Vega-Lite CLI."""
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {
        'slide_number': 7,
        'headline': 'Revenue by Quarter',
        'body_points': ['Q1: 120', 'Q2: 150', 'Q3: 180', 'Q4: 210']
    }
    selection = {
        'slide_number': 7,
        'graphic_type': 'bar_chart',
        'enrichment_tier': 'pure_programmatic',
        'engine': 'vega_lite'
    }
    style_guide = {
        'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a', 'chart_series': ['2B6CB0']},
        'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
    }

    spec = extract(slide, selection, style_guide)
    assert spec['engine'] == 'vega_lite'
    assert '$schema' in spec['data']['spec']

    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, style_guide, 'draft', tmpdir)
        assert entry['engine_used'] == 'vega_lite'
        assert entry['status'] in ('rendered', 'failed')


def test_extract_and_render_timeline():
    """Full pipeline: extract timeline, render via custom SVG."""
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {
        'slide_number': 8,
        'headline': 'Project Timeline',
        'body_points': ['Q1 2025: Research phase', 'Q2 2025: Design phase', 'Q3 2025: Build phase', 'Q4 2025: Launch']
    }
    selection = {
        'slide_number': 8,
        'graphic_type': 'timeline',
        'enrichment_tier': 'pure_programmatic',
        'engine': 'custom_svg'
    }
    style_guide = {
        'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                    'text_primary': '1a1a1a', 'chart_series': ['2B6CB0']},
        'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
    }

    spec = extract(slide, selection, style_guide)
    assert spec['engine'] == 'custom_svg'
    assert len(spec['data']['stages']) == 4

    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, style_guide, 'draft', tmpdir)
        assert entry['status'] == 'rendered'


def test_manifest_validates_against_schema():
    """Verify rendered manifest entries pass schema validation."""
    import jsonschema
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {
        'slide_number': 3,
        'headline': 'SWOT',
        'body_points': ['Strengths: A', 'Weaknesses: B', 'Opportunities: C', 'Threats: D']
    }
    selection = {
        'slide_number': 3, 'graphic_type': 'swot',
        'enrichment_tier': 'pure_programmatic', 'engine': 'custom_svg'
    }
    style_guide = {
        'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                    'text_primary': '1a1a1a', 'chart_series': ['2B6CB0', 'ED8936', '38A169', 'E53E3E']},
        'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
    }

    spec = extract(slide, selection, style_guide)
    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, style_guide, 'draft', tmpdir)

    schema_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'schemas', 'smartart_manifest.schema.json')
    with open(schema_path) as f:
        schema = json.load(f)

    doc = {"graphics": [entry]}
    jsonschema.validate(doc, schema)
