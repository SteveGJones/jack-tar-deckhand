# Jack-Tar — Deckhand

> *"A Jack-Tar never lets the deck go untended."*

**AI-powered skills and agents for building conference-quality presentation decks with Claude Code and Claude Desktop.**

---

## Vision

The existing `pptx` skill produces solid slide decks, but conference-quality presentations demand more: bespoke hero imagery, data-driven infographics, speaker-ready layouts, and a visual identity that holds up on a 40-foot projector screen in front of 2,000 people. This project closes that gap.

Jack-Tar is a coordinated suite of Claude skills and orchestration agents that combine image generation models, layout intelligence, and content-authoring tools into a single end-to-end pipeline. A speaker describes their talk, and the system delivers a polished, stage-ready `.pptx` — complete with generated visuals, consistent branding, typographic hierarchy, and speaker notes.

---

## Problem Statement

Building a conference deck today — even with AI assistance — still involves a fragmented workflow:

1. Draft an outline in one tool.
2. Generate images in another (Midjourney, DALL·E, Flux, etc.).
3. Manually place and resize assets in PowerPoint or Google Slides.
4. Iterate on layout, colour, and typography by hand.
5. Write speaker notes separately.
6. Run a visual QA pass yourself.

Each handoff loses context. The image generator doesn't know your slide dimensions. The layout tool doesn't know your narrative arc. Nobody enforces brand consistency across 30 slides. Jack-Tar eliminates these seams by keeping the entire pipeline inside Claude's skill and agent framework, where every component shares context.

---

## Architecture Overview

The system is organised into three layers:

```
┌─────────────────────────────────────────────────────────┐
│                   Orchestration Layer                    │
│          deck-conductor agent (top-level)                │
│   Receives talk brief → coordinates all skills → .pptx  │
└────────────┬──────────────┬──────────────┬──────────────┘
             │              │              │
     ┌───────▼──────┐ ┌────▼─────┐ ┌──────▼───────┐
     │  Content      │ │  Visual   │ │  Assembly &  │
     │  Skills       │ │  Skills   │ │  QA Skills   │
     │              │ │           │ │              │
     │ • narrative   │ │ • imagegen│ │ • layout     │
     │ • speaker-    │ │ • iconset │ │ • brand-qa   │
     │   notes       │ │ • palette │ │ • slide-qa   │
     │ • outline     │ │ • chart   │ │ • pptx-build │
     └──────────────┘ └───────────┘ └──────────────┘
```

**Orchestration Layer** — A top-level agent (`deck-conductor`) that accepts a talk brief (topic, audience, duration, tone) and breaks it into a sequenced plan. It calls the content, visual, and assembly skills in dependency order, passing shared context (palette, narrative arc, brand tokens) between them.

**Content Skills** — Responsible for the intellectual structure of the deck: outline generation, slide-by-slide narrative, headline copywriting, and speaker note drafting. These skills understand conference communication patterns (the "rule of three," progressive disclosure, audience callbacks).

**Visual Skills** — Handle all image and graphic asset creation: hero images via generation models, icon set curation, colour palette derivation, and data visualisation/chart generation. Every visual skill is resolution- and aspect-ratio-aware for standard slide dimensions (16:9 at 1920×1080 or 2560×1440).

**Assembly & QA Skills** — Take the content and visual outputs, compose them into `.pptx` using the existing `pptxgenjs` pipeline, enforce layout rules, and run automated visual QA (overlap detection, contrast checking, margin enforcement, text overflow).

---

## Project Components

### 1. `deck-conductor` — Orchestration Agent

The central agent that owns the end-to-end workflow.

**Responsibilities:**
- Parse and validate the talk brief (topic, audience profile, session length, tone, branding requirements).
- Generate a deck plan: slide count, slide types (title, section divider, content, data, quote, closing/CTA), and narrative flow.
- Coordinate skill invocations in dependency order.
- Maintain a shared context object (`DeckContext`) that carries palette, fonts, brand tokens, image manifest, and outline across all skill calls.
- Handle iteration: when QA finds issues, re-invoke the appropriate skill with corrective instructions.

