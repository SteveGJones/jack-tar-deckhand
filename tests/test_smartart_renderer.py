"""Tests for SmartArt renderer — engine dispatch, CLI calls, manifest."""

import os
import json
import tempfile
import pytest


class TestRenderCustomSvgEngine:
    def test_renders_swot_to_svg_file(self):
        from src.smartart_renderer import render_custom_svg_engine
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
        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_custom_svg_engine(spec, style_guide, tmpdir)
            assert result.endswith('.svg')
            assert os.path.exists(result)
            with open(result) as f:
                content = f.read()
            assert '<svg' in content


class TestRenderMermaid:
    def test_renders_flowchart_to_png(self):
        """render_mermaid() now returns a rasterised PNG, not SVG."""
        from src.smartart_renderer import render_mermaid
        spec = {
            'data': {
                'syntax': 'graph TD\n  A[Research] --> B[Design]\n  B --> C[Build]',
                'diagram_type': 'flowchart'
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_mermaid(spec, style_guide, tmpdir)
            assert result.endswith('.png'), f"Expected PNG, got {result}"
            assert os.path.exists(result)
            assert os.path.getsize(result) > 100


class TestRenderVegaLite:
    def test_renders_bar_chart_to_svg(self):
        from src.smartart_renderer import render_vega_lite
        spec = {
            'data': {
                'spec': {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "mark": "bar",
                    "encoding": {
                        "x": {"field": "label", "type": "ordinal"},
                        "y": {"field": "value", "type": "quantitative"}
                    },
                    "data": {"values": [
                        {"label": "Q1", "value": 120},
                        {"label": "Q2", "value": 150}
                    ]}
                }
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_vega_lite(spec, style_guide, tmpdir)
            assert result.endswith('.svg')
            assert os.path.exists(result)


class TestBuildManifestEntry:
    def test_builds_correct_entry(self):
        from src.smartart_renderer import build_manifest_entry
        entry = build_manifest_entry(
            slide_number=5,
            graphic_type='flowchart',
            engine='mermaid',
            enrichment_tier='pure_programmatic',
            file_path='./tmp/deck/smartart/slide-5-flowchart.png',
            svg_path='./tmp/deck/smartart/slide-5-flowchart.svg',
            dimensions={'width': 1920, 'height': 1080},
            alt_text='Flowchart showing process',
            node_count=4
        )
        assert entry['smartart_id'] == 'sa-slide-5-flowchart'
        assert entry['slide_number'] == 5
        assert entry['engine_used'] == 'mermaid'
        assert entry['status'] == 'rendered'
        assert entry['dimensions']['width'] == 1920
        assert entry['node_count'] == 4

    def test_manifest_entry_validates_against_schema(self):
        import jsonschema
        from src.smartart_renderer import build_manifest_entry

        schema_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'schemas', 'smartart_manifest.schema.json')
        with open(schema_path) as f:
            schema = json.load(f)

        entry = build_manifest_entry(
            slide_number=3, graphic_type='swot', engine='custom_svg',
            enrichment_tier='pure_programmatic',
            file_path='./smartart/slide-3.png', svg_path='./smartart/slide-3.svg',
            dimensions={'width': 1920, 'height': 1080}, alt_text='SWOT diagram'
        )
        doc = {"graphics": [entry]}
        jsonschema.validate(doc, schema)


class TestVegaLiteDimensions:
    def test_vega_lite_svg_is_landscape(self):
        """Vega-Lite SVGs must be landscape, not portrait."""
        from src.smartart_renderer import render_vega_lite
        import re
        spec = {
            'data': {
                'spec': {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "mark": "bar",
                    "encoding": {
                        "x": {"field": "label", "type": "ordinal"},
                        "y": {"field": "value", "type": "quantitative"}
                    },
                    "data": {"values": [
                        {"label": "A", "value": 10},
                        {"label": "B", "value": 20}
                    ]}
                }
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            svg_path = render_vega_lite(spec, style_guide, tmpdir)
            with open(svg_path) as f:
                svg = f.read()
            # Verify the spec included width/height by checking the VL spec JSON was written
            spec_files = [f for f in os.listdir(tmpdir) if f.startswith('vl-spec')]
            assert len(spec_files) > 0
            with open(os.path.join(tmpdir, spec_files[0])) as f:
                written_spec = json.load(f)
            assert written_spec.get('width') == 1600
            assert written_spec.get('height') == 900
            assert written_spec.get('autosize', {}).get('type') == 'fit'


class TestMermaidFixes:
    def test_mermaid_returns_png(self):
        """Mermaid now returns PNG (rasterised) not SVG."""
        from src.smartart_renderer import render_mermaid
        spec = {
            'data': {
                'syntax': 'graph TD\n  A[Start] --> B[End]',
                'diagram_type': 'flowchart'
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result_path = render_mermaid(spec, style_guide, tmpdir)
            assert result_path.endswith('.png'), f"Expected PNG, got {result_path}"
            assert os.path.exists(result_path)
            assert os.path.getsize(result_path) > 100

    def test_mermaid_svg_source_preserved(self):
        """SVG source should be kept alongside the PNG."""
        from src.smartart_renderer import render_mermaid
        spec = {
            'data': {
                'syntax': 'graph TD\n  A[Start] --> B[End]',
                'diagram_type': 'flowchart'
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = render_mermaid(spec, style_guide, tmpdir)
            svg_files = [f for f in os.listdir(tmpdir) if f.endswith('.svg')]
            assert len(svg_files) >= 1, "SVG source should exist"


class TestRender:
    def test_render_dispatches_custom_svg(self):
        from src.smartart_renderer import render
        spec = {
            'slide_number': 5,
            'graphic_type': 'swot',
            'engine': 'custom_svg',
            'enrichment_tier': 'pure_programmatic',
            'data': {
                'quadrants': [
                    {'label': 'S', 'position': 'top_left', 'items': ['a']},
                    {'label': 'W', 'position': 'top_right', 'items': ['b']},
                    {'label': 'O', 'position': 'bottom_left', 'items': ['c']},
                    {'label': 'T', 'position': 'bottom_right', 'items': ['d']}
                ]
            },
            'style_tokens': {'primary_color': '#1a73e8', 'font_family': 'Inter'},
            'comparator_engines': []
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a', 'chart_series': ['2B6CB0', 'ED8936', '38A169', 'E53E3E']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            entry = render(spec, style_guide, 'draft', tmpdir)
            assert entry['smartart_id'].startswith('sa-slide-5')
            assert entry['status'] in ('rendered', 'compared')
            assert entry['engine_used'] == 'custom_svg'
