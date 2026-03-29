# Synthesis: deck-qa

> Distilled from: research/07-qa-heuristics-anti-patterns.md, research/01-slide-layout-intelligence.md, docs/architecture/data-contracts.md

## 1. Anti-Pattern Checks (AP-01 through AP-25)

All 25 checks with their severity, QAReport category mapping, and check type (structural / visual / cross-slide).

| AP ID | Name | Severity | QAReport Category | Check Type |
|-------|------|----------|-------------------|------------|
| AP-01 | Wall of Text | error | text_overflow | structural |
| AP-02 | Font Size Below Projection Minimum | error | accessibility | structural |
| AP-03 | Too Many Font Families | warning | consistency | cross-slide |
| AP-04 | Inconsistent Bullet Styles | warning | consistency | cross-slide |
| AP-05 | Orphan/Widow Lines | info | text_overflow | structural |
| AP-06 | Elements Outside Safe Margins | warning | margin | structural |
| AP-07 | Low Contrast Text-on-Background | error | contrast | structural |
| AP-08 | Clashing Colours | warning (error for red-green) | accessibility | cross-slide |
| AP-09 | Missing Speaker Notes | warning | missing_content | cross-slide |
| AP-10 | Slide Count vs Duration Mismatch | warning | consistency | cross-slide |
| AP-11 | Placeholder Residue | error | placeholder_residue | structural |
| AP-12 | Image Resolution Too Low | error | image_quality | structural |
| AP-13 | Image Aspect Ratio Distortion | warning | image_quality | structural |
| AP-14 | Too Many Bullet Points | warning | text_overflow | structural |
| AP-15 | Consecutive Bullet-Heavy Slides | warning | consistency | cross-slide |
| AP-16 | Missing Title Slide | warning | missing_content | cross-slide |
| AP-17 | Missing Closing/CTA Slide | warning | missing_content | cross-slide |
| AP-18 | Inconsistent Heading Sizes | warning | consistency | cross-slide |
| AP-19 | Text Overflow/Clipping | warning | text_overflow | structural |
| AP-20 | Element Overlap | warning | overlap | structural |
| AP-21 | Excessive Animations | warning | consistency | cross-slide |
| AP-22 | Poor Data-Ink Ratio on Charts | warning | consistency | structural |
| AP-23 | Logos/Branding Inconsistent | info | consistency | cross-slide |
| AP-24 | Dead/Empty Slides | warning | missing_content | structural |
| AP-25 | Colourblind-Unsafe Palette | warning | accessibility | cross-slide |

## 2. Check Categorisation

### Structural Checks (per-slide, fast, no rendering needed)

These parse the .pptx with python-pptx and inspect shape properties, text frames, and XML attributes. They run in under 1 second for a typical deck.

- **AP-01** Wall of Text -- count words per text frame and per slide
- **AP-02** Font Size -- iterate runs, check `run.font.size.pt`
- **AP-05** Orphan/Widow -- inspect last line length in paragraphs
- **AP-06** Safe Margins -- compare `shape.left`, `shape.top`, `shape.width`, `shape.height` against slide dimensions
- **AP-07** Low Contrast -- extract `run.font.color.rgb` and slide background colour, compute WCAG contrast ratio
- **AP-11** Placeholder Residue -- regex match text against known placeholder patterns
- **AP-12** Image Resolution -- open embedded image blob with Pillow, compare pixel dimensions to placement size in inches
- **AP-13** Aspect Ratio Distortion -- compare native image aspect ratio to display shape aspect ratio
- **AP-14** Bullet Count -- count non-empty bulleted paragraphs per text frame
- **AP-19** Text Overflow -- inspect `bodyPr` XML for `normAutofit` with `fontScale < 90000`
- **AP-20** Element Overlap -- compute rectangle intersection area between content shapes
- **AP-22** Chart Junk -- inspect chart XML for `view3D` and `minorGridlines` elements
- **AP-24** Dead Slides -- check whether any shape has text, images, charts, or tables

### Cross-Slide Checks (deck-wide, fast, no rendering needed)

These analyse patterns across all slides. Still fast (under 1 second) because they only aggregate structural data.

- **AP-03** Font Families -- collect all `run.font.name` values across the deck, count unique families
- **AP-04** Bullet Consistency -- collect bullet characters per indent level, flag mismatches
- **AP-08** Clashing Colours -- collect all colours used, check HSV hue differences and saturation levels
- **AP-09** Speaker Notes -- count content slides with non-empty `notes_slide.notes_text_frame.text`
- **AP-10** Slide Count Ratio -- compare `len(presentation.slides)` to `duration_minutes` from TalkBrief
- **AP-15** Consecutive Bullets -- track runs of bullet-heavy slides, flag when >= 3 consecutive
- **AP-16** Missing Title Slide -- check first slide layout name and placeholder idx 0
- **AP-17** Missing Closing Slide -- search last slide text for CTA keywords
- **AP-18** Heading Consistency -- collect title placeholder font sizes, flag outliers beyond 2pt variance
- **AP-21** Excessive Animations -- count distinct transition types across the deck
- **AP-23** Branding Consistency -- find shapes named "logo", compare positions across slides
- **AP-25** Colourblind Safety -- simulate deuteranopia on palette, check Euclidean distance between simulated colours

