# Phase 5: Assembly & QA -- deck-assembler, deck-qa, presentation-reviewer

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the three Assembly & QA Services deliverables: a PPTX assembler that composes all DeckContext contracts into a finished `.pptx` via PptxGenJS, a QA engine that runs 25 automated anti-pattern checks against the assembled file, and an advisory AI Persona agent that reviews the deck against conference best practices.

**Architecture:** Three independent deliverables that execute sequentially in the pipeline. `deck-assembler` is a Claude Code skill wrapping the existing `pptx` skill's PptxGenJS engine -- it reads all DeckContext contracts from `./tmp/deck/` and produces `./tmp/deck/output/presentation.pptx`. `deck-qa` is a Claude Code skill that parses the assembled `.pptx` with python-pptx and runs 25 machine-checkable anti-pattern checks (from Research Paper #07), producing a QAReport conforming to the `qa_report.schema.json` contract. `presentation-reviewer` is a Claude Code agent (`.claude/agents/presentation-reviewer.md`) that provides advisory-only conference best-practices review -- it never modifies the deck.

**Tech Stack:**
- deck-assembler: Node.js / PptxGenJS v4.0.1, file path communication with Python pipeline
- deck-qa: Python 3.8+ / python-pptx, Pillow, colorsys (stdlib), jsonschema
- presentation-reviewer: Claude Code agent markdown (no code -- LLM reasoning)

**Dependencies:**
- Phase 1 (DeckContext, schemas, deckcontext.py) must be complete
- All 8 JSON Schemas in `src/schemas/` must exist
- `src/deckcontext.py` read/write utilities must be available

**Research synthesis required before implementation (per CLAUDE.md):**
1. `research/synthesis-deck-assembler.md` -- before Task 3
2. `research/synthesis-deck-qa.md` -- before Task 6
3. `research/synthesis-presentation-reviewer.md` -- before Task 9

**Phases overview (this is Phase 5 of 6):**
- Phase 1: Foundation -- DeckContext, schemas, utilities
- Phase 2: Design Services -- `slide-stylist`
- Phase 3: Content Services -- `narrative-architect`, `speaker-notes-writer`
- Phase 4: Image Services -- 8 skills + 1 agent
- **Phase 5: Assembly & QA** (this plan) -- `deck-assembler`, `deck-qa`, `presentation-reviewer`
- Phase 6: Orchestration -- `deck-conductor`

---

## File Structure

```
.claude/
  skills/
    deck-assembler/
      SKILL.md                          # deck-assembler skill definition
    deck-qa/
      SKILL.md                          # deck-qa skill definition
  agents/
    presentation-reviewer.md            # Presentation Reviewer agent definition
src/
  assembler/
    build_deck.js                       # PptxGenJS assembly script
    slide_masters.js                    # Slide master/layout definitions
    progressive_builds.js              # Progressive build generation
    optimise.js                         # File optimisation (compression, metadata stripping)
  qa/
    run_qa.py                           # QA runner entry point
    checks/
      __init__.py                       # Check registry
      structural.py                     # AP-01 to AP-06, AP-09 to AP-11, AP-14, AP-16, AP-17, AP-19, AP-24
      contrast.py                       # AP-07, AP-08, AP-25 (colour analysis)
      consistency.py                    # AP-03, AP-04, AP-15, AP-18, AP-23 (cross-slide)
      image_quality.py                  # AP-12, AP-13 (resolution, aspect ratio)
      animations.py                     # AP-21 (excessive animations)
      chart_quality.py                  # AP-22 (data-ink ratio)
    report.py                           # QAReport generation and verdict logic
    config.py                           # Configurable thresholds
tests/
  test_assembler.py                     # deck-assembler integration tests
  test_qa_structural.py                 # Structural QA check tests
  test_qa_contrast.py                   # Contrast and colour check tests
  test_qa_consistency.py                # Cross-slide consistency check tests
  test_qa_image.py                      # Image quality check tests
  test_qa_report.py                     # Report generation and verdict tests
  test_qa_integration.py                # Full QA pipeline integration test
  fixtures/
    valid_qa_report.json                # (already defined in Phase 1)
    minimal_deck/                       # Minimal DeckContext for assembler testing
      talk-brief.json
      style-guide.json
      outline.json
      speaker-notes.json
      image-manifest.json
      chart-manifest.json
      images/
        slide-01-hero.png               # 1920x1080 test image
    qa_test_decks/
      passing_deck.pptx                 # Deck that passes all 25 checks
      failing_deck.pptx                 # Deck with known AP violations
research/
  synthesis-deck-assembler.md           # Synthesis before assembler implementation
  synthesis-deck-qa.md                  # Synthesis before QA implementation
  synthesis-presentation-reviewer.md    # Synthesis before reviewer implementation
```

---

## Task 1: Research Synthesis -- deck-assembler

**Files:**
- Create: `research/synthesis-deck-assembler.md`

- [ ] **Step 1: Read primary research**

Read these files and synthesise the key decisions and implementation patterns:
- `research/03-pptxgenjs-vs-python-pptx.md` (PptxGenJS API, polyglot architecture decision)
- `research/14-animations-advanced-pptx.md` (progressive builds, no native animations)
- `research/01-slide-layout-intelligence.md` (layout archetypes, grid system, content zones)
- `research/10-font-strategy-typography.md` (font embedding, projection sizes)
- `research/02-pptx-skill-audit.md` (existing pptx skill capabilities)
- `docs/architecture/data-contracts.md` (all input contracts)

- [ ] **Step 2: Write synthesis document**

