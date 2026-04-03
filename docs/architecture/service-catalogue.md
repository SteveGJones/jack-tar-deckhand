# Service Catalogue -- Jack-Tar Deckhand

> Generated from canonical model: `jack-tar-deckhand.json` v1.4.0
> Date: 2026-04-03

---

## Summary Table

| Service ID | Name | Level | Parent | Type | AI Persona | Skill/Capability |
|---|---|---|---|---|---|---|
| `presentation-engineering` | Presentation Engineering | L0 | -- | core | No | -- |
| `content-services` | Content Services | L1 | presentation-engineering | core | No | -- |
| `content-outline-generation` | Outline Generation | L2 | content-services | core | No | `narrative-architect` |
| `content-speaker-notes` | Speaker Notes | L2 | content-services | core | No | `speaker-notes-writer` |
| `content-smartart-selection` | SmartArt Selection | L2 | content-services | core | **Yes** | `smartart-selector` |
| `content-smartart-extraction` | SmartArt Data Extraction | L2 | content-services | core | No | `smartart-extractor` |
| `design-services` | Design Services | L1 | presentation-engineering | core | No | -- |
| `design-style-derivation` | Style Derivation | L2 | design-services | core | No | `slide-stylist` |
| `design-brand-profile-management` | Brand Profile Management | L2 | design-services | core | No | `brand-manager` |
| `design-layout-intelligence` | Layout Intelligence | L2 | design-services | core | No | `slide-stylist` (capability) |
| `image-services` | Image Services | L1 | presentation-engineering | core | No | -- |
| `image-routing-discovery` | Image Routing & Discovery | L2 | image-services | core | No | `imagegen-bridge` |
| `image-ollama-generate` | Ollama Image Generation | L2 | image-services | core | No | `ollama-generate-image` |
| `image-ollama-icon` | Ollama Icon Generation | L2 | image-services | core | No | `ollama-generate-icon` |
| `image-ollama-pattern` | Ollama Pattern Generation | L2 | image-services | core | No | `ollama-generate-pattern` |
| `image-ollama-diagram` | Ollama Diagram Generation | L2 | image-services | core | No | `ollama-generate-diagram` |
| `image-cloud-generate` | Cloud Image Generation | L2 | image-services | core | No | `cloud-generate-image` |
| `image-cloud-icon` | Cloud Icon Generation | L2 | image-services | core | No | `cloud-generate-icon` |
| `image-chart-renderer` | Chart Rendering | L2 | image-services | core | No | `chart-renderer` |
| `image-post-processing` | Image Post-Processing | L2 | image-services | core | No | `image-processor` |
| `image-generation-expert` | Image Generation Expert | L2 | image-services | core | **Yes** | -- (agent/advisory) |
| `image-image-reviewer` | Image Reviewer | L2 | image-services | core | **Yes** | -- (agent/quality) |
| `image-smartart-rendering` | SmartArt Rendering | L2 | image-services | core | No | `smartart-renderer` |
| `assembly-qa-services` | Assembly & QA Services | L1 | presentation-engineering | core | No | -- |
| `assembly-pptx-build` | PPTX Build | L2 | assembly-qa-services | core | No | `deck-assembler` |
| `assembly-visual-qa` | Visual QA | L2 | assembly-qa-services | core | No | `deck-qa` |
| `assembly-file-optimisation` | File Optimisation | L2 | assembly-qa-services | core | No | `deck-assembler` (capability) |
| `assembly-presentation-reviewer` | Presentation Reviewer | L2 | assembly-qa-services | core | **Yes** | -- (agent/advisory) |
| `deck-conductor` | Deck Conductor | L1 | presentation-engineering | core | **Yes** | -- (agent/orchestration) |

**Total services:** 29 (1 L0, 5 L1, 23 L2)
**AI Personas:** 6 (Deck Conductor, Image Generation Expert, Image Reviewer, Presentation Reviewer, Prompt Engineer, SmartArt Selector)
**Skills (L2 invocable):** 16
**Capabilities (L2 internal):** 2

---

## L0: Presentation Engineering

### `presentation-engineering` -- Presentation Engineering

