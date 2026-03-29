"""Structural QA checks — fast path, no rendering required.

Implements AP-01, AP-02, AP-05, AP-06, AP-09, AP-10, AP-11,
AP-14, AP-16, AP-17, AP-19, AP-20, AP-24.

Detection algorithms from: research/07-qa-heuristics-anti-patterns.md
"""

import re
from lxml import etree
from ..config import QA_CONFIG

NSMAP = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}

PLACEHOLDER_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r'click to add',
        r'lorem ipsum',
        r'\bXXX\b',
        r'\bTODO\b',
        r'\bTBD\b',
        r'\[insert\b',
        r'\[your .+?\]',
        r'placeholder',
        r'sample text',
        r'edit (this|here)',
        r'replace (this|with)',
        r'type (here|your)',
        r'add (your|text|title|subtitle|content)',
    ]
]

CTA_KEYWORDS = [
    'contact', 'email', 'questions', 'next steps', 'call to action',
    'thank you', 'thanks', 'get in touch', 'follow up', 'resources',
    'learn more', 'summary', 'key takeaways', 'conclusion',
]


def check_wall_of_text(slide, slide_number, config=None):
    """AP-01: Check for excessive word counts per text box and per slide."""
    cfg = config or QA_CONFIG
    max_per_box = cfg['max_words_per_textbox']
    max_per_slide = cfg['max_words_per_slide']
    issues = []
    slide_word_count = 0
    for shape in slide.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text.strip()
            word_count = len(text.split()) if text else 0
            slide_word_count += word_count
            if word_count > max_per_box:
                issues.append({
                    'slide_number': slide_number,
                    'severity': 'error',
                    'category': 'text_overflow',
                    'description': f'Text box has {word_count} words (max {max_per_box})',
                    'suggested_fix': 'Break content across multiple slides. Target 30 words or fewer per slide.',
                    'affected_element': shape.name,
                    'auto_fixable': False,
                })
    if slide_word_count > max_per_slide:
        issues.append({
            'slide_number': slide_number,
            'severity': 'error',
            'category': 'text_overflow',
            'description': f'Slide has {slide_word_count} total words (max {max_per_slide})',
            'suggested_fix': 'Split content into multiple slides.',
            'affected_element': 'slide',
            'auto_fixable': False,
        })
    return issues


def check_font_size(slide, slide_number, config=None):
    """AP-02: Check for font sizes below projection minimum."""
    cfg = config or QA_CONFIG
    min_body = cfg['min_font_size_body_pt']
    min_title = cfg['min_font_size_title_pt']
    issues = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            try:
                is_title = (shape.placeholder_format is not None and
                            shape.placeholder_format.idx in (0, 1))
            except ValueError:
                is_title = False
            threshold = min_title if is_title else min_body
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if run.font.size is not None:
                        size_pt = run.font.size.pt
                        if size_pt < threshold:
                            issues.append({
                                'slide_number': slide_number,
                                'severity': 'error',
                                'category': 'consistency',
                                'description': f'Font size {size_pt}pt below minimum {threshold}pt',
                                'suggested_fix': f'Increase font size to at least {threshold}pt.',
                                'affected_element': shape.name,
                                'auto_fixable': True,
                            })
    return issues


def check_orphan_widow(slide, slide_number, config=None):
    """AP-05: Check for orphan/widow lines."""
    cfg = config or QA_CONFIG
    min_chars = cfg.get('min_last_line_chars', 15)
    issues = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                lines = text.split('\n')
                if len(lines) > 1:
                    last_line = lines[-1].strip()
                    if len(last_line) < min_chars and len(last_line.split()) <= 2:
                        issues.append({
                            'slide_number': slide_number,
                            'severity': 'info',
                            'category': 'consistency',
                            'description': f'Possible widow: last line "{last_line}" is very short',
                            'suggested_fix': 'Reword text to eliminate short trailing lines.',
                            'affected_element': shape.name,
                            'auto_fixable': False,
                        })
    return issues


def check_safe_margins(slide, slide_number, presentation, config=None):
    """AP-06: Check that text elements are within the safe margin."""
    cfg = config or QA_CONFIG
    margin_pct = cfg['safe_margin_pct']
    slide_width = presentation.slide_width
    slide_height = presentation.slide_height
    margin_left = int(slide_width * margin_pct)
    margin_top = int(slide_height * margin_pct)
    margin_right = slide_width - margin_left
    margin_bottom = slide_height - margin_top

    issues = []
    for shape in slide.shapes:
        if not shape.has_text_frame or not shape.text_frame.text.strip():
            continue
        if (shape.left < margin_left or
            shape.top < margin_top or
            shape.left + shape.width > margin_right or
            shape.top + shape.height > margin_bottom):
            issues.append({
                'slide_number': slide_number,
                'severity': 'warning',
                'category': 'margin',
                'description': f'Element "{shape.name}" extends outside {margin_pct*100:.0f}% safe margin',
                'suggested_fix': 'Move element inside the safe margin area.',
                'affected_element': shape.name,
                'auto_fixable': True,
            })
    return issues


