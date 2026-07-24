"""Deck-native annotation QA checks (issue #142 v2 — annotate-figure).

Implements AN-01, AN-02, AN-03 from
docs/superpowers/plans/2026-07-17-annotate-figure-v2.md §7. These checks
only fire for slides whose strategy-map entry has ``annotation_mode:
"native"`` — run_qa's dedicated routing branch (§7, F3a) is responsible
for that gating and for loading the SlideAnnotations payload
(``annotations/slide-NN-annotations.json``) before calling these
functions. Every OOXML shape the native assembler draws carries an
``annotation_*``-prefixed ``objectName``/``name`` (§4.5) — that naming
contract is what lets these checks select annotation shapes reliably.

Design: docs/superpowers/plans/2026-07-17-annotate-figure-v2.md §7.
"""

from src.process_image import compute_content_hash

# Distinct name prefixes per shape kind (F10) — chosen so no prefix is a
# string-prefix of another (e.g. 'annotation_dot_' vs 'annotation_dotring_'
# diverge at the character immediately after 'dot').
_PREFIX_LABEL = 'annotation_label_'
_PREFIX_LEADER = 'annotation_leader_'
_PREFIX_DOT = 'annotation_dot_'
_PREFIX_CASING = 'annotation_casing_'
_PREFIX_DOTRING = 'annotation_dotring_'


def _shape_name(shape):
    return getattr(shape, 'name', '') or ''


def check_annotation_contract(slide, slide_number, payload, image_entry=None, config=None):
    """AN-01: annotation contract honoured.

    For a slide contracted ``annotation_mode: native``:
      - payload ABSENT (``None``) -> error (F3c — the contract was dropped;
        pairs with the F5 operator-acknowledged degradation path).
      - ``base_image_hash`` != hash of the manifest image on disk -> error
        (F4 — stale anchors; the assembler warn-refuses the overlay in this
        case, so this is the QA-side tripwire that surfaces it).
      - otherwise, assert EXACT counts (F10) of ``annotation_label_*``,
        ``annotation_leader_*`` and ``annotation_dot_*`` shapes (each must
        equal ``len(payload['labels'])``), plus ``annotation_casing_*`` and
        ``annotation_dotring_*`` when ``style.casing_width_pt > 0``.

    Args:
        slide: python-pptx slide object.
        slide_number: 1-based slide index.
        payload: loaded SlideAnnotations dict (annotations.schema.json), or
            None when the payload file is absent/unreadable.
        image_entry: the slide's image-manifest entry dict (used to
            recompute the on-disk base image hash for the F4 check). None
            or a missing/unreadable ``file_path`` skips the hash check —
            the count check still runs.
        config: optional QA config dict (unused; kept for signature parity
            with the rest of the QA check suite).

    Returns:
        list of finding dicts.
    """
    if payload is None:
        return [{
            'slide_number': slide_number,
            'severity': 'error',
            'category': 'annotation',
            'description': (
                'Slide is contracted annotation_mode=native but no annotations '
                'payload was found (annotations/slide-NN-annotations.json absent '
                'or unreadable).'
            ),
            'suggested_fix': (
                'Re-run the imagegen-bridge native annotation sub-step to write '
                'the payload, or downgrade the slide per the F5 operator '
                'three-way choice (retry / raster-with-manual-anchors / ship-unlabeled).'
            ),
            'affected_element': 'slide',
            'auto_fixable': False,
        }]

    if image_entry:
        base_image_path = image_entry.get('file_path')
        expected_hash = payload.get('base_image_hash')
        if base_image_path and expected_hash:
            try:
                actual_hash = compute_content_hash(base_image_path)
            except OSError:
                actual_hash = None
            if actual_hash is not None and actual_hash != expected_hash:
                return [{
                    'slide_number': slide_number,
                    'severity': 'error',
                    'category': 'annotation',
                    'description': (
                        f'base_image_hash mismatch: payload was built for a different '
                        f'image (expected {expected_hash}, on-disk image hashes to '
                        f'{actual_hash}). Anchors are stale for the current base image.'
                    ),
                    'suggested_fix': (
                        'Re-run the anchor pass and build_annotation_payload for the '
                        'current base image (F4 invalidation contract).'
                    ),
                    'affected_element': 'slide',
                    'auto_fixable': False,
                }]

    n = len(payload.get('labels', []))
    style = payload.get('style', {}) or {}
    casing_enabled = style.get('casing_width_pt', 0) > 0

    expected_counts = {
        _PREFIX_LABEL: n,
        _PREFIX_LEADER: n,
        _PREFIX_DOT: n,
    }
    if casing_enabled:
        expected_counts[_PREFIX_CASING] = n
        expected_counts[_PREFIX_DOTRING] = n

    actual_counts = {prefix: 0 for prefix in expected_counts}
    for shape in slide.shapes:
        name = _shape_name(shape)
        for prefix in expected_counts:
            if name.startswith(prefix):
                actual_counts[prefix] += 1

    findings = []
    for prefix, expected in expected_counts.items():
        actual = actual_counts[prefix]
        if actual != expected:
            findings.append({
                'slide_number': slide_number,
                'severity': 'error',
                'category': 'annotation',
                'description': (
                    f'Expected exactly {expected} "{prefix}*" shape(s) '
                    f'(one per payload label), found {actual}.'
                ),
                'suggested_fix': (
                    'Re-render the native annotation overlay — shape counts must '
                    'match the payload label count exactly.'
                ),
                'affected_element': prefix.rstrip('_'),
                'auto_fixable': False,
            })
    return findings


