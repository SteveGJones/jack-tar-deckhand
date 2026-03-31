# Architecture Spike: Rendering Strategy Expansion — backGROUND, backDROP, and Pragmatic Composition

**Date:** 2026-03-30 (revised)
**Status:** Approved
**Scope:** Image Services (L1) + Assembly & QA Services (L1)

---

## 1. Problem Statement

The current `backdrop_render` strategy generates an AI background image and overlays text using a fixed layout: a semi-transparent rectangle covering the left 45% of the slide. This produces a uniform, repetitive layout that feels like a compromise rather than a design choice.

We are expanding the rendering strategy taxonomy from 3 to 5:

| Strategy | Description | Status |
|----------|-------------|--------|
| `full_render` | Entire slide is a single AI-generated image | Existing |
| `composed` | Standard PptxGenJS assembly (diagrams, charts, text) | Existing |
| `background` | Atmospheric AI image + text in template zones | Enhancement of existing `backdrop_render` |
| `backdrop` | Structured AI scene + vision-detected text positioning | New |
| `pragmatic_composition` | AI-generated element images + programmatic assembly | New |

---

## 2. The Five Strategies in Detail

### 2.1 full_render (unchanged)
Entire slide is a single AI-generated image. No PptxGenJS text boxes. Speaker notes carry the delivery. Used for title cards, section dividers, visual-impact moments.

### 2.2 composed (unchanged)
Standard PptxGenJS assembly. Shapes, text boxes, optional images placed programmatically. Used for diagrams, data charts, code slides, text-heavy content.

### 2.3 backGROUND (enhanced from current backdrop_render)
AI generates an atmospheric/mood background image. Text goes in a predefined template zone with a semi-transparent overlay for readability. The image does not need to "know" where text goes.

**Enhancement:** Five template zones instead of one:
- `left_panel` — Left 40% (current behaviour)
- `right_panel` — Right 40%
- `bottom_bar` — Bottom 30%, full-width
- `top_band` — Top 25%, full-width
- `center_float` — Centered box with generous padding

Template selection is per-slide, specified in the StrategyMap. This gives visual rhythm across backdrop slides without changing the fundamental approach.

### 2.4 backDROP (new — vision-analysed positioning)
AI generates a structured image with figurative visual elements (e.g., three computers, graph nodes, process boxes). After generation, a vision model analyses the image to detect where those figurative elements actually landed. The assembler places PptxGenJS text boxes at the detected positions.

**Why vision analysis, not prompt-prescribed positions:** Standard image generation models (FLUX, z-image-turbo, GPT-Image, Nanobanana) do NOT reliably follow precise spatial positioning instructions. They can do broad composition ("three things spread across the image") but not coordinate-level precision ("element at x=25%"). Prompt-prescribed positioning would result in visibly misaligned text labels. Vision post-analysis solves this by working with what the model actually produced.

**Flow:**
1. Prompt composer generates a spatial-intent prompt ("three computers arranged horizontally")
2. Image model generates the scene
3. Vision model (Claude vision) analyses the generated image: "I see three computer-like elements at approximately [x1,y1], [x2,y2], [x3,y3]"
4. Pipeline maps detected elements to slide content (body_points[0] → element 1, etc.)
5. Assembler places text boxes at detected positions with small semi-transparent backing pills

**Key challenge:** Semantic matching — associating detected bounding boxes with the correct content items. Mitigated by:
- Ordering elements left-to-right / top-to-bottom (natural reading order)
- Limiting to 5 elements maximum per slide
- Including element descriptions in the vision analysis prompt

**Best for:** Organic compositions where elements have natural visual identity — labelled systems, annotated processes, network diagrams.

### 2.5 Pragmatic Composition (new — deterministic element assembly)
Individual element images are generated separately (a computer, a node, an icon), then placed at exact pixel positions by the assembler on top of an atmospheric background image. Text labels are placed at predetermined positions adjacent to each element.

**Flow:**
1. Prompt composer breaks the slide into: 1 background image + N element images
2. Each element is generated individually (consistent style via prompt constraints)
3. Background is generated as an atmospheric/textured image
4. Assembler places background full-bleed, then positions each element image at exact coordinates
5. Text labels placed at known positions adjacent to elements

