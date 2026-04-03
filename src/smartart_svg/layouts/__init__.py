"""Layout registry — maps graphic_type to render function."""

from src.smartart_svg.layouts.swot import render_swot
from src.smartart_svg.layouts.feature_matrix import render_feature_matrix
from src.smartart_svg.layouts.venn import render_venn
from src.smartart_svg.layouts.timeline import render_timeline
from src.smartart_svg.layouts.pipeline_funnel import render_pipeline_funnel

LAYOUT_REGISTRY = {
    'swot': render_swot,
    'feature_matrix': render_feature_matrix,
    'venn': render_venn,
    'timeline': render_timeline,
    'pipeline_funnel': render_pipeline_funnel,
}