def check_label_text_verbatim(slide, slide_number, payload, config=None):
    """AN-02: label text verbatim.

    The multiset of ``annotation_label_*`` textbox strings must equal the
    multiset of ``payload['labels'][].text``, character-exact. Any
    mismatch (truncation, casing drift, missing/extra label) is an error
    naming expected vs actual — text is perfect by construction, and this
    check proves the contract survived assembly.

    Args:
        slide: python-pptx slide object.
        slide_number: 1-based slide index.
        payload: loaded SlideAnnotations dict, or None (payload absence is
            AN-01's concern — this check is a no-op when payload is None).
        config: optional QA config dict (unused; signature parity).

    Returns:
        list of finding dicts (0 or 1 — one combined mismatch finding).
    """
    if not payload:
        return []

    expected_texts = sorted(label['text'] for label in payload.get('labels', []))
    actual_texts = sorted(
        shape.text_frame.text
        for shape in slide.shapes
        if _shape_name(shape).startswith(_PREFIX_LABEL) and getattr(shape, 'has_text_frame', False)
    )

    if expected_texts == actual_texts:
        return []

    return [{
        'slide_number': slide_number,
        'severity': 'error',
        'category': 'annotation',
        'description': (
            f'Annotation label text mismatch: expected {expected_texts!r}, '
            f'found {actual_texts!r}.'
        ),
        'suggested_fix': (
            'Regenerate the annotation overlay — label text must be character-exact '
            '(the whole point of native annotation is perfect-by-construction text).'
        ),
        'affected_element': 'annotation_label',
        'auto_fixable': False,
    }]


def check_labels_within_bounds(slide, slide_number, presentation, config=None):
    """AN-03: label boxes within slide bounds.

    Every ``annotation_label_*`` shape rect must lie fully within
    ``[0, slide_w] x [0, slide_h]``. Off-slide is a warning (placement
    pushed a label off-canvas; operator should nudge ``label_pos`` or add
    an explicit style override), not an error — the figure itself is
    unaffected.

    Args:
        slide: python-pptx slide object.
        slide_number: 1-based slide index.
        presentation: python-pptx Presentation object (for slide_width/
            slide_height).
        config: optional QA config dict (unused; signature parity).

    Returns:
        list of finding dicts.
    """
    slide_w = presentation.slide_width
    slide_h = presentation.slide_height

    issues = []
    for shape in slide.shapes:
        name = _shape_name(shape)
        if not name.startswith(_PREFIX_LABEL):
            continue
        if (shape.left < 0 or shape.top < 0 or
                shape.left + shape.width > slide_w or
                shape.top + shape.height > slide_h):
            issues.append({
                'slide_number': slide_number,
                'severity': 'warning',
                'category': 'annotation',
                'description': f'Annotation label "{name}" extends outside the slide bounds.',
                'suggested_fix': (
                    'Nudge label_pos (or add a style override) so the label stays on-slide.'
                ),
                'affected_element': name,
                'auto_fixable': False,
            })
    return issues
