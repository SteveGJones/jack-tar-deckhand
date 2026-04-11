"""Chart quality QA checks.

Implements AP-22 (Poor Data-Ink Ratio).

Detection algorithms from: research/07-qa-heuristics-anti-patterns.md
"""

from ..config import QA_CONFIG

NSMAP_C = {
    'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
}


def check_chart_junk(slide, slide_number, config=None):
    """AP-22: Flag charts with 3D effects, heavy gridlines, or excessive decoration."""
    issues = []
    for shape in slide.shapes:
        if hasattr(shape, 'has_chart') and shape.has_chart:
            chart_xml = shape.chart._element
            view3D = chart_xml.find('.//c:view3D', NSMAP_C)
            if view3D is not None:
                issues.append({
                    'slide_number': slide_number,
                    'severity': 'warning',
                    'category': 'consistency',
                    'description': '3D chart effects detected — reduces data-ink ratio',
                    'suggested_fix': 'Remove 3D effects for a cleaner chart.',
                    'affected_element': shape.name,
                    'auto_fixable': True,
                })
            minor_gridlines = chart_xml.findall('.//c:minorGridlines', NSMAP_C)
            if minor_gridlines:
                issues.append({
                    'slide_number': slide_number,
                    'severity': 'info',
                    'category': 'consistency',
                    'description': 'Minor gridlines detected — consider removing for cleaner chart',
                    'suggested_fix': 'Remove minor gridlines. Use direct labelling instead.',
                    'affected_element': shape.name,
                    'auto_fixable': True,
                })
    return issues