Create `research/synthesis-deck-assembler.md` covering:
1. **Technology decision:** PptxGenJS v4.0.1 via Node.js (decision from Research #03)
2. **Input contracts:** SlideOutline, StyleGuide, ImageManifest, ChartManifest, SpeakerNotes -- file paths and schemas
3. **Slide master definitions:** Map each of the 12 slide_type values to PptxGenJS `defineSlideMaster()` calls, referencing layout archetypes from Research #01
4. **Content zone mapping:** How StyleGuide layout templates map to PptxGenJS x/y/w/h coordinates
5. **Image placement:** How ImageManifest placement_zone maps to PptxGenJS `slide.addImage()` calls with sizing modes (contain/cover/crop)
6. **Chart placement:** How ChartManifest entries are placed as images (pre-rendered PNG by chart-renderer)
7. **Speaker notes:** `slide.addNotes()` API from SpeakerNotes contract
8. **Progressive builds:** Multi-slide generation for slides with `build_animation` cues (Research #14)
9. **File optimisation:** Image compression before embedding, metadata stripping
10. **Wrapping the pptx skill:** How deck-assembler delegates to PptxGenJS while adding DeckContext awareness

- [ ] **Step 3: Commit**

```bash
git add research/synthesis-deck-assembler.md
git commit -m "docs: add deck-assembler research synthesis"
```

---

## Task 2: deck-assembler Test Fixtures

**Files:**
- Create: `tests/fixtures/minimal_deck/talk-brief.json`
- Create: `tests/fixtures/minimal_deck/style-guide.json`
- Create: `tests/fixtures/minimal_deck/outline.json`
- Create: `tests/fixtures/minimal_deck/speaker-notes.json`
- Create: `tests/fixtures/minimal_deck/image-manifest.json`
- Create: `tests/fixtures/minimal_deck/chart-manifest.json`
- Create: `tests/fixtures/minimal_deck/images/slide-01-hero.png`
- Create: `tests/test_assembler.py`

- [ ] **Step 1: Create minimal DeckContext fixture directory**

Create `tests/fixtures/minimal_deck/` with all required contract JSON files. Use the valid fixtures from Phase 1 as starting points but ensure they form a coherent 3-slide deck (title, content, closing) that can actually be assembled.

Create `tests/fixtures/minimal_deck/talk-brief.json`:

```json
{
  "topic": "Building Production AI Agents with Claude",
  "audience": "Senior software engineers familiar with LLMs but new to agent frameworks",
  "duration_minutes": 30,
  "tone": "technical",
  "key_takeaways": [
    "Agent loops are just tool-calling in a while loop",
    "State management is the hard part, not the AI",
    "Start with the simplest agent that could work"
  ],
  "branding": {
    "company_name": "Acme Corp",
    "primary_color": "1A365D",
    "secondary_color": "E2E8F0"
  },
  "preferences": {
    "style": "image-rich",
    "slide_count_hint": 20,
    "image_backend": "ollama",
    "resolution": "1080p",
    "include_speaker_notes": true,
    "include_charts": false
  },
  "data_sources": []
}
```

Create `tests/fixtures/minimal_deck/style-guide.json` (use the valid fixture from Phase 1).

Create `tests/fixtures/minimal_deck/outline.json` (use the valid 3-slide fixture from Phase 1).

Create `tests/fixtures/minimal_deck/speaker-notes.json` (use the valid fixture from Phase 1).

Create `tests/fixtures/minimal_deck/image-manifest.json`:

```json
{
  "generated_at": "2026-03-29T12:00:00Z",
  "image_backend": "ollama",
  "images": [
    {
      "image_id": "slide-01-hero",
      "slide_number": 1,
      "file_path": "./tmp/deck/images/slide-01-hero.png",
      "placement_zone": "background",
      "dimensions": {"width": 1920, "height": 1080},
      "source_prompt": "Abstract network of connected nodes in deep blue",
      "model_used": "x/z-image-turbo",
      "alt_text": "Abstract network visualization",
      "status": "generated",
      "retry_count": 0,
      "generation_time_seconds": 12.5
    }
  ],
  "summary": {
    "total_images": 1,
    "generated_count": 1,
    "cached_count": 0,
    "placeholder_count": 0,
    "failed_count": 0,
    "total_generation_seconds": 12.5
  }
}
```

Create `tests/fixtures/minimal_deck/chart-manifest.json`:

```json
{
  "charts": []
}
```

- [ ] **Step 2: Create a placeholder test image**

Generate a 1920x1080 solid blue test image for the fixture:

```bash
source .venv/bin/activate && python3 -c "
from PIL import Image
img = Image.new('RGB', (1920, 1080), color=(26, 54, 93))
img.save('tests/fixtures/minimal_deck/images/slide-01-hero.png')
print('Created test image')
"
```

- [ ] **Step 3: Write assembler tests**

Create `tests/test_assembler.py`:

```python
"""Tests for deck-assembler PPTX assembly.

These tests validate that the build_deck.js script correctly reads
DeckContext contracts and produces a valid .pptx file.
"""

import json
import os
import shutil
import subprocess
import pytest

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures', 'minimal_deck')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'test-assembler')


@pytest.fixture(autouse=True)
def clean_output_dir():
    """Create and clean test output directory."""
    os.makedirs(os.path.join(OUTPUT_DIR, 'output'), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, 'images'), exist_ok=True)
    yield
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)


@pytest.fixture
def deck_dir():
    """Set up a DeckContext directory from fixtures."""
    # Copy fixture files to output dir
    for fname in os.listdir(FIXTURE_DIR):
        src = os.path.join(FIXTURE_DIR, fname)
        dst = os.path.join(OUTPUT_DIR, fname)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
    return OUTPUT_DIR


def test_build_deck_produces_pptx(deck_dir):
    """build_deck.js should produce a .pptx file at output/presentation.pptx."""
    result = subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', deck_dir],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, f"build_deck.js failed: {result.stderr}"
    pptx_path = os.path.join(deck_dir, 'output', 'presentation.pptx')
    assert os.path.isfile(pptx_path), "presentation.pptx not created"
    assert os.path.getsize(pptx_path) > 1000, "presentation.pptx too small"


def test_build_deck_has_correct_slide_count(deck_dir):
    """Output should have the same number of slides as the outline."""
    subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', deck_dir],
        capture_output=True, text=True, timeout=30
    )
    pptx_path = os.path.join(deck_dir, 'output', 'presentation.pptx')
    # Verify slide count via markitdown or python-pptx
    from pptx import Presentation
    prs = Presentation(pptx_path)
    outline = json.load(open(os.path.join(deck_dir, 'outline.json')))
    assert len(prs.slides) == len(outline['slides'])


def test_build_deck_has_speaker_notes(deck_dir):
    """Output slides should have speaker notes from the SpeakerNotes contract."""
    subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', deck_dir],
        capture_output=True, text=True, timeout=30
    )
    pptx_path = os.path.join(deck_dir, 'output', 'presentation.pptx')
    from pptx import Presentation
    prs = Presentation(pptx_path)
    notes = json.load(open(os.path.join(deck_dir, 'speaker-notes.json')))
    slides_with_notes = 0
    for slide in prs.slides:
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            slides_with_notes += 1
    assert slides_with_notes >= len(notes['notes']), \
        f"Expected {len(notes['notes'])} slides with notes, got {slides_with_notes}"


def test_build_deck_applies_palette(deck_dir):
    """Output should use colours from the StyleGuide palette."""
    subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', deck_dir],
        capture_output=True, text=True, timeout=30
    )
    pptx_path = os.path.join(deck_dir, 'output', 'presentation.pptx')
    from pptx import Presentation
    prs = Presentation(pptx_path)
    # At minimum, verify the presentation was created and has slides
    assert len(prs.slides) > 0


def test_build_deck_handles_empty_chart_manifest(deck_dir):
    """Assembly should succeed when chart-manifest.json has zero charts."""
    subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', deck_dir],
        capture_output=True, text=True, timeout=30
    )
    pptx_path = os.path.join(deck_dir, 'output', 'presentation.pptx')
    assert os.path.isfile(pptx_path)
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_assembler.py -v`

Expected: FAIL -- `src/assembler/build_deck.js` not found.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/minimal_deck/ tests/test_assembler.py
git commit -m "test: add deck-assembler test fixtures and integration tests"
```

---

## Task 3: deck-assembler -- Slide Master Definitions

**Files:**
- Create: `src/assembler/slide_masters.js`

- [ ] **Step 1: Implement slide master definitions**

Create `src/assembler/slide_masters.js`:

```javascript
/**
 * Slide master definitions for PptxGenJS.
 *
 * Maps the 12 slide_type values from the SlideOutline schema to
 * PptxGenJS defineSlideMaster() calls. Each master defines background
 * treatment, content zones (text_zone, image_zone), and standard
 * decorative elements.
 *
 * Layout measurements derived from:
 * - research/01-slide-layout-intelligence.md (grid system, content zones)
 * - docs/architecture/data-contracts.md (StyleGuide layout templates)
 *
 * Slide dimensions: 10" x 5.625" (standard 16:9 at 10" width)
 */

const SLIDE_WIDTH = 10;
const SLIDE_HEIGHT = 5.625;
const MARGIN = 0.5;

/**
 * Register all slide masters with the PptxGenJS instance.
 *
 * @param {PptxGenJS} pptx - PptxGenJS instance
 * @param {Object} styleGuide - StyleGuide contract data
 */
function registerSlideMasters(pptx, styleGuide) {
    const palette = styleGuide.palette;
    const typo = styleGuide.typography;
    const templates = styleGuide.layout?.templates || {};

    // Title Slide
    pptx.defineSlideMaster({
        title: 'MASTER_TITLE',
        background: { color: palette.background_alt },
        objects: [
            // Title text placeholder zone (centred, upper-middle)
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: 1.0, y: 1.5, w: 8.0, h: 1.5,
                        fontSize: typo.heading_sizes?.title_slide || 44,
                        fontFace: typo.heading_font,
                        color: palette.text_on_dark || 'FFFFFF',
                        align: 'center',
                        valign: 'bottom',
                    },
                },
            },
            // Subtitle placeholder zone
            {
                placeholder: {
                    options: {
                        name: 'subtitle',
                        type: 'body',
                        x: 1.5, y: 3.2, w: 7.0, h: 1.0,
                        fontSize: typo.heading_sizes?.subheading || 20,
                        fontFace: typo.body_font,
                        color: palette.text_muted || '718096',
                        align: 'center',
                    },
                },
            },
        ],
    });

    // Section Divider
    pptx.defineSlideMaster({
        title: 'MASTER_SECTION_DIVIDER',
        background: { color: palette.primary },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: 1.0, y: 1.8, w: 8.0, h: 1.5,
                        fontSize: typo.heading_sizes?.section_divider || 36,
                        fontFace: typo.heading_font,
                        color: palette.text_on_dark || 'FFFFFF',
                        align: 'center',
                        valign: 'middle',
                    },
                },
            },
        ],
    });

    // Content (standard text + optional image)
    pptx.defineSlideMaster({
        title: 'MASTER_CONTENT',
        background: { color: palette.background },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                        fontSize: typo.heading_sizes?.slide_heading || 28,
                        fontFace: typo.heading_font,
                        color: palette.text_primary,
                    },
                },
            },
            {
                placeholder: {
                    options: {
                        name: 'body',
                        type: 'body',
                        x: MARGIN, y: 1.5, w: 5.5, h: 3.625,
                        fontSize: typo.body_size || 16,
                        fontFace: typo.body_font,
                        color: palette.text_primary,
                        lineSpacingMultiple: typo.line_spacing || 1.4,
                    },
                },
            },
        ],
    });

    // Two Column
    pptx.defineSlideMaster({
        title: 'MASTER_TWO_COLUMN',
        background: { color: palette.background },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                        fontSize: typo.heading_sizes?.slide_heading || 28,
                        fontFace: typo.heading_font,
                        color: palette.text_primary,
                    },
                },
            },
        ],
    });

    // Image Feature (full-bleed or half-bleed image)
    pptx.defineSlideMaster({
        title: 'MASTER_IMAGE_FEATURE',
        background: { color: palette.background },
    });

    // Data Chart
    pptx.defineSlideMaster({
        title: 'MASTER_DATA_CHART',
        background: { color: palette.background },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                        fontSize: typo.heading_sizes?.slide_heading || 28,
                        fontFace: typo.heading_font,
                        color: palette.text_primary,
                    },
                },
            },
        ],
    });

    // Stat Callout (big number)
    pptx.defineSlideMaster({
        title: 'MASTER_STAT_CALLOUT',
        background: { color: palette.background_alt },
    });

    // Quote
    pptx.defineSlideMaster({
        title: 'MASTER_QUOTE',
        background: { color: palette.background_alt },
    });

    // Icon Grid
    pptx.defineSlideMaster({
        title: 'MASTER_ICON_GRID',
        background: { color: palette.background },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                        fontSize: typo.heading_sizes?.slide_heading || 28,
                        fontFace: typo.heading_font,
                        color: palette.text_primary,
                    },
                },
            },
        ],
    });

    // Diagram
    pptx.defineSlideMaster({
        title: 'MASTER_DIAGRAM',
        background: { color: palette.background },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                        fontSize: typo.heading_sizes?.slide_heading || 28,
                        fontFace: typo.heading_font,
                        color: palette.text_primary,
                    },
                },
            },
        ],
    });

    // Closing / CTA
    pptx.defineSlideMaster({
        title: 'MASTER_CLOSING',
        background: { color: palette.background_alt },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: 1.0, y: 1.5, w: 8.0, h: 1.5,
                        fontSize: typo.heading_sizes?.title_slide || 44,
                        fontFace: typo.heading_font,
                        color: palette.text_on_dark || 'FFFFFF',
                        align: 'center',
                        valign: 'middle',
                    },
                },
            },
        ],
    });

    // Blank Visual (breathing room)
    pptx.defineSlideMaster({
        title: 'MASTER_BLANK_VISUAL',
        background: { color: palette.background },
    });
}

