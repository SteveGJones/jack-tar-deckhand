# Phase 2: Design Services -- slide-stylist Skill

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `slide-stylist` Claude Code skill that derives a complete StyleGuide (palette, typography, layout templates, image style tokens) from a TalkBrief and optional brand assets, writing the result to `./tmp/deck/style-guide.json`.

**Architecture:** The slide-stylist is a Claude Code skill (SKILL.md file) that acts as the Design Services domain. It reads `./tmp/deck/talk-brief.json` via `src/deckcontext.py` (from Phase 1), optionally analyses a logo file for brand colour extraction, and produces `./tmp/deck/style-guide.json`. It contains three capabilities: Style Derivation (primary), Brand Extraction (logo-to-palette), and Layout Intelligence (per-slide-type layout templates). Per CLAUDE.md rules, a research synthesis document must be created before the skill implementation.

**Tech Stack:** Claude Code skill (SKILL.md markdown), Python 3.8+ (deckcontext.py from Phase 1), pytest

**Phases overview (this is Phase 2 of 6):**
- Phase 1: Foundation (complete) -- DeckContext, schemas, utilities
- **Phase 2: Design Services** (this plan) -- `slide-stylist`
- Phase 3: Content Services -- `narrative-architect`, `speaker-notes-writer`
- Phase 4: Image Services -- 8 skills + 1 agent
- Phase 5: Assembly & QA -- `deck-assembler`, `deck-qa`, `presentation-reviewer`
- Phase 6: Orchestration -- `deck-conductor`

**Depends on Phase 1:** This phase uses `src/deckcontext.py` (init_deck, read_contract, write_contract, update_step), `src/schemas/style_guide.schema.json`, and `tests/fixtures/valid_style_guide.json`. Phase 1 must be implemented first.

---

## File Structure

```
research/
  synthesis-slide-stylist.md             # Research synthesis (CLAUDE.md requirement)
.claude/skills/slide-stylist/
  SKILL.md                               # The slide-stylist skill definition
tests/
  test_slide_stylist.py                  # Validation tests for skill output
  fixtures/
    valid_style_guide.json               # (from Phase 1 -- used for validation)
    valid_talk_brief.json                # (from Phase 1 -- used as input)
    minimal_talk_brief.json              # Minimal brief (no branding, no preferences)
    branded_talk_brief.json              # Brief with full branding section
```

---

## Task 1: Research Synthesis Document

**Files:**
- Create: `research/synthesis-slide-stylist.md`

Per CLAUDE.md: "Create `research/synthesis-[skill-name].md` before implementing any skill." This document synthesises findings from research papers #01 (Layout Intelligence), #09 (Brand Extraction), and #10 (Font Strategy) into actionable decisions for the slide-stylist skill.

- [ ] **Step 1: Create the synthesis document**

Create `research/synthesis-slide-stylist.md`:

```markdown
# Research Synthesis: slide-stylist Skill

> **Purpose:** Distil actionable design decisions from research papers #01, #09, and #10 into the slide-stylist skill implementation. This document bridges research findings and skill behaviour.
> **Date:** 2026-03-29
> **Source papers:**
> - `01-slide-layout-intelligence.md` -- Layout archetypes, grid system, design rules
> - `09-brand-extraction-style-transfer.md` -- Logo-to-palette, font heuristics, colour enforcement
> - `10-font-strategy-typography.md` -- 10 font pairings, projection sizes, embedding strategy

---

## 1. Palette Derivation Strategy

### Decision: Claude-Native Colour Derivation (No Python Libraries)

The slide-stylist runs as a Claude Code skill (SKILL.md). Claude can reason about colour theory directly -- we do not need ColorThief or colorsys at runtime. The skill uses Claude's knowledge to:

1. **With brand colours provided** (TalkBrief.branding.primary_color + optional secondary_color):
   - Use the provided hex values as palette.primary and palette.secondary
   - Derive accent via split-complementary hue rotation (+150 degrees from primary)
   - Derive background as near-white tinted with the primary hue (lightness 0.97, saturation 0.08)
   - Derive background_alt as near-black tinted with the primary hue (lightness 0.12, saturation 0.15)
   - Derive text colours ensuring WCAG AA contrast (4.5:1 minimum against their backgrounds)
   - Derive chart_series as 5 perceptually distinct colours anchored to the brand palette

2. **With logo provided** (TalkBrief.branding.logo_path):
   - Claude has vision capability -- it can SEE the logo and extract dominant colours
   - Identify 2-3 dominant colours from the logo image
   - Use the most saturated/distinctive colour as primary
   - Derive the full palette from those extracted colours using the same rules above

3. **Without any brand input:**
   - Map topic + tone to a curated palette using the industry/mood heuristic table
   - Fall back to the "professional blue" default: primary 1A365D, secondary 2B6CB0, accent ED8936

### Source: Research #09, Sections 1.1-1.4, 1.6

The 60-30-10 rule (Section 1.6) governs palette role assignment:
- 60% dominant = background (light neutral)
- 30% secondary = headings, charts, key visuals (brand primary)
- 10% accent = CTAs, highlights, emphasis (complementary/split-complementary)

### Contrast Validation

All palette pairings must satisfy WCAG AA (4.5:1 for normal text, 3:1 for large text). For projection, the skill targets 7:1 as recommended in Research #01, Section 6.2.

Key pairings to validate:
- text_primary on background (must pass)
- text_on_dark on background_alt (must pass)
- text_muted on background (must pass at large text ratio 3:1)

---

## 2. Font Pairing Selection

### Decision: 10 Scored Pairings with Topic/Tone Mapping

Research #10 provides 10 Google Font pairings with detailed projection legibility assessments. The skill selects from these based on the TalkBrief inputs.

### Selection Algorithm

```
IF branding.font_preference is set:
  Use font_preference as heading_font
  Select best body_font complement from the 10 pairings
ELIF tone == "technical":
  Use Inter (single family) -- pairing #4
ELIF tone == "professional" OR tone == "conversational":
  Use Montserrat + Open Sans -- pairing #1
ELIF tone == "inspirational":
  Use Playfair Display + Source Sans Pro -- pairing #2
ELIF tone == "provocative":
  Use Oswald + Merriweather -- pairing #8
ELIF tone == "storytelling":
  Use Raleway + Lato -- pairing #5
ELSE (no tone specified):
  Use Montserrat + Open Sans -- pairing #1 (default)
