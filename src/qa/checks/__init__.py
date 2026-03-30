"""QA check registry.

Organises all 25 anti-pattern checks into execution groups:
1. Structural (per-slide, fast, no rendering)
2. Cross-slide consistency (deck-level)
3. Image/visual quality (per-slide, may need image loading)

This mirrors the QA Pipeline Design from Research #07 Section 6.
"""

from .structural import (
    check_wall_of_text,
    check_font_size,
    check_orphan_widow,
    check_safe_margins,
    check_speaker_notes,
    check_slide_count_ratio,
    check_placeholder_residue,
    check_bullet_count,
    check_title_slide,
    check_closing_slide,
    check_text_overflow,
    check_dead_slides,
    check_element_overlap,
)
from .contrast import (
    check_contrast,
    check_clashing_colours,
    check_colourblind_safety,
)
from .consistency import (
    check_font_families,
    check_bullet_consistency,
    check_consecutive_bullet_slides,
    check_heading_consistency,
    check_branding_consistency,
)
from .image_quality import (
    check_image_resolution,
    check_aspect_ratio_distortion,
)
from .animations import check_excessive_animations
from .chart_quality import check_chart_junk
from .keynote_checks import check_palette_drift

# Per-slide structural checks (fast path)
STRUCTURAL_CHECKS = [
    check_wall_of_text,
    check_font_size,
    check_orphan_widow,
    check_placeholder_residue,
    check_bullet_count,
    check_text_overflow,
    check_dead_slides,
    check_element_overlap,
]

# Per-slide checks requiring presentation context (margins)
STRUCTURAL_CHECKS_WITH_PRESENTATION = [
    check_safe_margins,
]

# Deck-level structural checks
DECK_STRUCTURAL_CHECKS = [
    check_speaker_notes,
    check_title_slide,
    check_closing_slide,
]

# Deck-level consistency checks
CONSISTENCY_CHECKS = [
    check_font_families,
    check_bullet_consistency,
    check_consecutive_bullet_slides,
    check_heading_consistency,
    check_branding_consistency,
]

# Per-slide image quality checks
IMAGE_QUALITY_CHECKS = [
    check_image_resolution,
    check_aspect_ratio_distortion,
]

# Per-slide visual checks
VISUAL_CHECKS = [
    check_contrast,
    check_chart_junk,
]

# Deck-level animation check
ANIMATION_CHECKS = [
    check_excessive_animations,
]

# Deck-level colour checks
COLOUR_CHECKS = [
    check_clashing_colours,
    check_colourblind_safety,
]

# Per-slide keynote checks (applied only to full_render/backdrop_render slides)
KEYNOTE_CHECKS = [
    check_palette_drift,
]
