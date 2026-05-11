"""Tests for the v0.2 #25 brief-save lint.

Run 7 + Run 8 both shipped briefs with Section C that the EXACT-labels
extractor couldn't parse, because operators flattened the persona's
canonical ``- role: "exact text"`` format into plain bullets during
brief assembly. The lint catches this at brief-save time and surfaces
a clear error message before /enrich-deck silently confabulates.

The lint:
- Enumerates every IMAGE marker in Section C
- For each, calls extract_expected_text_for_marker
- If no labels found AND marker isn't declared atmospheric, errors

Atmospheric markers (vignettes, BG, decorative) opt out by including
words like "atmospheric" or "no text" in their subject brief.
"""
from __future__ import annotations

from src.creative_brief import (
    BriefLintError,
    lint_brief_for_extract_compatibility,
)


# ---------------------------------------------------------------------------
# No-error cases
# ---------------------------------------------------------------------------


def test_brief_with_canonical_exact_labels_passes_lint() -> None:
    """The Run 8 brief format — `- role: "exact text"` — passes lint."""
    brief = """# Creative Brief

## Section C — Placeholder Instructions

**Slide 4:**
Marker: `IMAGE:emblematic-thylacine`

> EXACT spelled labels REQUIRED:
> - common-name: "Thylacine"
> - scientific-name: "Thylacinus cynocephalus"
> - extinction-year: "1936"
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert errors == []


def test_atmospheric_marker_opts_out_via_keyword() -> None:
    """Atmospheric markers don't need EXACT-labels; opt out via subject brief."""
    brief = """## Section C — Placeholder Instructions

**Slide 8:**
Marker: `IMAGE:vignette-silent-forest`
Subject: atmospheric watercolour of a forest at dawn — no specific text.
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert errors == []


def test_vignette_keyword_opts_out() -> None:
    """The word 'vignette' alone is an atmospheric signal."""
    brief = """## Section C — Placeholder Instructions

Marker: `IMAGE:vignette-bleached-reef` — painterly vignette of a coral reef.
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert errors == []


def test_no_text_keyword_opts_out() -> None:
    """The phrase 'no text' is an explicit atmospheric declaration."""
    brief = """## Section C — Placeholder Instructions

Marker: `IMAGE:closing-living-species`
Subject: living bird on a fern. NO text in the image (overlaid separately).
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert errors == []


def test_brief_without_section_c_returns_empty() -> None:
    """No Section C means no markers to lint — caught by parse_brief instead."""
    brief = """# Creative Brief

## Section A — Narrative Architecture

Some content.
"""
    assert lint_brief_for_extract_compatibility(brief) == []


# ---------------------------------------------------------------------------
# Error cases — Run 7/8 reproduction
# ---------------------------------------------------------------------------


def test_text_bearing_marker_without_exact_labels_errors() -> None:
    """Run 7/8 reproduction: marker has text content but no EXACT block.

    This is the silent regression the lint catches: the operator forgot
    to add the EXACT-labels block, so /enrich-deck would have dispatched
    the reviewer without expected text and Haiku would confabulate.
    """
    brief = """## Section C — Placeholder Instructions

**Slide 4:**
Marker: `IMAGE:emblematic-thylacine`
Subject: A naturalist illustration of the Thylacine showing common name,
scientific name, location, and extinction year as caption text.
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert len(errors) == 1
    assert "IMAGE:emblematic-thylacine" in errors[0]
    assert "no EXACT-labels block found" in errors[0]


def test_flattened_bullets_format_errors() -> None:
    """Run 7 motivating case: persona produces canonical format, operator
    flattens to plain bullets ``- text`` (no `role:` prefix, no quotes).
    The extractor returns 0 labels; the lint catches it.
    """
    brief = """## Section C — Placeholder Instructions

Marker: `IMAGE:emblematic-thylacine`

> EXACT spelled labels REQUIRED:
> - Thylacine
> - Thylacinus cynocephalus
> - Tasmania
> - 1936
"""
    errors = lint_brief_for_extract_compatibility(brief)
    # Plain bullets without `role:` prefix don't match _LABEL_BULLET_RE,
    # so extractor returns 0 — lint flags it.
    assert len(errors) == 1
    assert "IMAGE:emblematic-thylacine" in errors[0]


def test_multiple_offending_markers_listed() -> None:
    """Lint reports every offending marker, not just the first."""
    brief = """## Section C — Placeholder Instructions

`IMAGE:wordmark-foo` carries the brand wordmark.

`IMAGE:wordmark-bar` carries another brand wordmark.

`IMAGE:wordmark-baz` carries a third brand wordmark.
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert len(errors) == 3
    error_text = "\n".join(errors)
    assert "IMAGE:wordmark-foo" in error_text
    assert "IMAGE:wordmark-bar" in error_text
    assert "IMAGE:wordmark-baz" in error_text


def test_some_markers_pass_others_fail_only_failures_reported() -> None:
    """Lint is selective: a brief with mixed correct + incorrect markers
    reports only the incorrect ones."""
    brief = """## Section C — Placeholder Instructions

**Slide 1:**
Marker: `IMAGE:correct-marker`

> EXACT spelled labels REQUIRED:
> - heading: "Hello World"

**Slide 2:**
Marker: `IMAGE:bad-marker` carries the company wordmark text.
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert len(errors) == 1
    assert "IMAGE:bad-marker" in errors[0]
    assert "IMAGE:correct-marker" not in "\n".join(errors)