**Key design decisions to make:**
- How `DeckContext` is serialised and passed between skills (JSON blob vs. file on disk).
- Retry and fallback strategy when an image generation call fails or returns low-quality output.
- Whether the conductor runs as a single long session or checkpoints to disk for resumability.

---

### 2. `narrative-architect` — Content Outline Skill

Transforms a talk brief into a structured slide outline.

**Inputs:** Topic, audience, duration, key takeaways, tone.  
**Outputs:** JSON outline with per-slide objects containing `slide_type`, `headline`, `key_points`, `narrative_beat`, `visual_direction` (a prose hint for the image generation skill).

**Conference-specific intelligence:**
- Understands common session formats (15-min lightning talk, 30-min breakout, 45-min keynote) and adjusts slide count and density accordingly.
- Applies narrative arc patterns: situation → complication → resolution, or hook → body → callback → CTA.
- Flags slides that need data visuals vs. hero imagery vs. diagrams.

---

### 3. `imagegen-bridge` — Image Generation Skill

Bridges Claude to one or more image generation backends to produce slide-ready visuals.

**Inputs:** `visual_direction` prompt from the outline, target dimensions, palette constraints, style guide tokens.  
**Outputs:** Generated image files (PNG/JPEG) at correct slide dimensions, plus metadata (alt text, source prompt, model used).

**Supported backends (planned):**
- DALL·E 3 (via OpenAI API)
- Flux (via Replicate or self-hosted)
- Stable Diffusion (via Stability API or local ComfyUI)
- Ideogram (for text-heavy graphics and logos)

**Key capabilities:**
- Prompt engineering layer that translates `visual_direction` prose into model-specific prompts, appending style modifiers, negative prompts, and aspect ratio directives.
- Resolution management: generates at native slide resolution (1920×1080 for 16:9) or at 2× for retina/high-DPI projection.
- Palette enforcement: injects dominant palette colours into the prompt or applies post-generation colour grading.
- Batch generation with selection: generates 2–4 variants per slide and uses a vision-model evaluation pass to pick the best fit.

---

### 4. `slide-stylist` — Layout & Design Skill

Owns the visual design system for the deck.

**Inputs:** Talk brief, audience, tone.  
**Outputs:** A `StyleGuide` object containing palette (primary, secondary, accent, background, text colours), font pairings (heading + body), spacing scale, and a set of approved layout templates per slide type.

**Capabilities:**
- Derives palette from topic semantics (a cybersecurity talk gets different colours than a sustainability talk).
- Selects font pairings from the available system/embedded font matrix.
- Defines layout templates as structured objects that the assembly skill can apply: column ratios, image placement zones, margin rules, text box dimensions.
- Supports brand override: if the user supplies a corporate brand guide or logo, the stylist adapts the palette and typography to match while maintaining conference-grade visual impact.

---

### 5. `speaker-notes-writer` — Speaker Notes Skill

Generates presentation-ready speaker notes for each slide.

**Inputs:** Slide outline, narrative arc, audience profile, speaker style preference (conversational, technical, storytelling).  
**Outputs:** Per-slide speaker notes in plain text, calibrated to target duration (roughly 1–2 minutes of spoken content per slide for a standard pace).

**Conference-specific features:**
- Timing markers (approximate minute marks for pacing).
- Transition cues ("When you click, the diagram will build in…").
- Audience interaction prompts ("Pause here for a show of hands").
- Key emphasis markers for the speaker to stress.

---

### 6. `chart-renderer` — Data Visualisation Skill

Generates publication-quality charts and infographics as images for embedding into slides.

**Inputs:** Data (inline JSON, CSV reference, or natural-language description of the data story), chart type preference, palette from `StyleGuide`.  
**Outputs:** Chart image (SVG rendered to PNG at slide resolution), plus alt-text description.

**Chart types:**
- Bar, line, area, pie/donut, scatter.
- Comparison tables with visual emphasis.
- Timeline / process flow diagrams.
- Large-number callout cards (e.g., "4.2M users" in 72pt with a subtle trend arrow).