```

Additionally, topic keywords can override:
- "AI", "ML", "data", "engineering", "developer" -> Inter or Work Sans + IBM Plex Sans
- "startup", "pitch", "product" -> Poppins + Roboto
- "design", "creative", "art" -> Raleway + Lato or Space Grotesk + DM Sans
- "research", "academic", "science" -> Fira Sans + Source Serif Pro
- "education", "community", "workshop" -> Nunito + Nunito Sans

### Font Sizes (from Research #10, "Practical Default for Jack-Tar Deckhand")

| Element | Size (pt) |
|---------|-----------|
| title_slide | 44 |
| section_divider | 36 |
| slide_heading | 28 |
| subheading | 20 |
| body_size | 16 |
| caption_size | 12 |
| line_spacing | 1.4 |

### Mono Font

Default: JetBrains Mono. For IBM Plex pairings: IBM Plex Mono. For Mozilla/Fira pairings: Fira Code.

---

## 3. Layout Templates for 12 Slide Types

### Decision: Fixed Zone Coordinates per Slide Type

Research #01 defines 18 layout archetypes, but the SlideOutline schema uses 12 slide types. The skill produces a layout template for each of these 12 types.

All coordinates are in inches for a 10" x 5.625" slide (the schema's slide_width_inches and slide_height_inches). Margins are 0.5" on all sides.

### Template Specifications

| Slide Type | text_zone (x, y, w, h) | image_zone (x, y, w, h) | background_treatment |
|------------|------------------------|--------------------------|---------------------|
| title | (1.0, 1.5, 8.0, 2.5) | (0, 0, 10.0, 5.625) | image_bleed |
| section_divider | (1.0, 1.5, 8.0, 2.5) | null | solid_dark |
| content | (0.5, 1.0, 5.5, 4.0) | (6.5, 0.5, 3.0, 4.625) | solid_light |
| two_column | (0.5, 1.0, 4.0, 4.0) | (5.5, 1.0, 4.0, 4.0) | solid_light |
| image_feature | (0.5, 3.5, 4.0, 1.5) | (0, 0, 10.0, 3.2) | image_bleed |
| data_chart | (0.5, 0.5, 9.0, 1.0) | (0.5, 1.6, 9.0, 3.5) | solid_light |
| stat_callout | (1.5, 1.0, 7.0, 3.5) | null | solid_dark |
| quote | (1.5, 1.0, 7.0, 3.0) | null | solid_dark |
| icon_grid | (0.5, 0.5, 9.0, 1.0) | (0.5, 1.6, 9.0, 3.5) | solid_light |
| diagram | (0.5, 0.5, 9.0, 1.0) | (0.5, 1.8, 9.0, 3.3) | solid_light |
| closing | (1.0, 1.0, 8.0, 3.5) | null | gradient |
| blank_visual | null | (0, 0, 10.0, 5.625) | image_bleed |

### Source: Research #01, Sections 1.1-1.2, 2.1-2.3

The 12-column grid (Section 2.1) and safe zones (Section 2.3) inform all template coordinates. Content margin of 0.5" applied universally. Image-feature and title slides use full-bleed images with text overlay zones.

---

## 4. Image Style Tokens

### Decision: Derive from Topic + Tone + Palette

Image style tokens are prompt appendages that ensure visual consistency across all generated images in the deck. They consist of:

- **mood**: Derived from tone (e.g., "professional" -> "clean and authoritative", "storytelling" -> "warm and narrative")
- **color_direction**: Derived from palette (e.g., "predominantly deep blue and warm orange tones with clean white space")
- **style_modifiers[]**: 3-5 terms derived from preferences.style:
  - minimalist: ["clean lines", "ample white space", "simple geometry", "flat colour"]
  - image-rich: ["high detail", "photographic quality", "rich textures", "dramatic lighting"]
  - data-heavy: ["clean infographic style", "structured layouts", "subtle gradients"]
  - diagram-heavy: ["precise lines", "clear labels", "structured flow", "technical illustration"]
  - corporate: ["professional photography", "polished", "brand-consistent", "executive"]
  - creative: ["artistic", "bold composition", "experimental", "vibrant textures"]

---

## 5. Brand Extraction Capability

### Decision: Claude Vision for Logo Analysis

When TalkBrief.branding.logo_path is provided, the skill:
1. Reads the logo file using the Read tool (Claude can see images natively)
2. Identifies 2-3 dominant colours and their approximate hex values
3. Uses those colours as the seed for palette derivation
4. Detects visual characteristics (geometric vs organic, modern vs classic) to inform font selection and image style tokens

This replaces the need for ColorThief/colour-science Python libraries -- Claude's vision capability handles colour extraction directly.

---

## 6. Output Schema Alignment

The skill output must match `src/schemas/style_guide.schema.json` from Phase 1 exactly:

```json
{
  "palette": {
    "primary": "6-char hex",
    "secondary": "6-char hex",
    "accent": "6-char hex",
    "background": "6-char hex",
    "background_alt": "6-char hex",
    "text_primary": "6-char hex",
    "text_muted": "6-char hex",
    "text_on_dark": "6-char hex",    // optional in schema
    "chart_series": ["hex", ...]      // 3-8 colours
  },
  "typography": {
    "heading_font": "string",          // required
    "body_font": "string",             // required
    "mono_font": "string",
    "heading_sizes": {
      "title_slide": number,
      "section_divider": number,
      "slide_heading": number,
      "subheading": number
    },
    "body_size": number,
    "caption_size": number,
    "line_spacing": number
  },
  "layout": {
    "slide_width_inches": 10,
    "slide_height_inches": 5.625,
    "margin_inches": 0.5,
    "templates": { ... per slide type ... }
  },
  "image_style_tokens": {
    "mood": "string",
    "color_direction": "string",
    "style_modifiers": ["string", ...]
  }
}
```

All hex values are 6-character WITHOUT the # prefix (schema pattern: `^[0-9A-Fa-f]{6}$`).
```

- [ ] **Step 2: Commit**

```bash
git add research/synthesis-slide-stylist.md
git commit -m "docs: add research synthesis for slide-stylist skill"
```

---

## Task 2: Test Fixtures for Skill Validation

**Files:**
- Create: `tests/fixtures/minimal_talk_brief.json`
- Create: `tests/fixtures/branded_talk_brief.json`

These fixtures provide test inputs for validating the slide-stylist skill output. The `valid_talk_brief.json` from Phase 1 already has branding with primary_color but no logo_path. We add a minimal brief (no branding at all) and a fully branded brief.

- [ ] **Step 1: Create minimal talk brief fixture**

Create `tests/fixtures/minimal_talk_brief.json`:

```json
{
  "topic": "Introduction to Machine Learning",
  "audience": "Business executives with no technical background",
  "duration_minutes": 20
}
```

- [ ] **Step 2: Create branded talk brief fixture**

Create `tests/fixtures/branded_talk_brief.json`:

```json
{
  "topic": "Q3 Revenue Growth and Strategic Outlook",
  "audience": "Board of directors and senior leadership team",
  "duration_minutes": 45,
  "tone": "professional",
  "key_takeaways": [
    "Revenue grew 23% year-over-year",
    "Three new market segments entered",
    "Operating margin improved to 18%"
  ],
  "branding": {
    "company_name": "Meridian Financial Group",
    "primary_color": "002D72",
    "secondary_color": "4A90D9",
    "font_preference": "Montserrat"
  },
  "preferences": {
    "style": "corporate",
    "slide_count_hint": 30,
    "image_backend": "ollama",
    "resolution": "1080p",
    "include_speaker_notes": true,
    "include_charts": true
  },
  "data_sources": [
    {
      "label": "quarterly_revenue",
      "type": "description",
      "content": "Q1: $12M, Q2: $14M, Q3: $17.2M showing consistent growth"
    }
  ]
}
```

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/minimal_talk_brief.json tests/fixtures/branded_talk_brief.json
git commit -m "test: add minimal and branded talk brief fixtures for slide-stylist validation"
```

---

## Task 3: StyleGuide Validation Tests

**Files:**
- Create: `tests/test_slide_stylist.py`

These tests validate that any StyleGuide JSON produced by the slide-stylist skill conforms to the schema and satisfies design quality rules. They do not invoke the skill directly (the skill is a Claude Code SKILL.md, not Python code) -- instead they validate the output contract.

- [ ] **Step 1: Write the validation test file**

Create `tests/test_slide_stylist.py`:

```python
"""Tests for slide-stylist skill output validation.

These tests verify that StyleGuide JSON files produced by the slide-stylist
skill conform to the schema and satisfy design quality rules derived from
research papers #01, #09, and #10.

To use: run the skill, then run these tests against the output:
  python3 -m pytest tests/test_slide_stylist.py -v
"""

import json
import math
import os
import pytest
from jsonschema import validate, ValidationError

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'schemas')
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
DECK_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'deck')


def load_schema(name):
    path = os.path.join(SCHEMA_DIR, f'{name}.schema.json')
    with open(path) as f:
        return json.load(f)


def load_fixture(name):
    path = os.path.join(FIXTURE_DIR, f'{name}.json')
    with open(path) as f:
        return json.load(f)


def hex_to_rgb(hex_str):
    """Convert 6-char hex string (no #) to (r, g, b) tuple 0-255."""
    return (
        int(hex_str[0:2], 16),
        int(hex_str[2:4], 16),
        int(hex_str[4:6], 16),
    )