def test_atmospheric_and_text_bearing_mixed_correctly_separated() -> None:
    """Atmospheric markers pass; text-bearing without EXACT-labels fail."""
    brief = """## Section C — Placeholder Instructions

`IMAGE:vignette-forest` — atmospheric, no text.

`IMAGE:wordmark-product` — carries the product wordmark.
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert len(errors) == 1
    assert "IMAGE:wordmark-product" in errors[0]
    assert "IMAGE:vignette-forest" not in "\n".join(errors)


def test_bg_markers_not_linted() -> None:
    """BG: and SMARTART-FROM-LIST: markers are out of scope for this lint."""
    brief = """## Section C — Placeholder Instructions

`BG:dawn-pivot` — full-bleed atmospheric (no exact labels needed).
`SMARTART-FROM-LIST:species-list` — bullet text comes from the marker shape.
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert errors == []


def test_only_section_c_image_markers_linted_not_section_a_examples() -> None:
    """Lint scope is Section C only — example marker references in
    Section A as narrative explanation don't trigger false positives."""
    brief = """## Section A — Narrative Architecture

We will use markers like `IMAGE:example-explainer` in Section C.

## Section C — Placeholder Instructions

`IMAGE:real-marker` carries text.

> EXACT spelled labels REQUIRED:
> - title: "Hello"
"""
    errors = lint_brief_for_extract_compatibility(brief)
    # `IMAGE:example-explainer` from Section A is NOT linted (Section A
    # is excluded). `IMAGE:real-marker` has its EXACT block. Clean.
    assert errors == []


# ---------------------------------------------------------------------------
# Public-API surface
# ---------------------------------------------------------------------------


def test_lint_returns_list_of_strings_not_exception() -> None:
    """The lint is non-throwing — it returns a list. SKILL.md decides
    whether to surface as a halt or a warning."""
    brief = """## Section C — Placeholder Instructions
`IMAGE:bad-marker` carries text.
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert isinstance(errors, list)
    assert all(isinstance(e, str) for e in errors)


def test_brief_lint_error_class_exists() -> None:
    """SKILL.md may want to raise BriefLintError when surfacing the lint
    failure to the operator. The class exists in the public surface."""
    assert issubclass(BriefLintError, ValueError)


# ---------------------------------------------------------------------------
# Issue #56 — soft-warn on inline separators in SMARTART-FROM-LIST blocks
# ---------------------------------------------------------------------------


def test_inline_middle_dot_list_in_smartart_from_list_block_warns() -> None:
    """Issue #56: inline · list inside a SMARTART-FROM-LIST block generates
    a soft warning. The bridge can recover at render time, but bullet-line
    format is preferred."""
    brief = """## Section C — Placeholder Instructions

`SMARTART-FROM-LIST:capability-themes` — process flow, 3–5 items.
Edge inference · Operator playbook · Customer overlap · GPU procurement · Registry seam
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert len(errors) == 1
    assert "SMARTART-FROM-LIST:capability-themes" in errors[0]
    assert "inline" in errors[0].lower() or "separator" in errors[0].lower()


def test_inline_pipe_list_in_smartart_from_list_block_warns() -> None:
    """Issue #56: inline | list also triggers the soft warning."""
    brief = """## Section C — Placeholder Instructions

`SMARTART-FROM-LIST:phase-steps` — 4-phase pipeline.
Discovery | Design | Build | Test | Ship
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert len(errors) == 1
    assert "SMARTART-FROM-LIST:phase-steps" in errors[0]


def test_inline_separator_in_image_marker_block_not_linted() -> None:
    """Issue #56: only SMARTART-FROM-LIST blocks are scanned for inline
    separators. An inline · in an IMAGE marker block does NOT trigger the
    warning (that pattern is fine for prose descriptions)."""
    brief = """## Section C — Placeholder Instructions

`IMAGE:schematic-trio` — three boxes: Alpha · Beta · Gamma · Delta

> EXACT spelled labels REQUIRED:
> - left: "Alpha"
> - middle: "Beta"
> - right: "Gamma"
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert errors == []


def test_inline_separator_below_threshold_not_warned() -> None:
    """Issue #56: two · characters in a SMARTART-FROM-LIST block is below
    the 3+ threshold and does NOT trigger the warning."""
    brief = """## Section C — Placeholder Instructions

`SMARTART-FROM-LIST:two-items` — just two items.
Phase A · Phase B (complete)
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert errors == []


def test_bullet_line_format_in_smartart_block_passes_lint() -> None:
    """Issue #56: the preferred bullet-line format has no inline separators
    and passes lint cleanly."""
    brief = """## Section C — Placeholder Instructions

`SMARTART-FROM-LIST:capability-themes` — process flow, ≤24 chars each:
- Edge inference
- Operator playbook
- Customer overlap
- GPU procurement
- Registry seam
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert errors == []


def test_inline_separator_lint_is_soft_warning_not_exception() -> None:
    """Issue #56: inline-separator detection must not raise — lint always
    returns a list so SKILL.md controls severity."""
    brief = """## Section C — Placeholder Instructions

`SMARTART-FROM-LIST:phases` — all phases.
Alpha · Beta · Gamma · Delta · Epsilon
"""
    errors = lint_brief_for_extract_compatibility(brief)
    assert isinstance(errors, list)
    assert all(isinstance(e, str) for e in errors)
