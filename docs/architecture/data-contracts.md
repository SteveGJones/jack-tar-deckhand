# Data Contract Summary -- Jack-Tar Deckhand

> Generated from canonical model: `jack-tar-deckhand.json` v1.0.0
> Date: 2026-03-28
> Full JSON schemas: see [Research Paper #12 -- DeckContext Serialisation & Pipeline State Management](../../research/12-deckcontext-state-management.md)

This document summarises all data contracts that flow between services in the Jack-Tar Deckhand architecture. Each contract is a JSON file persisted in the `./tmp/deck/` directory, forming the DeckContext shared state.

---

## Contract Overview

| Contract | File | Producer | Consumer(s) | Frozen After Creation |
|---|---|---|---|---|
| TalkBrief | `talk-brief.json` | Speaker (via Deck Conductor) | All services | Yes |
| PipelineState | `pipeline-state.json` | Deck Conductor | Deck Conductor | No (continuously updated) |
| StyleGuide | `style-guide.json` | slide-stylist | imagegen-bridge, chart-renderer, deck-assembler, Image Generation Expert, Presentation Reviewer | Yes |
| SlideOutline | `outline.json` | narrative-architect | speaker-notes-writer, imagegen-bridge, deck-assembler, Image Generation Expert, Presentation Reviewer | Yes (unless correction cycle) |
| SpeakerNotes | `speaker-notes.json` | speaker-notes-writer | deck-assembler, Presentation Reviewer | Yes |
| ImageManifest | `image-manifest.json` | imagegen-bridge | deck-assembler | Yes |
| ChartManifest | `chart-manifest.json` | chart-renderer | deck-assembler | Yes |
| QAReport | `qa-report.json` | deck-qa | Deck Conductor, Presentation Reviewer | Yes (per QA pass) |
| AvailableProviders | (in-memory / conversation) | imagegen-bridge | Deck Conductor, generation skills | Yes (per pipeline run) |
| DeckContext | `./tmp/deck/` (directory) | Deck Conductor | All services | No (directory of all above) |

---

## 1. TalkBrief

**File:** `./tmp/deck/talk-brief.json`
**Producer:** Speaker (input validated and frozen by Deck Conductor at pipeline start)
**Consumers:** All services (directly or indirectly)

### Description

The user's input describing what presentation to create. This is the immutable seed of the pipeline -- no service modifies it after the Deck Conductor validates and persists it.

### Key Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `topic` | string | Yes | Subject of the talk (min 3 chars) |
| `audience` | string | Yes | Who will be watching |
| `duration_minutes` | integer | Yes | Session length (5, 10, 15, 20, 30, 45, 60, 90) |
| `tone` | string | No | Presentation tone (professional, conversational, technical, inspirational, provocative, storytelling) |
| `key_takeaways` | string[] | No | 1-5 things the audience should remember |
| `branding` | object | No | Corporate branding: company_name, logo_path, primary_color, secondary_color, font_preference |
| `preferences` | object | No | Style preferences: style, slide_count_hint, image_backend, resolution, include_speaker_notes, include_charts |
| `data_sources` | object[] | No | Data for chart slides: label, type (inline_json, csv_path, description), content |

### Lifecycle

1. Speaker provides talk description (conversational or structured)
2. Deck Conductor parses and validates against schema
3. Written to `./tmp/deck/talk-brief.json`
4. SHA-256 hash stored in PipelineState for change detection
5. Never modified after this point

---

## 2. PipelineState

**File:** `./tmp/deck/pipeline-state.json`
**Producer:** Deck Conductor
**Consumers:** Deck Conductor (self -- for resumption and progress tracking)

### Description

The Conductor's control file. Tracks which pipeline steps have executed, their status, timing, and output file checksums. Enables checkpoint/resume if the pipeline is interrupted.

### Key Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `pipeline_id` | string | Yes | Unique identifier (ISO timestamp or UUID) |
| `created_at` | datetime | Yes | Pipeline start time |
| `updated_at` | datetime | No | Last modification time |
| `talk_brief_hash` | string | No | SHA-256 of talk-brief.json (change detection) |
| `status` | enum | No | Overall: running, completed, failed, paused |
| `current_step` | string | No | Step currently executing or that failed |
| `steps` | object | Yes | Per-step status (pending, running, completed, failed, skipped) with timestamps, output_file path, error message, retry_count, and checksum |
| `step_order` | string[] | No | Ordered execution sequence |

### Default Step Order

1. `validate-brief`
2. `slide-stylist`
3. `narrative-architect`
4. `speaker-notes-writer`
5. `imagegen-bridge`
6. `chart-renderer`
7. `deck-assembler`
8. `deck-qa`

### Lifecycle

Continuously updated by the Deck Conductor as each step starts, completes, or fails. This is the only contract that is not frozen after creation.

---

## 3. StyleGuide

**File:** `./tmp/deck/style-guide.json`
**Producer:** `slide-stylist` (design-style-derivation service)
**Consumers:** imagegen-bridge, chart-renderer, deck-assembler, Image Generation Expert, Presentation Reviewer

### Description

The complete visual design system for the deck. Defines palette, typography, layout rules, and image style tokens. All downstream services reference this to maintain visual consistency.

### Key Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `palette` | object | Yes | Colour palette: primary, secondary, accent, background, background_alt, text_primary, text_muted, text_on_dark, chart_series (all 6-char hex without #) |
| `typography` | object | Yes | Fonts: heading_font, body_font, mono_font, heading_sizes (title_slide, section_divider, slide_heading, subheading), body_size, caption_size, line_spacing |
| `layout` | object | No | Layout rules: slide_width_inches (10), slide_height_inches (5.625), margin_inches (0.5), templates (per slide type with text_zone, image_zone, background_treatment) |
| `image_style_tokens` | object | No | Prompt appendages for consistent image style: mood, color_direction, style_modifiers[] |

### Lifecycle

1. Produced by slide-stylist from TalkBrief + optional brand assets
2. Written to `./tmp/deck/style-guide.json`
3. Frozen after creation -- all services read but do not modify
4. If brand assets are provided, the brand-extraction capability runs first to derive palette

---

## 4. SlideOutline

**File:** `./tmp/deck/outline.json`
**Producer:** `narrative-architect` (content-outline-generation service)
**Consumers:** speaker-notes-writer, imagegen-bridge, deck-assembler, Image Generation Expert, Presentation Reviewer

### Description

The backbone of the deck. An ordered array of slide definitions forming the complete presentation structure, with per-slide type, headline, body points, narrative beat, visual direction, and layout template.

### Key Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `narrative_arc` | string | Yes | Arc pattern (e.g., situation-complication-resolution, hook-body-callback-cta) |
| `estimated_duration_minutes` | number | Yes | Estimated presentation duration |
| `total_slides` | integer | No | Total slide count |
| `slides` | array | Yes | Ordered slide definitions |

### Per-Slide Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `slide_number` | integer | Yes | Position in deck |
| `slide_type` | enum | Yes | title, section_divider, content, two_column, image_feature, data_chart, stat_callout, quote, icon_grid, diagram, closing, blank_visual |
| `headline` | string | Yes | Short, punchy conference headline |
| `body_points` | string[] | No | Bullet points (max 5) |
| `narrative_beat` | string | No | Position in arc (hook, evidence-2, callback, cta) |
| `visual_direction` | string | No | Prose description for image generation prompts |
| `visual_type` | enum | No | hero_image, diagram, chart, icon_set, pattern_background, none |
| `data` | object | No | Chart data: chart_type, data_source_label, inline_data |
| `layout_template` | string | No | Layout template name from StyleGuide |
| `transition_note` | string | No | How the speaker transitions from previous slide |

### Lifecycle

1. Produced by narrative-architect from TalkBrief + StyleGuide
2. Written to `./tmp/deck/outline.json`
3. Normally frozen after creation
4. May be regenerated during a correction cycle if the Deck Conductor requests structural changes

---

## 5. SpeakerNotes

**File:** `./tmp/deck/speaker-notes.json`
**Producer:** `speaker-notes-writer` (content-speaker-notes service)
**Consumers:** deck-assembler, Presentation Reviewer

### Description

Per-slide speaker notes with timing markers, cumulative time marks, and interaction cues (transitions, pauses, audience interactions).

### Key Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `target_pace_wpm` | integer | No | Target speaking pace (default 130 wpm) |
| `total_estimated_minutes` | number | No | Total estimated speaking duration |
| `notes` | array | Yes | Per-slide note entries |

### Per-Note Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `slide_number` | integer | Yes | Which slide this note belongs to |
| `text` | string | Yes | Speaker notes text with timing markers |
| `estimated_seconds` | integer | No | Estimated speaking duration for this slide |
| `timing_marker` | string | No | Cumulative time mark (e.g., ~5:30) |
| `cues` | array | No | Interaction cues: type (transition, pause, audience_interaction, emphasis, demo, build_animation) + text |

### Lifecycle

1. Produced by speaker-notes-writer from SlideOutline + TalkBrief (audience, duration)
2. Written to `./tmp/deck/speaker-notes.json`
3. Frozen after creation unless correction cycle requires regeneration

---

## 6. ImageManifest

**File:** `./tmp/deck/image-manifest.json`
**Producer:** `imagegen-bridge` (image-routing-discovery service)
**Consumers:** deck-assembler

### Description

Registry of all generated image assets with metadata: file paths, dimensions, source prompts, model used, alt text, cache status, and generation timing.

### Key Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `generated_at` | datetime | No | When images were generated |
| `image_backend` | string | No | Which backend was used (e.g., ollama/x-z-image-turbo) |
| `images` | array | Yes | Per-image entries |
| `summary` | object | No | Aggregate stats: total_images, generated/cached/placeholder/failed counts, total_generation_seconds |

### Per-Image Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `image_id` | string | Yes | Unique ID (e.g., slide-03-hero) |
| `slide_number` | integer | Yes | Target slide |
| `file_path` | string | Yes | Relative path (e.g., ./tmp/deck/images/slide-03-hero.png) |
| `placement_zone` | string | No | Layout zone (image_zone, background, icon_1) |
| `dimensions` | object | No | width, height in pixels |
| `source_prompt` | string | No | Exact prompt sent to model |
| `model_used` | string | No | Model identifier |
| `alt_text` | string | No | Accessibility alt text |
| `content_hash` | string | No | SHA-256 of image bytes |
| `cache_key` | string | No | Cache lookup key |
| `status` | enum | Yes | generated, cached, placeholder, failed |
| `retry_count` | integer | No | Number of retries |
| `generation_time_seconds` | number | No | Generation duration |

### Lifecycle

1. Produced by imagegen-bridge after routing and generating all images
2. Written to `./tmp/deck/image-manifest.json`
3. Image files written to `./tmp/deck/images/`
4. Frozen after creation unless correction cycle requires regeneration of specific images

---

## 7. ChartManifest

**File:** `./tmp/deck/chart-manifest.json`
**Producer:** `chart-renderer` (image-chart-renderer service)
**Consumers:** deck-assembler

### Description

Registry of all rendered chart assets. Same pattern as ImageManifest but specific to data visualisations produced by Matplotlib.

### Key Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `charts` | array | Yes | Per-chart entries |

### Per-Chart Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `chart_id` | string | Yes | Unique ID |
| `slide_number` | integer | Yes | Target slide |
| `file_path` | string | Yes | Path to rendered chart image |
| `chart_type` | enum | Yes | bar, line, area, pie, donut, scatter, comparison_table, timeline, stat_card |
| `data_source_label` | string | No | Reference to TalkBrief data source |
| `alt_text` | string | No | Accessibility alt text |
| `dimensions` | object | No | width, height in pixels |
| `content_hash` | string | No | SHA-256 of chart image bytes |
| `status` | enum | No | rendered, cached, failed |

### Lifecycle

1. Produced by chart-renderer from SlideOutline (data_chart slides) + StyleGuide (palette) + TalkBrief (data_sources)
2. Written to `./tmp/deck/chart-manifest.json`
3. Chart images written to `./tmp/deck/images/`
4. Only produced if `include_charts` is true in TalkBrief preferences

---

## 8. QAReport

**File:** `./tmp/deck/qa-report.json`
**Producer:** `deck-qa` (assembly-visual-qa service)
**Consumers:** Deck Conductor, Presentation Reviewer

### Description

Quality assurance findings from automated anti-pattern checks. The Deck Conductor uses this to decide whether to trigger correction cycles.

### Key Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `inspected_at` | datetime | No | When QA was run |
| `pptx_path` | string | No | Path to inspected .pptx |
| `verdict` | enum | Yes | pass, pass_with_warnings, fail |
| `summary` | object | No | Counts: total_slides, errors, warnings, info |
| `findings` | array | Yes | Per-finding entries |

### Per-Finding Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `slide_number` | integer | Yes | Affected slide |
| `severity` | enum | Yes | error, warning, info |
| `category` | enum | Yes | overlap, contrast, margin, text_overflow, consistency, image_quality, placeholder_residue, missing_content, accessibility |
| `description` | string | Yes | Human-readable issue description |
| `suggested_fix` | string | No | What the conductor should do |
| `affected_element` | string | No | Which element (headline text box, hero image, etc.) |
| `auto_fixable` | boolean | No | Whether the conductor can fix automatically |

### Lifecycle

1. Produced by deck-qa after inspecting the assembled .pptx
2. Written to `./tmp/deck/qa-report.json`
3. Deck Conductor reads verdict:
   - `pass`: proceed to Presentation Reviewer
   - `pass_with_warnings`: proceed but include warnings in delivery
   - `fail`: trigger correction cycle (max 2)
4. New QA report overwrites previous on each QA pass

---

## 9. AvailableProviders

**File:** Not persisted to disk (held in conversation context and optionally echoed to pipeline-state.json)
**Producer:** `imagegen-bridge` (image-routing-discovery service)
**Consumers:** Deck Conductor, generation skills

### Description

The runtime manifest of which image generation providers are available for this pipeline run. Produced at startup via the provider discovery probe sequence.

### Key Fields

| Field | Type | Description |
|---|---|---|
| `ollama` | object | Available: boolean, models: string[], endpoint: string |
| `openai` | object | Available: boolean, model: string |
| `google_vertex` | object | Available: boolean, model: string |
| `fal` | object | Available: boolean, models: string[] |
| `recraft` | object | Available: boolean, model: string |

### Lifecycle

1. Produced by imagegen-bridge at the start of the image generation phase
2. Reported to the Deck Conductor in conversation context
3. Conductor confirms available capabilities with the Speaker before proceeding
4. Not persisted as a separate file (captured in pipeline-state.json if needed)

---

## 10. DeckContext (Aggregate)

**Directory:** `./tmp/deck/`
**Owner:** Deck Conductor
**Consumers:** All services

### Description

DeckContext is not a single contract but the aggregate of all contracts above, persisted as a directory of JSON files. The directory layout acts as a natural checkpoint system -- the existence of a file proves that the corresponding pipeline step completed.

### Directory Layout

```
./tmp/deck/
  pipeline-state.json          # Pipeline metadata (continuous update)
  talk-brief.json              # Speaker input (frozen)
  style-guide.json             # Visual design system (frozen)
  outline.json                 # Slide structure (frozen)
  speaker-notes.json           # Per-slide notes (frozen)
  image-manifest.json          # Generated images registry (frozen)
  chart-manifest.json          # Chart images registry (frozen)
  qa-report.json               # QA findings (overwritten per pass)
  images/                      # Generated asset files
    slide-01-hero.png
    slide-03-diagram.png
    slide-07-chart.png
    ...
  output/                      # Final deliverables
    presentation.pptx
```

### Design Rationale (from Research Paper #12)

1. **Skill independence** -- each skill reads only the files it needs
2. **Natural checkpointing** -- file existence proves step completion
3. **Human debuggability** -- `cat ./tmp/deck/style-guide.json` to inspect
4. **Conversation context as cache, not source of truth** -- files on disk are authoritative
5. **CONSTITUTION.md Article 4.6 compliance** -- uses `./tmp/` (project-local, gitignored)

---

## Data Flow Diagram

```
Speaker
  |
  | TalkBrief
  v
Deck Conductor ----> [talk-brief.json] (frozen)
  |                   [pipeline-state.json] (continuous)
  |
  |---> slide-stylist ----> [style-guide.json]
  |
  |---> narrative-architect ----> [outline.json]
  |
  |---> speaker-notes-writer ----> [speaker-notes.json]
  |
  |---> imagegen-bridge ----> [image-manifest.json] + images/
  |
  |---> chart-renderer ----> [chart-manifest.json] + images/
  |
  |---> deck-assembler ----> output/presentation.pptx
  |       reads: outline, style-guide, image-manifest,
  |              chart-manifest, speaker-notes
  |
  |---> deck-qa ----> [qa-report.json]
  |       reads: output/presentation.pptx
  |
  |---> presentation-reviewer
  |       reads: .pptx, outline, style-guide, notes, brief
  |
  v
Speaker receives: .pptx + QAReport + Review + Cost summary
```
