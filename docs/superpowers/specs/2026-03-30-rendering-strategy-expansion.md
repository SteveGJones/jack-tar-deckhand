# Rendering Strategy Expansion: backGROUND, backDROP, and Pragmatic Composition

**Date:** 2026-03-30
**Status:** Approved
**Spike:** `docs/spikes/backdrop-content-aware-positioning.md`
**Canonical Model:** v1.2.0 (updated concurrently)

---

## Problem

The current `backdrop_render` strategy uses a single layout — a semi-transparent left panel on every slide. This produces a repetitive, "samey" feel that doesn't serve keynote-quality presentations. The overlay feels like a compromise rather than a design choice.

## Solution

Expand the rendering strategy taxonomy from 3 to 5. Implement in four phases: foundation first (schemas, classification), then three rendering approaches built on that foundation.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Implementation order | Foundation first, then backGROUND, pragmatic composition, backDROP | Schemas/routing must exist before any rendering path. backGROUND is simplest, backDROP is hardest. |
| Vision analysis for backDROP | Claude Code agent, not Python SDK | Jack-Tar runs inside Claude Code. Native vision is available. SAM is a future fallback if needed. |
| Testing | Mocked unit tests for CI + tagged Ollama integration tests | Ollama-only first pass — if it works with Ollama it works with everything. |
| Spatial positioning for backDROP | Vision post-analysis, not prompt-prescribed | Standard image models don't reliably follow coordinate-level spatial instructions. Vision finds where elements actually landed. |
| Spatial positioning for pragmatic composition | Deterministic — we control element placement | No vision needed. Elements generated individually, placed at exact coordinates. |

---

## Phase 1: Foundation (Schema + Strategy Classification)

### Schema Changes

**`strategy_map.schema.json`:**
- Expand strategy enum: `full_render`, `backdrop_render`, `composed`, `background`, `backdrop`, `pragmatic_composition`
- `backdrop_render` retained for backward compatibility (maps to `background` with `left_panel`)
- Add optional `backdrop_variant` field: enum of `left_panel`, `right_panel`, `bottom_bar`, `top_band`, `center_float`
- Add optional `element_layout` field:
  ```json
  {
    "template": "three_across",
    "elements": [
      {"id": "elem_1", "label_source": "body_points[0]", "x": 0.08, "y": 0.25, "w": 0.25, "h": 0.50}
    ],
    "title_region": {"x": 0.05, "y": 0.02, "w": 0.90, "h": 0.12}
  }
  ```

**`image_manifest.schema.json`:**
- Add optional `detected_positions` array per image: `{element_id, x, y, w, h, confidence}`
- Add optional `element_id` and `placement_zone` (`"background"` | `"element"`) fields per image entry

### Strategy Classification

**`slide_prompt_composer.py`:**
- `classify_slide_strategy()` expanded to classify into 5 strategies
- New `select_backdrop_variant(slide, arc_position)` function for backGROUND template selection
- Element layout template library — 5 templates:
  - `three_across` — 3 equal columns
  - `two_column` — 2 wide columns
  - `grid_2x2` — 2x2 grid
  - `process_flow` — horizontal row, 3-5 elements
  - `hub_and_spoke` — 1 center + 3-4 surrounding

### Assembler Routing

**`build_deck.js` main loop:**
- Expand strategy routing from 3 to 5 paths
- New paths initially stub to existing `buildBackdropRenderSlide` as fallback
- Read `backdrop_variant` and `element_layout` from strategy map entries, pass through ctx

### Tests
- Schema validation for new fields and enums
- Classification tests for all 5 strategies
- Template selection tests
- Backward compatibility: existing `backdrop_render` slides still work unchanged

---

## Phase 2: backGROUND (Template Zone Variety)

### Assembler

**New `buildBackgroundSlide(pptx, slideData, ctx)` function:**

Five overlay geometries:

| Variant | Overlay Position | Overlay Size | Transparency |
|---------|-----------------|-------------|-------------|
| `left_panel` | x: 0, y: 0 | w: 40% slide, h: 100% | 60% black |
| `right_panel` | x: 60% slide, y: 0 | w: 40% slide, h: 100% | 60% black |
| `bottom_bar` | x: 0, y: 70% slide | w: 100%, h: 30% | 60% black |
| `top_band` | x: 0, y: 0 | w: 100%, h: 25% | 60% black |
| `center_float` | centered | w: 60%, h: 50% | 65% black |