### Visual Checks (require rendering)

These require rendering the .pptx to images via LibreOffice headless + pdf2image. Performance depends on the rendering step (typically 2-5 seconds per slide). **Note:** For Phase 5 implementation, visual checks are deferred. All 25 AP checks can be implemented structurally using python-pptx XML inspection. AP-07 contrast and AP-12 resolution are implemented structurally by reading shape/run properties and embedded image blobs -- no rendering needed. Visual rendering would only be needed for pixel-level visual regression testing, which is out of scope for the initial implementation.

## 3. QAReport Category Mapping

The QAReport schema (`src/schemas/qa_report.schema.json`) defines 9 category values. Here is how each AP check maps to these categories.

### `overlap`
- **AP-20** Element Overlap -- text shapes overlapping by more than `max_overlap_pct`

### `contrast`
- **AP-07** Low Contrast Text-on-Background -- WCAG ratio below `min_contrast_ratio`

### `margin`
- **AP-06** Elements Outside Safe Margins -- content shapes extending beyond action-safe boundary

### `text_overflow`
- **AP-01** Wall of Text -- excessive word count per textbox or slide
- **AP-05** Orphan/Widow Lines -- very short trailing lines
- **AP-14** Too Many Bullet Points -- more than `max_bullets_per_slide` bullets
- **AP-19** Text Overflow/Clipping -- auto-shrink detected with fontScale below 90%

### `consistency`
- **AP-03** Too Many Font Families -- more than `max_font_families` unique families
- **AP-04** Inconsistent Bullet Styles -- same indent level using different bullet characters
- **AP-10** Slide Count vs Duration Mismatch -- ratio outside `slides_per_minute_min`..`slides_per_minute_max`
- **AP-15** Consecutive Bullet-Heavy Slides -- `max_consecutive_bullet_slides` or more in a row
- **AP-18** Inconsistent Heading Sizes -- title sizes varying beyond `max_heading_variance_pt`
- **AP-21** Excessive Animations -- more than `max_transition_types` transition types
- **AP-22** Poor Data-Ink Ratio -- 3D effects or minor gridlines on charts
- **AP-23** Logos/Branding Inconsistent -- logo position varies across slides

### `image_quality`
- **AP-12** Image Resolution Too Low -- effective DPI below `min_image_dpi_equiv` at placement size
- **AP-13** Image Aspect Ratio Distortion -- distortion exceeds `max_aspect_distortion_pct`

### `placeholder_residue`
- **AP-11** Placeholder Residue -- text matches known placeholder patterns (TODO, Lorem ipsum, Click to add, etc.)

### `missing_content`
- **AP-09** Missing Speaker Notes -- fewer than `min_speaker_notes_pct` of content slides have notes
- **AP-16** Missing Title Slide -- first slide is not a title layout
- **AP-17** Missing Closing/CTA Slide -- last slide lacks CTA keywords
- **AP-24** Dead/Empty Slides -- slides with no meaningful content

### `accessibility`
- **AP-02** Font Size Below Minimum -- font size below projection-safe thresholds
- **AP-08** Clashing Colours -- complementary colours at high saturation; red-green combinations
- **AP-25** Colourblind-Unsafe Palette -- palette colours indistinguishable under deuteranopia simulation

## 4. Threshold Defaults

All thresholds are configurable via a `QAConfig` dict/dataclass. Defaults are derived from research findings (Research 07, Section 6 Configuration Schema; Research 01, Quick Reference Top 10 Rules).

| Threshold | Default | Unit | Source |
|-----------|---------|------|--------|
| `max_words_per_textbox` | 40 | words | AP-01, 6x6 rule |
| `max_words_per_slide` | 75 | words | AP-01, Duarte: 30 ideal, 75 hard max |
| `min_font_size_body_pt` | 18 | pt | AP-02, projection minimum |
| `min_font_size_title_pt` | 24 | pt | AP-02, Kawasaki 10/20/30 |
| `max_font_families` | 2 | count | AP-03, professional standard |
| `safe_margin_pct` | 0.05 | fraction | AP-06, action-safe 5% |
| `min_contrast_ratio` | 4.5 | ratio | AP-07, WCAG AA (7.0 for AAA/projection) |
| `min_contrast_ratio_large` | 3.0 | ratio | AP-07, WCAG AA for 18pt+ text |
| `max_bullets_per_slide` | 6 | count | AP-14, Miller's 7+/-2 revised to 5 |
| `max_consecutive_bullet_slides` | 3 | count | AP-15, visual monotony |
| `min_speaker_notes_pct` | 0.5 | fraction | AP-09, 50% of content slides |
| `slides_per_minute_min` | 0.5 | ratio | AP-10, pacing lower bound |
| `slides_per_minute_max` | 2.0 | ratio | AP-10, pacing upper bound |
| `min_image_dpi_equiv` | 96 | DPI | AP-12, screen resolution minimum |
| `max_aspect_distortion_pct` | 5.0 | percent | AP-13, perceptible distortion |
| `max_overlap_pct` | 25 | percent | AP-20, overlap area threshold |
| `max_transition_types` | 2 | count | AP-21, professional limit |
| `colourblind_min_distance` | 30 | Euclidean | AP-25, simulated colour space |
| `min_last_line_chars` | 15 | chars | AP-05, orphan detection |
| `max_heading_variance_pt` | 2 | pt | AP-18, heading size consistency |
| `max_warnings_before_fail` | 10 | count | verdict logic |

