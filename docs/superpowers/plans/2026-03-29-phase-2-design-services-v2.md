# Phase 2: Design Services -- brand-manager + slide-stylist

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two Claude Code skills (brand-manager and slide-stylist) that together produce a StyleGuide from brand assets and Speaker collaboration, plus Python validation utilities for contrast checking and brand profile management.

**Architecture:** Two SKILL.md files define how Claude extracts brand profiles and derives StyleGuides through collaborative design exploration. Python utilities in `src/` handle brand profile persistence, contrast validation, and schema checking. Both skills use `src/deckcontext.py` (Phase 1) for DeckContext I/O. The BrandProfile schema was created during BSA restructure and is already at `src/schemas/brand_profile.schema.json`.

**Tech Stack:** Claude Code skills (SKILL.md markdown), Python 3.8+ (deckcontext.py, jsonschema, contrast utilities from src/qa/checks/contrast.py), pytest

**Dependencies:**
- Phase 1 (complete): `src/deckcontext.py`, `src/schemas/style_guide.schema.json`, `src/schemas/brand_profile.schema.json`, `src/schemas/talk_brief.schema.json`
- Phase 5 (complete): `src/qa/checks/contrast.py` (reuse `relative_luminance`, `contrast_ratio`)

**Supersedes:** `docs/superpowers/plans/2026-03-29-phase-2-design-services.md` (written for old single-skill architecture)

---

## File Structure

```
research/
  synthesis-brand-manager.md              # Research synthesis for brand-manager
  synthesis-slide-stylist.md              # Research synthesis for slide-stylist
src/
  brand_profile.py                        # Brand profile persistence + validation utilities
  style_validation.py                     # StyleGuide validation (contrast, completeness, compliance)
.claude/
  skills/
    brand-manager/
      SKILL.md                            # brand-manager skill definition
    slide-stylist/
      SKILL.md                            # slide-stylist skill definition
tests/
  test_brand_profile.py                   # Brand profile utility tests
  test_style_validation.py               # Style validation utility tests
  fixtures/
    minimal_talk_brief.json               # Brief with no branding (new)
    branded_talk_brief.json               # Brief with full branding section (new)
    valid_brand_profile.json              # Known-good BrandProfile (new)
```

---

## Task 1: Research Synthesis Documents

**Files:**
- Create: `research/synthesis-brand-manager.md`
- Create: `research/synthesis-slide-stylist.md`

Per CLAUDE.md: "Create `research/synthesis-[skill-name].md` before implementing any skill."

- [ ] **Step 1: Read primary research**

Read and synthesise:
- `research/09-brand-extraction-style-transfer.md` (logo-to-palette, colour enforcement, 60-30-10 rule)
- `research/10-font-strategy-typography.md` (10 font pairings, projection sizes, embedding)
- `research/01-slide-layout-intelligence.md` (grid system, content zones, layout archetypes)
- `docs/architecture/design-services.md` (L1 service document with full design)

- [ ] **Step 2: Write brand-manager synthesis**

Create `research/synthesis-brand-manager.md` covering:
1. **Brand input sources:** PDF extraction strategy, .pptx template parsing, logo vision analysis, manual entry, company-name inference
2. **Palette derivation rules:** 60-30-10 rule, split-complementary accent derivation, WCAG contrast requirements
3. **Persistence model:** `./brands/{brand-id}/` directory structure, `brand-profile.json` schema alignment
4. **Compliance modes:** Strict vs guided — what each locks and what each permits
5. **Speaker approval workflow:** How the brand-manager presents extracted data for confirmation

- [ ] **Step 3: Write slide-stylist synthesis**

Create `research/synthesis-slide-stylist.md` covering:
1. **Collaborative brainstorming workflow:** How options are proposed per design area
2. **Font pairing selection:** Full mapping from tone/topic to the 10 scored pairings from Research #10
3. **Image style token derivation:** Mood, colour direction, and style modifiers from tone + preferences
4. **Layout Intelligence:** 12 layout templates with zone coordinates (deterministic, not collaborative)
5. **Brand constraint application:** How strict and guided modes constrain the design space

- [ ] **Step 4: Commit**

```bash
git add research/synthesis-brand-manager.md research/synthesis-slide-stylist.md
git commit -m "docs: add research synthesis for brand-manager and slide-stylist skills"
```

---

## Task 2: Test Fixtures

**Files:**
- Create: `tests/fixtures/minimal_talk_brief.json`
- Create: `tests/fixtures/branded_talk_brief.json`
- Create: `tests/fixtures/valid_brand_profile.json`

- [ ] **Step 1: Create minimal TalkBrief fixture (no branding)**

Create `tests/fixtures/minimal_talk_brief.json`:

```json
{
  "topic": "Introduction to Machine Learning",
  "audience": "Business analysts with no ML background",
  "duration_minutes": 20,
  "tone": "conversational",
  "key_takeaways": [
    "ML is pattern recognition at scale",
    "You don't need to code to use ML"
  ],
  "preferences": {
    "style": "image-rich",
    "slide_count_hint": 15,
    "image_backend": "ollama",
    "resolution": "1080p",
    "include_speaker_notes": true,
    "include_charts": false
  },
  "data_sources": []
}
```

