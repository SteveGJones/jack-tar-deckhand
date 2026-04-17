# Template-Driven Layout Support — Design Spec

**Issue:** #45
**Date:** 2026-04-17
**Status:** Approved

## Summary

Allow speakers to provide a corporate .pptx template with predefined slide layouts. The pipeline extracts layout geometry, maps content to template placeholders, and produces a deck that inherits the template's slide masters — so the output looks like it belongs to the organisation.

## Scope

**v1 (this spec):** Use template slide masters, respect placeholder zones. Content placed into typed placeholders (TITLE, BODY, CONTENT, PICTURE). Decorative shapes inherited from the layout automatically but not explicitly managed.

**v2 (future):** Full visual fidelity — preserve and manage decorative shapes, allow per-layout customisation of accent elements.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Assembly engine | New python-pptx path (`build_deck_template.py`) | PptxGenJS can't open templates or use existing layouts. Clean parallel path, existing JS untouched. |
| Layout mapping | Auto-match by naming convention, Speaker confirms | Convention handles 80% of cases; Speaker catches edge cases and picks among variants. |
| Rendering strategies | Template mode constrains to `composed` + SmartArt | Corporate templates provide visual identity; AI backgrounds would clash. `full_render` allowed only for full-bleed PICTURE placeholders. |
| Layout fidelity | Placeholder zones respected, decorative shapes inherited | v1 inherits decorative shapes from the layout master automatically but doesn't explicitly manage them. |

## Architecture

### 1. Template Analysis Module

**New file: `src/template_analyser.py`**

Reads a .pptx template via python-pptx and produces a `TemplateProfile` JSON structure.

**Extraction per layout:**
- Layout name, index, parent slide master index
- Content placeholders with type classification: `title`, `subtitle`, `body`, `content`, `picture`, `chart`, `table`, `footer`, `slide_number`, `date`, `chapter_box`
- Placeholder geometry: `{x, y, w, h}` in inches (converted from EMU)
- Count of decorative (non-placeholder) shapes (not extracted in v1)
- Slide dimensions with non-standard aspect ratio warning

**Layout-to-slide-type auto-mapping convention table:**

| Layout name pattern | Maps to slide type |
|---|---|
| `Title Slide*`, `Title Only` | `title` |
| `Divider*`, `Section*` | `section_divider` |
| `Content 1*` (single content PH) | `content` |
| `Content 2*`–`Content 8*` (dual content PH) | `two_column` |
| `Content*Photo*`, `Content*` + PICTURE PH | `content_with_image` |
| `Comparison*` | `comparison` |
| `Conclusion*`, `End*` | `closing` |
| `Agenda*` | `agenda` |
| `Text*` | `quote` |
| `Blank` | `blank` |

When multiple layouts match the same slide type, the simpler one (fewer placeholders) becomes the default. Variants remain available for explicit selection.

**Output:** `template-profile.json` saved to the deck directory, schema-validated.

**Key functions:**
- `analyse_template(template_path) -> dict` — full extraction
- `auto_map_layouts(layouts) -> dict` — convention-based mapping
- `classify_placeholder(ph_type, ph_name) -> str` — maps OOXML placeholder types to our type vocabulary

### 2. Layout Mapping & Speaker Confirmation

Runs as a pipeline step between template analysis and brand-manager.

**Flow:**
1. Template analyser produces `template-profile.json` with auto-mapped layout assignments
2. Pipeline presents the mapping table to the Speaker, showing layout name, placeholder summary, and any unmapped slide types
3. Unmapped types fall back to the content layout with the largest single content placeholder
4. Speaker can override any mapping by specifying a different layout name
5. Final mapping saved with `speaker_approved: true` flag

**Reuse:** Template profiles are cached at `./brands/{brand-id}/template-profile.json` alongside the brand profile. Cache is keyed by `template_hash` (SHA-256 of the source .pptx). Same template file in a future deck loads the confirmed mapping without re-prompting. If the template file changes (different hash), re-analysis is triggered.

### 3. Template Assembly Engine

**New file: `src/assembler/build_deck_template.py`**

Python-pptx assembly path activated when `template-profile.json` exists.

**Core function: `build_deck(deck_dir, template_path, template_profile) -> str`**

Steps:
1. Open template with `Presentation(template_path)` — preserves all slide masters, layouts, themes, and embedded assets
2. Remove ALL existing slides from the template (corporate templates typically ship with example slides — we strip them all and add fresh slides from the outline)
3. For each slide in the outline, look up the mapped layout from `template_profile.layout_mapping`
4. Add a new slide via `prs.slides.add_slide(layout)`
5. Populate placeholders by type

**Content placement rules:**

| Placeholder type | Content source |
|---|---|
| TITLE | `slide.headline` from outline |
| BODY / SUBTITLE | `slide.body_points` joined, or subtitle text |
| CONTENT (OBJECT) | Body points as bulleted text, or left empty for SmartArt injection |
| PICTURE | Image from ImageManifest — `placeholder.insert_picture(image_path)` handles aspect-ratio-aware placement |
| CHART | Chart images placed as pictures in v1 |
| DATE / FOOTER / SLIDE_NUMBER | Template defaults, or overridden from StyleGuide if set |

**Text formatting:** Does not override template typography. Sets text content only — lets the template's theme control font family, size, and colour.

**Image handling:** `placeholder.insert_picture(image_path)` — python-pptx handles aspect-ratio-aware centring within placeholder bounds automatically.

**SmartArt integration:** Emits named placeholder rectangles (`pptx_native_placeholder_{n}`) inside the CONTENT placeholder's bounds, same convention as the JS assembler. The existing `assembler_patch.py` injection step runs after assembly, unchanged.

**Speaker notes:** Populates `slide.notes_slide.notes_text_frame` from `speaker-notes.json` for each slide.