| Field | Value |
|---|---|
| **Level** | L0 |
| **Parent** | -- (root) |
| **Mission** | Transform ideas into conference-quality visual presentations by orchestrating content, design, image, and assembly services. |
| **Service Type** | core |
| **Tags** | l0, orchestration, presentation |
| **AI Persona** | No |
| **Owner** | Steve Jones |

This is the root domain. All L1 services are children of this domain.

---

## L1: Deck Conductor

### `deck-conductor` -- Deck Conductor

| Field | Value |
|---|---|
| **Level** | L1 |
| **Parent** | presentation-engineering |
| **Mission** | Orchestrate the full pipeline from talk brief to finished deck. Owns the DeckContext lifecycle, sequences L1 service invocations, manages budget, and handles the QA correction loop. |
| **Service Type** | core |
| **Tags** | l1, agent, ai-persona, orchestration |
| **AI Persona** | **Yes** -- see [AI Persona Summaries](ai-persona-summaries.md) |
| **Owner** | Steve Jones |

The Deck Conductor is the only L1 service that is itself an AI Persona. It sits at the orchestration layer and invokes all other L1 service domains in dependency order.

---

## L1: Content Services

### `content-services` -- Content Services

| Field | Value |
|---|---|
| **Level** | L1 |
| **Parent** | presentation-engineering |
| **Mission** | Transform briefs and topics into structured narratives, outlines, and speaker-ready text. |
| **Service Type** | core |
| **Tags** | l1, content, narrative, reusable |
| **AI Persona** | No |
| **Owner** | Steve Jones |

### L2 Children

#### `content-outline-generation` -- Outline Generation

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | content-services |
| **Mission** | Transform a talk brief into a structured slide outline with per-slide type, headline, body points, narrative beat, and visual direction. |
| **Service Type** | core |
| **Tags** | l2, skill, narrative-architect |
| **AI Persona** | No |
| **Skill Name** | `narrative-architect` |

#### `content-speaker-notes` -- Speaker Notes

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | content-services |
| **Mission** | Generate timed, transition-cued speaker notes calibrated to talk duration and audience profile. |
| **Service Type** | core |
| **Tags** | l2, skill, speaker-notes-writer |
| **AI Persona** | No |
| **Skill Name** | `speaker-notes-writer` |

#### `content-smartart-selection` -- SmartArt Selection

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | content-services |
| **Mission** | Recommend graphic type and enrichment tier for SmartArt-candidate slides via negotiation with narrative-architect. Analyses content semantics, audience context, budget state, and adjacent slide strategies. |
| **Service Type** | core |
| **Tags** | l2, agent, ai-persona, smartart-selector |
| **AI Persona** | **Yes** -- see [AI Persona Summaries](ai-persona-summaries.md) |

#### `content-smartart-extraction` -- SmartArt Data Extraction

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | content-services |
| **Mission** | Transform approved slide content into engine-specific structured data (Mermaid syntax, Vega-Lite JSON, custom SVG data) ready for rendering by the smartart-renderer. |
| **Service Type** | core |
| **Tags** | l2, skill, smartart-extractor |
| **AI Persona** | No |
| **Skill Name** | `smartart-extractor` |

---

## L1: Design Services

### `design-services` -- Design Services

| Field | Value |
|---|---|
| **Level** | L1 |
| **Parent** | presentation-engineering |
| **Mission** | Derive and enforce visual identity: palettes, typography, layout rules, and brand consistency. |
| **Service Type** | core |
| **Tags** | l1, design, brand, reusable |
| **AI Persona** | No |
| **Owner** | Steve Jones |

### L2 Children

#### `design-style-derivation` -- Style Derivation

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | design-services |
| **Mission** | Derive a complete StyleGuide from a TalkBrief and BrandProfile. When no BrandProfile is provided, derive minimal brand defaults. Proposes design options within brand compliance mode (strict or guided) and collaborates with the Speaker to select a direction. Produces palette, typography, layout templates, and image style tokens. |
| **Service Type** | core |
| **Tags** | l2, skill, slide-stylist |
| **AI Persona** | No |
| **Skill Name** | `slide-stylist` |

#### `design-brand-profile-management` -- Brand Profile Management

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | design-services |
| **Mission** | Create, store, and serve reusable BrandProfile artefacts from multiple input formats (brand guidelines PDF, corporate .pptx template, logo image, manual hex/font input, briefing document). BrandProfiles persist beyond a single deck session and are shared across multiple presentations for the same brand. |
| **Service Type** | core |
| **Tags** | l2, skill, brand-manager |
| **AI Persona** | No |
| **Skill Name** | `brand-manager` |