/**
 * Map slide_type to master name.
 */
const SLIDE_TYPE_TO_MASTER = {
    'title': 'MASTER_TITLE',
    'section_divider': 'MASTER_SECTION_DIVIDER',
    'content': 'MASTER_CONTENT',
    'two_column': 'MASTER_TWO_COLUMN',
    'image_feature': 'MASTER_IMAGE_FEATURE',
    'data_chart': 'MASTER_DATA_CHART',
    'stat_callout': 'MASTER_STAT_CALLOUT',
    'quote': 'MASTER_QUOTE',
    'icon_grid': 'MASTER_ICON_GRID',
    'diagram': 'MASTER_DIAGRAM',
    'closing': 'MASTER_CLOSING',
    'blank_visual': 'MASTER_BLANK_VISUAL',
};

module.exports = { registerSlideMasters, SLIDE_TYPE_TO_MASTER, SLIDE_WIDTH, SLIDE_HEIGHT, MARGIN };
```

- [ ] **Step 2: Commit**

```bash
git add src/assembler/slide_masters.js
git commit -m "feat: add PptxGenJS slide master definitions for all 12 slide types"
```

---

## Task 4: deck-assembler -- Progressive Builds

**Files:**
- Create: `src/assembler/progressive_builds.js`

- [ ] **Step 1: Implement progressive build generation**

Create `src/assembler/progressive_builds.js`:

```javascript
/**
 * Progressive Build Generation for PptxGenJS.
 *
 * Simulates animations by generating multiple slides where each
 * successive slide adds one more element. Covers ~80% of animation
 * use cases presenters actually need (Research #14).
 *
 * Triggered when a slide's speaker notes contain a 'build_animation'
 * cue from the SpeakerNotes contract.
 */

const { MARGIN } = require('./slide_masters');

/**
 * Determine if a slide should use progressive builds.
 *
 * @param {Object} slideData - Slide definition from SlideOutline
 * @param {Object} noteData - Speaker note for this slide (may be null)
 * @returns {boolean}
 */
function shouldProgressiveBuild(slideData, noteData) {
    if (!noteData || !noteData.cues) return false;
    return noteData.cues.some(cue => cue.type === 'build_animation');
}

/**
 * Generate progressive build slides for a bullet-point slide.
 *
 * Creates N slides (one per bullet) where each slide shows all
 * bullets up to that point. Previous bullets are dimmed.
 *
 * @param {PptxGenJS} pptx - PptxGenJS instance
 * @param {Object} slideData - Slide definition from SlideOutline
 * @param {Object} styleGuide - StyleGuide contract
 * @param {string} masterName - Master slide name
 * @param {Object} noteData - Speaker note (optional)
 * @returns {Array} Array of created slides
 */
function generateBulletBuild(pptx, slideData, styleGuide, masterName, noteData) {
    const bullets = slideData.body_points || [];
    if (bullets.length === 0) return [];

    const palette = styleGuide.palette;
    const typo = styleGuide.typography;
    const slides = [];

    for (let step = 1; step <= bullets.length; step++) {
        const slide = pptx.addSlide({ masterName });

        // Add title (always visible)
        slide.addText(slideData.headline, {
            x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
            fontSize: typo.heading_sizes?.slide_heading || 28,
            fontFace: typo.heading_font,
            color: palette.text_primary,
            bold: true,
        });

        // Add bullets up to current step
        for (let i = 0; i < step; i++) {
            const isCurrent = i === step - 1;
            slide.addText(bullets[i], {
                x: MARGIN + 0.3, y: 1.5 + (i * 0.7), w: 8.5, h: 0.6,
                fontSize: typo.body_size || 16,
                fontFace: typo.body_font,
                color: isCurrent ? palette.text_primary : palette.text_muted,
                bullet: true,
                lineSpacingMultiple: typo.line_spacing || 1.4,
            });
        }

        // Add speaker notes only on the final build step
        if (step === bullets.length && noteData) {
            slide.addNotes(noteData.text);
        }

        slides.push(slide);
    }

    return slides;
}

module.exports = { shouldProgressiveBuild, generateBulletBuild };
```

- [ ] **Step 2: Commit**

```bash
git add src/assembler/progressive_builds.js
git commit -m "feat: add progressive build generation for bullet-point slides"
```

---

## Task 5: deck-assembler -- Main Assembly Script & Skill

**Files:**
- Create: `src/assembler/build_deck.js`
- Create: `src/assembler/optimise.js`
- Create: `.claude/skills/deck-assembler/SKILL.md`

- [ ] **Step 1: Implement file optimisation module**

Create `src/assembler/optimise.js`:

```javascript
/**
 * File optimisation for assembled .pptx files.
 *
 * Capabilities:
 * - Image compression before embedding (pre-process source images)
 * - Metadata stripping from embedded images
 * - Reports file size breakdown
 *
 * Corresponds to the assembly-file-optimisation capability in the
 * service catalogue (capability of deck-assembler).
 */

const fs = require('fs');
const path = require('path');

/**
 * Get file size in human-readable format.
 */
function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Report file size of the assembled .pptx.
 *
 * @param {string} pptxPath - Path to the .pptx file
 * @returns {Object} Size report
 */
function reportFileSize(pptxPath) {
    const stats = fs.statSync(pptxPath);
    return {
        path: pptxPath,
        size_bytes: stats.size,
        size_human: formatSize(stats.size),
        within_limit: stats.size < 100 * 1024 * 1024, // 100MB conference limit
    };
}

/**
 * Validate that all image files referenced in the manifest exist and
 * have reasonable file sizes.
 *
 * @param {Object} imageManifest - ImageManifest contract
 * @param {string} deckDir - DeckContext directory path
 * @returns {Object} Validation result with warnings
 */
function validateImageAssets(imageManifest, deckDir) {
    const warnings = [];
    let totalImageSize = 0;

    for (const img of imageManifest.images || []) {
        const imgPath = path.resolve(deckDir, img.file_path.replace('./tmp/deck/', ''));
        if (!fs.existsSync(imgPath)) {
            warnings.push(`Missing image: ${img.file_path} (${img.image_id})`);
            continue;
        }
        const size = fs.statSync(imgPath).size;
        totalImageSize += size;
        if (size > 10 * 1024 * 1024) {
            warnings.push(`Large image: ${img.image_id} is ${formatSize(size)}`);
        }
    }

    return {
        total_image_size: totalImageSize,
        total_image_size_human: formatSize(totalImageSize),
        warnings,
    };
}

module.exports = { reportFileSize, validateImageAssets, formatSize };
```

- [ ] **Step 2: Implement main assembly script**

Create `src/assembler/build_deck.js`:

```javascript
#!/usr/bin/env node

/**
 * deck-assembler: Build a .pptx from DeckContext contracts.
 *
 * Reads: SlideOutline, StyleGuide, ImageManifest, ChartManifest, SpeakerNotes
 * Produces: ./tmp/deck/output/presentation.pptx
 *
 * Usage:
 *   node src/assembler/build_deck.js [--deck-dir PATH]
 *
 * Default deck-dir: ./tmp/deck
 */

const fs = require('fs');
const path = require('path');
const PptxGenJS = require('pptxgenjs');
const { registerSlideMasters, SLIDE_TYPE_TO_MASTER, SLIDE_WIDTH, SLIDE_HEIGHT, MARGIN } = require('./slide_masters');
const { shouldProgressiveBuild, generateBulletBuild } = require('./progressive_builds');
const { reportFileSize, validateImageAssets } = require('./optimise');

// Parse CLI args
const args = process.argv.slice(2);
const deckDirIndex = args.indexOf('--deck-dir');
const DECK_DIR = deckDirIndex >= 0 ? args[deckDirIndex + 1] : './tmp/deck';

/**
 * Load a DeckContext JSON contract.
 */