**No vision analysis needed.** Positions are deterministic because we control where elements are placed, not the image model.

**Key challenge:** Style consistency across multiple generated elements. Mitigated by:
- Shared prompt prefix with palette and style tokens
- Using the same model for all elements in a slide
- Post-processing to normalise colour balance

**Best for:** Structured layouts requiring precision — comparison grids, process flows, feature showcases. When you need pixel-perfect alignment between text and visuals.

---

## 3. Strategy Selection Guide

| Slide Content | Best Strategy | Rationale |
|---------------|---------------|-----------|
| Dramatic visual moment, no text needed | `full_render` | Maximum visual impact |
| Conceptual/emotional with bullet text | `background` | Mood image + readable text zones |
| Structured scene with labelled elements | `backdrop` | Vision-detected element positioning |
| Precise grid/flow with multiple distinct items | `pragmatic_composition` | Deterministic positioning, style control |
| Diagrams, charts, data, code | `composed` | Programmatic precision |

Maximum element count: 5 for both `backdrop` and `pragmatic_composition`. Beyond 5, the slide is too dense for conference use.

---

## 4. Service Ownership

### No new services needed

| Responsibility | Owner | Notes |
|---|---|---|
| Strategy classification + backdrop_mode selection | `slide-prompt-composer` (Image Services) | Extends existing `classify_slide_strategy()` |
| Spatial prompt composition | Prompt Engineer persona (Image Services) | New composition rules for both modes |
| Element image generation | `image-keynote-rendering` via render funnel (Image Services) | Generates background + element images |
| Vision post-analysis (backDROP only) | New capability in Image Services | Vision model call to detect element positions |
| Template zone rendering (backGROUND) | `deck-assembler` (Assembly & QA) | 5 template variants |
| Detected-position rendering (backDROP) | `deck-assembler` (Assembly & QA) | Text at vision-detected coordinates |
| Composed-element rendering (pragmatic) | `deck-assembler` (Assembly & QA) | Multi-image assembly with text labels |

### AI Persona Changes

| Persona | Change |
|---|---|
| **Prompt Engineer** | New composition rules for backDROP (spatial intent) and pragmatic composition (element-level prompts). Receives element metadata in the brief. |
| **Image Generation Expert** | Gains advisory capability for vision analysis quality. Can recommend re-generation if element detection confidence is low. |
| **Deck Conductor** | Expanded strategy routing — 5 strategies instead of 3. |
| **Presentation Reviewer** | Reviews text-to-element alignment quality for backDROP and pragmatic slides. |

No new persona needed. Vision analysis is a capability within Image Services, not a delegation decision requiring a new persona.

---

## 5. Schema Changes

### 5.1 StrategyMap Schema (strategy_map.schema.json)

Strategy enum expands:
```json
"strategy": {
  "type": "string",
  "enum": ["full_render", "backdrop_render", "composed", "background", "backdrop", "pragmatic_composition"]
}
```

Note: `backdrop_render` retained for backward compatibility. New slides use `background` or `backdrop`.

New optional fields per slide entry:
```json
{
  "backdrop_variant": "bottom_bar",
  "element_layout": {
    "template": "three_across",
    "elements": [
      {"id": "elem_1", "label_source": "body_points[0]", "x": 0.08, "y": 0.25, "w": 0.25, "h": 0.50},
      {"id": "elem_2", "label_source": "body_points[1]", "x": 0.375, "y": 0.25, "w": 0.25, "h": 0.50},
      {"id": "elem_3", "label_source": "body_points[2]", "x": 0.67, "y": 0.25, "w": 0.25, "h": 0.50}
    ],
    "title_region": {"x": 0.05, "y": 0.02, "w": 0.90, "h": 0.12}
  }
}
```

- `backdrop_variant`: Used by `background` strategy. One of: `left_panel`, `right_panel`, `bottom_bar`, `top_band`, `center_float`.
- `element_layout`: Used by `backdrop` and `pragmatic_composition`. Contains prescribed element regions.
  - For `backdrop`: These are target regions — vision analysis may adjust positions.
  - For `pragmatic_composition`: These are exact placement positions — deterministic.

### 5.2 ImageManifest Schema (image_manifest.schema.json)

