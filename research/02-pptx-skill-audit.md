# Existing PPTX Skill Architecture Audit

**Date:** 2026-03-28
**Author:** Automated audit of existing skills in the Jack-Tar Deckhand project
**Purpose:** Inventory all presentation-related skills and agents, identify gaps for conference-quality output, and map where Jack-Tar extends, wraps, or replaces each component.

---

## 1. Skill and Agent Inventory

### 1.1 `claude-api:pptx` (also `document-skills:pptx`)

**Full file path:** `/Users/stevejones/.claude/plugins/marketplaces/anthropic-agent-skills/skills/pptx/SKILL.md`
(Sub-files: `editing.md`, `pptxgenjs.md` in the same directory -- could not read due to permissions on global plugin directory, but their purpose is documented in the main SKILL.md.)

**What it does:**
- The core PowerPoint skill. Handles three workflows: reading/analyzing PPTX content, editing existing presentations from templates, and creating presentations from scratch.
- Reading uses `markitdown` for text extraction and `thumbnail.py` for visual overview.
- Editing uses an unpack/manipulate/repack workflow on raw Open XML.
- Creation from scratch uses `pptxgenjs` (Node.js library) as the slide-building engine.
- Includes a comprehensive design system: 10 named color palettes, font pairing table, typography scale, layout guidance, spacing rules, and an explicit list of anti-patterns.
- Provides a rigorous QA protocol: content QA via markitdown, visual QA via LibreOffice PDF conversion + pdftoppm, with an explicit verification loop requirement.

**Engine/libraries:**
- `pptxgenjs` (npm, global install) for creation
- `python-pptx` (via markitdown) for reading
- LibreOffice (`soffice`) for PDF conversion
- Poppler (`pdftoppm`) for PDF-to-image
- Pillow for thumbnails

**Inputs:**
- For reading: any `.pptx` file path
- For editing: a template `.pptx` file
- For creation: user instructions describing the desired deck (no formal schema)

**Outputs:**
- A `.pptx` file
- QA feedback (content text, slide images for visual inspection)

**Known limitations:**
- No formal input schema or data contract -- relies on free-form user instructions.
- The editing workflow (`editing.md`) and creation reference (`pptxgenjs.md`) are in the global plugin directory and could not be directly audited, but the main SKILL.md documents their purpose.
- No built-in image generation -- the skill places images but does not create them.
- No speaker notes automation -- notes must be manually specified.
- No narrative intelligence -- it builds slides as instructed but does not understand talk structure, pacing, or audience.
- QA is visual-inspection-based (human or subagent reads images) rather than programmatic (no automated overlap detection, contrast checking, or margin measurement).
- The "NEVER use accent lines under titles" rule and other anti-patterns suggest these are recurring failure modes that the skill cannot prevent, only detect after the fact.
- No master slide or slide layout registration system -- each slide is built ad hoc.
- Palette selection is manual -- the skill suggests 10 palettes but does not derive a palette from the topic.

**Relevance to Jack-Tar:**
This is the foundational assembly engine. Jack-Tar's `deck-assembler` wraps and extends this skill, not replaces it. Every slide ultimately gets built through pptxgenjs.

---

### 1.2 `generate-presentation` (project-level)

**Full file path:** `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/generate-presentation/SKILL.md`

**What it does:**
- An orchestrator skill that combines image generation with slide creation. It is the closest existing predecessor to the full Jack-Tar pipeline.
- Six-step workflow: (1) Plan the presentation, (2) Choose palette and typography, (3) Generate visual assets, (4) Build the presentation, (5) QA, (6) Clean up and report.
- Plans slides with per-slide metadata: slide number, title, content summary, layout type, visual asset needed, and generation approach.
- Defines 8 layout types: title-slide, two-column, icon-grid, stat-callout, image-feature, diagram, section-divider, closing.
- Maps each layout type to a visual asset strategy (which generation skill to use).
- Supports `--no-images` mode for fast text-only decks.

**Engine/libraries:**
- `src/generate_image.py` for all image generation (delegates to Ollama)
- `pptxgenjs` for slide building (via the pptx skill)
- `markitdown` for content QA
- LibreOffice + pdftoppm for visual QA
- Consults the `image-generation-expert` agent for prompt strategies

