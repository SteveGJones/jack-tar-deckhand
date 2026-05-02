# Jack-Tar — Deckhand

> *"A Jack-Tar never lets the deck go untended."*

**AI-powered skills and agents for building conference-quality presentation decks with Claude Code and Claude Desktop.**

---

## Vision

The existing `/pptx` skill produces solid slide decks, but conference-quality presentations demand more: bespoke hero imagery, data-driven infographics, speaker-ready layouts, and a visual identity that holds up on a 40-foot projector screen in front of 2,000 people. This project closes that gap.

Jack-Tar is a coordinated suite of Claude skills and orchestration agents that combine image generation models, layout intelligence, and content-authoring tools into a single end-to-end pipeline. It offers **two entry points**: the Superpower Bridge route (the default, which collaborates with `/pptx`) and the Direct route (full Jack-Tar pipeline from a brief, no `/pptx` involvement). A speaker describes their talk — through either route — and the system delivers a polished, stage-ready `.pptx`.

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

## Two routes at a glance

Jack-Tar offers two entry points: the Superpower Bridge route (default, collaborates with `/pptx`) and the Direct route (full Jack-Tar pipeline from a brief).

Both routes support 1K / 2K / 4K cloud-rendered visuals via the `jack-tar-cloud` plugin (see EPIC #58).

---

## Choosing your route

```
                   Have you already run /pptx and want to fix the deck?
                                         │
                  ┌──────────────────────┴──────────────────────┐
                 Yes                                            No
                  │                                              │
                  ▼                                              ▼
      Bridge route, review-first              Are you starting from a brief?
      ──────────────────────────                          │
      /enrich-deck output.pptx           ┌────────────────┴────────────────┐
                                       Yes,                            Yes,
                                  collaborate with                full Jack-Tar
                                      /pptx                       pipeline only
                                        │                               │
                                        ▼                               ▼
                            Bridge route (default)              Direct route
                            ──────────────────────              ────────────
                            /bridge-brief →                /jack-tar-deckhand:
                            /pptx →                          deck-conductor
                            /enrich-deck
```

### 1. Bridge from the start (default)
Speaker invokes `/bridge-brief` first; uses the brief to drive `/pptx`; then `/enrich-deck` layers visuals onto the resulting deck. Speaker collaborates with the bridge throughout — visuals are designed for, not retrofitted onto, the slides.

### 2. Bridge after a stale `/pptx` run
Speaker has already run `/pptx` and isn't satisfied with the deck. The bridge takes a **review-first approach**: assesses what's there, identifies what's salvageable vs what needs redoing, and collaborates with the speaker on whether to enrich in place or rebuild the brief and start over. This is how the bridge handles "rescue" workflows.

### 3. Jack-Tar direct route
Speaker invokes `/jack-tar-deckhand:deck-conductor` for the full Jack-Tar pipeline — brand profile, narrative architect, strategy map, full QA, no `/pptx` involvement at all. Best for speakers who want the full Jack-Tar treatment from a brief, not retrofitting onto an existing deck.

---

## Quick Start

### Bridge route (default)

```
/bridge-brief "your topic"
/pptx ...                   # use the brief to drive the upstream /pptx skill
/enrich-deck output.pptx
```

### Direct route

```
/jack-tar-deckhand:deck-conductor "your topic"
```

---

## Architecture Overview

Jack-Tar is a **5-plugin Claude Code marketplace**. The two pipelines share a set of engine plugins (image generation, SmartArt) while differing in their entry point and orchestration layer.

### Direct route

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

*Diagram labels are functional roles; mapped skill names are listed in §8 below.*

### Bridge route

```
/pptx deck ──► /bridge-brief or /enrich-deck ──► enriched .pptx
                     (collaborates with deckhand skills)
```

---

## Project Components

### 8.1 Direct-route components

| Skill | Purpose |
|-------|---------|
| `deck-conductor` | Orchestration agent — accepts talk brief, coordinates all skills |
| `narrative-architect` | Transforms brief into structured slide outline |
| `imagegen-bridge` | Routes image generation to available engine plugins |
| `slide-stylist` | Owns visual design system: palette, typography, layout templates |
| `speaker-notes-writer` | Generates timed, cued speaker notes per slide |
| `chart-renderer` | Generates publication-quality charts as slide-ready images |
| `deck-assembler` | Final composition — produces the `.pptx` |
| `deck-qa` | Automated QA: overlap, contrast, margins, text overflow, consistency |

### 8.2 Bridge-route components

| Skill | Purpose |
|-------|---------|
| `/bridge-brief` | Plan a talk and produce a brief that drives the upstream `/pptx` skill |
| `/enrich-deck` | Review-first enrichment of an existing `.pptx` — assess salvageability, collaborate on enrich-in-place vs rebuild |
| shared engines | `jack-tar-cloud`, `jack-tar-ollama`, `jack-tar-msft-smartart`, `jack-tar-custom-smartart` |

---

## Plugin Marketplace

| Plugin | Purpose | Route(s) served |
|--------|---------|-----------------|
| `jack-tar-deckhand` | Full presentation pipeline orchestrator | Direct |
| `jack-tar-superpower-bridge` | Bridge between `/pptx` and Jack-Tar engine plugins | Bridge |
| `jack-tar-ollama` | Local AI image generation (draft tier, free) | Both |
| `jack-tar-cloud` | Cloud AI image generation (production tier, 1K/2K/4K) | Both |
| `jack-tar-msft-smartart` | Editable PowerPoint SmartArt (29 layouts) | Both |
| `jack-tar-custom-smartart` | Data viz and custom graphics (SVG, Mermaid, Vega) | Both |

Plugin documentation: [`plugins/jack-tar-deckhand/CLAUDE.md`](plugins/jack-tar-deckhand/CLAUDE.md) · [`plugins/jack-tar-superpower-bridge/CLAUDE.md`](plugins/jack-tar-superpower-bridge/CLAUDE.md)

---

## Shared Data Contracts

The following contracts apply to the **direct route** pipeline. All skills communicate through well-defined JSON interfaces:

**`TalkBrief`** — Input from the user describing their presentation needs. Fields include `topic`, `audience`, `duration_minutes`, `tone`, `key_takeaways`, `branding` (optional logo, corporate colours), and `preferences` (e.g., "minimalist," "data-heavy," "image-rich").

**`DeckContext`** — The shared state object that the conductor passes between skills. Accumulates outputs as the pipeline progresses: starts with the `TalkBrief`, gains the `StyleGuide` after the stylist runs, gains the `SlideOutline` after the narrative architect runs, gains the `ImageManifest` after image generation, and so on.

**`SlideOutline`** — Array of slide objects, each with `slide_number`, `slide_type`, `headline`, `body_points`, `narrative_beat`, `visual_direction`, `data` (optional, for chart slides), and `speaker_notes`.

**`StyleGuide`** — Palette, font pairings, spacing scale, layout template assignments per slide type, and brand override tokens.

**`ImageManifest`** — Array of generated image records: `slide_number`, `file_path`, `dimensions`, `alt_text`, `source_prompt`, `model_used`, `placement_zone`.

**`QAReport`** — Array of findings: `slide_number`, `severity` (error, warning, info), `category`, `description`, `suggested_fix`.

These contracts are formally defined as JSON schemas in `src/schemas/` and validated at each handoff point.

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

- BSA v1.4.0 (33 services, 6 AI personas, 60 interactions)
- 1010 monorepo + 33 cross-plugin integration tests passing
- Bridge route shipped through v0.1.0 → v0.2.0 (`jack-tar-superpower-bridge` plugin)
- EPIC #58 (1K / 2K / 4K resolution capability) in progress — available for testing via `jack-tar-cloud`

---

## Roadmap

| Phase | Milestone | Key Deliverables |
|-------|-----------|------------------|
| **0 — Foundation** | Data contracts & project scaffolding | JSON schemas for all contracts, project directory structure, eval prompt library | Done |
| **1 — Content Core** | `narrative-architect` + `speaker-notes-writer` | Working outline generation, speaker notes, eval results | Done |
| **2 — Visual Identity** | `slide-stylist` + `chart-renderer` | Palette derivation, layout templates, chart rendering pipeline | Done |
| **3 — Image Pipeline** | `imagegen-bridge` | Prompt engineering layer, backends, batch generation with selection | Done |
| **4 — Assembly** | `deck-assembler` | End-to-end `.pptx` build from all upstream outputs | Done |
| **5 — Quality Gate** | `deck-qa` | Automated QA checks, contrast/overlap/margin enforcement | Done |
| **6 — Orchestration** | `deck-conductor` | Full pipeline from talk brief to finished deck | Done |
| **7 — Polish & Eval** | Integration testing at scale | 1010 monorepo + 33 cross-plugin tests, SmartArt intelligent graphics, pptx_native engine | Done |
| **EPIC #58** | Resolution capability | 1K / 2K / 4K cloud-rendered visuals via `jack-tar-cloud`; available both routes | In progress |
| **Bridge maturation** | `jack-tar-superpower-bridge` v1.0 | Full bridge plugin release, `/bridge-brief` and `/enrich-deck` stable | Planned |

---

## License

TBD — to be determined.