---

### 7. `deck-assembler` — PPTX Build Skill

The final composition step. Takes all outputs and produces the `.pptx` file.

**Inputs:** Slide outline (with finalised headlines and body text), generated images (with placement metadata), `StyleGuide`, speaker notes.  
**Outputs:** A complete `.pptx` file.

**Built on:** The existing `pptxgenjs` pipeline from the core `pptx` skill — this component extends rather than replaces it.

**Additions over the base skill:**
- Automated image placement using layout template zones from the `slide-stylist`.
- Embedded speaker notes per slide.
- Consistent footer/slide-number treatment.
- Master slide and layout registration for brand consistency.

---

### 8. `deck-qa` — Visual Quality Assurance Skill

Automated QA that catches the issues humans miss on first pass.

**Inputs:** Generated `.pptx` file.  
**Outputs:** QA report (list of issues by slide, severity, and suggested fix), plus a pass/fail verdict.

**Checks:**
- **Overlap detection:** Text through shapes, elements stacked, content bleeding off-slide.
- **Contrast compliance:** WCAG AA minimum contrast ratios for all text against its background.
- **Margin enforcement:** No element closer than 0.5″ to slide edges.
- **Text overflow:** Detects text boxes where content is clipped or truncated.
- **Consistency audit:** Font sizes, colours, and spacing patterns are uniform across slides.
- **Image quality:** Resolution check (no upscaled-from-thumbnail images), aspect ratio correctness.
- **Placeholder residue:** Scans for leftover template text ("Click to add title", "Lorem ipsum", "XXX").

---

## Project Structure

```
jack-tar-deckhand/
├── README.md                          ← You are here
├── CONTRIBUTING.md                    ← Development workflow and conventions
├── CHANGELOG.md                       ← Release history
│
├── skills/                            ← All Claude skills (each is self-contained)
│   ├── deck-conductor/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   └── orchestration-patterns.md
│   │   └── agents/
│   │       └── conductor-agent.md
│   │
│   ├── narrative-architect/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── talk-formats.md
│   │       └── narrative-arcs.md
│   │
│   ├── imagegen-bridge/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── prompt-patterns.md
│   │   │   ├── dalle3.md
│   │   │   ├── flux.md
│   │   │   └── stable-diffusion.md
│   │   └── scripts/
│   │       ├── generate.py
│   │       └── evaluate.py
│   │
│   ├── slide-stylist/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── palettes.md
│   │   │   └── layout-templates.md
│   │   └── assets/
│   │       └── font-matrix.json
│   │
│   ├── speaker-notes-writer/
│   │   └── SKILL.md
│   │
│   ├── chart-renderer/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── render-chart.py
│   │
│   ├── deck-assembler/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── assemble.js
│   │
│   └── deck-qa/
│       ├── SKILL.md
│       └── scripts/
│           ├── qa-runner.py
│           └── contrast-checker.py
│
├── evals/                             ← Test cases and benchmarks
│   ├── prompts/                       ← Test talk briefs
│   │   ├── lightning-talk-ai.json
│   │   ├── keynote-sustainability.json
│   │   └── breakout-devops.json
│   ├── golden-outputs/                ← Reference decks for comparison
│   └── evals.json                     ← Assertion definitions
│
├── docs/                              ← Extended documentation
│   ├── architecture.md
│   ├── image-generation-strategy.md
│   ├── style-guide-spec.md
│   └── qa-checklist.md
│
└── examples/                          ← Sample outputs and demos
    ├── sample-lightning-talk.pptx
    └── sample-keynote.pptx
```

---

## Shared Data Contracts

All skills communicate through well-defined JSON interfaces. The core contracts are:

**`TalkBrief`** — Input from the user describing their presentation needs. Fields include `topic`, `audience`, `duration_minutes`, `tone`, `key_takeaways`, `branding` (optional logo, corporate colours), and `preferences` (e.g., "minimalist," "data-heavy," "image-rich").