- [ ] **Step 2: Create branded TalkBrief fixture (full branding)**

Create `tests/fixtures/branded_talk_brief.json`:

```json
{
  "topic": "Q3 Product Roadmap Review",
  "audience": "Engineering leadership team familiar with the product",
  "duration_minutes": 30,
  "tone": "professional",
  "key_takeaways": [
    "Three major features shipping in Q3",
    "Platform reliability target: 99.95%",
    "Team growing from 12 to 18 engineers"
  ],
  "branding": {
    "company_name": "Nexus Technologies",
    "brand_id": "nexus-tech",
    "primary_color": "0F4C81",
    "secondary_color": "6BA3D6",
    "font_preference": "Inter",
    "compliance_mode": "guided"
  },
  "preferences": {
    "style": "data-heavy",
    "slide_count_hint": 25,
    "image_backend": "ollama",
    "resolution": "1080p",
    "include_speaker_notes": true,
    "include_charts": true
  },
  "data_sources": []
}
```

- [ ] **Step 3: Create valid BrandProfile fixture**

Create `tests/fixtures/valid_brand_profile.json`:

```json
{
  "brand_id": "nexus-tech",
  "company_name": "Nexus Technologies",
  "source_inputs": [
    {"type": "manual", "values": {"primary_color": "0F4C81", "secondary_color": "6BA3D6", "font_preference": "Inter"}}
  ],
  "palette": {
    "primary": "0F4C81",
    "secondary": "6BA3D6",
    "accent": "E07A2F",
    "background": "F8FAFC",
    "background_alt": "0D1B2A",
    "text_primary": "1A202C",
    "text_muted": "718096",
    "text_on_dark": "F7FAFC",
    "chart_series": ["0F4C81", "6BA3D6", "E07A2F", "2D9C4A", "C03D3D"]
  },
  "typography": {
    "heading_font": "Inter",
    "body_font": "Inter",
    "mono_font": "JetBrains Mono"
  },
  "approved_image_styles": ["clean corporate photography", "professional data visualisation", "minimal flat icons"],
  "prohibited_image_styles": ["cartoon illustrations", "hand-drawn sketches"],
  "compliance_mode": "guided",
  "extracted_at": "2026-03-29T12:00:00Z",
  "source_hash": "a1b2c3d4e5f6"
}
```

- [ ] **Step 4: Validate fixtures against schemas**

Run:
```bash
source .venv/bin/activate && python3 -c "
import json
from jsonschema import validate

# Validate branded brief
brief = json.load(open('tests/fixtures/branded_talk_brief.json'))
schema = json.load(open('src/schemas/talk_brief.schema.json'))
validate(instance=brief, schema=schema)
print('branded_talk_brief.json validates')

# Validate brand profile
profile = json.load(open('tests/fixtures/valid_brand_profile.json'))
schema = json.load(open('src/schemas/brand_profile.schema.json'))
validate(instance=profile, schema=schema)
print('valid_brand_profile.json validates')
"
```

Expected: Both validate.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/minimal_talk_brief.json tests/fixtures/branded_talk_brief.json tests/fixtures/valid_brand_profile.json
git commit -m "test: add brand-manager and slide-stylist test fixtures"
```

---

## Task 3: Brand Profile Utilities

**Files:**
- Create: `src/brand_profile.py`
- Create: `tests/test_brand_profile.py`

- [ ] **Step 1: Write tests for brand profile utilities**

Create `tests/test_brand_profile.py`:

```python
"""Tests for brand profile persistence and validation utilities."""

import json
import os
import shutil
import pytest

from src.brand_profile import (
    load_brand_profile,
    save_brand_profile,
    brand_profile_exists,
    validate_brand_profile,
    generate_brand_id,
)

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
TEST_BRANDS_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'test-brands')


@pytest.fixture(autouse=True)
def clean_test_brands():
    """Create and clean test brands directory."""
    os.makedirs(TEST_BRANDS_DIR, exist_ok=True)
    yield
    if os.path.exists(TEST_BRANDS_DIR):
        shutil.rmtree(TEST_BRANDS_DIR)


class TestGenerateBrandId:
    def test_lowercases_and_slugifies(self):
        assert generate_brand_id("Acme Corp") == "acme-corp"

    def test_removes_special_chars(self):
        assert generate_brand_id("O'Brien & Sons Ltd.") == "obrien-sons-ltd"

    def test_collapses_multiple_dashes(self):
        assert generate_brand_id("My   Company   Name") == "my-company-name"

    def test_strips_leading_trailing_dashes(self):
        assert generate_brand_id("  Acme  ") == "acme"