**Inputs:**
- Topic/description (quoted text or `--prompt-file`)
- `--slides N` (approximate count, default 8-12)
- `--output PATH`
- `--style STYLE` (corporate, creative, technical, minimal)
- `--no-images` flag

**Outputs:**
- A `.pptx` file with generated visual assets
- Report: path, slide count, image count, palette, fonts, known limitations

**Known limitations:**
- Single image generation backend (Ollama only) -- no cloud API routing.
- No formal narrative architecture -- the "plan" step is ad hoc, not driven by talk format, duration, or audience analysis.
- No speaker notes generation.
- No data visualization / chart capability.
- No brand override or corporate template support.
- Palette selection is manual ("pick a palette that matches the topic") rather than algorithmically derived.
- No shared DeckContext object -- context is carried implicitly in the conversation, not as a formal data structure.
- QA reuses the pptx skill's visual-inspection approach -- no programmatic checks.
- Image generation is sequential (Ollama limitation), so a 10-slide deck with images can take several minutes.
- No iteration or refinement loop for the overall deck -- only individual images can be refined.
- Assets stored in `/tmp/presentation-assets` then deleted -- no caching or reuse.

**Relevance to Jack-Tar:**
This is the direct predecessor to `deck-conductor`. Jack-Tar replaces this skill with a more sophisticated pipeline that separates content planning, visual generation, assembly, and QA into discrete, contract-driven skills.

---

### 1.3 `generate-image` (project-level)

**Full file path:** `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/generate-image/SKILL.md`
**Helper script:** `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/generate_image.py`