**`DeckContext`** — The shared state object that the conductor passes between skills. Accumulates outputs as the pipeline progresses: starts with the `TalkBrief`, gains the `StyleGuide` after the stylist runs, gains the `SlideOutline` after the narrative architect runs, gains the `ImageManifest` after image generation, and so on.

**`SlideOutline`** — Array of slide objects, each with `slide_number`, `slide_type`, `headline`, `body_points`, `narrative_beat`, `visual_direction`, `data` (optional, for chart slides), and `speaker_notes`.

**`StyleGuide`** — Palette, font pairings, spacing scale, layout template assignments per slide type, and brand override tokens.

**`ImageManifest`** — Array of generated image records: `slide_number`, `file_path`, `dimensions`, `alt_text`, `source_prompt`, `model_used`, `placement_zone`.

**`QAReport`** — Array of findings: `slide_number`, `severity` (error, warning, info), `category`, `description`, `suggested_fix`.

These contracts will be formally defined as JSON schemas in `docs/` and validated at each handoff point.

---

## Development Approach

This project follows a high-ceremony, quality-first SDLC:

**Skill-by-skill delivery.** Each skill is developed, tested, and stabilised independently before integration. The delivery order follows the dependency graph: `slide-stylist` and `narrative-architect` first (no upstream dependencies), then `imagegen-bridge` and `chart-renderer` (depend on style guide), then `deck-assembler` (depends on all content and visual outputs), then `deck-qa` (depends on assembled deck), and finally `deck-conductor` (orchestrates everything).

**Eval-driven development.** Every skill gets a set of test prompts (`evals/prompts/`) and assertion-based benchmarks (`evals/evals.json`) before it ships. The skill-creator framework's eval loop (draft → test → review → improve → repeat) is the standard workflow for every component.

**Visual QA as a gate.** No skill is considered complete until its outputs have passed both automated QA checks and human visual review. For image generation and layout skills, this means rendering to images and inspecting every slide.

**Contract-first integration.** The JSON data contracts above are defined before implementation begins. Skills are developed against the contracts, and integration testing validates that each skill produces and consumes the correct shapes.

**Documentation as a deliverable.** Every skill ships with a complete `SKILL.md`, reference docs for any non-trivial logic, and inline comments in scripts. The `docs/` directory is maintained alongside the code, not after.

---

## Compatibility

**Claude Code** — Full support. The conductor agent can orchestrate multi-skill workflows using subagents, and the eval framework runs natively.

**Claude Desktop** — Supported for single-skill invocations and for the full pipeline when skills are installed locally. The conductor adapts its execution strategy (sequential rather than parallel) based on the environment.

**Image generation backends** — Require API keys configured as environment variables or MCP server connections. The `imagegen-bridge` skill documents the setup for each supported backend.

---

## Status

This project is in the **design and planning** phase. The README you are reading is the first deliverable: a shared understanding of what we are building, how the pieces fit together, and what "done" looks like for each component.

Next steps are outlined in the roadmap below.

---

## Roadmap

| Phase | Milestone | Key Deliverables |
|-------|-----------|------------------|
| **0 — Foundation** | Data contracts & project scaffolding | JSON schemas for all contracts, project directory structure, eval prompt library (5+ talk briefs) |
| **1 — Content Core** | `narrative-architect` + `speaker-notes-writer` | Working outline generation, speaker notes, eval results |
| **2 — Visual Identity** | `slide-stylist` + `chart-renderer` | Palette derivation, layout templates, chart rendering pipeline |
| **3 — Image Pipeline** | `imagegen-bridge` | Prompt engineering layer, at least one working backend, batch generation with selection |
| **4 — Assembly** | `deck-assembler` | End-to-end `.pptx` build from all upstream outputs |
| **5 — Quality Gate** | `deck-qa` | Automated QA checks, contrast/overlap/margin enforcement |
| **6 — Orchestration** | `deck-conductor` | Full pipeline from talk brief to finished deck |
| **7 — Polish & Eval** | Integration testing at scale | 10+ end-to-end test decks, benchmark scoring, description optimisation |

---

## License

TBD — to be determined during Phase 0.