class TestSaveAndLoad:
    def test_save_creates_directory_and_file(self):
        profile = json.load(open(os.path.join(FIXTURE_DIR, 'valid_brand_profile.json')))
        save_brand_profile(profile, brands_dir=TEST_BRANDS_DIR)
        expected_path = os.path.join(TEST_BRANDS_DIR, 'nexus-tech', 'brand-profile.json')
        assert os.path.isfile(expected_path)

    def test_load_returns_saved_profile(self):
        profile = json.load(open(os.path.join(FIXTURE_DIR, 'valid_brand_profile.json')))
        save_brand_profile(profile, brands_dir=TEST_BRANDS_DIR)
        loaded = load_brand_profile('nexus-tech', brands_dir=TEST_BRANDS_DIR)
        assert loaded['brand_id'] == 'nexus-tech'
        assert loaded['company_name'] == 'Nexus Technologies'

    def test_load_nonexistent_returns_none(self):
        result = load_brand_profile('nonexistent', brands_dir=TEST_BRANDS_DIR)
        assert result is None


class TestBrandProfileExists:
    def test_returns_false_for_missing(self):
        assert brand_profile_exists('nonexistent', brands_dir=TEST_BRANDS_DIR) is False

    def test_returns_true_for_existing(self):
        profile = json.load(open(os.path.join(FIXTURE_DIR, 'valid_brand_profile.json')))
        save_brand_profile(profile, brands_dir=TEST_BRANDS_DIR)
        assert brand_profile_exists('nexus-tech', brands_dir=TEST_BRANDS_DIR) is True


class TestValidateBrandProfile:
    def test_valid_profile_passes(self):
        profile = json.load(open(os.path.join(FIXTURE_DIR, 'valid_brand_profile.json')))
        errors = validate_brand_profile(profile)
        assert len(errors) == 0

    def test_missing_brand_id_fails(self):
        profile = {"company_name": "Test", "palette": {"primary": "FF0000"},
                    "typography": {}, "compliance_mode": "strict",
                    "extracted_at": "2026-03-29T12:00:00Z"}
        errors = validate_brand_profile(profile)
        assert len(errors) > 0

    def test_invalid_hex_colour_fails(self):
        profile = json.load(open(os.path.join(FIXTURE_DIR, 'valid_brand_profile.json')))
        profile['palette']['primary'] = 'ZZZZZZ'
        errors = validate_brand_profile(profile)
        assert len(errors) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_brand_profile.py -v`

Expected: FAIL — `src.brand_profile` not found.

- [ ] **Step 3: Implement brand profile utilities**

Create `src/brand_profile.py`:

```python
"""Brand profile persistence and validation utilities.

Manages BrandProfile JSON files at ./brands/{brand-id}/brand-profile.json.
Profiles persist across deck sessions for brand reuse.
"""

import json
import os
import re

import jsonschema

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schemas', 'brand_profile.schema.json')
DEFAULT_BRANDS_DIR = './brands'


def generate_brand_id(company_name):
    """Convert a company name to a URL-safe slug."""
    slug = company_name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    slug = slug.strip('-')
    return slug


def _brand_path(brand_id, brands_dir=None):
    """Return the path to a brand profile file."""
    base = brands_dir or DEFAULT_BRANDS_DIR
    return os.path.join(base, brand_id, 'brand-profile.json')


def brand_profile_exists(brand_id, brands_dir=None):
    """Check if a brand profile exists."""
    return os.path.isfile(_brand_path(brand_id, brands_dir))