**Output:** `{deck_dir}/output/presentation.pptx`

### 4. Pipeline Integration & Routing

**Assembler routing (deck-assembler skill):**
- `template-profile.json` exists in deck directory → `build_deck_template.py`
- Otherwise → `build_deck.js` (unchanged)
- Single decision point, no changes to the JS assembler

**Strategy map constraints:**
When a template profile exists, `src/slide_prompt_composer.py` applies template mode:
- Default all slides to `composed` strategy
- Exception: slides mapped to a layout with a full-bleed PICTURE placeholder (>90% of slide area) are eligible for `full_render`
- `background`, `backdrop`, `pragmatic_composition` strategies suppressed
- Controlled by `constrains_strategies: true` in the template profile

**Image generation impact:**
- Fewer AI-generated images (no atmospheric backgrounds)
- Images only generated for slides with PICTURE placeholders or SmartArt enrichment
- Template decks are significantly cheaper to produce
- Draft/production render funnel still applies to generated images

**Conductor changes:**
- New pipeline step `template-analysis` inserted before `brand-manager` in `DEFAULT_STEP_ORDER`
- When TalkBrief has `branding.template_pptx_path`, conductor runs template analysis as the first content step
- Template profile feeds into brand-manager (can extract palette from template theme) and slide-stylist (layout constraints)

**QA checks:**
- Existing checks (text overflow, image resolution, accessibility) still apply
- Skip checks that assume PptxGenJS output structure
- New check: verify every slide references a valid template layout (no orphaned slides)

### 5. Template Profile Schema

**New file: `src/schemas/template_profile.schema.json`**

```json
{
  "template_path": "string — path to source .pptx",
  "template_hash": "string — SHA-256 of the template file for cache invalidation",
  "slide_width_inches": "number",
  "slide_height_inches": "number",
  "master_index": "integer — which slide master to use (default 0)",
  "layouts": [
    {
      "name": "string — layout name from template",
      "index": "integer — layout index within the master",
      "placeholder_count": "integer",
      "placeholders": [
        {
          "idx": "integer — OOXML placeholder index",
          "type": "enum — title|subtitle|body|content|picture|chart|table|footer|slide_number|date|chapter_box|other",
          "name": "string — shape name from template",
          "x": "number — inches",
          "y": "number — inches",
          "w": "number — inches",
          "h": "number — inches"
        }
      ],
      "decorative_shape_count": "integer"
    }
  ],
  "layout_mapping": {
    "<slide_type>": {
      "layout_name": "string",
      "layout_index": "integer"
    }
  },
  "unmapped_fallback": {
    "layout_name": "string",
    "layout_index": "integer"
  },
  "constrains_strategies": "boolean — true when template is active",
  "speaker_approved": "boolean"
}
```

### 6. File Layout

**New files:**

| File | Purpose |
|---|---|
| `src/template_analyser.py` | Extract layouts and placeholders from .pptx template |
| `src/assembler/build_deck_template.py` | python-pptx assembly engine for template mode |
| `src/schemas/template_profile.schema.json` | Validates template-profile.json |
| `tests/test_template_analyser.py` | Template analysis tests (~20) |
| `tests/test_build_deck_template.py` | Template assembly tests (~25) |
| `tests/test_template_integration.py` | Pipeline routing and e2e tests (~7) |
| `tests/fixtures/templates/metamirror-template.pptx` | Test fixture |
| `tools/build_test_template.py` | Generates the Metamirror test template via python-pptx |

**Modified files:**

| File | Change |
|---|---|
| `src/slide_prompt_composer.py` | Add `constrains_strategies` check when template profile present |
| `src/deckcontext.py` | Add `template-analysis` to `DEFAULT_STEP_ORDER` |
| `plugins/jack-tar-deckhand/skills/deck-assembler/SKILL.md` | Add routing logic: template profile present → python-pptx path |
| `plugins/jack-tar-deckhand/agents/deck-conductor.md` | Add template-analysis step before brand-manager |

Plugin copies synced in same commits as source changes.

### 7. Test Strategy

**Test template:** `tests/fixtures/templates/metamirror-template.pptx` built via `tools/build_test_template.py` using python-pptx. Metamirror-branded (not Capgemini). Contains 1 slide master, 8 layouts (title with PICTURE, content, two-column, content-with-image, section divider, blank, comparison, closing), a few example slides to verify stripping.

**Test coverage:**

| Module | Tests | Coverage |
|---|---|---|
| `template_analyser.py` | ~20 | Layout extraction, placeholder classification, auto-mapping, non-standard dimensions, empty template |
| `build_deck_template.py` | ~25 | Title population, body points, image insertion into PICTURE PH, SmartArt placeholder emission, speaker notes, example slide stripping, missing image fallback |
| Layout mapping | ~10 | Convention matching, fallback for unmapped types, speaker override persistence, cache reuse |
| Strategy constraints | ~8 | Template mode suppresses background/backdrop, full-bleed PICTURE exception, flag propagation |
| Pipeline integration | ~5 | Routing to correct assembler, template-analysis step ordering, QA on template output |
| End-to-end | ~2 | Full pipeline: template + outline + images → .pptx with correct layouts and content |

**Estimated total: ~70 new tests**

**Manual gate:** Visual correctness in PowerPoint verified manually (same pattern as SmartArt). Real corporate template testing with Capgemini file is manual, not automated.

### 8. What This Does NOT Cover (v2)

- Decorative shape management (preserving/modifying accent bars, gradients, brand marks)
- Per-layout colour theme overrides
- Multi-master selection (choosing between Master 0/1/2 per slide)
- Template diffing (detecting changes between template versions)
- Chart placeholder population with live chart data (v1 uses chart images)
