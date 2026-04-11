"""Animation QA checks.

Implements AP-21 (Excessive Animations).

Detection algorithms from: research/07-qa-heuristics-anti-patterns.md
"""

from lxml import etree
from ..config import QA_CONFIG

NSMAP_P = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'}


def check_excessive_animations(presentation, config=None):
    """AP-21: Check for too many different transition types."""
    cfg = config or QA_CONFIG
    max_types = cfg['max_transition_types']
    transition_types = set()

    for slide in presentation.slides:
        slide_xml = slide._element
        transition = slide_xml.find('.//p:transition', NSMAP_P)
        if transition is not None:
            for child in transition:
                transition_types.add(etree.QName(child).localname)

    issues = []
    if len(transition_types) > max_types:
        issues.append({
            'slide_number': 0,
            'severity': 'warning',
            'category': 'consistency',
            'description': f'{len(transition_types)} different transition types (max {max_types}): {", ".join(transition_types)}',
            'suggested_fix': 'Limit to 1-2 subtle transition types (Fade, Push).',
            'affected_element': 'deck',
            'auto_fixable': True,
        })
    return issues