def check_speaker_notes(presentation, config=None):
    """AP-09: At least 50% of content slides should have speaker notes."""
    issues = []
    total_content_slides = 0
    slides_with_notes = 0
    for slide in presentation.slides:
        text_shapes = [s for s in slide.shapes
                       if s.has_text_frame and s.text_frame.text.strip()]
        if len(text_shapes) == 0:
            continue
        total_content_slides += 1
        if slide.has_notes_slide:
            notes_text = slide.notes_slide.notes_text_frame.text.strip()
            if notes_text:
                slides_with_notes += 1
    if total_content_slides > 0:
        pct = slides_with_notes / total_content_slides
        if pct < 0.5:
            issues.append({
                'slide_number': 0,
                'severity': 'warning',
                'category': 'missing_content',
                'description': f'Only {slides_with_notes}/{total_content_slides} content slides ({pct:.0%}) have speaker notes (minimum 50%)',
                'suggested_fix': 'Add concise speaker notes (30-60 words) to each content slide.',
                'affected_element': 'deck',
                'auto_fixable': False,
            })
    return issues


def check_slide_count_ratio(presentation, duration_minutes=None, config=None):
    """AP-10: Check slide count vs talk duration."""
    cfg = config or QA_CONFIG
    if duration_minutes is None:
        return []
    slide_count = len(presentation.slides)
    ratio = slide_count / duration_minutes
    issues = []
    if ratio > cfg['slides_per_minute_max']:
        issues.append({
            'slide_number': 0,
            'severity': 'warning',
            'category': 'consistency',
            'description': f'{slide_count} slides for {duration_minutes}min talk = {ratio:.1f} slides/min (max {cfg["slides_per_minute_max"]}). Too many slides.',
            'suggested_fix': 'Reduce slide count or increase talk duration.',
            'affected_element': 'deck',
            'auto_fixable': False,
        })
    elif ratio < cfg['slides_per_minute_min']:
        issues.append({
            'slide_number': 0,
            'severity': 'warning',
            'category': 'consistency',
            'description': f'{slide_count} slides for {duration_minutes}min talk = {ratio:.1f} slides/min (min {cfg["slides_per_minute_min"]}). Too few slides.',
            'suggested_fix': 'Add more slides or reduce talk duration.',
            'affected_element': 'deck',
            'auto_fixable': False,
        })
    return issues


def check_placeholder_residue(slide, slide_number, config=None):
    """AP-11: Check for leftover placeholder text."""
    issues = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text.strip()
            if not text:
                continue
            for pattern in PLACEHOLDER_PATTERNS:
                if pattern.search(text):
                    issues.append({
                        'slide_number': slide_number,
                        'severity': 'error',
                        'category': 'placeholder_residue',
                        'description': f'Placeholder text detected: "{text[:60]}"',
                        'suggested_fix': 'Replace placeholder text with actual content or remove the element.',
                        'affected_element': shape.name,
                        'auto_fixable': False,
                    })
                    break
    return issues


def check_bullet_count(slide, slide_number, config=None):
    """AP-14: Check for too many bullet points per text box."""
    cfg = config or QA_CONFIG
    max_bullets = cfg['max_bullets_per_slide']
    issues = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            bullet_count = 0
            for para in shape.text_frame.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                pPr = para._pPr
                has_bullet = pPr is not None and (
                    pPr.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}buChar') is not None or
                    pPr.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}buAutoNum') is not None
                )
                if has_bullet:
                    bullet_count += 1
            if bullet_count > max_bullets:
                issues.append({
                    'slide_number': slide_number,
                    'severity': 'warning',
                    'category': 'text_overflow',
                    'description': f'{bullet_count} bullet points (max {max_bullets})',
                    'suggested_fix': 'Split into multiple slides or convert bullets into visual elements.',
                    'affected_element': shape.name,
                    'auto_fixable': False,
                })
    return issues