New optional fields for vision-detected positions (backDROP only):
```json
{
  "detected_positions": [
    {"element_id": "elem_1", "x": 0.10, "y": 0.28, "w": 0.22, "h": 0.45, "confidence": 0.92},
    {"element_id": "elem_2", "x": 0.39, "y": 0.26, "w": 0.24, "h": 0.48, "confidence": 0.88}
  ]
}
```

New image type for pragmatic composition:
```json
{
  "image_id": "slide-11-elem-1",
  "slide_number": 11,
  "file_path": "./tmp/deck/images/slide-11-elem-1.png",
  "placement_zone": "element",
  "element_id": "elem_1",
  "status": "generated"
}
```

Multiple images per slide: one background + N element images.

### 5.3 SlideOutline Schema (slide_outline.schema.json)

No changes. The outline describes content (headline, body_points, visual_direction). Rendering strategy and layout are StrategyMap concerns.

---

## 6. Pipeline Flow Changes

### backGROUND flow
```
slide-prompt-composer
  -> strategy: "background", backdrop_variant: "bottom_bar"
  -> brief: {visual_direction, ...}

prompt-engineer
  -> atmospheric prompt (no spatial requirements)

render-funnel -> generates 1 image

deck-assembler
  -> buildBackgroundSlide() with template variant
  -> overlay in selected zone + text
```

### backDROP flow
```
slide-prompt-composer
  -> strategy: "backdrop", element_layout: {...}
  -> brief: {visual_direction, element_layout, ...}

prompt-engineer
  -> spatial-intent prompt ("three computers arranged horizontally")

render-funnel -> generates 1 structured scene image

vision-analysis (NEW STEP)
  -> analyses generated image
  -> returns detected element positions
  -> writes detected_positions to ImageManifest

deck-assembler
  -> buildBackdropSlide()
  -> reads detected_positions from ImageManifest
  -> places text at detected coordinates with backing pills
```

### Pragmatic Composition flow
```
slide-prompt-composer
  -> strategy: "pragmatic_composition", element_layout: {...}
  -> brief: {background_prompt, element_prompts[], ...}

prompt-engineer
  -> 1 background prompt + N element prompts (consistent style)

render-funnel -> generates 1 background + N element images

deck-assembler
  -> buildPragmaticSlide()
  -> places background full-bleed
  -> places each element image at exact prescribed coordinates
  -> places text labels adjacent to elements
```

---

## 7. Vision Analysis Design (backDROP)

### Input
- Generated image (PNG)
- Element descriptions from the outline (body_points content)
- Expected element count

### Process
- Vision model (Claude) receives the image + prompt:
  "This image contains N figurative elements representing [descriptions]. For each element, return its approximate bounding box as normalised coordinates {x, y, w, h} where 0,0 is top-left and 1,1 is bottom-right. Order elements left-to-right, then top-to-bottom."

### Output
- Array of `{element_id, x, y, w, h, confidence}` in normalised coordinates
- Confidence threshold: 0.7 minimum. Elements below threshold flagged in QA report.

### Cost
- Claude vision: ~$0.01-0.04 per image analysis
- Applied only to backDROP slides (typically 1-3 per deck)
- Budget tracker updated to track vision analysis costs

### Fallback
If vision analysis fails or returns low confidence for all elements:
1. Fall back to prescribed positions from `element_layout`
2. Flag in QA report as "vision fallback — positions may be approximate"

---

## 8. Layout Templates (Starter Set)

### backGROUND templates (5)

| Template | Overlay Position | Best For |
|---|---|---|
| `left_panel` | Left 40%, full height | Dense bullets, current default |
| `right_panel` | Right 40%, full height | Visual variety, image dominates left |
| `bottom_bar` | Bottom 30%, full width | Short text, image dominates |
| `top_band` | Top 25%, full width | Headline-heavy slides |
| `center_float` | Centered box, generous padding | Sparse text, image wraps |

### Element layout templates (5)

| Template | Elements | Layout | Best For |
|---|---|---|---|
| `three_across` | 3 | 3 equal columns | Comparison, options |
| `two_column` | 2 | 2 wide columns | Before/after, contrast |
| `grid_2x2` | 4 | 2x2 grid | Feature grid, quadrant |
| `process_flow` | 3-5 | Horizontal row | Sequential steps |
| `hub_and_spoke` | 1 center + 3-4 | Central + surrounding | Core concept + related |