Each variant defines text zone position (heading + body points) within the overlay area. Safe margins enforced at template definition time (minimum 0.5" from edges).

### Prompt Composer

`assemble_brief()` includes `backdrop_variant` so the Prompt Engineer knows where text will land:
- `left_panel` / `right_panel` → "keep the [opposite side] visually interesting, the [text side] can be simpler/darker"
- `bottom_bar` → "visual interest in the top two-thirds, bottom can be darker"
- `top_band` → "visual interest below, top area can be simpler"
- `center_float` → "visual interest at edges, center area less busy"

### Tests
- Unit test for each variant: overlay position, text zone bounds, safe margins
- Integration test: Ollama generates background, assemble with each variant, verify output .pptx structure

---

## Phase 3: Pragmatic Composition (Multi-Image Element Assembly)

### Prompt Composer

**New `split_element_briefs(slide, strategy, style_guide, brand_profile, element_layout)` function:**
- Input: slide + element layout template
- Output: 1 background brief + N element briefs
- Background brief: atmospheric/textured, no figurative elements, full-bleed
- Element briefs: individual objects on transparent/simple background
- Shared prompt prefix across all element briefs (palette hex, style tokens, "flat illustration, clean edges, no text") for style consistency
- Element dimensions derived from region size in layout template

### Image Generation

- Render funnel generates 1+N images per slide
- ImageManifest entries:
  - 1 with `placement_zone: "background"`, `element_id: null`
  - N with `placement_zone: "element"`, `element_id: "elem_1"` etc.

### Assembler

**New `buildPragmaticSlide(pptx, slideData, ctx)` function:**
1. Place background image full-bleed
2. For each element in `element_layout.elements`:
   - Find matching image by `element_id` in ImageManifest
   - Place at exact coordinates: `x * SLIDE_W`, `y * SLIDE_H`, `w * SLIDE_W`, `h * SLIDE_H`
3. Place text labels adjacent to each element:
   - Default: below element (element bottom + 0.1" gap)
   - If element in bottom third of slide: above instead
   - Small semi-transparent backing pill sized to text content
   - Text from mapped `label_source` (e.g., `body_points[0]`)
4. Place headline in `title_region`
5. Footer logo + speaker notes

### Tests
- Unit tests: coordinate normalisation (0-1 → inches), label placement logic (below vs above), multi-image lookup by element_id
- Integration test: Ollama generates 1 background + 3 elements with `three_across` template, assemble, verify all images and labels in output .pptx

---

## Phase 4: backDROP (Vision-Analysed Positioning)

### Vision Analyst Agent

**`.claude/agents/vision-analyst.md`:**
- Input: generated image path, element descriptions (from body_points), expected element count
- Process: Claude reads the image with its native vision, identifies figurative elements, returns bounding boxes
- Output: JSON array of `{element_id, x, y, w, h, confidence}` in normalised 0-1 coordinates
- Ordering convention: left-to-right, then top-to-bottom
- Confidence threshold: 0.7 minimum per element

### Pipeline Flow

1. Prompt composer assembles spatial-intent brief ("three computers arranged horizontally, evenly spaced")
2. Prompt Engineer composes prompt with spatial direction (no precise coordinates)
3. Render funnel generates 1 scene image
4. **Vision analyst agent** analyses image → returns detected positions
5. Detected positions written to ImageManifest as `detected_positions` array
6. Assembler reads detected positions for text placement

### Assembler

**New `buildBackdropSlide(pptx, slideData, ctx)` function:**
1. Place scene image full-bleed
2. Read `detected_positions` from ImageManifest
3. For each detected element: text label centered within detected bounding box, small backing pill
4. Headline in `title_region`
5. Footer logo + speaker notes

**Fallback chain:**
1. Vision-detected positions (preferred)
2. Prescribed positions from `element_layout` in StrategyMap (if vision confidence < 0.7 or fails)
3. QA flags AP-28 when fallback is used

### Tests
- Unit tests: position normalisation, fallback logic, label-within-bounding-box placement
- Mock vision agent responses for deterministic CI tests
- Integration test: Ollama generates scene, vision analysis runs, assemble with detected positions

---

## QA Changes

**AP-20 (overlap):** Skip for `backdrop` and `pragmatic_composition` slides where text-over-image is intentional.

**AP-27 (element layout validation):** New check for `backdrop` and `pragmatic_composition`:
- All regions within slide bounds (0.0-1.0)
- No two regions overlap by more than 10%
- `label_source` references exist in SlideOutline
- Element count 1-5

**AP-28 (vision confidence):** New check for `backdrop` slides:
- Flag elements with confidence < 0.7
- Flag slides where vision fell back to prescribed positions

---

## Test Strategy

**Unit tests (mocked, CI-friendly):**
- Schema validation for all new fields
- Strategy classification for all 5 strategies
- Template selection and coordinate maths
- Each assembler path with mock image data
- Vision fallback logic with mock agent responses
- QA checks AP-27 and AP-28

**Integration tests (tagged, require Ollama):**
- backGROUND: generate image + assemble with each of 5 variants
- Pragmatic composition: generate background + 3 elements + assemble
- backDROP: generate scene + vision analysis + assemble
- Full pipeline: outline → strategy map → images → assembly → QA

Estimated new tests: ~74 (per spike estimate).
