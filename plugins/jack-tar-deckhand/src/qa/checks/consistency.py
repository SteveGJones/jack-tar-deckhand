"""Cross-slide consistency QA checks.

Implements AP-03 (Font Families), AP-04 (Bullet Styles),
AP-15 (Consecutive Bullet Slides), AP-18 (Heading Sizes),
AP-23 (Branding Consistency).

Detection algorithms from: research/07-qa-heuristics-anti-patterns.md
"""

from collections import Counter
from ..config import QA_CONFIG


def check_font_families(presentation, config=None):
    """AP-03: Check that the deck uses no more than 2 font families."""
    cfg = config or QA_CONFIG
    max_families = cfg['max_font_families']
    font_families = set()
    for slide in presentation.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        if run.font.name:
                            font_families.add(run.font.name)
    issues = []
    if len(font_families) > max_families:
        issues.append({
            'slide_number': 0,
            'severity': 'warning',
            'category': 'consistency',
            'description': f'Deck uses {len(font_families)} font families (max {max_families}): {", ".join(sorted(font_families))}',
            'suggested_fix': 'Limit to 2 font families: one for headings, one for body.',
            'affected_element': 'deck',
            'auto_fixable': False,
        })
    return issues


def check_bullet_consistency(presentation, config=None):
    """AP-04: Check for inconsistent bullet characters across the deck."""
    bullet_styles = []
    for slide in presentation.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    pPr = para._pPr
                    if pPr is not None:
                        buChar = pPr.find(
                            './/{http://schemas.openxmlformats.org/drawingml/2006/main}buChar')
                        if buChar is not None:
                            bullet_styles.append({
                                'char': buChar.get('char'),
                                'level': para.level,
                            })

    level_chars = {}
    issues = []
    for style in bullet_styles:
        level = style['level']
        char = style['char']
        if level not in level_chars:
            level_chars[level] = char
        elif level_chars[level] != char:
            issues.append({
                'slide_number': 0,
                'severity': 'warning',
                'category': 'consistency',
                'description': f'Inconsistent bullet at level {level}: "{char}" vs "{level_chars[level]}"',
                'suggested_fix': 'Standardise bullet characters per level via slide master.',
                'affected_element': 'deck',
                'auto_fixable': True,
            })
            break  # Report once per inconsistency type
    return issues


def check_consecutive_bullet_slides(presentation, config=None):
    """AP-15: Check for too many consecutive bullet-heavy slides."""
    cfg = config or QA_CONFIG
    max_consecutive = cfg['max_consecutive_bullet_slides']
    issues = []
    consecutive = 0
    for i, slide in enumerate(presentation.slides):
        is_bullet_heavy = False
        for shape in slide.shapes:
            if shape.has_text_frame:
                bullet_count = sum(
                    1 for p in shape.text_frame.paragraphs
                    if p.text.strip() and p._pPr is not None
                )
                if bullet_count >= 4:
                    is_bullet_heavy = True
                    break
        if is_bullet_heavy:
            consecutive += 1
        else:
            consecutive = 0
        if consecutive >= max_consecutive:
            issues.append({
                'slide_number': i + 1,
                'severity': 'warning',
                'category': 'consistency',
                'description': f'{consecutive} consecutive bullet-heavy slides ending at slide {i + 1}',
                'suggested_fix': 'Intersperse with visual slides (images, diagrams, quotes).',
                'affected_element': 'slide',
                'auto_fixable': False,
            })
    return issues


def check_heading_consistency(presentation, config=None):
    """AP-18: Check that title placeholders use consistent font sizes."""
    cfg = config or QA_CONFIG
    max_variance = cfg['max_heading_variance_pt']
    title_sizes = []
    for slide in presentation.slides:
        for shape in slide.shapes:
            try:
                is_title_ph = (shape.placeholder_format is not None and
                               shape.placeholder_format.idx == 0)
            except ValueError:
                is_title_ph = False
            if is_title_ph:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        if run.font.size:
                            title_sizes.append(run.font.size.pt)
    issues = []
    if title_sizes:
        most_common = Counter(title_sizes).most_common(1)[0][0]
        outliers = [s for s in title_sizes if abs(s - most_common) > max_variance]
        if outliers:
            issues.append({
                'slide_number': 0,
                'severity': 'warning',
                'category': 'consistency',
                'description': f'Title sizes vary: most common {most_common}pt but found {set(outliers)}pt',
                'suggested_fix': 'Standardise heading sizes via slide master.',
                'affected_element': 'deck',
                'auto_fixable': True,
            })
    return issues


def check_branding_consistency(presentation, config=None):
    """AP-23: Check that logos appear consistently across slides."""
    issues = []
    logo_positions = []

    for i, slide in enumerate(presentation.slides):
        for shape in slide.shapes:
            if 'logo' in shape.name.lower():
                logo_positions.append({
                    'slide': i + 1,
                    'left': shape.left, 'top': shape.top,
                    'width': shape.width, 'height': shape.height,
                })

    if logo_positions and len(logo_positions) >= 2:
        ref = logo_positions[0]
        for pos in logo_positions[1:]:
            if (abs(pos['left'] - ref['left']) > 914400 // 10 or
                abs(pos['top'] - ref['top']) > 914400 // 10):
                issues.append({
                    'slide_number': pos['slide'],
                    'severity': 'info',
                    'category': 'consistency',
                    'description': f'Logo position varies between slide 1 and slide {pos["slide"]}',
                    'suggested_fix': 'Place logos on the slide master for consistent positioning.',
                    'affected_element': 'logo',
                    'auto_fixable': True,
                })
    return issues