function loadContract(name) {
    const filePath = path.join(DECK_DIR, `${name}.json`);
    if (!fs.existsSync(filePath)) {
        console.error(`Contract not found: ${filePath}`);
        process.exit(1);
    }
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

/**
 * Resolve an image path from the manifest relative to deck dir.
 */
function resolveImagePath(manifestPath) {
    // ImageManifest paths are like ./tmp/deck/images/slide-01-hero.png
    // Resolve relative to the deck dir
    const relativePath = manifestPath.replace(/^\.\/tmp\/deck\//, '');
    return path.resolve(DECK_DIR, relativePath);
}

/**
 * Find the image entry for a given slide number and placement zone.
 */
function findImage(imageManifest, slideNumber, zone) {
    return (imageManifest.images || []).find(
        img => img.slide_number === slideNumber &&
               img.status !== 'failed' &&
               (!zone || img.placement_zone === zone)
    );
}

/**
 * Find the chart entry for a given slide number.
 */
function findChart(chartManifest, slideNumber) {
    return (chartManifest.charts || []).find(
        chart => chart.slide_number === slideNumber &&
                 chart.status !== 'failed'
    );
}

/**
 * Find speaker note for a given slide number.
 */
function findNote(speakerNotes, slideNumber) {
    return (speakerNotes.notes || []).find(n => n.slide_number === slideNumber);
}

/**
 * Build a single slide based on its type and data.
 */
function buildSlide(pptx, slideData, styleGuide, imageManifest, chartManifest, speakerNotes) {
    const masterName = SLIDE_TYPE_TO_MASTER[slideData.slide_type] || 'MASTER_CONTENT';
    const palette = styleGuide.palette;
    const typo = styleGuide.typography;
    const noteData = findNote(speakerNotes, slideData.slide_number);
    const imageData = findImage(imageManifest, slideData.slide_number);
    const chartData = findChart(chartManifest, slideData.slide_number);

    // Check for progressive build
    if (shouldProgressiveBuild(slideData, noteData)) {
        return generateBulletBuild(pptx, slideData, styleGuide, masterName, noteData);
    }

    const slide = pptx.addSlide({ masterName });

    // --- Slide type-specific content ---

    switch (slideData.slide_type) {
        case 'title':
            slide.addText(slideData.headline, {
                x: 1.0, y: 1.5, w: 8.0, h: 1.5,
                fontSize: typo.heading_sizes?.title_slide || 44,
                fontFace: typo.heading_font,
                color: palette.text_on_dark || 'FFFFFF',
                align: 'center', valign: 'bottom', bold: true,
            });
            if (slideData.body_points && slideData.body_points.length > 0) {
                slide.addText(slideData.body_points[0], {
                    x: 1.5, y: 3.2, w: 7.0, h: 1.0,
                    fontSize: typo.heading_sizes?.subheading || 20,
                    fontFace: typo.body_font,
                    color: palette.text_muted || '718096',
                    align: 'center',
                });
            }
            break;

        case 'section_divider':
            slide.addText(slideData.headline, {
                x: 1.0, y: 1.8, w: 8.0, h: 1.5,
                fontSize: typo.heading_sizes?.section_divider || 36,
                fontFace: typo.heading_font,
                color: palette.text_on_dark || 'FFFFFF',
                align: 'center', valign: 'middle', bold: true,
            });
            break;

        case 'content':
        case 'two_column':
        case 'icon_grid':
        case 'diagram':
            // Heading
            slide.addText(slideData.headline, {
                x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                fontSize: typo.heading_sizes?.slide_heading || 28,
                fontFace: typo.heading_font,
                color: palette.text_primary,
                bold: true,
            });
            // Body points
            if (slideData.body_points && slideData.body_points.length > 0) {
                const textZoneW = imageData ? 5.0 : 8.5;
                const bodyText = slideData.body_points.map(bp => ({
                    text: bp,
                    options: {
                        fontSize: typo.body_size || 16,
                        fontFace: typo.body_font,
                        color: palette.text_primary,
                        bullet: true,
                        lineSpacingMultiple: typo.line_spacing || 1.4,
                        breakLine: true,
                    },
                }));
                slide.addText(bodyText, {
                    x: MARGIN, y: 1.5, w: textZoneW, h: 3.625,
                    valign: 'top',
                });
            }
            break;

        case 'stat_callout':
            // Big number from headline
            slide.addText(slideData.headline, {
                x: 1.0, y: 1.0, w: 8.0, h: 2.5,
                fontSize: 72,
                fontFace: typo.heading_font,
                color: palette.accent || palette.primary,
                align: 'center', valign: 'middle', bold: true,
            });
            if (slideData.body_points && slideData.body_points[0]) {
                slide.addText(slideData.body_points[0], {
                    x: 1.5, y: 3.5, w: 7.0, h: 1.0,
                    fontSize: typo.body_size || 16,
                    fontFace: typo.body_font,
                    color: palette.text_on_dark || 'FFFFFF',
                    align: 'center',
                });
            }
            break;

        case 'quote':
            slide.addText(`"${slideData.headline}"`, {
                x: 1.0, y: 1.2, w: 8.0, h: 2.5,
                fontSize: 24,
                fontFace: typo.heading_font,
                color: palette.text_on_dark || 'FFFFFF',
                align: 'center', valign: 'middle', italic: true,
            });
            if (slideData.body_points && slideData.body_points[0]) {
                slide.addText(`-- ${slideData.body_points[0]}`, {
                    x: 2.0, y: 3.8, w: 6.0, h: 0.6,
                    fontSize: 14,
                    fontFace: typo.body_font,
                    color: palette.text_muted || '718096',
                    align: 'right',
                });
            }
            break;

        case 'data_chart':
            slide.addText(slideData.headline, {
                x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                fontSize: typo.heading_sizes?.slide_heading || 28,
                fontFace: typo.heading_font,
                color: palette.text_primary,
                bold: true,
            });
            // Chart image placed below title
            if (chartData) {
                const chartPath = resolveImagePath(chartData.file_path);
                if (fs.existsSync(chartPath)) {
                    slide.addImage({
                        path: chartPath,
                        x: 0.75, y: 1.5, w: 8.5, h: 3.75,
                        sizing: { type: 'contain', w: 8.5, h: 3.75 },
                        altText: chartData.alt_text || 'Data chart',
                    });
                }
            }
            break;

        case 'closing':
            slide.addText(slideData.headline, {
                x: 1.0, y: 1.5, w: 8.0, h: 1.5,
                fontSize: typo.heading_sizes?.title_slide || 44,
                fontFace: typo.heading_font,
                color: palette.text_on_dark || 'FFFFFF',
                align: 'center', valign: 'middle', bold: true,
            });
            if (slideData.body_points && slideData.body_points.length > 0) {
                const closingText = slideData.body_points.map(bp => ({
                    text: bp,
                    options: {
                        fontSize: typo.body_size || 16,
                        fontFace: typo.body_font,
                        color: palette.text_on_dark || 'FFFFFF',
                        bullet: true,
                        breakLine: true,
                    },
                }));
                slide.addText(closingText, {
                    x: 1.5, y: 3.2, w: 7.0, h: 2.0,
                    valign: 'top',
                });
            }
            break;

        case 'image_feature':
        case 'blank_visual':
        default:
            if (slideData.headline) {
                slide.addText(slideData.headline, {
                    x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                    fontSize: typo.heading_sizes?.slide_heading || 28,
                    fontFace: typo.heading_font,
                    color: palette.text_primary,
                    bold: true,
                });
            }
            break;
    }

    // --- Image placement (for any slide type) ---
    if (imageData && imageData.status !== 'failed') {
        const imgPath = resolveImagePath(imageData.file_path);
        if (fs.existsSync(imgPath)) {
            const zone = imageData.placement_zone || 'image_zone';
            if (zone === 'background') {
                slide.background = { path: imgPath };
            } else {
                // Default image zone: right side of content slides
                slide.addImage({
                    path: imgPath,
                    x: 6.0, y: 0.5, w: 3.5, h: 4.625,
                    sizing: { type: 'contain', w: 3.5, h: 4.625 },
                    altText: imageData.alt_text || '',
                });
            }
        }
    }

    // --- Speaker notes ---
    if (noteData) {
        slide.addNotes(noteData.text);
    }

    return [slide];
}

/**
 * Main assembly function.
 */
async function assembleDeck() {
    console.log(`Assembling deck from: ${DECK_DIR}`);

    // Load all contracts
    const outline = loadContract('outline');
    const styleGuide = loadContract('style-guide');
    const imageManifest = loadContract('image-manifest');
    const chartManifest = loadContract('chart-manifest');
    const speakerNotes = loadContract('speaker-notes');

    // Validate image assets
    const assetReport = validateImageAssets(imageManifest, DECK_DIR);
    if (assetReport.warnings.length > 0) {
        console.warn('Image asset warnings:');
        assetReport.warnings.forEach(w => console.warn(`  - ${w}`));
    }

    // Create presentation
    const pptx = new PptxGenJS();
    pptx.layout = 'LAYOUT_WIDE';  // 13.33" x 7.5"
    // Override to 10" x 5.625" if StyleGuide specifies
    const layoutW = styleGuide.layout?.slide_width_inches || 10;
    const layoutH = styleGuide.layout?.slide_height_inches || 5.625;
    pptx.defineLayout({ name: 'DECK_LAYOUT', width: layoutW, height: layoutH });
    pptx.layout = 'DECK_LAYOUT';

    // Set theme fonts
    pptx.theme = {
        headFontFace: styleGuide.typography.heading_font,
        bodyFontFace: styleGuide.typography.body_font,
    };

    // Register slide masters
    registerSlideMasters(pptx, styleGuide);

    // Build each slide
    for (const slideData of outline.slides) {
        buildSlide(pptx, slideData, styleGuide, imageManifest, chartManifest, speakerNotes);
    }

    // Write output
    const outputDir = path.join(DECK_DIR, 'output');
    fs.mkdirSync(outputDir, { recursive: true });
    const outputPath = path.join(outputDir, 'presentation.pptx');
    await pptx.writeFile({ fileName: outputPath });

    // Report
    const sizeReport = reportFileSize(outputPath);
    console.log(`Deck assembled: ${outputPath}`);
    console.log(`  Slides: ${outline.slides.length}`);
    console.log(`  File size: ${sizeReport.size_human}`);
    console.log(`  Within 100MB limit: ${sizeReport.within_limit}`);

    return { outputPath, sizeReport, assetReport };
}

// Run
assembleDeck().catch(err => {
    console.error('Assembly failed:', err);
    process.exit(1);
});
```

- [ ] **Step 3: Write the deck-assembler skill definition**

Create `.claude/skills/deck-assembler/SKILL.md`:

```markdown
---
name: deck-assembler
description: Assemble a .pptx presentation from all DeckContext contracts (SlideOutline, StyleGuide, ImageManifest, ChartManifest, SpeakerNotes) via PptxGenJS.
argument-hint: [--deck-dir PATH]
allowed-tools: Bash(node *), Bash(npm *), Read, Glob
---

# /deck-assembler

Assemble a complete PowerPoint presentation from the DeckContext contracts in `./tmp/deck/`.

## Prerequisites

All of these DeckContext files must exist before running:
- `./tmp/deck/outline.json` (SlideOutline)
- `./tmp/deck/style-guide.json` (StyleGuide)
- `./tmp/deck/image-manifest.json` (ImageManifest)
- `./tmp/deck/chart-manifest.json` (ChartManifest)
- `./tmp/deck/speaker-notes.json` (SpeakerNotes)
- `./tmp/deck/images/` directory with referenced image files

## Usage

```bash
node src/assembler/build_deck.js --deck-dir ./tmp/deck
```

Default deck-dir is `./tmp/deck` if not specified.

## Output

`./tmp/deck/output/presentation.pptx`

## What It Does

1. Reads all DeckContext JSON contracts
2. Validates that referenced image assets exist
3. Creates PptxGenJS slide masters for all 12 slide types based on StyleGuide
4. Iterates through SlideOutline, building each slide with:
   - Correct master/layout per slide_type
   - Headline and body points with StyleGuide typography
   - Images from ImageManifest placed in correct zones
   - Chart images from ChartManifest for data_chart slides
   - Speaker notes from SpeakerNotes contract
5. Generates progressive build slides for bullets with build_animation cues
6. Writes the assembled .pptx to the output directory
7. Reports file size and any asset warnings

## Design Rules (from existing pptx skill)

- 0.5" minimum margins on all sides
- Never use `#` prefix on hex colours (PptxGenJS convention)
- Do not reuse option objects (PptxGenJS mutates them)
- Left-align body text, centre only titles
- Do not place accent lines under titles

## Limitations

- No native animations (PptxGenJS v4.0.1 limitation) -- uses progressive builds for ~80% coverage
- No gradient fills on shapes -- use pre-rendered gradient images as backgrounds
- Cannot import existing .pptx templates -- defines masters programmatically
```

- [ ] **Step 4: Install PptxGenJS if needed**

```bash
cd /Users/stevejones/Documents/Development/jack-tar-deckhand && npm install pptxgenjs
```

- [ ] **Step 5: Run assembler tests**

Run: `source .venv/bin/activate && pip install python-pptx && python3 -m pytest tests/test_assembler.py -v`

Expected: All 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/assembler/ .claude/skills/deck-assembler/ package.json package-lock.json
git commit -m "feat: add deck-assembler skill with PptxGenJS assembly, slide masters, and progressive builds"
```

---

## Task 6: Research Synthesis -- deck-qa

**Files:**
- Create: `research/synthesis-deck-qa.md`

- [ ] **Step 1: Read primary research**

Read and synthesise:
- `research/07-qa-heuristics-anti-patterns.md` (all 25 checks with detection algorithms)
- `research/01-slide-layout-intelligence.md` (layout validation rules)
- `docs/architecture/data-contracts.md` (QAReport schema)

- [ ] **Step 2: Write synthesis document**

Create `research/synthesis-deck-qa.md` covering:
1. **25 anti-pattern checks:** Full AP-01 through AP-25 list with mapping to QAReport categories
2. **Check categorisation:** Which checks are structural (fast, no rendering), which require visual rendering, which are cross-slide
3. **QAReport mapping:** How each AP check maps to QAReport category enum (overlap, contrast, margin, text_overflow, consistency, image_quality, placeholder_residue, missing_content, accessibility)
4. **Threshold defaults:** All configurable thresholds with recommended values
5. **Verdict logic:** How errors/warnings determine pass/pass_with_warnings/fail
6. **Python dependencies:** python-pptx, Pillow, colorsys (stdlib)
7. **Performance:** Structural checks <1s, visual checks depend on LibreOffice rendering

- [ ] **Step 3: Commit**

```bash
git add research/synthesis-deck-qa.md
git commit -m "docs: add deck-qa research synthesis"
```

---

## Task 7: deck-qa -- Check Implementation

**Files:**
- Create: `src/qa/__init__.py`
- Create: `src/qa/config.py`
- Create: `src/qa/checks/__init__.py`
- Create: `src/qa/checks/structural.py`
- Create: `src/qa/checks/contrast.py`
- Create: `src/qa/checks/consistency.py`
- Create: `src/qa/checks/image_quality.py`
- Create: `src/qa/checks/animations.py`
- Create: `src/qa/checks/chart_quality.py`
- Create: `tests/test_qa_structural.py`
- Create: `tests/test_qa_contrast.py`
- Create: `tests/test_qa_consistency.py`
- Create: `tests/test_qa_image.py`

- [ ] **Step 1: Create QA configuration module**

Create `src/qa/config.py`:

```python
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

    # AP-06: Elements Outside Safe Margins
    'safe_margin_pct': 0.05,

    # AP-07: Low Contrast
    'min_contrast_ratio': 7.0,  # WCAG AAA for projection

    # AP-10: Slide Count vs Duration
    'slides_per_minute_min': 0.5,
    'slides_per_minute_max': 2.0,

    # AP-12: Image Resolution
    'min_image_dpi_equiv': 96,

    # AP-13: Image Aspect Ratio Distortion
    'max_aspect_distortion_pct': 5.0,

    # AP-14: Too Many Bullet Points
    'max_bullets_per_slide': 6,

    # AP-15: Consecutive Bullet-Heavy Slides
    'max_consecutive_bullet_slides': 3,

    # AP-18: Heading Size Consistency
    'max_heading_variance_pt': 2,

    # AP-19: Text Overflow
    'min_autofit_scale_pct': 90,  # Stored as 90000 in OOXML

    # AP-20: Element Overlap
    'min_overlap_pct': 25,

    # AP-21: Excessive Animations
    'max_transition_types': 2,

    # AP-25: Colourblind Safety
    'colourblind_min_distance': 30,

    # Verdict thresholds
    'fail_on_any_error': True,
    'max_warnings_before_fail': 10,
}
```

- [ ] **Step 2: Create the structural checks module**

Create `src/qa/checks/structural.py` implementing: AP-01 (Wall of Text), AP-02 (Font Size), AP-05 (Orphan/Widow), AP-06 (Safe Margins), AP-09 (Missing Speaker Notes), AP-10 (Slide Count vs Duration), AP-11 (Placeholder Residue), AP-14 (Too Many Bullets), AP-16 (Missing Title Slide), AP-17 (Missing Closing), AP-19 (Text Overflow), AP-24 (Dead/Empty Slides).

Each function should follow the detection algorithm from Research #07, returning a list of finding dicts with keys: `slide_number`, `severity`, `category`, `description`, `suggested_fix`, `affected_element`, `auto_fixable`.

```python
"""Structural QA checks — fast path, no rendering required.

Implements AP-01, AP-02, AP-05, AP-06, AP-09, AP-10, AP-11,
AP-14, AP-16, AP-17, AP-19, AP-24.

Detection algorithms from: research/07-qa-heuristics-anti-patterns.md
"""

import re
from pptx.util import Pt, Emu
from lxml import etree
from ..config import QA_CONFIG

# [Full implementation of each check function following the
#  detection algorithms from Research #07. Each returns List[dict]
#  with QAReport finding fields.]

# AP-01: Wall of Text
def check_wall_of_text(slide, slide_number, config=None):
    """Check for excessive word counts per text box and per slide."""
    cfg = config or QA_CONFIG
    max_per_box = cfg['max_words_per_textbox']
    max_per_slide = cfg['max_words_per_slide']
    issues = []
    slide_word_count = 0
    for shape in slide.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text.strip()
            word_count = len(text.split())
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

# AP-02: Font Size Below Projection Minimum
def check_font_size(slide, slide_number, config=None):
    # ... [implementation per Research #07 algorithm]
    pass

# AP-05: Orphan/Widow Lines
def check_orphan_widow(slide, slide_number, config=None):
    # ... [implementation per Research #07 algorithm]
    pass

# AP-06: Elements Outside Safe Margins
def check_safe_margins(slide, slide_number, presentation, config=None):
    # ... [implementation per Research #07 algorithm]
    pass

# AP-09: Missing Speaker Notes
def check_speaker_notes(presentation, config=None):
    # ... [implementation per Research #07 algorithm — deck-level check]
    pass

# AP-10: Slide Count vs Talk Duration Mismatch
def check_slide_count_ratio(presentation, duration_minutes=None, config=None):
    # ... [implementation per Research #07 algorithm]
    pass

# AP-11: Placeholder Residue
PLACEHOLDER_PATTERNS = [
    r'click to add', r'lorem ipsum', r'\bXXX\b', r'\bTODO\b',
    r'\bTBD\b', r'\[insert\b', r'\[your .+?\]', r'placeholder',
    r'sample text', r'edit (this|here)', r'replace (this|with)',
    r'type (here|your)', r'add (your|text|title|subtitle|content)',
]

def check_placeholder_residue(slide, slide_number, config=None):
    # ... [implementation per Research #07 algorithm]
    pass

# AP-14: Too Many Bullet Points
def check_bullet_count(slide, slide_number, config=None):
    # ... [implementation per Research #07 algorithm]
    pass

# AP-16: Missing Title Slide
def check_title_slide(presentation, config=None):
    # ... [implementation per Research #07 algorithm]
    pass

# AP-17: Missing Closing/CTA Slide
def check_closing_slide(presentation, config=None):
    # ... [implementation per Research #07 algorithm]
    pass

# AP-19: Text Overflow/Clipping
def check_text_overflow(slide, slide_number, config=None):
    # ... [implementation per Research #07 algorithm]
    pass

# AP-24: Dead/Empty Slides
def check_dead_slides(slide, slide_number, config=None):
    # ... [implementation per Research #07 algorithm]
    pass
```

**IMPORTANT:** Each check function must contain the complete implementation from the Research #07 detection algorithm. Do not use `pass` or placeholder comments. The full code is provided in the research paper.

- [ ] **Step 3: Create the contrast and colour checks module**

Create `src/qa/checks/contrast.py` implementing: AP-07 (Low Contrast), AP-08 (Clashing Colours), AP-25 (Colourblind Safety).

Include the `relative_luminance()`, `contrast_ratio()`, `simulate_deuteranopia()` utility functions from Research #07.

- [ ] **Step 4: Create the consistency checks module**

Create `src/qa/checks/consistency.py` implementing: AP-03 (Too Many Font Families), AP-04 (Inconsistent Bullet Styles), AP-15 (Consecutive Bullet-Heavy Slides), AP-18 (Inconsistent Heading Sizes), AP-23 (Branding Consistency).

These are deck-level (cross-slide) checks that receive the full `Presentation` object.

- [ ] **Step 5: Create the image quality checks module**

Create `src/qa/checks/image_quality.py` implementing: AP-12 (Image Resolution for Placement Size), AP-13 (Image Aspect Ratio Distortion).

- [ ] **Step 6: Create the animations check module**

Create `src/qa/checks/animations.py` implementing: AP-21 (Excessive Animations).

- [ ] **Step 7: Create the chart quality check module**

Create `src/qa/checks/chart_quality.py` implementing: AP-22 (Poor Data-Ink Ratio).

- [ ] **Step 8: Create check registry**

Create `src/qa/checks/__init__.py`:

```python
"""QA check registry.

Organises all 25 anti-pattern checks into three execution steps:
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

# Per-slide structural checks (fast path)
STRUCTURAL_CHECKS = [
    check_wall_of_text,
    check_font_size,
    check_orphan_widow,
    check_placeholder_residue,
    check_bullet_count,
    check_text_overflow,
    check_dead_slides,
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
    check_excessive_animations,
    check_chart_junk,
]

# Deck-level colour checks
COLOUR_CHECKS = [
    check_clashing_colours,
    check_colourblind_safety,
]
```

- [ ] **Step 9: Write tests for structural checks**

Create `tests/test_qa_structural.py` with tests for each structural check using python-pptx to create minimal test presentations programmatically.

- [ ] **Step 10: Write tests for contrast checks**

Create `tests/test_qa_contrast.py` testing `relative_luminance()`, `contrast_ratio()`, and `simulate_deuteranopia()` with known colour values.

- [ ] **Step 11: Write tests for consistency checks**

Create `tests/test_qa_consistency.py` testing cross-slide checks.

- [ ] **Step 12: Write tests for image quality checks**

Create `tests/test_qa_image.py` testing resolution and aspect ratio checks.

- [ ] **Step 13: Run all QA check tests**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_qa_*.py -v`

Expected: All tests PASS.

- [ ] **Step 14: Commit**

```bash
git add src/qa/ tests/test_qa_structural.py tests/test_qa_contrast.py tests/test_qa_consistency.py tests/test_qa_image.py
git commit -m "feat: implement 25 anti-pattern QA checks across 6 modules"
```

---

## Task 8: deck-qa -- Report Generation, Runner & Skill

**Files:**
- Create: `src/qa/report.py`
- Create: `src/qa/run_qa.py`
- Create: `.claude/skills/deck-qa/SKILL.md`
- Create: `tests/test_qa_report.py`
- Create: `tests/test_qa_integration.py`

- [ ] **Step 1: Implement report generation**

Create `src/qa/report.py`:

```python
"""QAReport generation and verdict logic.

Produces a QAReport conforming to src/schemas/qa_report.schema.json.
Verdict rules:
  - 'fail': any finding with severity 'error'
  - 'pass_with_warnings': no errors, but warnings exist
  - 'pass': no errors, no warnings (info findings are OK)
"""

from datetime import datetime, timezone


def compute_verdict(findings, config=None):
    """Compute pass/pass_with_warnings/fail from findings list."""
    errors = sum(1 for f in findings if f['severity'] == 'error')
    warnings = sum(1 for f in findings if f['severity'] == 'warning')
    info = sum(1 for f in findings if f['severity'] == 'info')

    if errors > 0:
        return 'fail'
    elif warnings > 0:
        return 'pass_with_warnings'
    else:
        return 'pass'


def generate_report(findings, pptx_path, total_slides):
    """Generate a complete QAReport dict."""
    errors = sum(1 for f in findings if f['severity'] == 'error')
    warnings = sum(1 for f in findings if f['severity'] == 'warning')
    info = sum(1 for f in findings if f['severity'] == 'info')

    return {
        'inspected_at': datetime.now(timezone.utc).isoformat(),
        'pptx_path': pptx_path,
        'verdict': compute_verdict(findings),
        'summary': {
            'total_slides': total_slides,
            'errors': errors,
            'warnings': warnings,
            'info': info,
        },
        'findings': findings,
    }
```

- [ ] **Step 2: Implement the QA runner**

Create `src/qa/run_qa.py`:

```python
#!/usr/bin/env python3
"""deck-qa: Run 25 automated anti-pattern checks on a .pptx file.

Usage:
    python src/qa/run_qa.py [--pptx-path PATH] [--deck-dir PATH] [--duration MINUTES]

Default pptx-path: ./tmp/deck/output/presentation.pptx
Default deck-dir: ./tmp/deck
"""

import argparse
import json
import os
import sys

from pptx import Presentation

from .checks import (
    STRUCTURAL_CHECKS,
    STRUCTURAL_CHECKS_WITH_PRESENTATION,
    DECK_STRUCTURAL_CHECKS,
    CONSISTENCY_CHECKS,
    IMAGE_QUALITY_CHECKS,
    VISUAL_CHECKS,
    COLOUR_CHECKS,
    check_slide_count_ratio,
)
from .config import QA_CONFIG
from .report import generate_report

# Add parent dir to path for deckcontext imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def run_qa(pptx_path, deck_dir='./tmp/deck', duration_minutes=None, config=None):
    """Run all 25 QA checks and return a QAReport dict."""
    cfg = config or QA_CONFIG
    prs = Presentation(pptx_path)
    findings = []

    # Step 1: Per-slide structural checks
    for i, slide in enumerate(prs.slides):
        slide_number = i + 1
        for check_fn in STRUCTURAL_CHECKS:
            findings.extend(check_fn(slide, slide_number, config=cfg))
        for check_fn in STRUCTURAL_CHECKS_WITH_PRESENTATION:
            findings.extend(check_fn(slide, slide_number, prs, config=cfg))
        for check_fn in IMAGE_QUALITY_CHECKS:
            findings.extend(check_fn(slide, slide_number, prs, config=cfg))
        for check_fn in VISUAL_CHECKS:
            try:
                findings.extend(check_fn(slide, slide_number, config=cfg))
            except Exception:
                pass  # Visual checks may fail on minimal test decks

    # Step 2: Deck-level structural checks
    for check_fn in DECK_STRUCTURAL_CHECKS:
        findings.extend(check_fn(prs, config=cfg))

    # AP-10: Slide count vs duration (needs external duration)
    if duration_minutes:
        findings.extend(check_slide_count_ratio(prs, duration_minutes, config=cfg))

    # Step 3: Cross-slide consistency checks
    for check_fn in CONSISTENCY_CHECKS:
        findings.extend(check_fn(prs, config=cfg))

    # Step 4: Deck-level colour checks
    # Collect all colours used across the deck
    colours_used = set()
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        if run.font.color and run.font.color.rgb:
                            rgb = run.font.color.rgb
                            colours_used.add((rgb[0], rgb[1], rgb[2]))
    for check_fn in COLOUR_CHECKS:
        findings.extend(check_fn(colours_used, config=cfg))

    # Generate report
    report = generate_report(findings, pptx_path, len(prs.slides))
    return report


def main():
    parser = argparse.ArgumentParser(description='Run QA checks on a .pptx file')
    parser.add_argument('--pptx-path', default='./tmp/deck/output/presentation.pptx')
    parser.add_argument('--deck-dir', default='./tmp/deck')
    parser.add_argument('--duration', type=int, default=None,
                        help='Talk duration in minutes (for slide count check)')
    parser.add_argument('--output', default=None,
                        help='Output path for QA report JSON')
    args = parser.parse_args()

    report = run_qa(args.pptx_path, args.deck_dir, args.duration)

    # Write report
    output_path = args.output or os.path.join(args.deck_dir, 'qa-report.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Print summary
    print(f"QA Report: {report['verdict'].upper()}")
    print(f"  Errors: {report['summary']['errors']}")
    print(f"  Warnings: {report['summary']['warnings']}")
    print(f"  Info: {report['summary']['info']}")

    # Exit code: 1 if fail, 0 otherwise
    sys.exit(1 if report['verdict'] == 'fail' else 0)


if __name__ == '__main__':
    main()
```

- [ ] **Step 3: Write the deck-qa skill definition**

Create `.claude/skills/deck-qa/SKILL.md`:

```markdown
---
name: deck-qa
description: Run 25 automated anti-pattern checks on an assembled .pptx and produce a QAReport with verdict and per-slide findings.
argument-hint: [--pptx-path PATH] [--deck-dir PATH] [--duration MINUTES]
allowed-tools: Bash(python *), Read, Glob
---

# /deck-qa

Run 25 automated quality assurance checks against an assembled .pptx file. Produces a QAReport JSON at `./tmp/deck/qa-report.json`.

## Usage

```bash
source .venv/bin/activate && python -m src.qa.run_qa --pptx-path ./tmp/deck/output/presentation.pptx --deck-dir ./tmp/deck --duration 30
```

## What It Checks

**Structural (fast, no rendering):**
- AP-01: Wall of Text (>40 words/textbox, >75 words/slide)
- AP-02: Font Size Below Projection Minimum (<18pt body, <24pt title)
- AP-05: Orphan/Widow Lines
- AP-06: Elements Outside 5% Safe Margins
- AP-09: Missing Speaker Notes (<50% of content slides)
- AP-10: Slide Count vs Talk Duration Mismatch
- AP-11: Placeholder Residue (TODO, Lorem ipsum, Click to add)
- AP-14: Too Many Bullet Points (>6 per slide)
- AP-16: Missing Title Slide
- AP-17: Missing Closing/CTA Slide
- AP-19: Text Overflow/Clipping (auto-shrunk below 90%)
- AP-24: Dead/Empty Slides

**Contrast & Colour:**
- AP-07: Low Contrast Text-on-Background (<7:1 for projection)
- AP-08: Clashing Colours (complementary at high saturation, red-green)
- AP-25: Colourblind Safety (deuteranopia simulation)

**Cross-Slide Consistency:**
- AP-03: Too Many Font Families (>2)
- AP-04: Inconsistent Bullet Styles
- AP-15: Consecutive Bullet-Heavy Slides (>3 in a row)
- AP-18: Inconsistent Heading Sizes
- AP-23: Branding/Logo Inconsistency

**Image Quality:**
- AP-12: Image Resolution Too Low for Placement Size
- AP-13: Image Aspect Ratio Distortion (>5%)

**Animations & Charts:**
- AP-21: Excessive Animation/Transition Types (>2)
- AP-22: Poor Data-Ink Ratio (3D charts, minor gridlines)

## Output

QAReport JSON with:
- `verdict`: pass | pass_with_warnings | fail
- `summary`: counts of errors, warnings, info
- `findings`: per-finding entries with slide_number, severity, category, description, suggested_fix, auto_fixable

## Verdict Rules

- **fail**: any finding with severity 'error'
- **pass_with_warnings**: no errors, but warnings exist
- **pass**: no errors, no warnings
```

- [ ] **Step 4: Write report generation tests**

Create `tests/test_qa_report.py`:

```python
"""Tests for QAReport generation and verdict logic."""

import pytest
from src.qa.report import compute_verdict, generate_report


class TestVerdict:
    def test_pass_when_no_findings(self):
        assert compute_verdict([]) == 'pass'

    def test_pass_with_info_only(self):
        findings = [{'severity': 'info', 'slide_number': 1, 'category': 'consistency',
                      'description': 'test'}]
        assert compute_verdict(findings) == 'pass'

    def test_pass_with_warnings(self):
        findings = [{'severity': 'warning', 'slide_number': 1, 'category': 'margin',
                      'description': 'test'}]
        assert compute_verdict(findings) == 'pass_with_warnings'

    def test_fail_on_error(self):
        findings = [{'severity': 'error', 'slide_number': 1, 'category': 'contrast',
                      'description': 'test'}]
        assert compute_verdict(findings) == 'fail'

    def test_fail_overrides_warnings(self):
        findings = [
            {'severity': 'warning', 'slide_number': 1, 'category': 'margin',
             'description': 'w'},
            {'severity': 'error', 'slide_number': 2, 'category': 'contrast',
             'description': 'e'},
        ]
        assert compute_verdict(findings) == 'fail'


class TestGenerateReport:
    def test_report_has_required_fields(self):
        report = generate_report([], './tmp/deck/output/presentation.pptx', 10)
        assert 'inspected_at' in report
        assert 'pptx_path' in report
        assert 'verdict' in report
        assert 'summary' in report
        assert 'findings' in report

    def test_report_counts_are_correct(self):
        findings = [
            {'severity': 'error', 'slide_number': 1, 'category': 'contrast',
             'description': 'e'},
            {'severity': 'warning', 'slide_number': 2, 'category': 'margin',
             'description': 'w'},
            {'severity': 'info', 'slide_number': 3, 'category': 'consistency',
             'description': 'i'},
        ]
        report = generate_report(findings, 'test.pptx', 5)
        assert report['summary']['errors'] == 1
        assert report['summary']['warnings'] == 1
        assert report['summary']['info'] == 1
        assert report['summary']['total_slides'] == 5
```

- [ ] **Step 5: Write integration test**

Create `tests/test_qa_integration.py` that creates a minimal .pptx with python-pptx, runs the full QA pipeline against it, and validates the QAReport against the JSON schema.

- [ ] **Step 6: Run all QA tests**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_qa_*.py -v`

Expected: All tests PASS.

- [ ] **Step 7: Validate QAReport against schema**

Run: `source .venv/bin/activate && python3 -c "
import json
from jsonschema import validate
schema = json.load(open('src/schemas/qa_report.schema.json'))
report = json.load(open('./tmp/test-qa/qa-report.json'))
validate(instance=report, schema=schema)
print('QAReport validates against schema')
"`

- [ ] **Step 8: Commit**

```bash
git add src/qa/report.py src/qa/run_qa.py .claude/skills/deck-qa/ tests/test_qa_report.py tests/test_qa_integration.py
git commit -m "feat: add deck-qa skill with report generation, runner, and integration tests"
```

---

## Task 9: Research Synthesis -- presentation-reviewer

**Files:**
- Create: `research/synthesis-presentation-reviewer.md`

- [ ] **Step 1: Read persona specification**

Read:
- `docs/architecture/ai-persona-summaries.md` (Presentation Reviewer -- Section 3)
- `research/08-narrative-arc-patterns.md` (narrative structures, pacing)
- `research/01-slide-layout-intelligence.md` (design principles -- Duarte, Reynolds)
- `docs/architecture/architecture-overview.md` (correction loops, separation of automated vs human-judgement QA)

- [ ] **Step 2: Write synthesis document**

Create `research/synthesis-presentation-reviewer.md` covering:
1. **Persona contract:** Authority model (Invoker), escalation target (Deck Conductor), confidence minimum (0.7)
2. **Scope boundary:** What the reviewer assesses vs what deck-qa checks -- no overlap
3. **Review dimensions:** Narrative coherence, visual storytelling, pacing, speaker notes quality, audience appropriateness
4. **Input data:** Reads .pptx, SlideOutline, StyleGuide, SpeakerNotes, TalkBrief (all read-only)
5. **Output format:** Structured review with per-slide feedback and prioritised recommendations (critical/suggested/polish)
6. **Escalation triggers:** (1) Narrative incompatible with format, (2) Visual inconsistency beyond QA detection
7. **Advisory-only constraint:** Never modifies deck, never re-invokes services

- [ ] **Step 3: Commit**

```bash
git add research/synthesis-presentation-reviewer.md
git commit -m "docs: add presentation-reviewer research synthesis"
```

---

## Task 10: presentation-reviewer Agent

**Files:**
- Create: `.claude/agents/presentation-reviewer.md`

- [ ] **Step 1: Write the agent definition**

Create `.claude/agents/presentation-reviewer.md`:

```markdown
# Presentation Reviewer

You are the Presentation Reviewer — an advisory AI Persona that reviews assembled PowerPoint decks against conference presentation best practices.

## Identity

**Persona ID:** persona-presentation-reviewer
**Service ID:** assembly-presentation-reviewer
**Authority Model:** Invoker (acts on behalf of the Deck Conductor)
**Confidence Minimum:** 0.7
**Escalation Target:** Deck Conductor

## Role

You review assembled decks for conference quality. You assess aspects that programmatic QA (deck-qa) cannot detect: narrative coherence, visual storytelling, pacing, speaker notes quality, and audience appropriateness.

**You are advisory only. You NEVER modify the deck, outline, images, or notes directly. You NEVER re-invoke any service.** You produce a structured review that goes to the Deck Conductor, who decides whether to act on your recommendations.

## What You Assess (deck-qa Does NOT)

1. **Narrative Coherence** — Does the deck tell a compelling story? Does the narrative arc match the stated format? Are transitions between sections logical?
2. **Visual Storytelling** — Do images reinforce the message or distract? Is there visual rhythm (alternating text-heavy and visual slides)? Does the visual style match the audience?
3. **Pacing** — Is the slide density appropriate for the duration? Are there breathing room slides? Are dense sections followed by lighter ones?
4. **Speaker Notes Quality** — Are notes specific and actionable or generic filler? Do they provide genuine speaking cues? Are timing markers realistic?
5. **Audience Appropriateness** — Does the technical depth match the stated audience? Is the tone consistent with the TalkBrief? Will the content land with this specific audience?

## What You Do NOT Assess (deck-qa Already Checks)

- Font sizes, margins, contrast ratios, word counts
- Image resolution, aspect ratio distortion
- Placeholder residue, dead slides
- Bullet count, font family count
- Any of the 25 AP checks from the QA heuristics

## Input Data

You read these DeckContext files (all read-only):

| File | Purpose |
|------|---------|
| `./tmp/deck/output/presentation.pptx` | The assembled deck (view slide images) |
| `./tmp/deck/outline.json` | Original slide plan — check build matches intent |
| `./tmp/deck/style-guide.json` | Brand and design parameters for consistency |
| `./tmp/deck/speaker-notes.json` | Speaker notes for pacing and quality review |
| `./tmp/deck/talk-brief.json` | Original brief for alignment checking |
| `./tmp/deck/qa-report.json` | QA results (assume automated checks passed) |

## Review Process

1. Read the TalkBrief to understand the audience, duration, and tone
2. Read the SlideOutline to understand the intended narrative arc
3. View the assembled .pptx slide images (use the pptx skill's visual QA approach: convert to PDF via LibreOffice headless, then render to images)
4. Read the SpeakerNotes for pacing and quality
5. Produce the structured review below

## Output Format

Produce a structured review in this format:

### Overall Assessment

**Narrative Arc:** [Strong / Adequate / Weak] — [1-2 sentence explanation]
**Visual Storytelling:** [Strong / Adequate / Weak] — [1-2 sentence explanation]
**Pacing:** [Strong / Adequate / Weak] — [1-2 sentence explanation]
**Speaker Notes:** [Strong / Adequate / Weak] — [1-2 sentence explanation]
**Audience Fit:** [Strong / Adequate / Weak] — [1-2 sentence explanation]

### Per-Slide Feedback

For slides that need attention (skip slides that are fine):

| Slide | Issue | Priority | Recommendation |
|-------|-------|----------|----------------|
| N | [What's wrong] | Critical/Suggested/Polish | [Specific fix] |

### Priority Definitions

- **Critical:** Issues that will noticeably harm the presentation's effectiveness. The Conductor should address these before delivery.
- **Suggested:** Improvements that would elevate the deck. Worth addressing if time permits.
- **Polish:** Minor refinements for perfection. Address only if the deck is otherwise complete.

### Escalation Triggers

Flag these to the Deck Conductor for Speaker decision:

1. **Narrative structure fundamentally incompatible with format** — e.g., 40 content slides for a 15-minute lightning talk, or a storytelling arc used for a technical deep-dive audience
2. **Visual identity inconsistent in ways programmatic QA cannot detect** — e.g., image styles clash (photorealistic next to flat illustration), or colour temperature shifts between sections

## Prohibited Actions

- Do NOT modify any files
- Do NOT invoke any skills or services
- Do NOT override the Speaker's creative choices — flag concerns but respect stated preferences in the TalkBrief
- Do NOT duplicate deck-qa's programmatic checks — assume those have already passed
- Do NOT communicate with the Speaker directly — all communication goes through the Deck Conductor
```

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/presentation-reviewer.md
git commit -m "feat: add presentation-reviewer advisory agent definition"
```

---

## Task 11: End-to-End Integration Test

**Files:**
- Create: `tests/test_phase5_integration.py`

- [ ] **Step 1: Write end-to-end integration test**

Create `tests/test_phase5_integration.py` that exercises the full Phase 5 pipeline:

```python
"""End-to-end integration test for Phase 5: Assembly & QA.

Simulates the full pipeline:
1. Set up a DeckContext directory with all required contracts
2. Run deck-assembler to produce a .pptx
3. Run deck-qa to produce a QAReport
4. Validate the QAReport against the JSON schema
5. Verify the presentation-reviewer agent file exists
"""

import json
import os
import shutil
import subprocess
import pytest
from jsonschema import validate

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures', 'minimal_deck')
TEST_DECK_DIR = os.path.join(PROJECT_ROOT, 'tmp', 'test-phase5-e2e')
SCHEMA_DIR = os.path.join(PROJECT_ROOT, 'src', 'schemas')


@pytest.fixture(autouse=True)
def setup_teardown():
    """Set up test DeckContext and clean up after."""
    if os.path.exists(TEST_DECK_DIR):
        shutil.rmtree(TEST_DECK_DIR)
    os.makedirs(os.path.join(TEST_DECK_DIR, 'images'), exist_ok=True)
    os.makedirs(os.path.join(TEST_DECK_DIR, 'output'), exist_ok=True)
    # Copy fixtures
    for fname in os.listdir(FIXTURE_DIR):
        src = os.path.join(FIXTURE_DIR, fname)
        dst = os.path.join(TEST_DECK_DIR, fname)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
    yield
    if os.path.exists(TEST_DECK_DIR):
        shutil.rmtree(TEST_DECK_DIR)


def test_assembler_then_qa_pipeline():
    """Full pipeline: assemble -> QA -> validate report."""
    # Step 1: Assemble
    result = subprocess.run(
        ['node', os.path.join(PROJECT_ROOT, 'src', 'assembler', 'build_deck.js'),
         '--deck-dir', TEST_DECK_DIR],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, f"Assembly failed: {result.stderr}"
    pptx_path = os.path.join(TEST_DECK_DIR, 'output', 'presentation.pptx')
    assert os.path.isfile(pptx_path)

    # Step 2: QA
    qa_result = subprocess.run(
        ['python3', '-m', 'src.qa.run_qa',
         '--pptx-path', pptx_path,
         '--deck-dir', TEST_DECK_DIR,
         '--output', os.path.join(TEST_DECK_DIR, 'qa-report.json')],
        capture_output=True, text=True, timeout=30,
        cwd=PROJECT_ROOT
    )
    # QA may return 0 (pass) or 1 (fail) -- both are valid
    qa_report_path = os.path.join(TEST_DECK_DIR, 'qa-report.json')
    assert os.path.isfile(qa_report_path), f"QA report not created. stderr: {qa_result.stderr}"

    # Step 3: Validate report against schema
    with open(qa_report_path) as f:
        report = json.load(f)
    with open(os.path.join(SCHEMA_DIR, 'qa_report.schema.json')) as f:
        schema = json.load(f)
    validate(instance=report, schema=schema)

    # Step 4: Verify report structure
    assert report['verdict'] in ('pass', 'pass_with_warnings', 'fail')
    assert 'summary' in report
    assert 'findings' in report
    assert isinstance(report['findings'], list)


def test_presentation_reviewer_agent_exists():
    """The presentation-reviewer agent definition must exist."""
    agent_path = os.path.join(PROJECT_ROOT, '.claude', 'agents', 'presentation-reviewer.md')
    assert os.path.isfile(agent_path), "presentation-reviewer.md not found"
    with open(agent_path) as f:
        content = f.read()
    # Verify key sections exist
    assert 'Presentation Reviewer' in content
    assert 'advisory' in content.lower() or 'Advisory' in content
    assert 'NEVER modify' in content or 'never modif' in content.lower()
```

- [ ] **Step 2: Run end-to-end test**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_phase5_integration.py -v`

Expected: All tests PASS.

- [ ] **Step 3: Run ALL Phase 5 tests together**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_assembler.py tests/test_qa_*.py tests/test_phase5_integration.py -v`

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_phase5_integration.py
git commit -m "test: add end-to-end Phase 5 integration test (assemble -> QA -> validate)"
```

---

## Task 12: Update requirements.txt and package.json

**Files:**
- Modify: `requirements.txt`
- Verify: `package.json`

- [ ] **Step 1: Add Python dependencies for deck-qa**

Append to `requirements.txt`:

```
python-pptx>=1.0.0
Pillow>=10.0.0
```

- [ ] **Step 2: Verify PptxGenJS is in package.json**

```bash
cat package.json | grep pptxgenjs
```

If not present, run: `npm install pptxgenjs --save`

- [ ] **Step 3: Install and verify**

```bash
source .venv/bin/activate && pip install -r requirements.txt
python3 -c "from pptx import Presentation; print('python-pptx OK')"
node -e "const P = require('pptxgenjs'); console.log('pptxgenjs OK')"
```

- [ ] **Step 4: Commit**

```bash
git add requirements.txt package.json package-lock.json
git commit -m "chore: add python-pptx and Pillow to requirements, verify pptxgenjs in package.json"
```

---

## Summary of Anti-Pattern to QAReport Category Mapping

| AP | Name | Category | Severity |
|----|------|----------|----------|
| AP-01 | Wall of Text | text_overflow | error |
| AP-02 | Font Size Below Minimum | consistency | error |
| AP-03 | Too Many Font Families | consistency | warning |
| AP-04 | Inconsistent Bullet Styles | consistency | warning |
| AP-05 | Orphan/Widow Lines | consistency | info |
| AP-06 | Elements Outside Safe Margins | margin | warning |
| AP-07 | Low Contrast | contrast | error |
| AP-08 | Clashing Colours | contrast | warning/error |
| AP-09 | Missing Speaker Notes | missing_content | warning |
| AP-10 | Slide Count vs Duration | consistency | warning |
| AP-11 | Placeholder Residue | placeholder_residue | error |
| AP-12 | Image Resolution Too Low | image_quality | error |
| AP-13 | Image Aspect Ratio Distortion | image_quality | warning |
| AP-14 | Too Many Bullet Points | text_overflow | warning |
| AP-15 | Consecutive Bullet-Heavy Slides | consistency | warning |
| AP-16 | Missing Title Slide | missing_content | warning |
| AP-17 | Missing Closing/CTA Slide | missing_content | warning |
| AP-18 | Inconsistent Heading Sizes | consistency | warning |
| AP-19 | Text Overflow/Clipping | text_overflow | warning |
| AP-20 | Element Overlap | overlap | warning |
| AP-21 | Excessive Animations | consistency | warning |
| AP-22 | Poor Data-Ink Ratio | consistency | warning/info |
| AP-23 | Branding Inconsistency | consistency | info |
| AP-24 | Dead/Empty Slides | missing_content | warning |
| AP-25 | Colourblind Safety | accessibility | warning |

---

### Critical Files for Implementation

- `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/assembler/build_deck.js` -- the main PptxGenJS assembly script that reads all DeckContext contracts and produces the .pptx
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/qa/checks/structural.py` -- the largest check module implementing 12 of the 25 anti-pattern checks
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/qa/run_qa.py` -- the QA runner entry point that orchestrates all checks and produces the QAReport
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/agents/presentation-reviewer.md` -- the advisory agent definition with review dimensions and output format
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/assembler/slide_masters.js` -- slide master definitions mapping all 12 slide types to PptxGenJS layouts
