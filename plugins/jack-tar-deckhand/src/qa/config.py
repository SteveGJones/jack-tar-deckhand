"""Configurable QA thresholds for deck-qa checks.

All thresholds are tunable. Defaults are derived from research:
- Research #07: Conference Presentation QA Heuristics & Anti-Patterns
- Research #01: Slide Layout Intelligence & Design Rules Engine

Category mappings for QAReport schema:
  overlap, contrast, margin, text_overflow, consistency,
  image_quality, placeholder_residue, missing_content, accessibility
"""

QA_CONFIG = {
    # AP-01: Wall of Text
    'max_words_per_textbox': 40,
    'max_words_per_slide': 75,

    # AP-02: Font Size Below Projection Minimum
    'min_font_size_body_pt': 18,
    'min_font_size_title_pt': 24,

    # AP-03: Too Many Font Families
    'max_font_families': 2,

    # AP-05: Orphan/Widow
    'min_last_line_chars': 15,

    # AP-06: Elements Outside Safe Margins
    'safe_margin_pct': 0.05,

    # AP-07: Low Contrast (WCAG AA minimum for body text: 4.5:1)
    'min_contrast_ratio': 4.5,

    # AP-10: Slide Count vs Duration
    'slides_per_minute_min': 0.5,
    'slides_per_minute_max': 2.0,

    # AP-12: Image Resolution (72 DPI = screen resolution minimum for presentations)
    'min_image_dpi_equiv': 72,

    # AP-13: Image Aspect Ratio Distortion
    'max_aspect_distortion_pct': 5.0,

    # AP-14: Too Many Bullet Points
    'max_bullets_per_slide': 6,

    # AP-15: Consecutive Bullet-Heavy Slides
    'max_consecutive_bullet_slides': 3,

    # AP-18: Heading Size Consistency
    'max_heading_variance_pt': 2,

    # AP-19: Text Overflow
    'min_autofit_scale_pct': 90,

    # AP-20: Element Overlap
    'min_overlap_pct': 25,

    # AP-21: Excessive Animations
    'max_transition_types': 2,

    # AP-25: Colourblind Safety
    'colourblind_min_distance': 30,
}