def load_brand_profile(brand_id, brands_dir=None):
    """Load a brand profile by ID. Returns None if not found."""
    path = _brand_path(brand_id, brands_dir)
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_brand_profile(profile, brands_dir=None):
    """Save a brand profile to ./brands/{brand-id}/brand-profile.json."""
    brand_id = profile['brand_id']
    path = _brand_path(brand_id, brands_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(profile, f, indent=2)
    return path


def validate_brand_profile(profile):
    """Validate a BrandProfile dict against the JSON schema. Returns list of error messages."""
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)
    return [e.message for e in validator.iter_errors(profile)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_brand_profile.py -v`

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/brand_profile.py tests/test_brand_profile.py
git commit -m "feat: add brand profile persistence and validation utilities"
```

---

## Task 4: Style Validation Utilities

**Files:**
- Create: `src/style_validation.py`
- Create: `tests/test_style_validation.py`

- [ ] **Step 1: Write tests for style validation**

Create `tests/test_style_validation.py`:

```python
"""Tests for StyleGuide validation utilities."""

import json
import os
import pytest

from src.style_validation import (
    validate_style_guide,
    check_palette_contrast,
    check_completeness,
    check_brand_compliance,
)

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def _load_fixture(name):
    with open(os.path.join(FIXTURE_DIR, name)) as f:
        return json.load(f)


class TestValidateStyleGuide:
    def test_valid_style_guide_passes(self):
        sg = _load_fixture('valid_style_guide.json')
        errors = validate_style_guide(sg)
        assert len(errors) == 0

    def test_missing_palette_fails(self):
        sg = {"typography": {"heading_font": "Inter", "body_font": "Inter"}, "layout": {}}
        errors = validate_style_guide(sg)
        assert len(errors) > 0


class TestPaletteContrast:
    def test_high_contrast_passes(self):
        palette = {
            'text_primary': '1A202C',
            'background': 'FFFFFF',
            'text_on_dark': 'F7FAFC',
            'background_alt': '1A202C',
            'text_muted': '718096',
        }
        issues = check_palette_contrast(palette)
        assert len(issues) == 0

    def test_low_contrast_fails(self):
        palette = {
            'text_primary': 'CCCCCC',
            'background': 'DDDDDD',
            'text_on_dark': '333333',
            'background_alt': '222222',
            'text_muted': 'EEEEEE',
        }
        issues = check_palette_contrast(palette)
        assert len(issues) > 0

    def test_returns_specific_failing_pairs(self):
        palette = {
            'text_primary': 'CCCCCC',
            'background': 'DDDDDD',
            'text_on_dark': 'F7FAFC',
            'background_alt': '1A202C',
            'text_muted': '718096',
        }
        issues = check_palette_contrast(palette)
        assert any('text_primary' in i for i in issues)


class TestCompleteness:
    def test_all_layout_templates_present(self):
        sg = _load_fixture('valid_style_guide.json')
        # Add all 12 templates
        sg['layout']['templates'] = {
            'title': {}, 'section_divider': {}, 'content': {},
            'two_column': {}, 'image_feature': {}, 'data_chart': {},
            'stat_callout': {}, 'quote': {}, 'icon_grid': {},
            'diagram': {}, 'closing': {}, 'blank_visual': {},
        }
        issues = check_completeness(sg)
        template_issues = [i for i in issues if 'template' in i.lower()]
        assert len(template_issues) == 0

    def test_missing_templates_reported(self):
        sg = _load_fixture('valid_style_guide.json')
        sg['layout']['templates'] = {'content': {}}
        issues = check_completeness(sg)
        assert len(issues) > 0


class TestBrandCompliance:
    def test_strict_mode_passes_when_values_match(self):
        brand = _load_fixture('valid_brand_profile.json')
        brand['compliance_mode'] = 'strict'
        sg = _load_fixture('valid_style_guide.json')
        sg['palette']['primary'] = brand['palette']['primary']
        sg['palette']['secondary'] = brand['palette']['secondary']
        sg['typography']['heading_font'] = brand['typography']['heading_font']
        sg['typography']['body_font'] = brand['typography']['body_font']
        issues = check_brand_compliance(sg, brand)
        assert len(issues) == 0

    def test_strict_mode_fails_when_primary_differs(self):
        brand = _load_fixture('valid_brand_profile.json')
        brand['compliance_mode'] = 'strict'
        sg = _load_fixture('valid_style_guide.json')
        sg['palette']['primary'] = 'FF0000'
        issues = check_brand_compliance(sg, brand)
        assert any('primary' in i for i in issues)

    def test_guided_mode_always_passes(self):
        brand = _load_fixture('valid_brand_profile.json')
        brand['compliance_mode'] = 'guided'
        sg = _load_fixture('valid_style_guide.json')
        sg['palette']['primary'] = 'FF0000'
        issues = check_brand_compliance(sg, brand)
        assert len(issues) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_style_validation.py -v`

Expected: FAIL — `src.style_validation` not found.

- [ ] **Step 3: Implement style validation utilities**

Create `src/style_validation.py`:

```python
"""StyleGuide validation utilities.

Validates StyleGuide outputs for contrast, completeness, and brand compliance.
Reuses contrast functions from src/qa/checks/contrast.py.
"""

import json
import os

import jsonschema

from src.qa.checks.contrast import relative_luminance, contrast_ratio

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schemas', 'style_guide.schema.json')

REQUIRED_LAYOUT_TEMPLATES = [
    'title', 'section_divider', 'content', 'two_column',
    'image_feature', 'data_chart', 'stat_callout', 'quote',
    'icon_grid', 'diagram', 'closing', 'blank_visual',
]

# Minimum contrast ratios
MIN_CONTRAST_NORMAL = 4.5   # WCAG AA
MIN_CONTRAST_PROJECTION = 7.0  # Conference projection recommendation

# Palette pairings to validate: (foreground_key, background_key, min_ratio)
CONTRAST_PAIRS = [
    ('text_primary', 'background', MIN_CONTRAST_PROJECTION),
    ('text_on_dark', 'background_alt', MIN_CONTRAST_PROJECTION),
    ('text_muted', 'background', MIN_CONTRAST_NORMAL),
]


def _hex_to_rgb(hex_str):
    """Convert 6-char hex string to (r, g, b) tuple."""
    return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))


def validate_style_guide(style_guide):
    """Validate a StyleGuide dict against the JSON schema. Returns list of error messages."""
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)
    return [e.message for e in validator.iter_errors(style_guide)]


def check_palette_contrast(palette):
    """Check that palette colour pairings meet contrast requirements. Returns list of issue strings."""
    issues = []
    for fg_key, bg_key, min_ratio in CONTRAST_PAIRS:
        fg_hex = palette.get(fg_key)
        bg_hex = palette.get(bg_key)
        if not fg_hex or not bg_hex:
            continue
        fg_rgb = _hex_to_rgb(fg_hex)
        bg_rgb = _hex_to_rgb(bg_hex)
        ratio = contrast_ratio(fg_rgb, bg_rgb)
        if ratio < min_ratio:
            issues.append(
                f'{fg_key} on {bg_key}: contrast {ratio:.1f}:1 below minimum {min_ratio}:1'
            )
    return issues


def check_completeness(style_guide):
    """Check that all required fields and templates are present. Returns list of issue strings."""
    issues = []
    templates = style_guide.get('layout', {}).get('templates', {})
    missing = [t for t in REQUIRED_LAYOUT_TEMPLATES if t not in templates]
    if missing:
        issues.append(f'Missing layout templates: {", ".join(missing)}')

    typography = style_guide.get('typography', {})
    if not typography.get('heading_font'):
        issues.append('Missing heading_font in typography')
    if not typography.get('body_font'):
        issues.append('Missing body_font in typography')

    palette = style_guide.get('palette', {})
    if not palette.get('chart_series'):
        issues.append('Missing chart_series in palette')

    return issues


def check_brand_compliance(style_guide, brand_profile):
    """Check StyleGuide compliance with BrandProfile. Returns list of issue strings.

    In strict mode, brand palette and font values must appear unchanged.
    In guided mode, no enforcement (brand is advisory).
    """
    if brand_profile.get('compliance_mode') != 'strict':
        return []

    issues = []
    bp_palette = brand_profile.get('palette', {})
    sg_palette = style_guide.get('palette', {})

    for key in ['primary', 'secondary']:
        bp_val = bp_palette.get(key)
        sg_val = sg_palette.get(key)
        if bp_val and sg_val and bp_val.lower() != sg_val.lower():
            issues.append(
                f'Strict compliance: palette.{key} is {sg_val} but brand mandates {bp_val}'
            )

    bp_typo = brand_profile.get('typography', {})
    sg_typo = style_guide.get('typography', {})
    for key in ['heading_font', 'body_font']:
        bp_val = bp_typo.get(key)
        sg_val = sg_typo.get(key)
        if bp_val and sg_val and bp_val != sg_val:
            issues.append(
                f'Strict compliance: typography.{key} is "{sg_val}" but brand mandates "{bp_val}"'
            )

    return issues
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_style_validation.py -v`

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/style_validation.py tests/test_style_validation.py
git commit -m "feat: add StyleGuide validation utilities (contrast, completeness, brand compliance)"
```

---

## Task 5: brand-manager Skill Definition

**Files:**
- Create: `.claude/skills/brand-manager/SKILL.md`

- [ ] **Step 1: Read the research synthesis and design services doc**

Read:
- `research/synthesis-brand-manager.md`
- `docs/architecture/design-services.md` (Brand Profile Management section)
- `src/schemas/brand_profile.schema.json`

- [ ] **Step 2: Write the brand-manager skill**

Create `.claude/skills/brand-manager/SKILL.md`:

```markdown
---
name: brand-manager
description: Create, load, or update a reusable BrandProfile from brand assets (PDF guidelines, .pptx template, logo, manual input). Persists profiles for cross-deck reuse.
argument-hint: [--deck-dir PATH] [--brands-dir PATH]
allowed-tools: Bash(python *), Read, Glob, Write
---

# /brand-manager

Create or load a reusable BrandProfile from brand assets. Profiles persist at `./brands/{brand-id}/` for reuse across multiple deck sessions.

## Prerequisites

- `./tmp/deck/talk-brief.json` must exist (produced by the Speaker via Deck Conductor)

## Usage

Invoked by the Deck Conductor before slide-stylist. Can also be invoked directly:

```
/brand-manager
/brand-manager --brands-dir ./brands
```

## What It Does

### Step 1: Read TalkBrief Branding Section

Read `./tmp/deck/talk-brief.json` and examine the `branding` object. Determine which inputs are available:

| Field | What It Means |
|-------|---------------|
| `brand_id` | Load an existing profile from `./brands/{brand_id}/brand-profile.json` |
| `brand_guidelines_path` | Read the PDF and extract mandated colours, fonts, spacing rules, logo usage |
| `template_pptx_path` | Read the .pptx and extract slide master colours, fonts, layouts |
| `logo_path` | View the logo image and extract dominant colours and visual character |
| `primary_color` + `secondary_color` | Use as direct palette seeds |
| `font_preference` | Use as heading_font, select complementary body_font |
| `company_name` (only) | Infer appropriate defaults from industry/domain context |
| `compliance_mode` | `strict` or `guided` (default: `guided`) |

### Step 2: Load or Extract

**If `brand_id` is present and profile exists:**

```bash
source .venv/bin/activate && python3 -c "
from src.brand_profile import load_brand_profile
import json
profile = load_brand_profile('BRAND_ID')
if profile:
    print(json.dumps(profile, indent=2))
else:
    print('NOT FOUND')
"
```

If found, present the profile to the Speaker:
> "I found an existing brand profile for **{company_name}**. Here's what it contains:
> - Primary: #{primary}, Secondary: #{secondary}, Accent: #{accent}
> - Fonts: {heading_font} / {body_font}
> - Compliance: {compliance_mode}
> - Last extracted: {extracted_at}
>
> **Is this still current, or should I re-extract from updated assets?**"

If the Speaker confirms, copy to `./tmp/deck/brand-profile.json` and exit.

**If brand assets are provided, extract a new profile:**

1. **PDF guidelines:** Read the file using the Read tool. Look for:
   - Mandated hex colours (primary, secondary, accent)
   - Approved font families
   - Logo usage rules
   - Colour usage rules (what's prohibited)
   - Image style guidance

2. **Corporate .pptx template:** Read the file. Look for:
   - Slide master background colours
   - Title and body font families and sizes
   - Accent colours used in shapes/lines

3. **Logo image:** View the image using the Read tool. Identify:
   - 2-3 dominant colours and approximate hex values
   - Visual character: geometric vs organic, modern vs classic, bold vs subtle

4. **Manual colours/fonts:** Use directly as palette seeds.

5. **Company name only:** Infer from topic and company context:
   - Tech company → blues, greys, Inter/Work Sans
   - Finance → navy, gold, Montserrat/Open Sans
   - Creative → vibrant, Raleway/Lato
   - Default → professional blue palette (primary: 1A365D)

### Step 3: Derive Full Palette

From the extracted seed colours, derive a complete palette following the 60-30-10 rule:

- **primary** — main brand colour (from extraction)
- **secondary** — supporting brand colour (from extraction, or analogous to primary)
- **accent** — split-complementary hue rotation (+150° from primary)
- **background** — near-white tinted with primary hue (lightness ~0.97)
- **background_alt** — near-black tinted with primary hue (lightness ~0.12)
- **text_primary** — dark neutral ensuring 7:1+ contrast on background
- **text_muted** — medium grey ensuring 4.5:1+ contrast on background
- **text_on_dark** — near-white ensuring 7:1+ contrast on background_alt
- **chart_series** — 5 perceptually distinct colours anchored to brand palette

**Validate contrast:** All text/background pairings must meet WCAG AA (4.5:1) minimum. Target 7:1 for projection readability.

### Step 4: Present to Speaker for Approval

> "Here's the brand profile I've extracted for **{company_name}**:
>
> **Palette:**
> - Primary: #{primary} | Secondary: #{secondary} | Accent: #{accent}
> - Background: #{background} | Alt: #{background_alt}
> - Text: #{text_primary} on light, #{text_on_dark} on dark
>
> **Typography:** {heading_font} / {body_font}
>
> **Image styles approved:** {approved_image_styles}
> **Image styles prohibited:** {prohibited_image_styles}
>
> **Compliance mode:** {compliance_mode}
>
> **Does this look right? Any adjustments?**"

Apply any Speaker corrections.

### Step 5: Persist

```bash
source .venv/bin/activate && python3 -c "
import json
from src.brand_profile import save_brand_profile, validate_brand_profile

profile = json.load(open('./tmp/deck/brand-profile.json'))
errors = validate_brand_profile(profile)
if errors:
    print('Validation errors:', errors)
else:
    path = save_brand_profile(profile)
    print(f'Brand profile saved to {path}')
"
```

Save the profile to both:
- `./brands/{brand-id}/brand-profile.json` (persistent)
- `./tmp/deck/brand-profile.json` (current deck session)

## Output

`./brands/{brand-id}/brand-profile.json` and `./tmp/deck/brand-profile.json`

## Design Rules

- All hex values are 6 characters WITHOUT the # prefix
- Compliance mode defaults to `guided` if not specified
- Never skip the Speaker approval step — even for cached profiles
- If no brand assets are provided at all, still produce a minimal BrandProfile with inferred defaults
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/brand-manager/
git commit -m "feat: add brand-manager skill for reusable brand profile extraction"
```

---

## Task 6: slide-stylist Skill Definition

**Files:**
- Create: `.claude/skills/slide-stylist/SKILL.md`

- [ ] **Step 1: Read the research synthesis and design services doc**

Read:
- `research/synthesis-slide-stylist.md`
- `research/10-font-strategy-typography.md` (10 font pairings table)
- `docs/architecture/design-services.md` (Style Derivation section)
- `src/schemas/style_guide.schema.json`

- [ ] **Step 2: Write the slide-stylist skill**

Create `.claude/skills/slide-stylist/SKILL.md`:

```markdown
---
name: slide-stylist
description: Derive a complete StyleGuide through collaborative design exploration with the Speaker, working within brand constraints when a BrandProfile exists.
argument-hint: [--deck-dir PATH]
allowed-tools: Bash(python *), Read, Glob, Write
---

# /slide-stylist

Derive a complete StyleGuide (palette, typography, layout templates, image style tokens) through collaborative exploration with the Speaker.

## Prerequisites

- `./tmp/deck/talk-brief.json` must exist
- `./tmp/deck/brand-profile.json` may exist (produced by brand-manager)

## Usage

Invoked by the Deck Conductor after brand-manager. Can also be invoked directly:

```
/slide-stylist
/slide-stylist --deck-dir ./tmp/deck
```

## What It Does

### Step 1: Read Inputs

Read `./tmp/deck/talk-brief.json` for topic, audience, tone, and preferences.
Read `./tmp/deck/brand-profile.json` if it exists for brand constraints.

Determine the design mode:
- **BrandProfile with strict compliance:** Palette and fonts locked. Only propose accent, image mood, layout preferences.
- **BrandProfile with guided compliance:** Brand provides foundation. Propose variations.
- **No BrandProfile:** Full creative latitude.

### Step 2: Palette Direction

**With strict brand:** Skip — use BrandProfile palette directly. Tell the Speaker:
> "Using your brand palette (strict compliance). Primary: #{primary}, Secondary: #{secondary}."

**With guided brand:** Propose 2-3 variations:
> "Your brand palette starts with Primary: #{primary}. Here are three accent directions:
> 1. **Split-complementary warm:** Accent #{accent1} — energetic, draws attention to CTAs
> 2. **Analogous cool:** Accent #{accent2} — cohesive, professional feel
> 3. **Triadic balanced:** Accent #{accent3} — vibrant, good for data-heavy decks
>
> Which direction? (Or suggest your own)"

**No brand:** Propose 2-3 complete palettes based on topic + tone:
> "For a **{tone}** talk about **{topic}**, here are three palette directions:
> 1. **{name1}:** Primary #{p1}, Secondary #{s1}, Accent #{a1} — {description}
> 2. **{name2}:** Primary #{p2}, Secondary #{s2}, Accent #{a2} — {description}
> 3. **{name3}:** Primary #{p3}, Secondary #{s3}, Accent #{a3} — {description}
>
> Which direction? (Or describe what you're looking for)"

After Speaker selects, derive the full palette (background, text colours, chart series) ensuring all contrast ratios meet thresholds.

### Step 3: Font Pairing

**With brand font preference:** Use brand font as heading, select best body complement:
> "Using **{brand_font}** for headings (per brand). For body text, I recommend **{body_font}** — {rationale}. Does that work?"

**Without brand font:** Select from the 10 scored pairings based on tone and topic:

| Tone | Recommended Pairing |
|------|-------------------|
| technical | Inter (single family) — #4 |
| professional | Montserrat + Open Sans — #1 |
| conversational | Montserrat + Open Sans — #1 |
| inspirational | Playfair Display + Source Sans Pro — #2 |
| provocative | Oswald + Merriweather — #8 |
| storytelling | Raleway + Lato — #5 |

Topic keyword overrides:
- AI/ML/data/engineering/developer → Inter or Work Sans + IBM Plex Sans
- startup/pitch/product → Poppins + Roboto
- design/creative/art → Raleway + Lato or Space Grotesk + DM Sans
- research/academic/science → Fira Sans + Source Serif Pro

Present the recommendation:
> "For a **{tone}** talk about **{topic}**, I recommend:
> - **Heading:** {heading_font}
> - **Body:** {body_font}
> - **Code:** {mono_font}
>
> {brief rationale}. Does this feel right?"

### Step 4: Image Style Tokens

Derive from tone + preferences.style + palette:

> "For the visual style of generated images, I suggest:
> - **Mood:** {mood}
> - **Colour direction:** {color_direction}
> - **Style:** {style_modifiers}
>
> This means images will have a {description}. Does that match your vision?"

Mood mapping:
- professional → "clean and authoritative"
- conversational → "friendly and approachable"
- technical → "precise and structured"
- inspirational → "bold and aspirational"
- provocative → "edgy and thought-provoking"
- storytelling → "warm and narrative"

Style modifier mapping from preferences.style:
- minimalist → ["clean lines", "ample white space", "simple geometry", "flat colour"]
- image-rich → ["high detail", "photographic quality", "rich textures", "dramatic lighting"]
- data-heavy → ["clean infographic style", "structured layouts", "subtle gradients"]
- diagram-heavy → ["precise lines", "clear labels", "structured flow", "technical illustration"]
- corporate → ["professional photography", "polished", "brand-consistent", "executive"]
- creative → ["artistic", "bold composition", "experimental", "vibrant textures"]

### Step 5: Produce StyleGuide

Assemble the final StyleGuide with:
- Agreed palette (all 10 colour values)
- Agreed typography (heading_font, body_font, mono_font, heading_sizes, body_size, caption_size, line_spacing)
- All 12 layout templates (these are fixed engineering constants, not design choices):

| Slide Type | text_zone (x,y,w,h) | image_zone (x,y,w,h) | background_treatment |
|---|---|---|---|
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

- Agreed image style tokens (mood, color_direction, style_modifiers[])

Font sizes (fixed defaults from Research #10):
- title_slide: 44, section_divider: 36, slide_heading: 28, subheading: 20
- body_size: 16, caption_size: 12, line_spacing: 1.4

Layout dimensions (fixed):
- slide_width_inches: 10, slide_height_inches: 5.625, margin_inches: 0.5

### Step 6: Validate and Write

Validate the StyleGuide before writing:

```bash
source .venv/bin/activate && python3 -c "
import json
from src.style_validation import validate_style_guide, check_palette_contrast, check_completeness
sg = json.load(open('./tmp/deck/style-guide.json'))
schema_errors = validate_style_guide(sg)
contrast_issues = check_palette_contrast(sg.get('palette', {}))
completeness_issues = check_completeness(sg)
for e in schema_errors: print(f'SCHEMA: {e}')
for e in contrast_issues: print(f'CONTRAST: {e}')
for e in completeness_issues: print(f'COMPLETENESS: {e}')
if not schema_errors and not contrast_issues and not completeness_issues:
    print('StyleGuide validates successfully')
"
```

If validation fails, fix the issues and re-validate. Write the validated StyleGuide to `./tmp/deck/style-guide.json`.

## Output

`./tmp/deck/style-guide.json`

## Design Rules

- All hex values are 6 characters WITHOUT the # prefix (PptxGenJS convention)
- Left-align body text, centre only titles
- Target 7:1+ contrast ratio for all text/background pairs (projection readability)
- Never skip the Speaker collaboration steps — always propose and get approval
- Layout templates are fixed constants — do not ask the Speaker about coordinates
- Font sizes are fixed defaults — do not ask the Speaker about point sizes
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/slide-stylist/
git commit -m "feat: add slide-stylist skill for collaborative StyleGuide derivation"
```

---

## Task 7: Schema Tests for New Fixtures

**Files:**
- Modify: `tests/test_schemas.py`

- [ ] **Step 1: Add BrandProfile schema tests**

Add to `tests/test_schemas.py`:

```python
class TestBrandProfileSchema:
    def test_valid_profile(self):
        profile = json.load(open('tests/fixtures/valid_brand_profile.json'))
        schema = json.load(open('src/schemas/brand_profile.schema.json'))
        validate(instance=profile, schema=schema)

    def test_missing_brand_id_fails(self):
        schema = json.load(open('src/schemas/brand_profile.schema.json'))
        profile = {"company_name": "Test", "palette": {"primary": "FF0000"},
                    "typography": {}, "compliance_mode": "strict",
                    "extracted_at": "2026-03-29T12:00:00Z"}
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=schema)

    def test_invalid_compliance_mode_fails(self):
        profile = json.load(open('tests/fixtures/valid_brand_profile.json'))
        profile['compliance_mode'] = 'invalid'
        schema = json.load(open('src/schemas/brand_profile.schema.json'))
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=schema)
```

- [ ] **Step 2: Add branded TalkBrief schema test**

Add to `tests/test_schemas.py`:

```python
class TestTalkBriefBrandingExtensions:
    def test_branded_brief_validates(self):
        brief = json.load(open('tests/fixtures/branded_talk_brief.json'))
        schema = json.load(open('src/schemas/talk_brief.schema.json'))
        validate(instance=brief, schema=schema)

    def test_brand_id_pattern_enforced(self):
        brief = json.load(open('tests/fixtures/branded_talk_brief.json'))
        brief['branding']['brand_id'] = 'INVALID CAPS'
        schema = json.load(open('src/schemas/talk_brief.schema.json'))
        with pytest.raises(ValidationError):
            validate(instance=brief, schema=schema)
```

- [ ] **Step 3: Run all schema tests**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_schemas.py -v`

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_schemas.py
git commit -m "test: add BrandProfile and branded TalkBrief schema tests"
```

---

## Task 8: Run Full Test Suite and Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Run all tests**

Run: `source .venv/bin/activate && python3 -m pytest tests/ -v`

Expected: All tests PASS (327 existing + new Phase 2 tests).

- [ ] **Step 2: Update CLAUDE.md implementation table**

Add to the implementation table:

```
| Brand profile utils | `src/brand_profile.py` | N | Done |
| Style validation | `src/style_validation.py` | N | Done |
```

Update Phase 2 status from "planned, NEXT" to "COMPLETE".

- [ ] **Step 3: Mark old plan as superseded**

Add a note at the top of `docs/superpowers/plans/2026-03-29-phase-2-design-services.md`:

```markdown
> **SUPERSEDED** by `docs/superpowers/plans/2026-03-29-phase-2-design-services-v2.md`. The architecture was restructured to elevate Brand Profile Management to its own L2 service. This plan is retained for historical reference.
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs/superpowers/plans/2026-03-29-phase-2-design-services.md
git commit -m "docs: update CLAUDE.md with Phase 2 completion status"
```

---

### Critical Files for Implementation

- `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/brand-manager/SKILL.md` — the brand-manager skill that extracts and persists reusable BrandProfiles
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/slide-stylist/SKILL.md` — the slide-stylist skill with collaborative brainstorming workflow
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/brand_profile.py` — brand profile persistence utilities (save, load, validate, generate_brand_id)
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/style_validation.py` — StyleGuide validation (contrast, completeness, brand compliance)
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/docs/architecture/design-services.md` — L1 service document (the authoritative design reference)