#### `design-layout-intelligence` -- Layout Intelligence

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | design-services |
| **Mission** | Apply machine-checkable layout rules: 12-column grid system, content zones, safe margins, visual hierarchy per slide type. |
| **Service Type** | core |
| **Tags** | l2, capability, slide-stylist |
| **AI Persona** | No |
| **Capability of** | `slide-stylist` |

---

## L1: Image Services

### `image-services` -- Image Services

| Field | Value |
|---|---|
| **Level** | L1 |
| **Parent** | presentation-engineering |
| **Mission** | Generate, manipulate, and optimise visual assets from text prompts and data. |
| **Service Type** | core |
| **Tags** | l1, image, generation, reusable |
| **AI Persona** | No |
| **Owner** | Steve Jones |

### L2 Children

#### `image-routing-discovery` -- Image Routing & Discovery

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | image-services |
| **Mission** | Entry point for all image generation. Discovers available providers at runtime, routes to best model per asset type and budget, returns generated image. |
| **Service Type** | core |
| **Tags** | l2, skill, imagegen-bridge, routing |
| **AI Persona** | No |
| **Skill Name** | `imagegen-bridge` |

#### `image-ollama-generate` -- Ollama Image Generation

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | image-services |
| **Mission** | Generate raster images via local Ollama models (z-image-turbo, flux2-klein). |
| **Service Type** | core |
| **Tags** | l2, skill, ollama-generate-image, local |
| **AI Persona** | No |
| **Skill Name** | `ollama-generate-image` |

#### `image-ollama-icon` -- Ollama Icon Generation

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | image-services |
| **Mission** | Generate icon and pictogram images via Ollama with icon-specific prompt wrapping. |
| **Service Type** | core |
| **Tags** | l2, skill, ollama-generate-icon, local |
| **AI Persona** | No |
| **Skill Name** | `ollama-generate-icon` |

#### `image-ollama-pattern` -- Ollama Pattern Generation

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | image-services |
| **Mission** | Generate seamless textures and repeating patterns via Ollama. |
| **Service Type** | core |
| **Tags** | l2, skill, ollama-generate-pattern, local |
| **AI Persona** | No |
| **Skill Name** | `ollama-generate-pattern` |

#### `image-ollama-diagram` -- Ollama Diagram Generation

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | image-services |
| **Mission** | Generate illustrative diagrams via Ollama. Honest about text quality limitations -- use for conceptual visuals, not precise technical diagrams. |
| **Service Type** | core |
| **Tags** | l2, skill, ollama-generate-diagram, local |
| **AI Persona** | No |
| **Skill Name** | `ollama-generate-diagram` |

#### `image-cloud-generate` -- Cloud Image Generation

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | image-services |
| **Mission** | Generate images via cloud APIs (OpenAI GPT Image 1.5, Google Imagen 4, FLUX.2 Pro) with provider routing based on availability and asset type. |
| **Service Type** | core |
| **Tags** | l2, skill, cloud-generate-image, cloud |
| **AI Persona** | No |
| **Skill Name** | `cloud-generate-image` |

#### `image-cloud-icon` -- Cloud Icon Generation

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | image-services |
| **Mission** | Generate SVG icons via Recraft V4 or raster icons via cloud models. SVG output is preferred for scalability. |
| **Service Type** | core |
| **Tags** | l2, skill, cloud-generate-icon, cloud, svg |
| **AI Persona** | No |
| **Skill Name** | `cloud-generate-icon` |

#### `image-chart-renderer` -- Chart Rendering

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | image-services |
| **Mission** | Generate publication-quality data visualisations via Matplotlib and Seaborn at 300 DPI, styled to the brand palette. |
| **Service Type** | core |
| **Tags** | l2, skill, chart-renderer, data-viz |
| **AI Persona** | No |
| **Skill Name** | `chart-renderer` |

#### `image-post-processing` -- Image Post-Processing

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | image-services |
| **Mission** | Background removal (rembg), resize, crop, colour correction, and file optimisation (pngquant) for generated images. |
| **Service Type** | core |
| **Tags** | l2, skill, image-processor |
| **AI Persona** | No |
| **Skill Name** | `image-processor` |