## 5. Verdict Logic

The QAReport `verdict` field is one of: `pass`, `pass_with_warnings`, `fail`.

### Rules

1. **Count findings by severity.** After all checks run, tally `error`, `warning`, and `info` counts.
2. **Determine verdict:**
   - `fail` -- any finding with `severity == "error"`, OR `warning` count exceeds `max_warnings_before_fail` (default 10)
   - `pass_with_warnings` -- no errors, but at least one `warning`
   - `pass` -- no errors and no warnings (info-only findings are acceptable)
3. **Deck Conductor behaviour:**
   - `pass` -- proceed to Presentation Reviewer
   - `pass_with_warnings` -- proceed but include warnings in delivery
   - `fail` -- trigger correction cycle (max 2 correction cycles)
4. **Each QA pass overwrites the previous report.** The report file is `./tmp/deck/qa-report.json`.

### Implementation

```python
def compute_verdict(findings: list[dict], max_warnings: int = 10) -> str:
    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = sum(1 for f in findings if f["severity"] == "warning")
    if errors > 0 or warnings > max_warnings:
        return "fail"
    elif warnings > 0:
        return "pass_with_warnings"
    else:
        return "pass"
```

## 6. Python Dependencies

| Package | Import | Purpose | Install |
|---------|--------|---------|---------|
| python-pptx | `from pptx import Presentation` | Parse .pptx files, read shapes, text, images, XML | `pip install python-pptx` |
| Pillow | `from PIL import Image` | Open embedded image blobs, get dimensions | `pip install Pillow` |
| colorsys | `import colorsys` | RGB-to-HSV conversion for colour clash detection (AP-08) | stdlib |
| re | `import re` | Regex matching for placeholder detection (AP-11) | stdlib |
| lxml | `from lxml import etree` | XML inspection for autofit, animations, charts | transitive via python-pptx |
| collections | `from collections import Counter` | Heading size frequency analysis (AP-18) | stdlib |
| io | `import io` | BytesIO for image blob handling | stdlib |

**Not required for Phase 5 initial implementation:** opencv-contrib-python (BRISQUE), pdf2image (rendering), LibreOffice (headless conversion). These would only be needed for visual regression testing which is out of scope.

## 7. Performance

| Check Type | Expected Time | Notes |
|------------|---------------|-------|
| Structural checks (13 checks) | < 500ms | Single-pass python-pptx parse, shape iteration |
| Cross-slide checks (12 checks) | < 500ms | Aggregate data from same parse, no re-read |
| Total (all 25 checks) | < 1s | Structural + cross-slide combined |
| Image resolution checks (AP-12, AP-13) | +100-200ms | Pillow opens embedded image blobs |
| Visual rendering (deferred) | 2-5s per slide | LibreOffice headless + pdf2image |

The structural and cross-slide checks share a single pass over `presentation.slides`. The .pptx is opened once and all checks draw from the same parsed object. Image blobs are only opened when image shapes are encountered (AP-12, AP-13), adding minimal overhead.

## 8. QAReport Contract

File: `./tmp/deck/qa-report.json`. Schema: `src/schemas/qa_report.schema.json`.

Required fields: `verdict` (pass | pass_with_warnings | fail), `findings` (array).

Per-finding required fields: `slide_number`, `severity` (error | warning | info), `category` (one of the 9 enum values), `description`.

Per-finding optional fields: `suggested_fix`, `affected_element`, `auto_fixable`.

Summary object (optional): `total_slides`, `errors`, `warnings`, `info`.

## 9. Anti-Patterns to Avoid in Implementation

- Never render slides to images just for structural checks -- python-pptx gives direct access to all shape properties
- Never hard-code thresholds -- always read from a config dict/dataclass with the defaults above
- Never assume slide background is white -- extract it from `slide.background.fill` (fall back to white if undefined)
- Never skip AP-11 (placeholder residue) -- it is the single most embarrassing QA failure
- Never treat `info` severity as contributing to failure -- info findings are advisory only
