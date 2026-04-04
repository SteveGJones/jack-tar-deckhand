"""SmartArt QA checks: SA-01 to SA-05.

Implements five quality gates for SmartArt graphics:
  SA-01: Data integrity — body_points covered by SmartArtSpec data
  SA-02: Label legibility — font size thresholds + WCAG contrast
  SA-03: Enrichment alignment — enrichment images present and dimensions matched
  SA-04: Overflow handling — truncation indicator present when overflow applied
  SA-05: Accessibility — <title>, <desc>, alt_text, aria attributes
"""

import re

from src.smartart_svg.tokens import _contrast_ratio


# ---------------------------------------------------------------------------
# SA-01: Data Integrity
# ---------------------------------------------------------------------------

def _collect_custom_svg_labels(data):
    """Flatten all string values from a custom_svg data dict into a set of labels."""
    labels = set()
    if not isinstance(data, dict):
        return labels
    for value in data.values():
        if isinstance(value, str):
            labels.add(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    labels.add(item)
                elif isinstance(item, dict):
                    # e.g. quadrant items, node lists
                    for v in item.values():
                        if isinstance(v, str):
                            labels.add(v)
                        elif isinstance(v, list):
                            labels.update(s for s in v if isinstance(s, str))
    return labels


def check_data_integrity(outline_slide, spec, slide_number):
    """SA-01: Verify body_points from the outline are represented in the SmartArtSpec data.

    Args:
        outline_slide: dict from SlideOutline with 'body_points' list.
        spec: SmartArtSpec dict with 'engine', 'data', and 'overflow_applied'.
        slide_number: 1-based slide index.

    Returns:
        list of finding dicts.
    """
    findings = []
    body_points = outline_slide.get('body_points', [])
    if not body_points:
        return findings

    overflow_applied = spec.get('overflow_applied', 'none')
    if overflow_applied and overflow_applied != 'none':
        # Overflow was deliberately applied — missing points are expected
        return findings

    engine = spec.get('engine', '')
    data = spec.get('data', {})
    missing = []

    if engine == 'mermaid':
        syntax = data.get('syntax', '')
        for point in body_points:
            if point not in syntax:
                missing.append(point)
    else:
        # custom_svg and any other engine: flatten all string values in data
        labels = _collect_custom_svg_labels(data)
        for point in body_points:
            if point not in labels:
                missing.append(point)

    if missing:
        findings.append({
            'slide_number': slide_number,
            'severity': 'error',
            'category': 'smartart',
            'description': (
                f'SA-01: {len(missing)} body point(s) missing from SmartArtSpec data: '
                + ', '.join(repr(m) for m in missing)
            ),
        })

    return findings


# ---------------------------------------------------------------------------
# SA-02: Label Legibility
# ---------------------------------------------------------------------------

# Regex: match <text ... font-size="N" ... fill="#RRGGBB" ...> (attributes in either order)
# Using separate patterns to avoid complex alternation inside character classes.
_TEXT_FONT_FILL_RE = re.compile(
    r'<text\b[^>]*?font-size=["\'](\d+(?:\.\d+)?)["\'][^>]*?fill=["\']'
    r'(#[0-9a-fA-F]{6})["\'][^>]*?>',
)
_TEXT_FILL_FONT_RE = re.compile(
    r'<text\b[^>]*?fill=["\']'
    r'(#[0-9a-fA-F]{6})["\'][^>]*?font-size=["\'](\d+(?:\.\d+)?)["\'][^>]*?>',
)


def _extract_text_attrs(svg_content):
    """Return list of (font_size_float, fill_hex) from all <text> elements."""
    results = []
    for m in _TEXT_FONT_FILL_RE.finditer(svg_content):
        results.append((float(m.group(1)), m.group(2)))
    for m in _TEXT_FILL_FONT_RE.finditer(svg_content):
        results.append((float(m.group(2)), m.group(1)))
    return results


def check_label_legibility(svg_content, bg_color, slide_number):
    """SA-02: Check font size thresholds and WCAG contrast for all SVG text labels.

    Args:
        svg_content: SVG markup string.
        bg_color: Background hex colour string (e.g. '#ffffff'). Use None / 'ai_background'
                  for AI-generated backgrounds where contrast is unverifiable.
        slide_number: 1-based slide index.

    Returns:
        list of finding dicts.
    """
    findings = []

    ai_background = bg_color is None or str(bg_color).lower() in ('ai_background', 't1', 't2')

    text_attrs = _extract_text_attrs(svg_content)

    for font_size, fill_hex in text_attrs:
        # Font size checks
        if font_size < 12:
            findings.append({
                'slide_number': slide_number,
                'severity': 'error',
                'category': 'smartart',
                'description': (
                    f'SA-02: Text label font size {font_size}px is below minimum 12px '
                    f'(fill: {fill_hex})'
                ),
            })
            continue  # No point checking contrast on unreadably small text
        elif font_size < 16:
            findings.append({
                'slide_number': slide_number,
                'severity': 'warning',
                'category': 'smartart',
                'description': (
                    f'SA-02: Text label font size {font_size}px is below recommended 16px '
                    f'(fill: {fill_hex})'
                ),
            })

        # Contrast checks
        if ai_background:
            findings.append({
                'slide_number': slide_number,
                'severity': 'warning',
                'category': 'smartart',
                'description': (
                    f'SA-02: Contrast unverifiable — AI-generated background; '
                    f'text fill {fill_hex} at {font_size}px requires manual review'
                ),
            })
        else:
            ratio = _contrast_ratio(fill_hex, bg_color)
            # WCAG AA: 4.5:1 for normal text (<24px), 3:1 for large text (>=24px)
            threshold = 3.0 if font_size >= 24 else 4.5
            if ratio < threshold:
                findings.append({
                    'slide_number': slide_number,
                    'severity': 'error',
                    'category': 'smartart',
                    'description': (
                        f'SA-02: WCAG contrast {ratio:.2f}:1 fails {threshold}:1 threshold '
                        f'for {font_size}px text (fill: {fill_hex}, bg: {bg_color})'
                    ),
                })

    return findings


# ---------------------------------------------------------------------------
# SA-03: Enrichment Alignment
# ---------------------------------------------------------------------------

def check_enrichment_alignment(manifest_entry, image_manifest, slide_number):
    """SA-03: Verify enrichment images exist and match declared dimensions.

    Args:
        manifest_entry: SmartArt manifest entry dict with 'smartart_id',
                        'enrichment_tier', and optional 'dimensions'.
        image_manifest: image-manifest.json dict with 'images' list.
        slide_number: 1-based slide index.

    Returns:
        list of finding dicts.
    """
    enrichment_tier = manifest_entry.get('enrichment_tier', '')
    if enrichment_tier == 'pure_programmatic':
        return []

    smartart_id = manifest_entry.get('smartart_id', '')
    images = image_manifest.get('images', [])

    # Find matching enrichment image(s)
    matching = [img for img in images if img.get('smartart_ref') == smartart_id]

    if not matching:
        return [{
            'slide_number': slide_number,
            'severity': 'error',
            'category': 'smartart',
            'description': (
                f'SA-03: No enrichment image found for smartart_id "{smartart_id}" '
                f'(tier: {enrichment_tier})'
            ),
        }]

    findings = []
    declared_dims = manifest_entry.get('dimensions')

    for img in matching:
        # Check status
        status = img.get('status', '')
        if status == 'failed':
            findings.append({
                'slide_number': slide_number,
                'severity': 'error',
                'category': 'smartart',
                'description': (
                    f'SA-03: Enrichment image "{img.get("image_id")}" for smartart '
                    f'"{smartart_id}" has status "failed"'
                ),
            })
            continue

        # Check dimension match if declared
        if declared_dims:
            img_dims = img.get('dimensions', {})
            if (img_dims.get('width') != declared_dims.get('width') or
                    img_dims.get('height') != declared_dims.get('height')):
                findings.append({
                    'slide_number': slide_number,
                    'severity': 'error',
                    'category': 'smartart',
                    'description': (
                        f'SA-03: Enrichment image dimensions '
                        f'{img_dims.get("width")}x{img_dims.get("height")} '
                        f'do not match declared '
                        f'{declared_dims.get("width")}x{declared_dims.get("height")} '
                        f'for smartart "{smartart_id}"'
                    ),
                })

    return findings


# ---------------------------------------------------------------------------
# SA-04: Overflow Handling
# ---------------------------------------------------------------------------

_OVERFLOW_INDICATOR_RE = re.compile(r'\.\.\.')


def check_overflow_handling(spec, svg_content, slide_number):
    """SA-04: When overflow_applied is 'truncate', verify a visible indicator exists.

    Args:
        spec: SmartArtSpec dict with 'overflow_applied' field.
        svg_content: SVG markup string.
        slide_number: 1-based slide index.

    Returns:
        list of finding dicts.
    """
    overflow_applied = spec.get('overflow_applied', 'none')

    if overflow_applied == 'none' or not overflow_applied:
        return []

    if overflow_applied == 'truncate':
        if not _OVERFLOW_INDICATOR_RE.search(svg_content):
            return [{
                'slide_number': slide_number,
                'severity': 'error',
                'category': 'smartart',
                'description': (
                    'SA-04: overflow_applied is "truncate" but no "..." indicator '
                    'found in SVG content — truncation must be visually signalled'
                ),
            }]

    return []


# ---------------------------------------------------------------------------
# SA-05: Accessibility
# ---------------------------------------------------------------------------

_TITLE_TAG_RE = re.compile(r'<title\b[^>]*>(.*?)</title>', re.DOTALL)
_DESC_TAG_RE = re.compile(r'<desc\b[^>]*>(.*?)</desc>', re.DOTALL)
_ROLE_IMG_RE = re.compile(r'<[^>]+role=["\']img["\'][^>]*aria-label=["\'][^"\']+["\']')
_ARIA_LABEL_RE = re.compile(r'<[^>]+aria-label=["\'][^"\']+["\'][^>]*role=["\']img["\']')


def check_accessibility(svg_content, manifest_entry, slide_number):
    """SA-05: Verify SVG accessibility attributes and manifest alt_text.

    Checks:
      - <title> tag present and non-empty
      - <desc> tag present and non-empty
      - alt_text in manifest entry
      - <g role="img" aria-label="..."> present

    Args:
        svg_content: SVG markup string.
        manifest_entry: SmartArt manifest entry dict.
        slide_number: 1-based slide index.

    Returns:
        list of finding dicts.
    """
    findings = []

    # Check <title>
    title_match = _TITLE_TAG_RE.search(svg_content)
    if not title_match or not title_match.group(1).strip():
        findings.append({
            'slide_number': slide_number,
            'severity': 'error',
            'category': 'smartart',
            'description': 'SA-05: SVG <title> tag is missing or empty',
        })

    # Check <desc>
    desc_match = _DESC_TAG_RE.search(svg_content)
    if not desc_match or not desc_match.group(1).strip():
        findings.append({
            'slide_number': slide_number,
            'severity': 'error',
            'category': 'smartart',
            'description': 'SA-05: SVG <desc> tag is missing or empty',
        })

    # Check alt_text in manifest
    if not manifest_entry.get('alt_text', '').strip():
        findings.append({
            'slide_number': slide_number,
            'severity': 'error',
            'category': 'smartart',
            'description': 'SA-05: manifest entry is missing alt_text',
        })

    # Check role="img" aria-label="..." (either attribute order)
    has_role_aria = (
        _ROLE_IMG_RE.search(svg_content) or _ARIA_LABEL_RE.search(svg_content)
    )
    if not has_role_aria:
        findings.append({
            'slide_number': slide_number,
            'severity': 'error',
            'category': 'smartart',
            'description': (
                'SA-05: SVG is missing <g role="img" aria-label="..."> '
                'accessibility wrapper'
            ),
        })

    return findings
