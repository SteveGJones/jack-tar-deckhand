# SmartArt Intelligent Graphics System — Design Specification

**Date:** 2026-04-03
**Status:** Approved
**Issue:** [#17 — feat: AI-driven SmartArt](https://github.com/SteveGJones/jack-tar-deckhand/issues/17)
**Research:** `research/ai-driven-templated-graphic-generation-research.md`
**BSA Version:** v1.3.0 → v1.4.0

---

## 1. Overview

An AI-driven templated graphic generation system that automatically produces intelligent, data-populated diagrams, charts, and infographics from structured data, lists, and narrative content. The system uses a negotiation pattern between the narrative-architect and a new SmartArt selector agent to choose the right graphic type and enrichment level, then extracts structured data, renders via competing engines, and composites with optional AI-generated imagery.

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Federated — new agents/modules, shared infrastructure | Clean separation of SmartArt logic; reuses existing image generation, budget, and review infrastructure |
| Graphic type selection | Negotiation between narrative-architect and selector agent | Narrative has semantic understanding; selector has visual vocabulary; neither alone picks the best answer |
| Data extraction | Dedicated Python module, not agent | Deterministic transformation is testable and debuggable; LLM only called for semantic parsing when regex can't handle it |
| Rendering engines | Three: Mermaid.js + Vega-Lite + Custom SVG (Matplotlib via existing render_chart.py) | Each engine plays to its strength; enables comparator pattern |
| Comparator | Draft phase only, lock winner for production | Mirrors existing draft/production lifecycle; explores in draft, executes cheaply in production |
| Enrichment | Four tiers (T0-T3), selected during negotiation | Full spectrum from pure programmatic to full AI render; different content suits different enrichment |
| v1 scope | 10 graphic types across all 5 categories | Proves every engine and enrichment tier |

---

## 2. Pipeline Integration

### Revised Step Order

```
 1. validate-brief
 2. brand-manager
 3. slide-stylist
 4. narrative-architect          <- states visual_intent per slide
 5. smartart-selector            <- NEW: negotiates graphic type + enrichment tier
 6. strategy-map                 <- gains 'smartart' strategy value
 7. smartart-extractor           <- NEW: transforms content to engine-ready data
 8. speaker-notes-writer
 9. imagegen-bridge              <- generates enrichment assets (T1/T2/T3)
10. smartart-renderer            <- NEW: renders graphics, runs comparator in draft
11. chart-renderer
12. deck-assembler               <- extended with buildSmartArtSlide()
13. deck-qa                      <- extended with 5 SmartArt checks
```

### Ordering Rationale

- **smartart-selector before strategy-map**: Selector output (graphic type + enrichment tier) informs strategy-map classification.
- **smartart-extractor after strategy-map**: By this point we know graphic type, enrichment tier, AND rendering strategy. Extractor generates engine-specific data with full context.
- **imagegen-bridge before smartart-renderer**: Enrichment assets (AI backgrounds, element icons) must be generated before the renderer composites them with the programmatic graphic.
- **smartart-renderer after imagegen-bridge**: Takes programmatic SVG + enrichment images from manifest and produces final composite.

### Impact on Existing Steps

| Step | Change |
|------|--------|
| `narrative-architect` | Gains optional `visual_intent` field in SlideOutline |
| `strategy-map` | Gains `smartart` as valid strategy value with `smartart_config` sub-fields |
| `imagegen-bridge` | No structural changes — enrichment images are additional ImageManifest entries with `smartart_ref` |
| `deck-assembler` | New `buildSmartArtSlide()` function |
| `deck-qa` | 5 new SmartArt-specific checks (SA-01 through SA-05) |
| `conductor.py` | 3 new steps in `DEFAULT_STEP_ORDER` and state machine |

---

## 3. SmartArt Selector Agent — Negotiation Pattern

### Agent Identity

| Field | Value |
|-------|-------|
| Name | `smartart-selector` |
| File | `.claude/agents/smartart-selector.md` |
| Model | Haiku (Sonnet escalation after 2 rejections) |
| Authority | Invoker (proposes, never decides — narrative-architect has final say) |
| Pattern | Multi-option proposal with negotiation loop |

### Negotiation Flow

```
Round 1:
  narrative-architect passes SlideOutline (with visual_intent) to selector
  -> selector analyses content semantics
  -> selector returns 2-3 ranked recommendations, each with:
      - graphic_type
      - enrichment_tier
      - rationale
      - confidence score (0-1)

Round 2:
  narrative-architect evaluates recommendations against:
      - narrative arc (does this graphic serve the story?)
      - audience context (from TalkBrief)
      - adjacent slides (avoid 3 flowcharts in a row)
  -> narrative-architect selects one, or rejects all with feedback

  If rejected:
      -> selector generates 2-3 new recommendations incorporating feedback
      -> narrative-architect selects (max 2 rejection rounds, then fallback to 'composed')
```

### Enrichment Tier Definitions

| Tier | Name | Description | Render Cost |
|------|------|-------------|-------------|
| T0 | `pure_programmatic` | Clean SVG, styled with design tokens only | Free |
| T1 | `ai_background` | Programmatic graphic composited over AI-generated atmospheric background | 1 image gen |
| T2 | `ai_elements` | Programmatic structure + AI-generated icons/illustrations per node | N image gens |
| T3 | `full_ai_render` | Entire graphic rendered as AI image from structured data prompt | 1 image gen |

### Selection Heuristics

- Data-heavy slides (charts, matrices) -> T0 or T1 (text legibility critical)
- Conceptual slides (journey maps, mind maps) -> T2 or T3 (visual impact matters more)
- Slide position in arc (opening/closing -> higher enrichment, mid-deck detail -> lower)
- Budget state: if `degrade` or `typography_only`, force T0
- Adjacent slide strategies: avoid enrichment fatigue

### Agent Contract

```
Input:
  - SlideOutline (full deck — needs adjacency context)
  - StyleGuide (design tokens for feasibility assessment)
  - TalkBrief (audience, tone)
  - BudgetState (current spend)

Output: SmartArtRecommendations
  - slide_number
  - recommendations: [
      {
        graphic_type: enum (flowchart | decision_tree | bar_chart | line_chart |
                           radar_chart | swot | feature_matrix | venn |
                           timeline | pipeline_funnel | gantt | none)
        enrichment_tier: enum (pure_programmatic | ai_background | ai_elements | full_ai_render)
        engine: enum (mermaid | vega_lite | matplotlib | custom_svg)
        rationale: string
        confidence: number (0-1)
        data_hint: string
      }
    ]
  - narrative_feedback: string (if retry after rejection)
```

---

## 4. Data Extraction — SmartArt Extractor

A Python module (`src/smartart_extractor.py`) that transforms approved slide content into engine-specific structured data. Deterministic transformation with LLM fallback only for semantic parsing that regex cannot handle.

### Architecture

```
smartart_extractor.py
  |-- extract(slide_outline, smartart_selection) -> SmartArtSpec
  |-- extract_graph_data(content, graphic_type) -> nodes + edges
  |-- extract_tabular_data(content, graphic_type) -> rows + columns
  |-- extract_series_data(content, graphic_type) -> labels + values
  |-- extract_spatial_data(content, graphic_type) -> regions + items
  +-- validate_spec(spec, engine) -> bool + errors
```

### Data Structures Per Engine

**Mermaid engine** (flowchart, decision_tree, gantt):
```json
{
  "engine": "mermaid",
  "syntax": "graph TD\n  A[Research] --> B[Design]\n  B --> C[Build]\n  C --> D[Launch]",
  "diagram_type": "flowchart",
  "node_count": 4,
  "overflow_policy": "paginate"
}
```

**Vega-Lite engine** (bar_chart, line_chart, radar_chart):
```json
{
  "engine": "vega_lite",
  "spec": {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "mark": "bar",
    "encoding": {
      "x": {"field": "quarter", "type": "ordinal"},
      "y": {"field": "revenue", "type": "quantitative"}
    },
    "data": {"values": [{"quarter": "Q1", "revenue": 120}]}
  },
  "chart_type": "bar_chart"
}
```

**Matplotlib engine** (bar_chart, line_chart — comparator candidate):
```json
{
  "engine": "matplotlib",
  "chart_type": "bar",
  "data": {"labels": ["Q1", "Q2"], "values": [120, 150]},
  "series_count": 1
}
```

**Custom SVG engine** (swot, feature_matrix, venn, timeline, pipeline_funnel):
```json
{
  "engine": "custom_svg",
  "graphic_type": "swot",
  "data": {
    "quadrants": [
      {"label": "Strengths", "position": "top_left", "items": ["Brand", "Team"]},
      {"label": "Weaknesses", "position": "top_right", "items": ["Scale", "Funding"]},
      {"label": "Opportunities", "position": "bottom_left", "items": ["AI", "Asia"]},
      {"label": "Threats", "position": "bottom_right", "items": ["Regulation"]}
    ]
  },
  "constraint_hints": {"max_items_per_quadrant": 5}
}
```

### Overflow Handling

| Policy | Behaviour | Applied When |
|--------|-----------|--------------|
| `truncate` | Keep first N items, add "... and X more" | Matrices, lists |
| `paginate` | Split across multiple graphics on the same slide | Flowcharts with >12 nodes |
| `summarise` | Call LLM to condense items | Any type, when truncation loses meaning |
| `reject` | Flag back to selector to choose a different type | When data fundamentally doesn't fit |

### SmartArtSpec Schema

New schema: `src/schemas/smartart_spec.schema.json`

```json
{
  "slide_number": 5,
  "graphic_type": "flowchart",
  "engine": "mermaid",
  "enrichment_tier": "ai_background",
  "data": {},
  "overflow_applied": "none",
  "style_tokens": {
    "primary_color": "#1a73e8",
    "font_family": "Inter",
    "node_shape": "rounded_rect"
  },
  "validation_status": "valid",
  "comparator_engines": ["mermaid", "custom_svg"]
}
```

The `comparator_engines` field is populated when multiple engines can render this graphic type. During draft, the renderer produces output from each.

---

## 5. SmartArt Renderer & Comparator

A Python module (`src/smartart_renderer.py`) that renders SmartArtSpecs via the appropriate engine(s), runs the comparator in draft phase, and composites enrichment assets.

### Architecture

```
smartart_renderer.py
  |-- render(smartart_spec, style_guide, phase) -> SmartArtManifest entry
  |-- render_mermaid(spec) -> SVG string
  |-- render_vega_lite(spec) -> SVG string
  |-- render_matplotlib(spec) -> PNG path (reuses render_chart.py)
  |-- render_custom_svg(spec) -> SVG string
  |-- run_comparator(candidates, spec, style_guide) -> winner
  |-- composite_enrichment(svg, enrichment_images, tier) -> final PNG
  +-- rasterise(svg, dimensions) -> PNG path
```

### Engine Details

**Mermaid rendering:**
- Uses `@mermaid-js/mermaid-cli` (mmdc) — CLI tool, no headless browser in our process
- Custom theme injection via Mermaid `%%{init: {'theme': 'base', 'themeVariables': {...}}}%%` directive
- Design tokens from StyleGuide mapped to Mermaid theme variables
- Output: SVG file

**Vega-Lite rendering:**
- Uses `vl2svg` from `vega-lite` + `vega-cli` npm packages (CLI, no browser needed)
- StyleGuide tokens mapped to Vega config (range colours, font, background)
- Output: SVG file

**Matplotlib rendering:**
- Reuses existing `render_chart.py` — no new dependency
- Already has StyleGuide integration
- Output: PNG file (rasterised at 300 DPI)

**Custom SVG rendering:**
- New Python package: `src/smartart_svg/`
- Constraint-based layout engine
- Design token injection for colours, fonts, border radii, shadows
- Output: SVG string

### Comparator

Runs only during draft phase when `comparator_engines` has more than one entry.

**Draft phase:**
1. Render via engine A -> SVG/PNG
2. Render via engine B -> SVG/PNG
3. Rasterise both to same dimensions
4. Dispatch image-reviewer agent on each with `review_context: "smartart_comparator"`
5. Reviewer returns weighted scores per candidate
6. Select winner by highest `weighted_score`
7. Record winning engine in SmartArtManifest
8. Log comparison results in render-log.json

**Production phase:**
1. Read winning engine from SmartArtManifest
2. Render via winner only
3. Apply production-quality rasterisation (high DPI)

**Comparator scoring weights:**

| Criterion | Weight | Assessment |
|-----------|--------|------------|
| Data legibility | 0.35 | Every label and value readable at presentation scale |
| Layout clarity | 0.25 | Visual hierarchy obvious, relationships clear |
| Aesthetic quality | 0.20 | Professional appearance, balanced whitespace |
| Style compliance | 0.20 | Colours, fonts match StyleGuide tokens |

### Enrichment Compositing

**T0 — pure_programmatic:**
```
SVG -> rasterise to PNG -> done
```

**T1 — ai_background:**
```
imagegen-bridge generates atmospheric background (in ImageManifest with smartart_ref)
SVG -> rasterise to transparent PNG
Composite: background PNG + SmartArt PNG (centred, with padding)
-> final PNG
```

**T2 — ai_elements:**
```
imagegen-bridge generates N element icons (one per node, in ImageManifest with smartart_ref)
SVG rendered with placeholder regions for icons
Composite: SVG + element icons positioned at node centres
-> final PNG
```

**T3 — full_ai_render:**
```
SmartArtSpec data -> structured prompt describing the graphic
imagegen-bridge generates entire graphic as AI image
image-reviewer validates data accuracy (data fidelity criterion)
-> PNG (no programmatic SVG involved)
If data fidelity fails after 3 attempts: auto-downgrade to T1 and log in manifest
```

**Compositing tool:** Sharp (existing dependency). Layered compositing via `sharp.composite()`.

### SmartArtManifest Schema

New schema: `src/schemas/smartart_manifest.schema.json`

```json
{
  "graphics": [
    {
      "smartart_id": "sa-slide-5-flowchart",
      "slide_number": 5,
      "graphic_type": "flowchart",
      "engine_used": "mermaid",
      "enrichment_tier": "ai_background",
      "file_path": "./tmp/deck/smartart/slide-5-flowchart.png",
      "svg_source_path": "./tmp/deck/smartart/slide-5-flowchart.svg",
      "status": "rendered | compared | enriched | failed",
      "dimensions": {"width": 1920, "height": 1080},
      "node_count": 4,
      "alt_text": "Flowchart showing 4-step process: Research -> Design -> Build -> Launch",
      "content_hash": "sha256_hex",
      "comparator_results": {
        "candidates": [
          {"engine": "mermaid", "score": 0.87, "file_path": "..."},
          {"engine": "custom_svg", "score": 0.72, "file_path": "..."}
        ],
        "winner": "mermaid",
        "phase": "draft"
      },
      "enrichment_refs": ["img-slide-5-bg-001"],
      "review_summary": "pass -- layout clear, all labels legible"
    }
  ]
}
```

---

## 6. Custom SVG Engine

A Python package (`src/smartart_svg/`) that generates professional SVG graphics for 5 graphic types using constraint-based layout.

### Package Structure

```
src/smartart_svg/
  |-- __init__.py              -- public API: render_custom_svg(spec, style) -> SVG string
  |-- engine.py                -- constraint solver, container management
  |-- primitives.py            -- SVG building blocks (rect, circle, text, arrow, group)
  |-- tokens.py                -- StyleGuide -> SVG style attribute mapper + contrast resolver
  |-- layouts/
  |   |-- __init__.py
  |   |-- swot.py              -- 2x2 quadrant layout
  |   |-- feature_matrix.py    -- NxM grid with icons/checkmarks
  |   |-- venn.py              -- 2-3 circle overlap with label positioning
  |   |-- timeline.py          -- horizontal/vertical sequential layout
  |   +-- pipeline_funnel.py   -- tapered stage layout with value labels
  +-- tests/
      +-- test_smartart_svg.py
```

### Constraint Engine (`engine.py`)

Proportional box model (CSS flexbox-inspired, much simpler):

```python
class Container:
    """A rectangular region that can be subdivided."""
    width: float
    height: float
    padding: Spacing

    def split_grid(self, rows, cols, gap) -> list[Container]
    def split_horizontal(self, ratios, gap) -> list[Container]
    def split_vertical(self, ratios, gap) -> list[Container]
    def fit_text(self, text, font_size, max_lines) -> FittedText
    def center_point(self) -> (x, y)
```

Every layout function receives a root Container matching slide dimensions and subdivides it. The container handles:
- **Auto-sizing text**: `fit_text()` reduces font size until text fits, minimum readable threshold
- **Overflow**: Container reports overflow; extractor's policy kicks in
- **Aspect ratio**: Containers maintain proportional relationships regardless of slide dimensions

### Layout Specifications

**SWOT (`swot.py`):**
- Root container -> title region (top 10%) + grid region (bottom 90%)
- Grid: `split_grid(2, 2, gap=16)`
- Each quadrant: header + bullet list
- Quadrant colours from StyleGuide `chart_series[0..3]`

**Timeline (`timeline.py`):**
- Root container -> title region (top 12%) + timeline region (bottom 88%)
- Horizontal spine line at vertical centre
- Equal-ratio horizontal split for N stages
- Circle nodes on spine + labels above/below (alternating)
- Auto-scale node size based on N

**Feature Matrix (`feature_matrix.py`):**
- Header row (column labels) + body rows (one per feature)
- `split_grid(features+1, columns+1, gap=2)`
- Checkmark/cross/value icons in cells
- Alternating row background tint

**Venn (`venn.py`):**
- Title region (top 10%) + diagram region (bottom 90%)
- 2 circles: offset by overlap percentage, semi-transparent fill
- 3 circles: triangular arrangement
- Label positioning: exclusive items outside overlap, shared items in overlap zone

**Pipeline/Funnel (`pipeline_funnel.py`):**
- Title region (top 10%) + funnel region (bottom 90%)
- N trapezoid stages, widest at top, narrowest at bottom
- Width proportional to values (or equal if no values)
- Colour gradient from StyleGuide primary -> accent

### SVG Primitives (`primitives.py`)

```python
def svg_rect(x, y, w, h, rx, fill, stroke, class_name) -> str
def svg_circle(cx, cy, r, fill, opacity) -> str
def svg_text(x, y, text, font_family, font_size, fill, anchor) -> str
def svg_arrow(x1, y1, x2, y2, stroke, marker) -> str
def svg_group(children, transform, role, aria_label) -> str
def svg_document(width, height, children, title, desc) -> str
```

Every `svg_document` includes `<title>` and `<desc>` tags for WCAG 2.2 compliance. Groups use `role="img"` and `aria-label` for screen reader support.

### Style Token Mapping (`tokens.py`)

| StyleGuide Field | SVG Usage |
|-----------------|-----------|
| `palette.primary` | Node fill, header backgrounds |
| `palette.accent` | Highlights, active states |
| `palette.chart_series[0..n]` | Multi-category colouring (SWOT quadrants, Venn circles) |
| `palette.background` | Container background |
| `palette.text` | Label text colour |
| `typography.heading_font` | Graphic title |
| `typography.body_font` | Node labels, values |
| `image_style.border_radius` | Node corner rounding |

### Contrast-Safe Colour Resolver

```python
def resolve_text_colour(background_colour, preferred_colour, style_guide) -> str:
    """Returns preferred_colour if WCAG contrast ratio passes,
    otherwise falls back to palette.text or white/black."""
```

Called by every layout function when placing text over coloured regions. Prevents contrast failures at generation time rather than catching them at QA.

---

## 7. Schema Changes

### New Schemas (4)

| Schema | File | Purpose |
|--------|------|---------|
| SmartArtRecommendations | `src/schemas/smartart_recommendations.schema.json` | Selector agent output |
| SmartArtSpec | `src/schemas/smartart_spec.schema.json` | Extractor output |
| SmartArtManifest | `src/schemas/smartart_manifest.schema.json` | Renderer output |
| SmartArtComparator | `src/schemas/smartart_comparator.schema.json` | Comparator results (embedded in manifest) |

### Modified Schemas (4)

**`slide_outline.schema.json`** — new optional field:
```json
"visual_intent": {
  "type": "string",
  "description": "Natural language description of the visual the speaker wants"
}
```

**`strategy_map.schema.json`** — new strategy enum value + sub-fields:
```json
"strategy": {
  "enum": ["full_render", "background", "backdrop", "pragmatic_composition", "composed", "smartart"]
},
"smartart_config": {
  "graphic_type": "enum of 10 v1 types + none",
  "enrichment_tier": "enum of T0-T3",
  "engine": "enum of mermaid | vega_lite | matplotlib | custom_svg",
  "comparator_engines": ["array of eligible engines"]
}
```

**`image_manifest.schema.json`** — new optional field:
```json
"smartart_ref": {
  "type": "string",
  "description": "Links enrichment image to a SmartArt graphic ID"
}
```

**`qa_report.schema.json`** — new check category for SA-01 through SA-05.

### Unchanged Schemas (4)

`talk_brief`, `brand_profile`, `style_guide`, `speaker_notes` — no modification needed.

### DeckContext Files

```
tmp/deck/
  |-- talk-brief.json               (existing)
  |-- brand-profile.json            (existing)
  |-- style-guide.json              (existing)
  |-- slide-outline.json            (existing, gains visual_intent)
  |-- smartart-recommendations.json  <- NEW
  |-- strategy-map.json             (existing, gains smartart strategy)
  |-- smartart-spec.json            <- NEW
  |-- speaker-notes.json            (existing)
  |-- image-manifest.json           (existing, gains smartart_ref)
  |-- smartart-manifest.json        <- NEW
  |-- chart-manifest.json           (existing)
  |-- render-log.json               (existing, gains SmartArt entries)
  |-- qa-report.json                (existing, gains SmartArt checks)
  +-- pipeline-state.json           (existing, gains new step statuses)
```

---

## 8. Assembler Integration

### `buildSmartArtSlide()`

New function in `src/assembler/build_deck.js`, dispatched when `strategy === 'smartart'`:

```
1. Read SmartArtManifest entry for this slide
2. Based on enrichment_tier:

   T0 (pure_programmatic):
     -> Place SmartArt PNG as single image, centred with padding
     -> Add slide title as text box above

   T1 (ai_background):
     -> Place enrichment background image as full-bleed
     -> Place SmartArt PNG centred with semi-transparent backing rectangle
     -> Add slide title as text box

   T2 (ai_elements):
     -> Place SmartArt PNG (already composited with element icons by renderer)
     -> Same layout as T0

   T3 (full_ai_render):
     -> Place AI-generated image as full-bleed (same as full_render strategy)
     -> No programmatic graphic

3. Add footer logo via addFooterLogo()
4. Add speaker notes from SpeakerNotes contract
```

### Layout Zones

| Tier | Graphic Region | Title Region | Notes |
|------|---------------|--------------|-------|
| T0 | 85% of slide, centred | Top 12% | Clean, professional |
| T1 | 75% of slide, centred with backing | Top 12% | Backing rect at 85% opacity |
| T2 | 85% of slide, centred | Top 12% | Icons already composited |
| T3 | 100% full-bleed | Overlay if short enough | Same as full_render |

---

## 9. QA Checks (5 new, 35 total)

Added to `src/qa/checks/smartart_checks.py`:

**SA-01: Data Integrity**
- Parse original slide outline body_points
- Parse SmartArtSpec data (nodes, labels, values)
- Verify every meaningful data point from outline appears in spec
- FAIL if data points missing without `overflow_applied` flag

**SA-02: Label Legibility**
- Size checks:
  - Parse all `<text>` elements in SVG source
  - Check font-size >= 14px minimum at 1920x1080
  - Check text doesn't overflow container
  - WARN if font-size < 16px, FAIL if < 12px
- Contrast checks:
  - For each `<text>` element, resolve fill colour
  - Resolve background colour behind it (parent `<rect>` fill or container background)
  - Calculate WCAG 2.2 contrast ratio using relative luminance formula
  - FAIL if contrast ratio < 4.5:1 for text < 24px (normal text)
  - FAIL if contrast ratio < 3:1 for text >= 24px (large text)
  - For enrichment tiers T1/T2 with AI background: WARN "contrast unverifiable against AI background -- manual review recommended"

**SA-03: Enrichment Alignment**
- Verify enrichment image exists in ImageManifest with matching `smartart_ref`
- Verify dimensions match SmartArt dimensions
- Verify enrichment image status is not `failed` or `placeholder`
- FAIL if enrichment asset missing or mismatched

**SA-04: Overflow Handling**
- If `truncate`: verify indicator text present ("... and N more")
- If `paginate`: verify multiple graphic entries for same slide
- If `summarise`: verify condensed items convey original meaning
- FAIL if overflow applied but no visible indicator

**SA-05: Accessibility**
- Verify `<title>` tag present and non-empty in SVG
- Verify `<desc>` tag present and non-empty in SVG
- Verify `alt_text` populated in SmartArtManifest
- Verify `<g>` elements with `role="img"` have `aria-label`
- FAIL if any accessibility element missing

---

## 10. Image Reviewer Adaptations

The existing image-reviewer agent is reused for three SmartArt contexts via the `review_context` field.

### Context 1: Comparator Judging (`smartart_comparator`)

| Criterion | Weight | Assessment |
|-----------|--------|------------|
| Data legibility | 0.35 | Every label and value readable at presentation scale |
| Layout clarity | 0.25 | Visual hierarchy obvious, relationships clear |
| Aesthetic quality | 0.20 | Professional appearance, balanced whitespace |
| Style compliance | 0.20 | Colours, fonts match StyleGuide tokens |

### Context 2: Enrichment Review (`smartart_enrichment`)

Uses standard 5 criteria with SmartArt-specific guidance:

| Standard Criterion | SmartArt Adaptation |
|--------------------|-------------------|
| Artifacts | Same — reject garbles, impossible geometry |
| Subject match | T1: atmospheric/abstract, must NOT contain text or diagram-like structures. T2: icons must depict their concept |
| Palette compliance | Same — match brand palette |
| Composition | T1: large uniform centre region for SmartArt overlay. T2: centred icon, clean edges |
| Strategy fit | Will programmatic SmartArt layer remain legible when composited? |

### Context 3: T3 Full AI Render (`smartart_full_render`)

Additional criterion: **Data fidelity** — does the AI-rendered image accurately represent the structured data? Correct node count, correct labels, correct relationships.

**T3 downgrade policy:** If data fidelity fails after 3 attempts, auto-downgrade to T1 (programmatic graphic + AI background) and log in SmartArtManifest.

### Dispatch Payload

```json
{
  "review_context": "smartart_comparator | smartart_enrichment | smartart_full_render",
  "smartart_type": "flowchart",
  "enrichment_tier": "ai_background",
  "data_summary": "4-node flowchart: Research -> Design -> Build -> Launch"
}
```

---

## 11. BSA Architecture Impact

### New AI Persona

| Field | Value |
|-------|-------|
| Name | SmartArt Selector |
| ID | `persona-smartart-selector` |
| Role | Recommends graphic type + enrichment tier |
| Authority | Invoker |
| Model | Haiku (Sonnet escalation) |
| Total personas | 5 -> 6 |

### L1 Service Placement

| New Service | L1 Domain | Rationale |
|-------------|-----------|-----------|
| `SVC-SMARTART-SELECT` | Content Services | Content decision — what visual represents this content? |
| `SVC-SMARTART-EXTRACT` | Content Services | Data transformation is content work |
| `SVC-SMARTART-RENDER` | Image Services | Rendering is image work |

### New Interactions

```
narrative-architect -> smartart-selector (visual_intent + outline)
smartart-selector -> narrative-architect (recommendations)
narrative-architect -> smartart-selector (approval/rejection + feedback)
smartart-extractor -> smartart-renderer (SmartArtSpec)
smartart-renderer -> imagegen-bridge (enrichment requests)
imagegen-bridge -> smartart-renderer (enrichment images)
smartart-renderer -> image-reviewer (comparator candidates + enrichment review)
smartart-renderer -> deck-assembler (SmartArtManifest)
smartart-renderer -> deck-qa (SmartArt SVG sources)
```

### BSA Version: v1.3.0 -> v1.4.0

---

## 12. v1 Graphic Type Scope

10 types across all 5 categories, proving every engine and enrichment tier:

| Type | Category | Engine | Comparator Pair |
|------|----------|--------|-----------------|
| Flowchart | Process | Mermaid | custom_svg |
| Decision Tree | Process | Mermaid | -- |
| Bar/Line Chart | Data Viz | Vega-Lite | matplotlib |
| Radar Chart | Comparison | Vega-Lite | -- |
| SWOT Analysis | Matrix | Custom SVG | -- |
| Feature Matrix | Comparison | Custom SVG | -- |
| Venn Diagram | Relationship | Custom SVG | -- |
| Timeline | Flow | Custom SVG | -- |
| Pipeline/Funnel | Flow | Custom SVG | -- |
| Gantt Chart | Data Viz | Mermaid | -- |

---

## 13. Full Inventory

### New Components

| Category | Count | Items |
|----------|-------|-------|
| Agents | 1 | smartart-selector |
| Skills | 3 | smartart-selector, smartart-extractor, smartart-renderer |
| Python modules | 4 | smartart_extractor.py, smartart_renderer.py, smartart_svg/ (package), qa/checks/smartart_checks.py |
| Schemas | 4 | smartart_recommendations, smartart_spec, smartart_manifest, smartart_comparator |
| Node dependencies | 2 | @mermaid-js/mermaid-cli, vega-lite + vega-cli |

### Modified Components

| Category | Count | Items |
|----------|-------|-------|
| Python modules | 4 | deckcontext.py, conductor.py, slide_prompt_composer.py, image_router.py |
| JS modules | 1 | assembler/build_deck.js |
| Schemas | 4 | slide_outline, strategy_map, image_manifest, qa_report |

### Reused (No Modification)

| Component | Reused For |
|-----------|-----------|
| prompt-engineer agent | Enrichment image prompts (T1/T2/T3) |
| image-reviewer agent | Comparator scoring + enrichment review |
| render_chart.py | Matplotlib engine in comparator |
| budget_tracker.py | SmartArt enrichment cost tracking |
| provider_discovery.py | Enrichment image provider availability |
| process_image.py | SVG rasterisation via Sharp |
| cache_manager.py | Caching rendered SmartArt by content_hash |

---

## 14. Node.js Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| `@mermaid-js/mermaid-cli` | Mermaid syntax -> SVG (CLI) | `npm install @mermaid-js/mermaid-cli` |
| `vega-lite` | Vega-Lite spec -> Vega spec | `npm install vega-lite` |
| `vega-cli` | Vega spec -> SVG (CLI via `vg2svg`) | `npm install vega-cli` |
