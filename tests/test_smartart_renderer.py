"""Tests for SmartArt renderer — engine dispatch, CLI calls, manifest."""

import os
import json
import tempfile
import pytest
from PIL import Image


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


class TestMermaidPngDirect:
    def test_mermaid_png_direct_has_content(self):
        """mmdc --outputFormat png should produce a non-blank PNG with text."""
        from src.smartart_renderer import render_mermaid
        spec = {
            'data': {
                'syntax': 'graph TD\n    A[Start] --> B[End]'
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'sans-serif'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_mermaid(spec, style_guide, tmpdir)
            assert result.endswith('.png')
            assert os.path.exists(result)
            # PNG should be non-trivial size — Puppeteer renders real content
            assert os.path.getsize(result) > 2000

    def test_mermaid_svg_source_preserved(self):
        """SVG source file should be kept alongside the PNG for debugging."""
        from src.smartart_renderer import render_mermaid
        spec = {
            'data': {
                'syntax': 'graph LR\n    A[Hello] --> B[World]'
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'sans-serif'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = render_mermaid(spec, style_guide, tmpdir)
            svg_path = png_path.replace('.png', '.svg')
            assert os.path.exists(svg_path), "SVG source should be preserved alongside PNG"


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


class TestPreAssemblyChecks:
    def test_pa01_rejects_zero_dimensions(self):
        from src.smartart_renderer import validate_svg_dimensions
        findings = validate_svg_dimensions('<svg width="0" height="0"></svg>', 5)
        assert any(f['severity'] == 'error' for f in findings)

    def test_pa01_accepts_valid_dimensions(self):
        from src.smartart_renderer import validate_svg_dimensions
        findings = validate_svg_dimensions(
            '<svg width="1600" height="900" viewBox="0 0 1600 900"></svg>', 5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0

    def test_pa01_rejects_bad_aspect(self):
        from src.smartart_renderer import validate_svg_dimensions
        findings = validate_svg_dimensions(
            '<svg width="400" height="800" viewBox="0 0 400 800"></svg>', 5)
        assert any('aspect' in f['description'].lower() for f in findings)

    def test_pa02_rejects_flowchart_no_text(self):
        from src.smartart_renderer import validate_svg_text_content
        findings = validate_svg_text_content(
            '<svg><rect/></svg>', 5, graphic_type='flowchart', node_count=4)
        assert any(f['severity'] == 'error' for f in findings)

    def test_pa02_accepts_with_text(self):
        from src.smartart_renderer import validate_svg_text_content
        svg = '<svg><text>A</text><text>B</text><text>C</text><text>D</text></svg>'
        findings = validate_svg_text_content(svg, 5, graphic_type='flowchart', node_count=4)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0

    def test_pa03_rejects_small_font(self):
        from src.smartart_renderer import validate_svg_font_sizes
        findings = validate_svg_font_sizes('<svg><text font-size="8">Tiny</text></svg>', 5)
        assert any(f['severity'] == 'error' for f in findings)

    def test_pa03_accepts_valid_font(self):
        from src.smartart_renderer import validate_svg_font_sizes
        findings = validate_svg_font_sizes('<svg><text font-size="14">OK</text></svg>', 5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0

    def test_pa04_rejects_blank_png(self):
        from src.smartart_renderer import validate_png_not_blank
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (100, 100), (255, 255, 255))
            img.save(f.name)
            findings = validate_png_not_blank(f.name, 5)
        assert any(f['severity'] == 'error' for f in findings)

    def test_pa04_accepts_content_png(self):
        from src.smartart_renderer import validate_png_not_blank
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (100, 100), (255, 255, 255))
            for x in range(20, 80):
                for y in range(20, 80):
                    img.putpixel((x, y), (30, 60, 90))
            img.save(f.name)
            findings = validate_png_not_blank(f.name, 5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0


class TestVegaLiteFontConfig:
    def test_axis_font_sizes_injected(self):
        """Vega-Lite spec should have axis/legend/title font sizes after render."""
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
                    "data": {"values": [{"label": "Q1", "value": 100}]}
                }
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            render_vega_lite(spec, style_guide, tmpdir)
            spec_files = [f for f in os.listdir(tmpdir) if f.startswith('vl-spec-')]
            assert len(spec_files) == 1
            with open(os.path.join(tmpdir, spec_files[0])) as f:
                written_spec = json.load(f)
            assert written_spec['config']['axis']['labelFontSize'] >= 14
            assert written_spec['config']['axis']['titleFontSize'] >= 16
            assert written_spec['config']['legend']['labelFontSize'] >= 14
            assert written_spec['config']['title']['fontSize'] >= 18

    def test_user_font_sizes_not_overwritten(self):
        """User-provided font sizes in the spec should be preserved."""
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
                    "data": {"values": [{"label": "Q1", "value": 100}]},
                    "config": {
                        "axis": {"labelFontSize": 20}
                    }
                }
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            render_vega_lite(spec, style_guide, tmpdir)
            spec_files = [f for f in os.listdir(tmpdir) if f.startswith('vl-spec-')]
            with open(os.path.join(tmpdir, spec_files[0])) as f:
                written_spec = json.load(f)
            # User's 20 should be preserved, not overwritten to 14
            assert written_spec['config']['axis']['labelFontSize'] == 20