**What it does:**
- Generates images using local Ollama models. Two modes: one-shot (single generation, no review) and iterative (generate-review-refine loop using Claude's native vision to evaluate and improve).
- In iterative mode, scores each image on 6 weighted dimensions, applies mutation strategies based on score bands, and uses convergence rules to stop early.
- Discovers available models by listing Ollama's `x/`-prefixed image generation models.

**Engine/libraries:**
- Ollama REST API (`http://localhost:11434/api/generate`)
- Python `requests` library
- Two supported models: `x/z-image-turbo` (fast photorealism, 8 steps) and `x/flux2-klein` (text/spatial precision, 20 steps)

**Inputs:**
- `--prompt` or `--prompt-file`
- `--model` (default: `x/z-image-turbo`)
- `--output PATH`
- `--iterations N` (default: 1)
- `--width`, `--height`, `--steps`, `--seed`

**Outputs:**
- PNG image file at specified path
- In iterative mode: best-scoring image with score breakdown and iteration summary

**Known limitations:**
- Ollama-only -- no cloud API backends (no OpenAI, Gemini, FLUX.2 Max, Recraft, Ideogram).
- No native transparency/alpha channel support.
- No background removal capability.
- No inpainting or outpainting.
- No style reference or consistency across multiple generations.
- No post-processing (sharpening, color grading, palette enforcement).
- Image quality is constrained by local model capabilities -- `x/z-image-turbo` and `x/flux2-klein` are significantly below GPT Image 1.5, FLUX.2 Max, or Gemini 3 Pro in quality benchmarks.
- Text rendering in generated images is unreliable (acknowledged in the diagram skill).
- Sequential generation only (Ollama cannot handle parallel requests).
- The helper script (`generate_image.py`) is a thin wrapper -- 104 lines, no retry logic, no caching, no metadata tracking.

**Relevance to Jack-Tar:**
Jack-Tar's `imagegen-bridge` wraps this for local Ollama generation and extends it with cloud API routing, background removal, palette enforcement, and batch generation with selection. The existing skill remains the local/offline fallback.

---

### 1.4 `generate-icon` (project-level)

**Full file path:** `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/generate-icon/SKILL.md`

**What it does:**
- Generates application icons, favicons, and document markers optimized for small sizes.
- Supports three styles: flat (default), 3d, outlined.
- Wraps user descriptions in style-specific prompt templates that emphasize simplicity, geometric shapes, and legibility at small sizes.
- Can generate multiple sizes (e.g., 64, 128, 256, 512) independently.
- Defaults to `x/flux2-klein` for cleaner geometric shapes.

**Engine/libraries:**
- `src/generate_image.py` (same Ollama helper)
- Default model: `x/flux2-klein`

**Inputs:**
- Description or `--prompt-file`
- `--sizes` (comma-separated, default: 512)
- `--style` (flat, 3d, outlined)
- `--output PATH`
- `--model`

**Outputs:**
- PNG icon file(s) at specified path(s)

**Known limitations:**
- Raster output only -- no SVG/vector generation (critical gap vs. Recraft V4).
- No icon set consistency -- each icon is generated independently with no shared style reference.
- No palette integration -- does not accept or enforce a presentation palette.
- Small sizes (64, 128) are generated independently rather than downscaled from a master, which can produce inconsistent results.
- No background removal -- icons may have background artifacts that need manual cleanup.
- For presentation use, the skill acknowledges that react-icons (Font Awesome, Material Design) should be preferred when a standard icon exists.

**Relevance to Jack-Tar:**
Jack-Tar's visual pipeline can use this for custom icon generation when standard icon libraries lack a needed concept. The `imagegen-bridge` should add palette enforcement and background removal as post-processing steps. For conference quality, SVG icon generation (via Recraft V4 API) would be a significant upgrade.

---

### 1.5 `generate-pattern` (project-level)

**Full file path:** `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/generate-pattern/SKILL.md`

**What it does:**
- Generates seamless textures and repeating patterns for backgrounds, materials, and design assets.
- Five styles: geometric, organic, textile, abstract, material. Auto-infers style from description if not specified.
- Uses style-specific prompt templates optimized for tileability.
- Can generate multiple variations with different seeds.
- Defaults to `x/z-image-turbo` (faster, good for textures).

**Engine/libraries:**
- `src/generate_image.py` (same Ollama helper)
- Default model: `x/z-image-turbo`
- Default size: 1024x1024 (square for tiling)

**Inputs:**
- Description or `--prompt-file`
- `--style` (geometric, organic, textile, abstract, material)
- `--output PATH`
- `--model`
- `--count N` (variations)
- `--width`, `--height`

**Outputs:**
- PNG pattern file(s)

**Known limitations:**
- No actual seamlessness verification -- the prompt asks for "seamless" but there is no post-processing to ensure tiles match at edges.
- No palette enforcement -- cannot force a pattern to use specific presentation colours.
- No contrast control -- for slide backgrounds, patterns need to be subtle/low-contrast, but this is only achieved through prompt wording, not post-processing.
- No tiling preview -- no way to verify the pattern tiles correctly before use.

**Relevance to Jack-Tar:**
Useful for title slide backgrounds and section dividers. Jack-Tar should add: (1) palette-aware colour grading post-processing, (2) contrast reduction for use behind text, (3) optional tiling verification.

---

### 1.6 `generate-diagram` (project-level)

**Full file path:** `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/generate-diagram/SKILL.md`

**What it does:**
- Generates technical diagrams using AI image generation: flowcharts, architecture diagrams, sequence diagrams, network diagrams.
- Uses type-specific prompt templates with FLUX spatial hierarchy approach.
- Defaults to `x/flux2-klein` for better text rendering and spatial accuracy.
- Includes an honest disclaimer about text legibility limitations.

**Engine/libraries:**
- `src/generate_image.py` (same Ollama helper)
- Default model: `x/flux2-klein`
- Default size: 1024x768 (landscape)

**Inputs:**
- Description or `--prompt-file`
- `--type` (flowchart, architecture, sequence, network, general)
- `--output PATH`
- `--model`
- `--width`, `--height`

**Outputs:**
- PNG diagram image

**Known limitations:**
- Text in generated diagrams is frequently garbled or partially readable -- this is an inherent limitation of diffusion models.
- The skill honestly recommends using generated diagrams as "visual illustrations" and overlaying actual labels via pptxgenjs text boxes.
- No programmatic diagram generation (Mermaid, D2, Graphviz) -- only AI-generated raster images.
- Output is a flat image, not editable.
- No validation of diagram correctness or logical consistency.

**Relevance to Jack-Tar:**
For conference quality, Jack-Tar should primarily use programmatic diagramming tools (Mermaid, D2) rendered to SVG/PNG for technical diagrams, reserving AI-generated diagrams only for conceptual/illustrative purposes where exact text is not critical. The `chart-renderer` skill planned in the README addresses this gap.

---

### 1.7 `image-generation-expert` Agent

**Full file path:** `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/agents/image-generation-expert.md`

**What it does:**
- A knowledge resource (not an orchestrator) that provides domain expertise on Ollama image generation.
- Documents supported models, prompt engineering strategies for both Z-Image Turbo and FLUX.2 Klein, universal prompt rules, a 6-dimension scoring rubric, score band mutation strategies, convergence rules, and presentation-specific image guidance.
- The "Images for Presentations" section is particularly relevant: covers sizing for 16:9 slides, background image guidelines, content image guidelines, icon guidelines, diagram guidelines, colour palette matching, and speed-vs-quality trade-offs.
- Documents Ollama API quirks and tested lessons learned.

**Engine/libraries:** None (pure knowledge resource).

**Inputs:** Consulted by other skills (generate-image, generate-icon, generate-diagram, generate-pattern, generate-presentation).

**Outputs:** Prompt engineering advice, scoring criteria, refinement strategies.

**Known limitations:**
- Knowledge is specific to Ollama's two local models -- no guidance for cloud APIs.
- Scoring rubric is designed for single-image evaluation, not deck-wide consistency assessment.
- No guidance on brand enforcement, corporate template integration, or multi-model routing.
- The "Images for Presentations" section is excellent but limited to the local Ollama context.

**Relevance to Jack-Tar:**
This agent's knowledge should be preserved and extended. Jack-Tar needs an expanded version that covers cloud API prompt strategies, multi-model routing logic, and deck-wide visual consistency assessment. The existing scoring rubric and convergence rules are directly reusable for the iterative refinement loop.

---

### 1.8 `claude-api:theme-factory` (also `document-skills:theme-factory`)

**Full file path:** Global plugin directory (could not read due to permissions).

**What it does (from skill description):**
- Toolkit for styling artifacts with a theme. Supports slides, docs, reportings, HTML landing pages, etc.
- Provides 10 pre-set themes with colours and fonts.
- Can generate new themes on-the-fly.
- Can apply a theme to any artifact that has been created.

**Known limitations (inferred):**
- Generic theming tool, not presentation-specific.
- Likely provides colour/font definitions but not slide layout intelligence.
- Unknown whether it integrates with pptxgenjs or operates independently.

**Relevance to Jack-Tar:**
Potential integration point for the `slide-stylist` skill. If theme-factory can generate and serialize a theme definition (palette + fonts), Jack-Tar could consume it as an input to the style guide. Needs further investigation once permissions allow reading the full skill.

---

## 2. Feature Inventory Summary

| Capability | pptx | generate-presentation | generate-image | generate-icon | generate-pattern | generate-diagram | image-gen-expert | theme-factory |
|---|---|---|---|---|---|---|---|---|
| Read/parse PPTX | Yes | No | No | No | No | No | No | No |
| Edit existing PPTX | Yes | No | No | No | No | No | No | No |
| Create PPTX from scratch | Yes | Yes (orchestrates) | No | No | No | No | No | No |
| Color palette system | 10 presets | References pptx skill | No | No | No | No | Matching tips | 10 presets |
| Typography system | Font pairing table | References pptx skill | No | No | No | No | No | Yes (inferred) |
| Layout templates | Design guidelines | 8 layout types | No | No | No | No | No | No |
| Image generation | No | Orchestrates | Yes (Ollama) | Yes (Ollama) | Yes (Ollama) | Yes (Ollama) | Knowledge only | No |
| Cloud API image gen | No | No | No | No | No | No | No | No |
| Iterative refinement | No | Single retry | Full loop | No | No | Optional review | Rubric/strategy | No |
| Speaker notes | No | No | No | No | No | No | No | No |
| Narrative planning | No | Basic slide plan | No | No | No | No | No | No |
| Data visualization | No | No | No | No | No | No | No | No |
| Programmatic diagrams | No | No | No | No | No | No (AI only) | No | No |
| Background removal | No | No | No | No | No | No | No | No |
| Brand/template support | No | No | No | No | No | No | No | Partial |
| Automated QA | Visual inspection | Visual inspection | Score rubric | No | No | Honest note | Rubric defined | No |
| Programmatic QA | No | No | No | No | No | No | No | No |
| DeckContext / contracts | No | No | No | No | No | No | No | No |

---

## 3. Gap Analysis: What "Conference Quality" Requires

Conference-quality presentations differ from standard business decks in several critical dimensions. The following gaps are ordered by impact.

### 3.1 CRITICAL GAPS (must close for conference quality)

**Gap 1: No narrative intelligence.**
Conference presentations follow specific structural patterns based on session format (15-min lightning, 30-min breakout, 45-min keynote). The existing skills have no concept of talk format, audience analysis, narrative arc, pacing, or progressive disclosure. The `generate-presentation` skill's "plan" step is a general-purpose slide planner, not a conference-aware narrative architect.

**Gap 2: No speaker notes.**
No existing skill generates speaker notes. Conference speakers need per-slide notes with timing markers, transition cues, audience interaction prompts, and emphasis markers. This is a complete blind spot.

**Gap 3: No data visualization pipeline.**
The existing skills cannot produce charts, infographics, or data callouts. The `generate-diagram` skill produces AI-generated raster images with garbled text -- unusable for data-driven slides. Conference decks frequently need bar charts, trend lines, comparison tables, and large-number callouts.

**Gap 4: No programmatic QA.**
QA is entirely visual-inspection-based -- a human or subagent looks at slide images. Conference quality requires automated checks: WCAG contrast ratios, margin enforcement, text overflow detection, font consistency auditing, image resolution verification, and placeholder residue scanning. The pptx skill documents what to look for but cannot check it programmatically.

**Gap 5: No cloud image generation.**
All image generation is Ollama-only (local models). The research documents (`ai-image-models-for-presentations.md`) establish that local models are significantly below cloud models in quality. Conference-quality hero images, icons, and backgrounds need GPT Image 1.5, FLUX.2 Max, Recraft V4, or Gemini 3 Pro. The current pipeline cannot access any of these.

### 3.2 SIGNIFICANT GAPS (materially affect quality)

**Gap 6: No formal data contracts.**
Skills communicate implicitly through conversation context. There is no serialized DeckContext, SlideOutline, StyleGuide, ImageManifest, or QAReport. This prevents reliable multi-skill orchestration and makes the pipeline fragile.

**Gap 7: No brand/template integration.**
No skill can ingest a corporate brand guide, extract colours from a logo, or work with an existing corporate PPTX template. Conference presentations often must conform to organizational branding.

**Gap 8: No background removal or image post-processing.**
Generated images cannot have backgrounds removed, be colour-graded to match a palette, be sharpened, or be composited with overlays. The `image-generation-expert` agent notes that "semi-transparent overlays (transparency 30-40%) make text readable over any generated image" but no skill implements this.

**Gap 9: No SVG/vector icon generation.**
All icon generation produces raster PNGs. Conference decks projected on large screens benefit from vector assets that scale without pixelation. Recraft V4 produces true SVGs but is not integrated.

**Gap 10: No cross-slide visual consistency enforcement.**
Each image is generated independently. There is no style reference passing between generations, no deck-wide colour harmony check, and no mechanism to ensure visual coherence across 30 slides.

### 3.3 NICE-TO-HAVE GAPS (polish and differentiation)

**Gap 11: No programmatic diagram generation.** Mermaid/D2/Graphviz integration would produce clean, accurate technical diagrams with legible text.

**Gap 12: No font embedding or management.** The pptx skill suggests font pairings from a fixed table but cannot embed custom fonts or verify font availability.

**Gap 13: No animation or build support.** Conference slides often use progressive builds (bullet points appearing one at a time). No skill addresses this.

**Gap 14: No aspect ratio intelligence.** Image generation uses fixed dimensions rather than calculating optimal dimensions from the layout zone where the image will be placed.

---

## 4. Integration Map

This section maps each planned Jack-Tar component to its relationship with existing skills.

| Jack-Tar Component | Relationship | Existing Skill | What Changes |
|---|---|---|---|
| **deck-conductor** | **REPLACES** | `generate-presentation` | Complete replacement. The existing skill is a monolithic orchestrator; deck-conductor is a contract-driven pipeline coordinator with checkpointing, retry, and shared DeckContext. |
| **narrative-architect** | **NEW** | (none) | No existing skill addresses talk format, narrative arc, or conference-specific content planning. Built from scratch. |
| **imagegen-bridge** | **EXTENDS** | `generate-image`, `generate-icon`, `generate-pattern`, `generate-diagram` | Wraps all four existing skills as the "local Ollama" backend. Adds cloud API routing (OpenAI, FLUX, Recraft, Gemini), background removal, palette enforcement, and batch generation with selection. |
| **slide-stylist** | **NEW** (partial overlap) | `pptx` skill palettes, `theme-factory` | The pptx skill's palette table and font pairings are a starting point. The stylist adds algorithmic palette derivation from topic, brand override, and layout template definitions as structured objects. May consume theme-factory output. |
| **speaker-notes-writer** | **NEW** | (none) | Complete new capability. No existing skill generates speaker notes. |
| **chart-renderer** | **NEW** | (none) | No existing data visualization capability. Uses Matplotlib/Seaborn or programmatic charting. |
| **deck-assembler** | **WRAPS** | `pptx` skill (pptxgenjs) | The pptx skill's pptxgenjs engine is the assembly backend. The assembler adds: automated image placement from layout templates, speaker notes insertion, footer/slide-number consistency, and master slide registration. |
| **deck-qa** | **EXTENDS** | `pptx` skill QA protocol | The pptx skill defines what to check and how to visually inspect. deck-qa adds programmatic checking: contrast measurement, margin calculation, text overflow detection, consistency auditing, and image resolution verification. |
| **image-generation-expert (extended)** | **EXTENDS** | `image-generation-expert` | Existing agent's knowledge is preserved and expanded with cloud API prompt strategies, multi-model routing decision trees, and deck-wide consistency scoring. |

### Integration Dependency Graph

```
deck-conductor
  |
  +-- narrative-architect (NEW)
  |     |
  |     +-- (consumes TalkBrief, produces SlideOutline)
  |
  +-- slide-stylist (NEW, partial overlap with pptx palettes + theme-factory)
  |     |
  |     +-- (consumes TalkBrief, produces StyleGuide)
  |
  +-- imagegen-bridge (EXTENDS generate-image, -icon, -pattern, -diagram)
  |     |
  |     +-- (consumes SlideOutline + StyleGuide, produces ImageManifest)
  |     +-- Cloud APIs: OpenAI, FLUX, Recraft, Gemini (NEW)
  |     +-- Post-processing: rembg, palette grading, compositing (NEW)
  |     +-- Local fallback: existing Ollama skills (PRESERVED)
  |
  +-- speaker-notes-writer (NEW)
  |     |
  |     +-- (consumes SlideOutline, produces per-slide notes)
  |
  +-- chart-renderer (NEW)
  |     |
  |     +-- (consumes data + StyleGuide, produces chart images)
  |
  +-- deck-assembler (WRAPS pptx skill / pptxgenjs)
  |     |
  |     +-- (consumes all upstream outputs, produces .pptx)
  |
  +-- deck-qa (EXTENDS pptx QA)
        |
        +-- (consumes .pptx, produces QAReport)
        +-- Programmatic checks (NEW)
        +-- Visual inspection (PRESERVED from pptx skill)
```

---

## 5. Recommendations

### 5.1 Skills to EXTEND (not rebuild)

1. **`generate-image`** -- The Ollama helper script and iterative refinement loop are solid. Extend by adding cloud API backends alongside, not replacing, the local path. The scoring rubric and convergence rules from the expert agent should be reused verbatim.

2. **`pptx` skill (pptxgenjs engine)** -- This is battle-tested. The deck-assembler should be a thin orchestration layer on top, not a reimplementation. Preserve all design guidelines and QA protocols.

3. **`image-generation-expert` agent** -- Expand the knowledge base to cover cloud APIs, but keep the existing Ollama-specific guidance. The "Images for Presentations" section is directly applicable.

### 5.2 Skills to WRAP (use as-is behind a new interface)

4. **`generate-icon`** -- Wrap behind imagegen-bridge's routing logic. For local generation, call this skill. For cloud generation, route to Recraft V4 for SVG output. Add palette enforcement as a post-processing step.

5. **`generate-pattern`** -- Same wrapping strategy. Add palette-aware colour grading and contrast reduction for slide backgrounds.

6. **`generate-diagram`** -- Wrap but downgrade to "illustrative use only." Primary diagram generation should use Mermaid/D2 for accuracy. Keep this skill as a fallback for conceptual diagrams where exact text is not needed.

### 5.3 Skills to BUILD NEW

7. **`narrative-architect`** -- No existing foundation. Build from scratch with conference-specific intelligence: talk format awareness, narrative arc patterns, audience calibration.

8. **`speaker-notes-writer`** -- No existing foundation. Build from scratch with timing calibration, transition cues, and emphasis markers.

9. **`chart-renderer`** -- No existing foundation. Use Matplotlib/Seaborn with presentation-grade styling (large fonts, brand palette, no chartjunk).

10. **`deck-qa` (programmatic)** -- The pptx skill's QA checklist provides the specification. Build programmatic implementations of each check: WCAG contrast via colorsys, margin measurement via pptxgenjs element coordinates, text overflow via font metrics, consistency auditing via cross-slide comparison.

### 5.4 Priority Order

Based on the dependency graph and gap severity:

| Priority | Component | Rationale |
|---|---|---|
| P0 | Data contracts (JSON schemas) | Everything depends on these. Define TalkBrief, DeckContext, SlideOutline, StyleGuide, ImageManifest, QAReport before any implementation. |
| P1 | `narrative-architect` + `slide-stylist` | No upstream dependencies. Produce the SlideOutline and StyleGuide that all downstream skills consume. |
| P2 | `imagegen-bridge` (cloud API routing) | The single largest quality lever. Moving from local Ollama to cloud APIs transforms image quality from "acceptable" to "conference-grade." |
| P3 | `chart-renderer` + `speaker-notes-writer` | Both are content producers with well-defined interfaces. Can be developed in parallel. |
| P4 | `deck-assembler` | Depends on all upstream outputs being available. Wraps pptxgenjs with automated layout placement. |
| P5 | `deck-qa` (programmatic) | Depends on deck-assembler producing decks to check. Converts the pptx skill's visual checklist into automated gates. |
| P6 | `deck-conductor` | The orchestrator comes last -- it coordinates components that must already exist and be tested individually. |

---

## 6. Key Technical Decisions Required

1. **DeckContext serialization:** JSON file on disk (resumable, inspectable) vs. in-memory object (faster, simpler). Recommendation: JSON file, enabling checkpointing and debugging.

2. **Cloud API authentication:** Environment variables per provider vs. a unified credential manager. The research recommends aggregators (Fal.ai, Together AI) to simplify multi-model routing.

3. **Image generation routing logic:** Rule-based (asset type -> model) vs. LLM-decided. The research recommends rule-based routing with the decision tree: text-heavy -> Ideogram 3.0, vector icon -> Recraft V4, photorealism -> FLUX.2 Max, fast background -> Gemini Flash.

4. **Local vs. cloud default:** Should the pipeline default to local Ollama (free, private, slower, lower quality) or cloud APIs (paid, faster, higher quality)? Recommendation: cloud-first with local fallback when no API keys are configured.

5. **QA gate enforcement:** Should deck-qa be a blocking gate (fail = rebuild) or advisory (report issues, let user decide)? Recommendation: advisory with severity levels -- errors block, warnings report.

---

## Appendix A: File Manifest

All files examined in this audit:

| File | Location |
|---|---|
| pptx SKILL.md | `/Users/stevejones/.claude/plugins/marketplaces/anthropic-agent-skills/skills/pptx/SKILL.md` |
| generate-presentation SKILL.md | `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/generate-presentation/SKILL.md` |
| generate-image SKILL.md | `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/generate-image/SKILL.md` |
| generate-icon SKILL.md | `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/generate-icon/SKILL.md` |
| generate-pattern SKILL.md | `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/generate-pattern/SKILL.md` |
| generate-diagram SKILL.md | `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/generate-diagram/SKILL.md` |
| image-generation-expert agent | `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/agents/image-generation-expert.md` |
| generate_image.py helper | `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/generate_image.py` |
| README.md (project vision) | `/Users/stevejones/Documents/Development/jack-tar-deckhand/README.md` |
| Tool research report | `/Users/stevejones/Documents/Development/jack-tar-deckhand/research/presentation-engineering-tool-research.md` |
| AI image models research | `/Users/stevejones/Documents/Development/jack-tar-deckhand/research/ai-image-models-for-presentations.md` |

### Files referenced but not readable (global plugin directory permissions)

| File | Location |
|---|---|
| pptx editing.md | `/Users/stevejones/.claude/plugins/marketplaces/anthropic-agent-skills/skills/pptx/editing.md` |
| pptx pptxgenjs.md | `/Users/stevejones/.claude/plugins/marketplaces/anthropic-agent-skills/skills/pptx/pptxgenjs.md` |
| theme-factory SKILL.md | Global plugin directory (exact path unknown) |