---

## 9. QA Implications

### Existing checks adjusted
- **Overlap check (AP-20):** backDROP and pragmatic slides have intentional text-over-image overlap. QA should not flag these when the strategy is known.
- **Margin check (AP-06):** Layout templates guarantee safe margins at definition time.

### New check
- **AP-27: Element layout validation** — For `backdrop` and `pragmatic_composition` slides:
  - All element regions within slide bounds (0.0-1.0)
  - No two regions overlap by more than 10%
  - `label_source` references exist in SlideOutline
  - Element count within 1-5 range

### backDROP-specific check
- **AP-28: Vision confidence** — Flag slides where any detected element has confidence < 0.7 or where vision analysis fell back to prescribed positions.

---

## 10. Implementation Estimate

| Task | Service | Effort | Tests |
|---|---|---|---|
| StrategyMap schema: expand strategy enum + new fields | Image Services | Small | ~5 |
| ImageManifest schema: detected_positions + element images | Image Services | Small | ~4 |
| backGROUND template zones (5 variants) | Assembly & QA (`build_deck.js`) | Medium | ~10 |
| backDROP vision analysis capability | Image Services (new module) | Medium | ~8 |
| backDROP detected-position assembler | Assembly & QA (`build_deck.js`) | Medium | ~8 |
| Pragmatic composition: element prompt splitting | Image Services (`slide_prompt_composer.py`) | Medium | ~8 |
| Pragmatic composition: multi-image assembler | Assembly & QA (`build_deck.js`) | Medium | ~10 |
| Element layout template library (5 templates) | Image Services (`slide_prompt_composer.py`) | Small | ~6 |
| Strategy classification updates | Image Services (`slide_prompt_composer.py`) | Small | ~6 |
| Prompt Engineer: spatial + element composition rules | Image Services (agent) | Small | -- |
| AP-27 + AP-28 QA checks | Assembly & QA (`deck-qa`) | Small | ~6 |
| Budget tracker: vision analysis cost tracking | Image Services | Small | ~3 |
| **Total** | | | **~74 tests** |

---

## 11. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| Vision analysis returns wrong element ordering | Text labels assigned to wrong elements | Medium | Order detection left-to-right, top-to-bottom. Include element descriptions in vision prompt. |
| Vision confidence too low on Ollama drafts | Fallback to prescribed positions on every draft | High | Acceptable — drafts are for concept validation. Cloud renders produce cleaner images for better detection. |
| Style inconsistency across pragmatic elements | Elements look like they come from different images | Medium | Shared prompt prefix, same model, post-process normalisation. |
| Vision API cost accumulation | Unexpected spend on large decks | Low | Budget tracker caps. Typically 1-3 backDROP slides per deck at $0.01-0.04 each. |
| Semantic matching fails for abstract elements | Vision can't map "process node 2" to a bounding box | Medium | backDROP works best for figurative (recognisable) elements. Abstract layouts should use pragmatic composition instead. |

---

## 12. Decision Record

| Question | Decision | Rationale |
|---|---|---|
| How many rendering strategies? | 5 (full_render, composed, background, backdrop, pragmatic_composition) | Each serves a distinct use case. No overlap in purpose. |
| How does backDROP know element positions? | Vision post-analysis (Claude vision) | Standard image models don't follow precise spatial instructions. Vision finds where elements actually landed. |
| How does pragmatic composition achieve precision? | Generate elements individually, assemble at exact coordinates | No position detection needed — we control placement. |
| Prompt-prescribed positioning? | Rejected as primary approach | Image models are not spatially reliable enough. Retained as fallback for backDROP when vision fails. |
| New AI Persona? | No | Vision analysis is a capability, not a delegation decision. Fits within Image Services. |
| New L2 service? | No | Capabilities distribute across existing slide-prompt-composer, render funnel, and deck-assembler. |
| Backward compatibility? | `backdrop_render` retained in schema, maps to `background` mode with `left_panel` variant | Existing outlines continue to work unchanged. |