def check_title_slide(presentation, config=None):
    """AP-16: Check that the first slide is a title slide."""
    issues = []
    if len(presentation.slides) == 0:
        return [{'slide_number': 0, 'severity': 'error', 'category': 'missing_content',
                 'description': 'Presentation has no slides',
                 'suggested_fix': 'Add slides to the presentation.',
                 'affected_element': 'deck', 'auto_fixable': False}]
    first_slide = presentation.slides[0]
    layout_name = first_slide.slide_layout.name.lower()
    has_title_layout = 'title' in layout_name
    has_title_placeholder = False
    for shape in first_slide.shapes:
        try:
            if shape.placeholder_format is not None and shape.placeholder_format.idx == 0:
                has_title_placeholder = True
                break
        except ValueError:
            pass
    if not has_title_layout and not has_title_placeholder:
        issues.append({
            'slide_number': 1,
            'severity': 'warning',
            'category': 'missing_content',
            'description': 'First slide does not appear to be a title slide',
            'suggested_fix': 'Use the Title Slide layout for the first slide.',
            'affected_element': 'slide',
            'auto_fixable': False,
        })
    return issues


def check_closing_slide(presentation, config=None):
    """AP-17: Check that the last slide is a closing/CTA slide."""
    issues = []
    if len(presentation.slides) < 2:
        return issues
    last_slide = presentation.slides[-1]
    all_text = ' '.join(
        shape.text_frame.text.lower()
        for shape in last_slide.shapes if shape.has_text_frame
    )
    has_cta = any(kw in all_text for kw in CTA_KEYWORDS)
    if not has_cta:
        issues.append({
            'slide_number': len(presentation.slides),
            'severity': 'warning',
            'category': 'missing_content',
            'description': 'Last slide does not appear to be a closing/CTA slide',
            'suggested_fix': 'Add a closing slide with summary, CTA, or contact information.',
            'affected_element': 'slide',
            'auto_fixable': False,
        })
    return issues


def check_text_overflow(slide, slide_number, config=None):
    """AP-19: Check for text overflow/clipping (auto-shrunk text)."""
    cfg = config or QA_CONFIG
    min_scale = cfg.get('min_autofit_scale_pct', 90)
    issues = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            tf_xml = shape.text_frame._txBody
            bodyPr = tf_xml.find('.//a:bodyPr', NSMAP)
            if bodyPr is not None:
                norm = bodyPr.find('a:normAutofit', NSMAP)
                if norm is not None:
                    scale = norm.get('fontScale')
                    if scale and int(scale) < min_scale * 1000:
                        issues.append({
                            'slide_number': slide_number,
                            'severity': 'warning',
                            'category': 'text_overflow',
                            'description': f'Text auto-shrunk to {int(scale)/1000:.0f}% to fit container',
                            'suggested_fix': 'Reduce text content or increase container size.',
                            'affected_element': shape.name,
                            'auto_fixable': False,
                        })
    return issues


def check_dead_slides(slide, slide_number, config=None):
    """AP-24: Check if a slide has no meaningful content."""
    meaningful_content = False
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip():
            meaningful_content = True
            break
        if shape.shape_type == 13:  # Picture
            meaningful_content = True
            break
        if hasattr(shape, 'has_chart') and shape.has_chart:
            meaningful_content = True
            break
        if hasattr(shape, 'has_table') and shape.has_table:
            meaningful_content = True
            break

    issues = []
    if not meaningful_content:
        issues.append({
            'slide_number': slide_number,
            'severity': 'warning',
            'category': 'missing_content',
            'description': f'Slide {slide_number} appears to have no meaningful content',
            'suggested_fix': 'Remove empty slide or add content.',
            'affected_element': 'slide',
            'auto_fixable': False,
        })
    return issues


def check_element_overlap(slide, slide_number, config=None):
    """AP-20: Check for shapes that overlap more than threshold."""
    cfg = config or QA_CONFIG
    min_overlap_pct = cfg['min_overlap_pct']
    shapes_with_content = []
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip():
            shapes_with_content.append({
                'name': shape.name,
                'left': shape.left, 'top': shape.top,
                'right': shape.left + shape.width,
                'bottom': shape.top + shape.height,
                'area': shape.width * shape.height,
            })

    issues = []
    for i in range(len(shapes_with_content)):
        for j in range(i + 1, len(shapes_with_content)):
            a, b = shapes_with_content[i], shapes_with_content[j]
            x_overlap = max(0, min(a['right'], b['right']) - max(a['left'], b['left']))
            y_overlap = max(0, min(a['bottom'], b['bottom']) - max(a['top'], b['top']))
            overlap_area = x_overlap * y_overlap
            smaller_area = min(a['area'], b['area'])
            if smaller_area > 0:
                overlap_pct = (overlap_area / smaller_area) * 100
                if overlap_pct > min_overlap_pct:
                    issues.append({
                        'slide_number': slide_number,
                        'severity': 'warning',
                        'category': 'overlap',
                        'description': f'Elements "{a["name"]}" and "{b["name"]}" overlap by {overlap_pct:.0f}%',
                        'suggested_fix': 'Reposition elements to eliminate unintentional overlap.',
                        'affected_element': f'{a["name"]}, {b["name"]}',
                        'auto_fixable': False,
                    })
    return issues