def relative_luminance(r, g, b):
    """Calculate relative luminance per WCAG 2.0 formula."""
    def linearize(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(hex1, hex2):
    """Calculate WCAG contrast ratio between two 6-char hex colours."""
    l1 = relative_luminance(*hex_to_rgb(hex1))
    l2 = relative_luminance(*hex_to_rgb(hex2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# --- Schema Conformance Tests ---

class TestStyleGuideSchemaConformance:
    """Verify the fixture file passes schema validation."""

    @pytest.fixture
    def schema(self):
        return load_schema('style_guide')

    def test_valid_fixture_passes_schema(self, schema):
        guide = load_fixture('valid_style_guide')
        validate(instance=guide, schema=schema)

    def test_missing_palette_fails(self, schema):
        guide = {"typography": {"heading_font": "Inter", "body_font": "Inter"}}
        with pytest.raises(ValidationError):
            validate(instance=guide, schema=schema)

    def test_missing_typography_fails(self, schema):
        guide = {
            "palette": {
                "primary": "1A365D", "secondary": "2B6CB0", "accent": "ED8936",
                "background": "FFFFFF", "background_alt": "1A202C",
                "text_primary": "1A202C", "text_muted": "718096"
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=guide, schema=schema)

    def test_invalid_hex_colour_fails(self, schema):
        guide = load_fixture('valid_style_guide')
        guide["palette"]["primary"] = "ZZZZZZ"
        with pytest.raises(ValidationError):
            validate(instance=guide, schema=schema)

    def test_hex_with_hash_prefix_fails(self, schema):
        guide = load_fixture('valid_style_guide')
        guide["palette"]["primary"] = "#1A365D"
        with pytest.raises(ValidationError):
            validate(instance=guide, schema=schema)


# --- Design Quality Tests ---

class TestPaletteQuality:
    """Verify palette satisfies design quality rules from Research #01 and #09."""

    @pytest.fixture
    def guide(self):
        return load_fixture('valid_style_guide')

    def test_text_on_background_contrast_wcag_aa(self, guide):
        """COL-001: text_primary on background must have >= 4.5:1 contrast."""
        ratio = contrast_ratio(
            guide["palette"]["text_primary"],
            guide["palette"]["background"]
        )
        assert ratio >= 4.5, (
            f'text_primary ({guide["palette"]["text_primary"]}) on '
            f'background ({guide["palette"]["background"]}) contrast is '
            f'{ratio:.1f}:1, needs >= 4.5:1'
        )

    def test_text_on_dark_contrast_wcag_aa(self, guide):
        """text_on_dark on background_alt must have >= 4.5:1 contrast."""
        if "text_on_dark" not in guide["palette"]:
            pytest.skip("text_on_dark not present")
        ratio = contrast_ratio(
            guide["palette"]["text_on_dark"],
            guide["palette"]["background_alt"]
        )
        assert ratio >= 4.5, (
            f'text_on_dark ({guide["palette"]["text_on_dark"]}) on '
            f'background_alt ({guide["palette"]["background_alt"]}) contrast is '
            f'{ratio:.1f}:1, needs >= 4.5:1'
        )

    def test_chart_series_minimum_count(self, guide):
        """Chart series must have at least 3 colours (schema minimum)."""
        if "chart_series" not in guide["palette"]:
            pytest.skip("chart_series not present")
        assert len(guide["palette"]["chart_series"]) >= 3

    def test_chart_series_are_distinct(self, guide):
        """Chart series colours must be perceptually distinct (no duplicates)."""
        if "chart_series" not in guide["palette"]:
            pytest.skip("chart_series not present")
        series = guide["palette"]["chart_series"]
        assert len(series) == len(set(series)), "Chart series contains duplicate colours"

    def test_all_palette_values_are_valid_hex(self, guide):
        """Every palette value must be exactly 6 hex characters."""
        import re
        hex_pattern = re.compile(r'^[0-9A-Fa-f]{6}$')
        for key, value in guide["palette"].items():
            if key == "chart_series":
                for colour in value:
                    assert hex_pattern.match(colour), f'chart_series colour {colour} is not valid hex'
            else:
                assert hex_pattern.match(value), f'palette.{key} value {value} is not valid hex'


class TestTypographyQuality:
    """Verify typography satisfies design rules from Research #10."""

    @pytest.fixture
    def guide(self):
        return load_fixture('valid_style_guide')

    def test_heading_font_present(self, guide):
        assert guide["typography"]["heading_font"], "heading_font must not be empty"

    def test_body_font_present(self, guide):
        assert guide["typography"]["body_font"], "body_font must not be empty"

    def test_title_slide_size_minimum(self, guide):
        """TYP-001: Title slide heading >= 36pt (projection minimum)."""
        if "heading_sizes" not in guide["typography"]:
            pytest.skip("heading_sizes not present")
        assert guide["typography"]["heading_sizes"]["title_slide"] >= 36, (
            f'title_slide size {guide["typography"]["heading_sizes"]["title_slide"]}pt '
            f'is below 36pt projection minimum'
        )

    def test_body_size_minimum(self, guide):
        """Body text >= 14pt (absolute minimum for captions)."""
        if "body_size" not in guide["typography"]:
            pytest.skip("body_size not present")
        assert guide["typography"]["body_size"] >= 14

    def test_title_to_body_ratio(self, guide):
        """TYP-004: Title font size / body font size >= 1.33 (Perfect Fourth)."""
        if "heading_sizes" not in guide["typography"]:
            pytest.skip("heading_sizes not present")
        if "body_size" not in guide["typography"]:
            pytest.skip("body_size not present")
        ratio = guide["typography"]["heading_sizes"]["slide_heading"] / guide["typography"]["body_size"]
        assert ratio >= 1.33, (
            f'Heading/body ratio is {ratio:.2f}, needs >= 1.33 (Perfect Fourth)'
        )

    def test_line_spacing_adequate(self, guide):
        """TYP-007: Line spacing >= 1.2."""
        if "line_spacing" not in guide["typography"]:
            pytest.skip("line_spacing not present")
        assert guide["typography"]["line_spacing"] >= 1.2


class TestLayoutQuality:
    """Verify layout templates satisfy rules from Research #01."""

    @pytest.fixture
    def guide(self):
        return load_fixture('valid_style_guide')

    def test_slide_dimensions_16_9(self, guide):
        """PRJ-001: Slide dimensions must be 16:9."""
        if "layout" not in guide:
            pytest.skip("layout not present")
        width = guide["layout"]["slide_width_inches"]
        height = guide["layout"]["slide_height_inches"]
        ratio = width / height
        assert abs(ratio - 16/9) < 0.01, (
            f'Slide aspect ratio {ratio:.3f} is not 16:9 ({16/9:.3f})'
        )

    def test_margin_minimum(self, guide):
        """LAY-001: Margin >= 0.5 inches."""
        if "layout" not in guide:
            pytest.skip("layout not present")
        assert guide["layout"]["margin_inches"] >= 0.5

    def test_templates_have_description(self, guide):
        """Each template should have a description field."""
        if "layout" not in guide or "templates" not in guide["layout"]:
            pytest.skip("layout.templates not present")
        for name, template in guide["layout"]["templates"].items():
            assert "description" in template, f'Template {name} missing description'

    def test_text_zones_within_slide_bounds(self, guide):
        """All text zones must fit within slide dimensions."""
        if "layout" not in guide or "templates" not in guide["layout"]:
            pytest.skip("layout.templates not present")
        w = guide["layout"]["slide_width_inches"]
        h = guide["layout"]["slide_height_inches"]
        for name, template in guide["layout"]["templates"].items():
            if "text_zone" in template and template["text_zone"] is not None:
                tz = template["text_zone"]
                assert tz["x"] >= 0, f'{name} text_zone x < 0'
                assert tz["y"] >= 0, f'{name} text_zone y < 0'
                assert tz["x"] + tz["w"] <= w + 0.01, f'{name} text_zone exceeds slide width'
                assert tz["y"] + tz["h"] <= h + 0.01, f'{name} text_zone exceeds slide height'


class TestImageStyleTokens:
    """Verify image_style_tokens are present and well-formed."""

    @pytest.fixture
    def guide(self):
        return load_fixture('valid_style_guide')

    def test_mood_present(self, guide):
        if "image_style_tokens" not in guide:
            pytest.skip("image_style_tokens not present")
        assert guide["image_style_tokens"]["mood"], "mood must not be empty"

    def test_color_direction_present(self, guide):
        if "image_style_tokens" not in guide:
            pytest.skip("image_style_tokens not present")
        assert guide["image_style_tokens"]["color_direction"], "color_direction must not be empty"

    def test_style_modifiers_present(self, guide):
        if "image_style_tokens" not in guide:
            pytest.skip("image_style_tokens not present")
        mods = guide["image_style_tokens"]["style_modifiers"]
        assert len(mods) >= 2, "Need at least 2 style modifiers"


# --- Live Output Validation ---

class TestLiveStyleGuideOutput:
    """Validate the actual style-guide.json produced by the skill.

    These tests only run when ./tmp/deck/style-guide.json exists.
    After invoking the slide-stylist skill, run:
      python3 -m pytest tests/test_slide_stylist.py::TestLiveStyleGuideOutput -v
    """

    @pytest.fixture
    def schema(self):
        return load_schema('style_guide')

    @pytest.fixture
    def guide(self):
        path = os.path.join(DECK_DIR, 'style-guide.json')
        if not os.path.exists(path):
            pytest.skip("No live style-guide.json -- run slide-stylist skill first")
        with open(path) as f:
            return json.load(f)

    def test_schema_valid(self, schema, guide):
        validate(instance=guide, schema=schema)

    def test_has_all_12_layout_templates(self, guide):
        """The skill must produce templates for all 12 slide types."""
        expected_types = [
            "title", "section_divider", "content", "two_column",
            "image_feature", "data_chart", "stat_callout", "quote",
            "icon_grid", "diagram", "closing", "blank_visual"
        ]
        if "layout" not in guide or "templates" not in guide["layout"]:
            pytest.fail("layout.templates missing from output")
        templates = guide["layout"]["templates"]
        for slide_type in expected_types:
            assert slide_type in templates, f'Missing template for slide type: {slide_type}'

    def test_text_contrast_wcag_aa(self, guide):
        ratio = contrast_ratio(
            guide["palette"]["text_primary"],
            guide["palette"]["background"]
        )
        assert ratio >= 4.5, f'Text contrast {ratio:.1f}:1 below WCAG AA 4.5:1'

    def test_font_pairing_from_known_list(self, guide):
        """Heading font should be from one of the 10 recommended pairings."""
        known_heading_fonts = [
            "Montserrat", "Playfair Display", "Poppins", "Inter",
            "Raleway", "Nunito", "Work Sans", "Oswald",
            "Space Grotesk", "Fira Sans",
        ]
        heading = guide["typography"]["heading_font"]
        assert heading in known_heading_fonts, (
            f'Heading font "{heading}" is not from the 10 recommended pairings: {known_heading_fonts}'
        )

    def test_image_style_tokens_present(self, guide):
        assert "image_style_tokens" in guide, "image_style_tokens missing from output"
        assert guide["image_style_tokens"]["mood"]
        assert guide["image_style_tokens"]["color_direction"]
        assert len(guide["image_style_tokens"]["style_modifiers"]) >= 2
```

- [ ] **Step 2: Run tests against the fixture to verify test infrastructure works**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_slide_stylist.py -v -k "not TestLiveStyleGuideOutput"`

Expected: All fixture-based tests PASS. Live output tests are SKIPPED (no style-guide.json yet).

- [ ] **Step 3: Commit**

```bash
git add tests/test_slide_stylist.py
git commit -m "test: add StyleGuide validation tests for slide-stylist skill"
```

---

## Task 4: Create the slide-stylist Skill

**Files:**
- Create: `.claude/skills/slide-stylist/SKILL.md`

This is the core deliverable. The SKILL.md file IS the implementation -- it is a prompt engineering document that tells Claude Code what to do when the skill is invoked. The skill reads a TalkBrief, derives a complete StyleGuide, validates it against the schema, and writes it to disk.

- [ ] **Step 1: Create the skill directory**

Run:
```bash
mkdir -p .claude/skills/slide-stylist
```

- [ ] **Step 2: Create the SKILL.md file**

Create `.claude/skills/slide-stylist/SKILL.md`:

````markdown
---
name: slide-stylist
description: Derive a complete visual design system (StyleGuide) from a TalkBrief and optional brand assets. Produces palette, typography, layout templates for all 12 slide types, and image style tokens.
argument-hint: [--deck-dir PATH] [--brief-path PATH]
allowed-tools: Bash(python *), Read, Write, Glob
---

# /slide-stylist

Derive a complete StyleGuide from the TalkBrief and write it to the DeckContext. This skill owns all visual design decisions: palette, fonts, layout templates, and image style tokens.

## Parse Arguments

Parse `$ARGUMENTS` for:
- **--deck-dir PATH**: DeckContext directory (default: `./tmp/deck`)
- **--brief-path PATH**: Direct path to a talk brief JSON file (overrides reading from deck-dir)

## Step 1: Read the TalkBrief

Read the TalkBrief input:

If `--brief-path` was provided, read that file directly using the Read tool.

Otherwise, read `{deck-dir}/talk-brief.json` using the Read tool.

If neither exists, stop and tell the user: "No TalkBrief found. Provide a talk brief at ./tmp/deck/talk-brief.json or use --brief-path."

Parse the JSON. Extract these fields for design decisions:
- `topic` (required) -- informs palette mood and font selection
- `audience` (required) -- informs formality level
- `tone` (optional, default "professional") -- primary driver for font and palette selection
- `branding.company_name` (optional) -- used in metadata
- `branding.logo_path` (optional) -- triggers Brand Extraction
- `branding.primary_color` (optional) -- 6-char hex, seeds palette
- `branding.secondary_color` (optional) -- 6-char hex, seeds palette
- `branding.font_preference` (optional) -- overrides font selection
- `preferences.style` (optional, default "image-rich") -- drives image style tokens

## Step 2: Brand Extraction (if brand assets provided)

### 2a: Logo Analysis (if branding.logo_path is set)

Read the logo file using the Read tool. You can see images natively.

Analyse the logo and identify:
1. The 2-3 most dominant/distinctive colours as 6-character hex values (WITHOUT # prefix)
2. Visual character: geometric vs organic, modern vs classic, bold vs refined
3. Any text style cues (serif vs sans-serif, weight)

Use the most saturated/distinctive colour as `extracted_primary`. Use the second colour as `extracted_secondary`. If only one colour is distinctive, derive the secondary using split-complementary hue rotation.

### 2b: Brand Colour Override (if branding.primary_color is set)

If `branding.primary_color` is provided, use it directly as the palette primary -- it takes precedence over logo extraction. If `branding.secondary_color` is also provided, use it as the palette secondary.

If logo was analysed AND explicit colours were provided, the explicit colours win. Log a note that brand colours override logo extraction.

## Step 3: Derive Palette

Build the complete palette object. All values are 6-character hex WITHOUT the # prefix.

### 3a: With brand colours (from Step 2)

Starting from primary_color:

1. **primary**: The provided or extracted primary colour
2. **secondary**: The provided/extracted secondary, OR derive via complementary hue shift (+180 degrees in HSL)
3. **accent**: Derive via split-complementary (+150 degrees from primary in HSL). Should be a warm colour if primary is cool, and vice versa. Must be visually distinct from both primary and secondary.
4. **background**: Near-white tinted with primary hue. Take the primary's hue, set saturation to ~8%, lightness to ~97%. Result should be close to white but with a subtle warm/cool tint matching the brand.
5. **background_alt**: Near-black tinted with primary hue. Take the primary's hue, set saturation to ~15%, lightness to ~12%. This is for dark slides (section dividers, stat callouts, quotes).
6. **text_primary**: Dark colour with high contrast against background. Take the primary's hue, set saturation to ~20%, lightness to ~13%. Must achieve >= 4.5:1 contrast ratio against background.
7. **text_muted**: Mid-grey for secondary text. Take the primary's hue, set saturation to ~10%, lightness to ~40%. Must achieve >= 3:1 contrast ratio against background (large text standard).
8. **text_on_dark**: Light colour for text on background_alt. Take the primary's hue, set saturation to ~5%, lightness to ~93%. Must achieve >= 4.5:1 contrast ratio against background_alt.
9. **chart_series**: Array of 5 perceptually distinct colours anchored to the brand. Include primary and accent, then generate 3 additional colours spread across the hue wheel at sufficient perceptual distance. Ensure each colour achieves >= 3:1 contrast against both background and background_alt.

### 3b: Without brand colours (derive from topic + tone)

Select a curated palette based on topic keywords and tone:

| Condition | Primary | Secondary | Accent | Mood |
|-----------|---------|-----------|--------|------|
| Topic contains "AI", "ML", "tech", "data", "code" | 1A365D | 2B6CB0 | ED8936 | Technical blue |
| Topic contains "finance", "banking", "investment" | 002D72 | 4A90D9 | F5A623 | Corporate navy |
| Topic contains "health", "medical", "wellness" | 0D6B4E | 38A169 | E53E3E | Healing green |
| Topic contains "design", "creative", "art" | 6B46C1 | 9F7AEA | F6AD55 | Creative purple |
| Topic contains "education", "learning", "workshop" | 2C5282 | 4299E1 | FC8181 | Educational blue |
| Topic contains "startup", "product", "launch" | E53E3E | FC8181 | 38A169 | Energetic red |
| Topic contains "sustainability", "climate", "green" | 276749 | 48BB78 | ECC94B | Environmental green |
| Tone is "inspirational" | 744210 | D69E2E | 4299E1 | Warm gold |
| Tone is "provocative" | 9B2C2C | E53E3E | ECC94B | Bold red |
| Default (professional/conversational/none) | 1A365D | 2B6CB0 | ED8936 | Professional blue |

After selecting the base colours, derive the remaining palette fields (background, background_alt, text_primary, text_muted, text_on_dark, chart_series) using the same rules as Step 3a.

### 3c: Contrast Validation

After deriving all palette values, validate these contrast pairings:

1. text_primary on background: MUST be >= 4.5:1
2. text_on_dark on background_alt: MUST be >= 4.5:1
3. text_muted on background: SHOULD be >= 3:1

If any MUST check fails, adjust the text colour: darken text_primary or lighten text_on_dark until the ratio passes. Never adjust the background colours -- they anchor the visual system.

To calculate contrast ratio: convert each hex to RGB (0-255), compute relative luminance using `L = 0.2126 * R' + 0.7152 * G' + 0.0722 * B'` where `R' = (R/255 <= 0.03928) ? R/255/12.92 : ((R/255 + 0.055)/1.055)^2.4`, then `ratio = (lighter + 0.05) / (darker + 0.05)`.

## Step 4: Select Font Pairing

Choose fonts from these 10 Google Font pairings, each with a projection legibility score:

| # | Heading | Body | Mono | Best For | Score |
|---|---------|------|------|----------|-------|
| 1 | Montserrat | Open Sans | JetBrains Mono | General conference, business | 9/10 |
| 2 | Playfair Display | Source Sans Pro | JetBrains Mono | Luxury, editorial keynotes | 7/10 |
| 3 | Poppins | Roboto | JetBrains Mono | Consumer tech, startups | 9/10 |
| 4 | Inter | Inter | JetBrains Mono | Tech, SaaS, data-heavy | 10/10 |
| 5 | Raleway | Lato | JetBrains Mono | Creative, design events | 7/10 |
| 6 | Nunito | Nunito Sans | JetBrains Mono | Education, healthcare | 8/10 |
| 7 | Work Sans | IBM Plex Sans | IBM Plex Mono | Enterprise tech, developer | 9/10 |
| 8 | Oswald | Merriweather | JetBrains Mono | Impact keynotes, bold talks | 7/10 |
| 9 | Space Grotesk | DM Sans | JetBrains Mono | AI/ML, futuristic themes | 8/10 |
| 10 | Fira Sans | Source Serif Pro | Fira Code | Academic, research | 9/10 |

### Selection logic:

1. **If branding.font_preference is set**: Use it as heading_font. Find the best matching body_font from the table above. If font_preference does not match any heading font in the table, use it anyway and pair with Open Sans as body.

2. **Otherwise, select by tone first:**
   - "technical" -> #4 Inter + Inter
   - "professional" -> #1 Montserrat + Open Sans
   - "conversational" -> #3 Poppins + Roboto
   - "inspirational" -> #2 Playfair Display + Source Sans Pro
   - "provocative" -> #8 Oswald + Merriweather
   - "storytelling" -> #5 Raleway + Lato

3. **Then check topic keywords (override tone selection if strong match):**
   - Topic contains "AI", "ML", "machine learning", "data science" -> #4 Inter + Inter
   - Topic contains "startup", "pitch", "product launch" -> #3 Poppins + Roboto
   - Topic contains "design", "creative", "UX" -> #9 Space Grotesk + DM Sans
   - Topic contains "research", "academic", "science", "paper" -> #10 Fira Sans + Source Serif Pro
   - Topic contains "education", "learning", "workshop", "training" -> #6 Nunito + Nunito Sans
   - Topic contains "enterprise", "infrastructure", "platform" -> #7 Work Sans + IBM Plex Sans

4. **If no tone and no keyword match**: Default to #1 Montserrat + Open Sans.

### Typography sizes (fixed -- research-validated defaults):

```json
{
  "heading_sizes": {
    "title_slide": 44,
    "section_divider": 36,
    "slide_heading": 28,
    "subheading": 20
  },
  "body_size": 16,
  "caption_size": 12,
  "line_spacing": 1.4
}
```

## Step 5: Generate Layout Templates

Produce a template for each of the 12 slide types used in the SlideOutline schema. Each template has:
- `description`: One-line purpose
- `text_zone`: `{x, y, w, h}` in inches, or `null` if no text zone
- `image_zone`: `{x, y, w, h}` in inches, or `null` if no image zone
- `background_treatment`: one of "solid_light", "solid_dark", "image_bleed", "pattern_tile", "gradient"

Slide dimensions: 10" wide x 5.625" tall. Margins: 0.5" on all sides.

Generate these exact 12 templates:

```json
{
  "title": {
    "description": "Opening slide with large title, subtitle, and full-bleed background image",
    "text_zone": {"x": 1.0, "y": 1.5, "w": 8.0, "h": 2.5},
    "image_zone": {"x": 0, "y": 0, "w": 10.0, "h": 5.625},
    "background_treatment": "image_bleed"
  },
  "section_divider": {
    "description": "Bold section title on dark background to mark major transitions",
    "text_zone": {"x": 1.0, "y": 1.5, "w": 8.0, "h": 2.5},
    "image_zone": null,
    "background_treatment": "solid_dark"
  },
  "content": {
    "description": "Standard content slide with text left, optional image right",
    "text_zone": {"x": 0.5, "y": 1.0, "w": 5.5, "h": 4.0},
    "image_zone": {"x": 6.5, "y": 0.5, "w": 3.0, "h": 4.625},
    "background_treatment": "solid_light"
  },
  "two_column": {
    "description": "Two equal columns for comparison or parallel content",
    "text_zone": {"x": 0.5, "y": 1.0, "w": 4.0, "h": 4.0},
    "image_zone": {"x": 5.5, "y": 1.0, "w": 4.0, "h": 4.0},
    "background_treatment": "solid_light"
  },
  "image_feature": {
    "description": "Hero image dominates top two-thirds, text caption below",
    "text_zone": {"x": 0.5, "y": 3.5, "w": 9.0, "h": 1.5},
    "image_zone": {"x": 0, "y": 0, "w": 10.0, "h": 3.2},
    "background_treatment": "image_bleed"
  },
  "data_chart": {
    "description": "Chart or data visualisation with declarative title above",
    "text_zone": {"x": 0.5, "y": 0.5, "w": 9.0, "h": 1.0},
    "image_zone": {"x": 0.5, "y": 1.6, "w": 9.0, "h": 3.5},
    "background_treatment": "solid_light"
  },
  "stat_callout": {
    "description": "Giant number or key metric centred on dark background",
    "text_zone": {"x": 1.5, "y": 1.0, "w": 7.0, "h": 3.5},
    "image_zone": null,
    "background_treatment": "solid_dark"
  },
  "quote": {
    "description": "Centred quotation with attribution on dark background",
    "text_zone": {"x": 1.5, "y": 1.0, "w": 7.0, "h": 3.0},
    "image_zone": null,
    "background_treatment": "solid_dark"
  },
  "icon_grid": {
    "description": "Grid of 3-6 icon-label pairs with shared heading",
    "text_zone": {"x": 0.5, "y": 0.5, "w": 9.0, "h": 1.0},
    "image_zone": {"x": 0.5, "y": 1.6, "w": 9.0, "h": 3.5},
    "background_treatment": "solid_light"
  },
  "diagram": {
    "description": "Technical diagram or flowchart with title above",
    "text_zone": {"x": 0.5, "y": 0.5, "w": 9.0, "h": 1.0},
    "image_zone": {"x": 0.5, "y": 1.8, "w": 9.0, "h": 3.3},
    "background_treatment": "solid_light"
  },
  "closing": {
    "description": "Final slide with call-to-action, contact details, gradient background",
    "text_zone": {"x": 1.0, "y": 1.0, "w": 8.0, "h": 3.5},
    "image_zone": null,
    "background_treatment": "gradient"
  },
  "blank_visual": {
    "description": "Full-bleed visual with no text overlay -- breathing room slide",
    "text_zone": null,
    "image_zone": {"x": 0, "y": 0, "w": 10.0, "h": 5.625},
    "background_treatment": "image_bleed"
  }
}
```

## Step 6: Generate Image Style Tokens

Derive tokens that will be appended to all image generation prompts for visual consistency.

### mood

Map the tone to a mood description:
- "professional" -> "clean and authoritative"
- "technical" -> "precise and structured"
- "conversational" -> "warm and approachable"
- "inspirational" -> "uplifting and aspirational"
- "provocative" -> "bold and dramatic"
- "storytelling" -> "warm and narrative"
- No tone -> "professional and calm"

### color_direction

Describe the palette in natural language for image generation prompts. Example format: "predominantly {primary colour name} and {secondary colour name} tones with {background character} space"

Use the actual palette colours. Convert hex to colour names (e.g., 1A365D -> "deep navy blue", ED8936 -> "warm orange", 2B6CB0 -> "medium blue"). Example: "predominantly deep navy blue and medium blue tones with clean white space"

### style_modifiers

Select 3-5 modifiers based on preferences.style:

- "minimalist": ["clean lines", "ample white space", "simple geometry", "flat colour"]
- "image-rich": ["high detail", "photographic quality", "rich textures", "dramatic lighting"]
- "data-heavy": ["clean infographic style", "structured layouts", "subtle gradients", "precise lines"]
- "diagram-heavy": ["precise lines", "clear labels", "structured flow", "technical illustration"]
- "corporate": ["professional photography", "polished finish", "brand-consistent", "executive tone"]
- "creative": ["artistic composition", "bold colours", "experimental textures", "vibrant energy"]
- No style preference: ["clean lines", "minimal", "corporate photography style"]

## Step 7: Assemble and Validate the StyleGuide

Assemble the complete StyleGuide JSON object:

```json
{
  "palette": { ... from Step 3 ... },
  "typography": { ... from Step 4 ... },
  "layout": {
    "slide_width_inches": 10,
    "slide_height_inches": 5.625,
    "margin_inches": 0.5,
    "templates": { ... from Step 5 ... }
  },
  "image_style_tokens": { ... from Step 6 ... }
}
```

### Validation

Before writing, validate the StyleGuide using the Phase 1 infrastructure:

```bash
python3 -c "
import json, sys
sys.path.insert(0, 'src')
from deckcontext import write_contract, init_deck

deck_dir = 'DECK_DIR_VALUE'
init_deck(deck_dir)

style_guide = json.loads('''STYLE_GUIDE_JSON''')

write_contract(deck_dir, 'style-guide', style_guide)
print('StyleGuide validated and written successfully')
"
```

Replace `DECK_DIR_VALUE` with the actual deck-dir path and `STYLE_GUIDE_JSON` with the assembled JSON.

If validation fails (jsonschema.ValidationError), fix the issue and retry. Common fixes:
- Hex values must be exactly 6 characters, no # prefix
- chart_series must have 3-8 items
- heading_font and body_font are required
- palette must include primary, secondary, accent, background, background_alt, text_primary, text_muted

If writing via deckcontext fails for any reason, fall back to writing the JSON file directly:

```bash
python3 -c "
import json
style_guide = json.loads('''STYLE_GUIDE_JSON''')
with open('DECK_DIR/style-guide.json', 'w') as f:
    json.dump(style_guide, f, indent=2)
print('StyleGuide written to DECK_DIR/style-guide.json')
"
```

## Step 8: Update Pipeline State

If a pipeline-state.json exists in the deck directory, update the slide-stylist step:

```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from deckcontext import update_step

deck_dir = 'DECK_DIR_VALUE'
update_step(deck_dir, 'slide-stylist', 'completed', output_file='style-guide.json')
print('Pipeline state updated')
"
```

If pipeline-state.json does not exist, skip this step silently.

## Step 9: Report

Report the following to the user:

1. **Palette summary**: Show the 9 palette colours with their hex values and roles
2. **Font pairing**: Heading font + Body font + Mono font, with the selection rationale
3. **Layout templates**: Confirm all 12 slide types have templates
4. **Image style tokens**: Show mood, color_direction, and style_modifiers
5. **Output path**: The full path to the written style-guide.json
6. **Contrast validation**: Report the text_primary/background and text_on_dark/background_alt contrast ratios

Format as a clean summary, not raw JSON. Example:

```
StyleGuide written to ./tmp/deck/style-guide.json

Palette:
  Primary:        1A365D (deep navy blue)
  Secondary:      2B6CB0 (medium blue)
  Accent:         ED8936 (warm orange)
  Background:     F7FAFC (cool white)
  Background Alt: 1A202C (dark charcoal)
  Text Primary:   1A202C (near-black)    -- contrast 15.2:1 on background [PASS]
  Text Muted:     718096 (slate grey)    -- contrast 4.1:1 on background [PASS]
  Text on Dark:   F7FAFC (cool white)    -- contrast 13.8:1 on background_alt [PASS]
  Chart Series:   2B6CB0, ED8936, 38A169, E53E3E, 805AD5

Typography:
  Heading: Montserrat (Bold 700)
  Body:    Open Sans (Regular 400)
  Mono:    JetBrains Mono
  Reason:  Topic "Building AI Agents" + tone "technical" -> general conference pairing

Layout: 12 templates generated (title, section_divider, content, two_column, image_feature, data_chart, stat_callout, quote, icon_grid, diagram, closing, blank_visual)

Image Style Tokens:
  Mood:            clean and authoritative
  Color Direction: predominantly deep navy blue and medium blue tones with clean white space
  Modifiers:       high detail, photographic quality, rich textures, dramatic lighting
```

Do not ask follow-up questions. Do not offer to modify the StyleGuide. Report and stop.
````

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/slide-stylist/SKILL.md
git commit -m "feat: add slide-stylist skill for StyleGuide derivation"
```

---

## Task 5: Smoke Test -- Minimal Brief (No Branding)

**Files:** None (invocation test)

This task tests the skill with the minimal talk brief fixture (no branding, no preferences, no tone). The skill should derive everything from the topic and audience alone.

- [ ] **Step 1: Set up the DeckContext with a minimal brief**

```bash
source .venv/bin/activate && python3 -c "
import sys
sys.path.insert(0, 'src')
from deckcontext import init_deck, write_contract

init_deck('./tmp/deck')
brief = {
    'topic': 'Introduction to Machine Learning',
    'audience': 'Business executives with no technical background',
    'duration_minutes': 20
}
write_contract('./tmp/deck', 'talk-brief', brief)
print('Minimal brief written to ./tmp/deck/talk-brief.json')
"
```

Expected: Brief written successfully.

- [ ] **Step 2: Invoke the slide-stylist skill**

Run: `/slide-stylist`

Expected: The skill reads the brief, derives a palette (topic contains "Machine Learning" so should use a technical/AI palette), selects Inter + Inter fonts (topic keyword match), generates all 12 layout templates, and writes style-guide.json.

- [ ] **Step 3: Validate the output**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_slide_stylist.py::TestLiveStyleGuideOutput -v`

Expected: All live output tests PASS.

- [ ] **Step 4: Inspect the output manually**

Run: `cat ./tmp/deck/style-guide.json | python3 -m json.tool`

Verify:
- palette has all 9 fields with valid 6-char hex values
- typography has heading_font, body_font, mono_font, heading_sizes, body_size, caption_size, line_spacing
- layout has slide_width_inches=10, slide_height_inches=5.625, margin_inches=0.5, and 12 templates
- image_style_tokens has mood, color_direction, and style_modifiers array

---

## Task 6: Smoke Test -- Branded Brief (With Colours and Font Preference)

**Files:** None (invocation test)

This task tests the skill with full branding input: company name, explicit brand colours, and a font preference.

- [ ] **Step 1: Set up the DeckContext with a branded brief**

```bash
source .venv/bin/activate && python3 -c "
import sys, json
sys.path.insert(0, 'src')
from deckcontext import init_deck, write_contract
import shutil, os

# Clean previous run
if os.path.exists('./tmp/deck'):
    shutil.rmtree('./tmp/deck')

init_deck('./tmp/deck')
with open('tests/fixtures/branded_talk_brief.json') as f:
    brief = json.load(f)
write_contract('./tmp/deck', 'talk-brief', brief)
print('Branded brief written to ./tmp/deck/talk-brief.json')
"
```

Expected: Brief written successfully.

- [ ] **Step 2: Invoke the slide-stylist skill**

Run: `/slide-stylist`

Expected: The skill reads the branded brief with primary_color "002D72", secondary_color "4A90D9", and font_preference "Montserrat". It should use those exact brand colours as palette.primary and palette.secondary, select Montserrat as heading_font (matching the preference to pairing #1), and derive the rest.

- [ ] **Step 3: Validate the output**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_slide_stylist.py::TestLiveStyleGuideOutput -v`

Expected: All live output tests PASS.

- [ ] **Step 4: Verify brand colours are preserved**

Run:
```bash
source .venv/bin/activate && python3 -c "
import json
with open('./tmp/deck/style-guide.json') as f:
    guide = json.load(f)

assert guide['palette']['primary'] == '002D72', f'Expected 002D72, got {guide[\"palette\"][\"primary\"]}'
assert guide['palette']['secondary'] == '4A90D9', f'Expected 4A90D9, got {guide[\"palette\"][\"secondary\"]}'
assert guide['typography']['heading_font'] == 'Montserrat', f'Expected Montserrat, got {guide[\"typography\"][\"heading_font\"]}'
print('Brand colours and font preference correctly preserved')
print(f'Primary: {guide[\"palette\"][\"primary\"]}')
print(f'Secondary: {guide[\"palette\"][\"secondary\"]}')
print(f'Heading font: {guide[\"typography\"][\"heading_font\"]}')
print(f'Body font: {guide[\"typography\"][\"body_font\"]}')
"
```

Expected: Brand colours are exactly "002D72" and "4A90D9". Heading font is "Montserrat". Body font is "Open Sans" (pairing #1 complement).

---

## Task 7: Run Full Test Suite and Commit

**Files:** None (verification)

- [ ] **Step 1: Run the complete test suite**

Run: `source .venv/bin/activate && python3 -m pytest tests/ -v --tb=short`

Expected: All tests PASS (Phase 1 schema tests + Phase 1 deckcontext tests + Phase 1 integration test + Phase 2 slide-stylist validation tests).

- [ ] **Step 2: Verify no test files have syntax errors**

Run: `source .venv/bin/activate && python3 -m py_compile tests/test_slide_stylist.py && echo "Syntax OK"`

Expected: "Syntax OK"

- [ ] **Step 3: Verify the synthesis document exists**

Run: `ls -la research/synthesis-slide-stylist.md`

Expected: File exists.

- [ ] **Step 4: Verify the skill file exists**

Run: `ls -la .claude/skills/slide-stylist/SKILL.md`

Expected: File exists.

- [ ] **Step 5: Final commit (if any files changed during smoke tests)**

```bash
git add -A
git status
# Only commit if there are changes
git commit -m "test: verify slide-stylist skill with minimal and branded brief smoke tests"
```

---

## Summary

After completing all 7 tasks, Phase 2 provides:

| Artifact | Purpose |
|----------|---------|
| `research/synthesis-slide-stylist.md` | Research synthesis bridging papers #01, #09, #10 to skill decisions |
| `.claude/skills/slide-stylist/SKILL.md` | Complete skill definition for StyleGuide derivation |
| `tests/test_slide_stylist.py` | Schema conformance + design quality + live output validation tests |
| `tests/fixtures/minimal_talk_brief.json` | Minimal input fixture (topic + audience + duration only) |
| `tests/fixtures/branded_talk_brief.json` | Full branded input fixture (colours, font preference, data sources) |

**What the slide-stylist skill does:**
1. Reads TalkBrief from DeckContext (or --brief-path)
2. Extracts brand colours from logo (vision) or uses provided hex values
3. Derives a complete palette with WCAG AA contrast validation
4. Selects fonts from 10 scored Google Font pairings based on topic/tone/preference
5. Generates layout templates for all 12 slide types with exact zone coordinates
6. Creates image style tokens (mood, color_direction, style_modifiers) for downstream image generation
7. Validates output against the StyleGuide JSON Schema
8. Writes to `./tmp/deck/style-guide.json` via deckcontext.write_contract()

**Downstream consumers (future phases):**
- Phase 3: `narrative-architect` reads StyleGuide for layout_template assignment per slide
- Phase 4: `imagegen-bridge` reads image_style_tokens for prompt engineering; chart-renderer reads palette for chart colours
- Phase 5: `deck-assembler` reads palette + typography + layout templates for PPTX construction; `deck-qa` reads palette for contrast validation

---

### Critical Files for Implementation
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/docs/superpowers/plans/2026-03-29-phase-1-foundation.md` (format template and Phase 1 dependency details)
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/research/09-brand-extraction-style-transfer.md` (palette derivation algorithms, 60-30-10 rule, WCAG contrast formulas)
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/research/10-font-strategy-typography.md` (10 font pairings with scores, projection sizes, selection guide)
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/research/01-slide-layout-intelligence.md` (12-column grid, 18 archetypes, zone coordinates, machine-checkable rules)
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/deckcontext.py` (Phase 1 dependency -- init_deck, read_contract, write_contract, update_step)
