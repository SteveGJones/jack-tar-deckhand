# SmartArt Quality Gates & Rendering Fixes — Design Specification

**Date:** 2026-04-04
**Status:** Approved
**Cause:** Demo deck visual audit revealed 18/28 slides with quality failures
**Branch:** `feat/smartart-intelligent-graphics`

---

## 1. Problem Statement

The first SmartArt demo deck assembled structurally (28 slides, 1.1 MB .pptx) but failed visual inspection on 18 slides. Five root causes:

| Category | Slides | Root Cause |
|----------|--------|------------|
| Blank slides | 1, 2, 9, 21, 28 | Strategies requiring AI images but imagegen-bridge not run |
| Mermaid no text / 0x0 | 4, 11, 24 | Mermaid SVG uses foreignObject for text (PowerPoint can't render), viewBox not parsed to pixel dimensions |
| Vega-Lite stretched | 8, 18, 19, 23, 26, 27 | No width/height in VL spec, defaults to ~200x400 portrait, stretched to 16:9 |
| Tiny text < 12px | 6, 12, 19, 27 | Container.fit_text min_size=10, feature matrices trigger reduction |
| No background on composed | 13, 22 | Composed slides have no brand treatment — white void |

The review process failed because: (a) deck-qa was never run, (b) image-reviewer was never dispatched, (c) presentation-reviewer was never dispatched, (d) "assembler didn't crash" was treated as "deck is ready."

---

## 2. Two-Stage Visual Inspection

Every SmartArt graphic and every assembled slide must pass visual review before the deck is declared ready.

### Stage 1: SmartArt Creation Review

**When:** After each graphic is rendered by `smartart_renderer.py`, before writing to SmartArtManifest.

**How:** Dispatch image-reviewer agent with `review_context: "smartart_graphic"`.

**Criteria:**
- **Data accuracy** — does the graphic represent the structured data correctly? Right number of nodes, labels match body_points.
- **Text readability** — all labels legible at 1920x1080 scale, no truncation without indicator.
- **Colour correctness** — palette matches StyleGuide tokens, contrast meets WCAG 4.5:1.
- **Layout clarity** — visual hierarchy is clear, elements don't overlap unintentionally.

**Verdict:** pass/refine. If refine, the renderer retries with adjusted parameters (larger font, fewer items). Max 2 retries, then flag as `accepted_with_issues`.

### Stage 2: Post-Assembly Slide Review

**When:** After deck-assembler produces the .pptx, after deck-qa runs the 35 automated checks.

**How:**
1. Rasterise every slide to PNG at 1920x1080 via LibreOffice headless (`soffice --headless --convert-to png --outdir <dir> <pptx>`), which correctly renders all embedded images, shapes, and text
2. Dispatch image-reviewer agent per slide with `review_context: "slide_visual_inspection"`

**Criteria:**
- **Blank detection** — is the slide empty or near-empty? (< 5% non-white pixels)
- **Text readability** — all text legible at presentation scale
- **Image distortion** — embedded images stretched or squashed beyond 20% aspect deviation
- **Brand consistency** — palette, typography, visual style match the deck's StyleGuide
- **Layout coherence** — composition makes visual sense, elements properly placed
- **Content completeness** — slide appears to have all content the outline promised

**Verdict:** pass/fail per slide. If ANY slide fails, the pipeline reports failures and does NOT declare the deck ready.

**Cost:** 28 slides x Haiku ≈ $0.03 total.

### Pipeline Position

```
smartart-renderer (render + Stage 1 review per graphic)
  → deck-assembler
    → deck-qa (35 automated checks)
      → slide-visual-review (Stage 2 — NEW, every slide rasterised + reviewed)
        → presentation-reviewer (narrative/storytelling)
```

---

## 3. Pre-Assembly Automated Checks

Catch rendering defects at the point they're produced, before they reach the assembler.

### PA-01: SVG Dimension Validation

**Location:** `src/smartart_renderer.py`, after every render call.

- Parse SVG for `width`, `height`, and `viewBox` attributes
- For Mermaid: extract dimensions from viewBox (format: `"0 0 W H"`), set explicit `width="W" height="H"` pixel attributes
- FAIL if dimensions are 0x0 or missing
- FAIL if aspect ratio deviates >20% from 16:9 (1.78)
- FAIL triggers status: "failed" in manifest entry

### PA-02: SVG Text Content Verification

**Location:** `src/smartart_renderer.py`, after every render call.

- Count text elements: `<text>`, `<tspan>`, `<foreignObject>` (Mermaid uses foreignObject)
- For flowcharts/decision trees: FAIL if text element count < node count from spec
- For all types: WARN if zero text elements found
- FAIL triggers status: "failed" in manifest entry

### PA-03: Minimum Font Size Enforcement

**Location:** `src/smartart_renderer.py`, after every custom SVG render.

- Parse all `font-size` attributes from SVG content
- FAIL if any font-size < 12px
- The renderer should never produce < 12px — this is a safety net
- FAIL triggers status: "failed" in manifest entry

### PA-04: Mermaid Rasterisation Gate

**Location:** `src/smartart_renderer.py`, after Mermaid SVG → PNG conversion.

- Verify PNG file has non-zero dimensions
- Verify PNG is not all-white (sample pixels — if >95% white, likely blank)
- FAIL triggers status: "failed" in manifest entry

---

## 4. Rendering Pipeline Fixes

### Fix 1: Vega-Lite Dimensions

**File:** `src/smartart_renderer.py` — `render_vega_lite()`

Before writing the VL spec to file, inject:
```python
vl_spec['width'] = 1600
vl_spec['height'] = 900
vl_spec['autosize'] = {'type': 'fit', 'contains': 'padding'}
```

This ensures the chart fills a 16:9 container. The 1600x900 leaves room for the title region when placed in the 85% graphic zone.

### Fix 2: Mermaid Dimensions + Rasterisation

**File:** `src/smartart_renderer.py` — `render_mermaid()`

Changes:
1. Pass `--width 1600` flag to `npx mmdc` to control output width
2. After SVG is generated, post-process: extract viewBox, set explicit `width` and `height` pixel attributes
3. Always rasterise Mermaid SVG to PNG before returning (PowerPoint can't render foreignObject HTML)
4. Use Sharp via Node.js subprocess or Pillow as fallback for rasterisation
5. Return the PNG path, not the SVG path, as the primary `file_path` in the manifest (keep SVG as `svg_source_path`)

### Fix 3: Minimum Font Size 12px

**File:** `src/smartart_svg/engine.py` — `Container.fit_text()`

Change:
```python
min_size = 10  # OLD
min_size = 12  # NEW
```

Add `recommended_min` parameter (default 14) that layouts can pass. If text fits at `recommended_min` or above, use it. If not, reduce to `min_size` (12). Below 12, overflow is True.

### Fix 4: Composed Slide Brand Styling

**File:** `src/assembler/build_deck.js` — `buildComposedSlide()`

Apply to every composed slide:
- Background fill: `palette.background` (e.g., #F5F0E8 parchment)
- Bottom accent line: 2px wide, `palette.accent` colour, full width at y=95%
- Heading: `typography.heading_font`, `palette.text_primary`
- Body: `typography.body_font`, `palette.text_primary`

This ensures no composed slide is ever a white void.

### Fix 5: Background Strategy Fallback

**File:** `src/assembler/build_deck.js` — `buildBackgroundSlide()`

When no AI background image exists in the ImageManifest for this slide:
- Fill the background with `palette.background` colour
- Add a subtle gradient or accent element so it's not flat
- Don't leave it white

---

## 5. Demo Deck Strategy Changes

These slides change strategy to avoid requiring AI image generation for the initial demo:

| Slide | Old Strategy | New Strategy | Rationale |
|-------|-------------|--------------|-----------|
| 2 | backdrop | composed | Text-heavy problem statement, doesn't need vision-detected positioning |
| 9 | pragmatic_composition | composed | Section divider text, nautical elements are nice-to-have not essential |
| 21 | backdrop | composed | Section divider, brand styling sufficient |

Slides 1 and 28 keep full_render but with fallback:
- If Ollama available: generate nautical title/closing images
- If not: solid navy (#1B3A4B) background with gold (#C67B2F) heading text + parchment subtitle

---

## 6. Image Reviewer Context Extensions

**File:** `.claude/agents/image-reviewer.md`

Add two new review contexts:

### `smartart_graphic`

```
You are reviewing a SmartArt graphic — a data-driven diagram, chart, or infographic.
Assess against these criteria:
1. Data accuracy — correct number of nodes/items, labels match the data
2. Text readability — all labels legible at 1920x1080, minimum 12px font
3. Colour correctness — matches brand palette, WCAG 4.5:1 contrast on all text
4. Layout clarity — visual hierarchy clear, no unintentional overlap
```

### `slide_visual_inspection`

```
You are reviewing an assembled presentation slide — the final output the audience sees.
Assess against these criteria:
1. Blank detection — is the slide empty, mostly white, or missing expected content?
2. Text readability — all text legible, no truncation, no overflow
3. Image distortion — are embedded images stretched, squashed, or pixelated?
4. Brand consistency — palette, typography, and visual style match the deck
5. Layout coherence — composition makes sense, elements properly positioned
6. Content completeness — does the slide deliver what the headline promises?
```

---

## 7. New Module: Visual Inspection

**File:** `src/qa/checks/visual_inspection.py`

```python
def rasterise_slide(pptx_path, slide_number, output_dir) -> str:
    """Convert a single slide to PNG at 1920x1080. Returns PNG path."""

def inspect_slide(png_path, slide_number, outline_slide, style_guide) -> dict:
    """Run automated visual checks on a rasterised slide.
    Returns finding dict with severity and description."""

def run_visual_inspection(pptx_path, outline, style_guide, output_dir) -> list:
    """Rasterise all slides, run automated checks, return findings."""
```

The automated checks in `inspect_slide` are fast pre-filters:
- **Blank detection:** Count non-background pixels. If < 5% of area has content, flag as blank.
- **Dominant colour check:** Extract top 3 colours, verify at least one is from the brand palette.

These automated checks run first. Then the image-reviewer agent is dispatched for the full 6-criterion assessment on every slide.

### Registration in `run_qa.py`

Visual inspection runs as Step 2 (after Step 1: anti-pattern checks):

```python
# Step 2: Visual inspection (post-assembly, per-slide)
if visual_inspection_enabled:
    slide_pngs = rasterise_all_slides(pptx_path, output_dir)
    for png_path, slide_num in slide_pngs:
        # Automated pre-filter
        auto_findings = inspect_slide(png_path, slide_num, outline, style_guide)
        findings.extend(auto_findings)
        # Image-reviewer agent dispatch happens in the skill layer, not here
```

---

## 8. Test Plan

| Category | Tests | What's Tested |
|----------|-------|---------------|
| VL dimension injection | 2 | Spec has width/height after render, SVG matches 16:9 |
| Mermaid dimension post-process | 2 | SVG has explicit width/height, extracted from viewBox |
| Mermaid rasterisation | 2 | PNG produced, non-zero size, not all-white |
| fit_text min_size=12 | 2 | Text never below 12px, overflow True if can't fit |
| PA-01 dimension validation | 2 | Reject 0x0, reject wrong aspect ratio |
| PA-02 text content | 2 | Reject flowchart with 0 text, accept with text |
| PA-03 font size | 2 | Reject < 12px, accept >= 12px |
| PA-04 raster gate | 2 | Reject blank PNG, accept content PNG |
| Composed slide styling | 2 | Background colour applied, accent line present |
| Background fallback | 2 | Non-white background when no AI image |
| Visual inspection module | 4 | Blank detection, colour check, rasterise function, finding format |
| Demo deck fixture updates | 2 | Slides 2/9/21 strategy changed, validate against schema |
| **Total** | **~26** | |
