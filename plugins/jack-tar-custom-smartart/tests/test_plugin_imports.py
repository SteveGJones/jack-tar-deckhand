"""Verify jack-tar-custom-smartart modules load from plugin directory."""
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))


def test_smartart_svg_engine_imports():
    from src.smartart_svg.engine import Container
    assert Container is not None


def test_smartart_svg_primitives_imports():
    from src.smartart_svg.primitives import svg_rect, svg_text
    assert callable(svg_rect)
    assert callable(svg_text)


def test_smartart_svg_tokens_imports():
    from src.smartart_svg.tokens import extract_style_tokens
    assert callable(extract_style_tokens)


def test_all_svg_layouts_import():
    from src.smartart_svg.layouts import flowchart, decision_tree, timeline
    from src.smartart_svg.layouts import venn, swot, feature_matrix
    from src.smartart_svg.layouts import pipeline_funnel, radar_chart, gantt
    assert flowchart is not None
    assert gantt is not None


def test_render_chart_imports():
    from src.render_chart import render_chart
    assert callable(render_chart)


def test_smartart_renderer_imports():
    from src.smartart_renderer import render
    assert callable(render)