#### `image-generation-expert` -- Image Generation Expert

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | image-services |
| **Mission** | Advisory AI Persona for prompt engineering, model-specific translation, image quality scoring, and iteration convergence guidance. |
| **Service Type** | core |
| **Tags** | l2, agent, ai-persona, advisory |
| **AI Persona** | **Yes** -- see [AI Persona Summaries](ai-persona-summaries.md) |

#### `image-image-reviewer` -- Image Reviewer

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | image-services |
| **Mission** | Quality assurance AI Persona for image review, aesthetic validation, brand alignment, and production readiness assessment across all rendering strategies. |
| **Service Type** | core |
| **Tags** | l2, agent, ai-persona, quality |
| **AI Persona** | **Yes** -- see [AI Persona Summaries](ai-persona-summaries.md) |

#### `image-smartart-rendering` -- SmartArt Rendering

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | image-services |
| **Mission** | Render SmartArtSpec through three engines (Mermaid CLI, Vega-Lite CLI, Custom SVG) with draft-phase comparator and optional AI enrichment compositing (T0-T3). |
| **Service Type** | core |
| **Tags** | l2, skill, smartart-renderer, data-viz |
| **AI Persona** | No |
| **Skill Name** | `smartart-renderer` |

---

## L1: Assembly & QA Services

### `assembly-qa-services` -- Assembly & QA Services

| Field | Value |
|---|---|
| **Level** | L1 |
| **Parent** | presentation-engineering |
| **Mission** | Compose content and visual assets into finished, validated presentation files. |
| **Service Type** | core |
| **Tags** | l1, assembly, qa, pptx |
| **AI Persona** | No |
| **Owner** | Steve Jones |

### L2 Children

#### `assembly-pptx-build` -- PPTX Build

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | assembly-qa-services |
| **Mission** | Compose outline, style guide, image manifest, and speaker notes into a .pptx file via PptxGenJS. |
| **Service Type** | core |
| **Tags** | l2, skill, deck-assembler |
| **AI Persona** | No |
| **Skill Name** | `deck-assembler` |

#### `assembly-visual-qa` -- Visual QA

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | assembly-qa-services |
| **Mission** | Run 30 automated anti-pattern checks: contrast validation, margin enforcement, font size compliance, consistency audit, image quality thresholds, element alignment, grid reading order, label text fit. |
| **Service Type** | core |
| **Tags** | l2, skill, deck-qa, automated |
| **AI Persona** | No |
| **Skill Name** | `deck-qa` |

#### `assembly-file-optimisation` -- File Optimisation

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | assembly-qa-services |
| **Mission** | Image compression, font subsetting, metadata stripping, and file size management for the assembled .pptx. |
| **Service Type** | core |
| **Tags** | l2, capability, deck-assembler |
| **AI Persona** | No |
| **Capability of** | `deck-assembler` |

#### `assembly-presentation-reviewer` -- Presentation Reviewer

| Field | Value |
|---|---|
| **Level** | L2 |
| **Parent** | assembly-qa-services |
| **Mission** | Review assembled decks against conference presentation best practices: narrative coherence, visual storytelling, pacing, speaker notes quality, audience appropriateness. |
| **Service Type** | core |
| **Tags** | l2, agent, ai-persona, advisory, craft-review |
| **AI Persona** | **Yes** -- see [AI Persona Summaries](ai-persona-summaries.md) |

---

## Service Counts by Level

| Level | Count | Description |
|---|---|---|
| L0 | 1 | Root domain |
| L1 | 5 | Service domains (Content, Design, Image, Assembly & QA, Deck Conductor) |
| L2 | 23 | Skills (16), Capabilities (2), AI Persona Agents (5) |
| **Total** | **29** | |

## Service Counts by Tag Type

| Tag | Count | Services |
|---|---|---|
| `skill` | 16 | Invocable L2 services that map to Claude Code skills |
| `capability` | 2 | Internal capabilities of a parent skill (not independently invocable) |
| `agent` / `ai-persona` | 6 | AI Personas with authority models and scope boundaries |
| `local` | 4 | Services that use local Ollama for inference |
| `cloud` | 3 | Services that use cloud APIs for generation |
| `reusable` | 3 | L1 domains marked as reusable across different orchestrators |
