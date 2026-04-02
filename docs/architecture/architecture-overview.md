# Architecture Overview -- Jack-Tar Deckhand

> Generated from canonical model: `jack-tar-deckhand.json` v1.1.0
> Date: 2026-03-29
> Status: Draft -- pre-implementation review document

---

## What This System Is

Jack-Tar Deckhand is an AI-First Business Service Architecture for a **Claude Code skill suite** that generates conference-quality PowerPoint presentations. A speaker provides a talk brief (topic, audience, duration, tone) and the system produces a complete `.pptx` file with structured narrative, branded visuals, AI-generated images, data charts, and timed speaker notes.

The system is designed as a set of **independent, reusable service domains** orchestrated by an AI Persona called the Deck Conductor. Each domain is implemented as one or more Claude Code skills that can be invoked independently or as part of the full pipeline.

**Key characteristics:**
- Runs entirely within Claude Code (no external server or database)
- State persisted as JSON files on the local filesystem (`./tmp/deck/`)
- Image generation via local Ollama and/or cloud APIs (OpenAI, Google, FAL.ai, Recraft)
- Graceful degradation when providers are unavailable
- Budget-aware cloud API usage with Speaker approval gates

---

## Service Hierarchy

The architecture follows a three-level hierarchy: L0 (root domain), L1 (service domains), L2 (skills and capabilities).

```
L0  Presentation Engineering
    |
    +-- L1  Deck Conductor  [AI Persona - Orchestrator]
    |
    +-- L1  Design Services
    |   +-- L2  Style Derivation          [skill: slide-stylist]
    |   +-- L2  Brand Profile Management  [skill: brand-manager]
    |   +-- L2  Layout Intelligence       [capability: slide-stylist]
    |
    +-- L1  Content Services
    |   +-- L2  Outline Generation        [skill: narrative-architect]
    |   +-- L2  Speaker Notes             [skill: speaker-notes-writer]
    |
    +-- L1  Image Services
    |   +-- L2  Image Routing & Discovery     [skill: imagegen-bridge]
    |   +-- L2  Slide Prompt Composition      [skill: slide-prompt-composer]
    |   +-- L2  Ollama Image Generation       [skill: ollama-generate-image]
    |   +-- L2  Ollama Icon Generation        [skill: ollama-generate-icon]
    |   +-- L2  Ollama Pattern Generation     [skill: ollama-generate-pattern]
    |   +-- L2  Ollama Diagram Generation     [skill: ollama-generate-diagram]
    |   +-- L2  Cloud Image Generation        [skill: cloud-generate-image]
    |   +-- L2  Cloud Icon Generation         [skill: cloud-generate-icon]
    |   +-- L2  Chart Rendering               [skill: chart-renderer]
    |   +-- L2  Image Post-Processing         [skill: image-processor]
    |   +-- L2  Keynote Rendering             [capability: render funnel]
    |   +-- L2  Image Generation Expert       [AI Persona - Advisory]
    |   +-- L2  Image Reviewer                [AI Persona - Quality]
    |   +-- L2  Prompt Engineer               [AI Persona - Prompt Engineering]
    |
    +-- L1  Assembly & QA Services
        +-- L2  PPTX Build               [skill: deck-assembler]
        +-- L2  Visual QA                 [skill: deck-qa]
        +-- L2  File Optimisation         [capability: deck-assembler]
        +-- L2  Presentation Reviewer     [AI Persona - Advisory]
```

**Totals:** 1 L0, 5 L1, 23 L2 (15 skills, 3 capabilities, 5 AI Personas)

### Architecture Diagrams

![Presentation Engineering L1 — Enterprise View](diagrams/jack-tar-deckhand-presentation-engineering-l1.svg)

Drill-down diagrams for each L1 domain:

- [Content Services L2](diagrams/jack-tar-deckhand-content-services-l2.svg)
- [Design Services L2](diagrams/jack-tar-deckhand-design-services-l2.svg)
- [Image Services L2](diagrams/jack-tar-deckhand-image-services-l2.svg)
- [Assembly & QA Services L2](diagrams/jack-tar-deckhand-assembly-qa-services-l2.svg)

---

## The Five AI Personas

### 1. Deck Conductor (L1 -- Orchestrator)

**Authority:** Hybrid (autonomous above 0.8 confidence, escalates to Speaker below)

The top-level orchestration agent. It receives the talk brief, sequences all L1 service invocations, maintains pipeline state, and manages the draft/production lifecycle. During early drafts, it may use Ollama for layout testing; during later drafts, it uses the target cloud provider at reduced quality so prompt refinement happens against the actual model that will produce the final images. When the Speaker approves the draft, it triggers a production render at full quality. It tracks cumulative cost across all cycles, handles the QA correction loop, and never generates content directly -- it always delegates to the appropriate service domain.

### 2. Image Generation Expert (L2 -- Advisory)

**Authority:** Invoker (acts on behalf of the calling skill, escalates to Conductor)

An advisory persona consulted by image generation skills for prompt engineering, model-specific prompt translation, quality scoring against a 6-dimension rubric (composition, colour, clarity, relevance, technical quality, text accuracy), and iteration convergence guidance. It never generates images directly.

### 3. Prompt Engineer (L2 -- Prompt Engineering)

**Authority:** Invoker (acts on behalf of the calling skill, escalates to Conductor)

Receives structured briefs and produces creative image generation prompts. Dispatched at Haiku by default, escalated to Sonnet when quality doesn't converge.

### 4. Presentation Reviewer (L2 -- Advisory)

**Authority:** Invoker (acts on behalf of the Conductor, escalates to Conductor)

An advisory persona that reviews assembled decks against conference presentation best practices. It assesses narrative coherence, visual storytelling, pacing, speaker notes quality, and audience appropriateness. It produces structured recommendations but never modifies the deck directly.

### 5. Image Reviewer (L2 -- Quality)

**Authority:** Invoker (acts on behalf of the calling skill, escalates to Conductor)

Visual quality gate for generated images. Dispatched per image, returns pass/refine verdict. Haiku default, Sonnet escalation.

---

## Pipeline Execution Flow

The pipeline operates in two phases: **Draft** and **Production**. The Speaker iterates through multiple draft cycles to refine content, layout, narrative, and image prompts before committing to a full-quality production render.

### Draft Phase (iterative)

Each draft cycle runs the full pipeline to produce a reviewable deck. The Speaker iterates on narrative, layout, slide structure, and visual direction across multiple cycles:

- **Design + Content**: Run at full quality (LLM text generation, no cost difference between draft and production). The brand-manager runs first to obtain or create a BrandProfile, then the slide-stylist derives the StyleGuide from it
- **Strategy Map**: The slide prompt composer classifies each slide's rendering strategy (full_render, background, backdrop, pragmatic_composition, or composed), the prompt engineer generates prompts, and the Speaker approves
- **Image**: Uses draft-quality rendering — Ollama for structural placeholders, or cloud providers at reduced size/quality for prompt refinement
- **Assembly + QA + Review**: Build and review the draft deck

The Speaker reviews the draft, gives feedback (adjust narrative, change visual direction, reorder slides, refine prompts), and the Conductor re-runs the affected parts of the pipeline. This cycle repeats until the Speaker approves the draft.

**Important**: Image prompts are model-specific. A prompt tuned for Ollama's flux2-klein will produce very different results on GPT Image 1.5 or Imagen 4. Ollama drafts are useful for testing composition and layout placement, but when the Speaker is refining visual direction for cloud-rendered images, the draft cycle should use the target cloud provider at a reduced quality tier (smaller size, lower resolution) rather than Ollama. The Image Generation Expert persona handles model-specific prompt translation when switching between providers.

### Production Phase (single pass, full quality)

Once the Speaker approves the draft:

1. The Conductor re-renders all images at full quality and full resolution using the approved providers
2. Assembly rebuilds the deck with production images
3. Final QA and Presentation Review run
4. Finished deck is delivered

**The production budget covers full-quality renders only.** Draft cycles with Ollama are free; draft cycles with cloud providers at reduced quality are cheaper but not zero. The Conductor tracks cumulative spend across all cycles.

![Pipeline Execution Flow](diagrams/jack-tar-deckhand-pipeline-flow.svg)

### Step Dependencies

| Step | Requires | Produces |
|---|---|---|
| Brand Profile | TalkBrief, brand assets (logo, PDF, .pptx template, hex/font input) | BrandProfile |
| Design | TalkBrief, BrandProfile | StyleGuide |
| Content | TalkBrief, StyleGuide | SlideOutline, SpeakerNotes |
| Strategy Map | SlideOutline, StyleGuide | RenderStrategy per slide, image prompts (Speaker approved) |
| Image (draft) | SlideOutline, StyleGuide, AvailableProviders, RenderStrategy | ImageManifest (low-res) |
| Image (production) | SlideOutline, StyleGuide, AvailableProviders, RenderStrategy, Speaker approval | ImageManifest (full quality) |
| Assembly | SlideOutline, StyleGuide, ImageManifest, ChartManifest, SpeakerNotes | .pptx |
| QA | .pptx | QAReport |
| Review | .pptx, SlideOutline, StyleGuide, SpeakerNotes, TalkBrief | Structured review |

---

## System Actors and Provider Discovery

The architecture depends on 8 system actors:

| Actor | Type | Purpose | Detection |
|---|---|---|---|
| **Ollama** | Local runtime | Free image generation (z-image-turbo, flux2-klein) | HTTP health check to localhost:11434 |
| **OpenAI API** | Cloud API | GPT Image 1.5 (highest quality) | OPENAI_API_KEY env var |
| **Google Vertex AI** | Cloud API | Imagen 4 (budget workhorse) | GOOGLE_CLOUD_PROJECT env var |
| **FAL.ai** | Cloud aggregator | FLUX.2 Pro, Recraft V4, Ideogram 3.0 | FAL_KEY env var |
| **Recraft API** | Cloud API | Native SVG icon generation | RECRAFT_API_KEY env var |
| **PptxGenJS** | JS library | .pptx file assembly | Always available (npm) |
| **Matplotlib** | Python library | Chart rendering at 300 DPI | Always available (pip) |
| **Filesystem** | Local storage | DeckContext state (./tmp/deck/) | Always available |

### Provider Discovery

At the start of each pipeline run, the `imagegen-bridge` probes all providers and builds an `AvailableProviders` manifest. The Deck Conductor confirms available capabilities with the Speaker before proceeding. The system operates on a "use what's available" principle -- it works with Ollama alone, with cloud APIs alone, or with any combination.

---

## Key Design Principles

### 1. Reusability

L1 service domains (Content, Design, Image, Assembly) are designed as independent, reusable domains. They can be orchestrated by the Deck Conductor for full pipeline runs, or invoked individually for targeted tasks. Each L2 skill reads only the DeckContext files it needs.

### 2. Domain Independence

Each service domain owns its decisions within its scope. The slide-stylist owns design decisions. The narrative-architect owns structural decisions. The imagegen-bridge owns routing decisions. The Deck Conductor orchestrates but does not override domain expertise.

### 3. Graceful Degradation

The system degrades gracefully when providers are unavailable:
- **Cloud preferred model** unavailable: try alternative cloud provider
- **All cloud** unavailable: fall back to local Ollama
- **Ollama** unavailable: use placeholder images (coloured rectangles with alt text)
- **All providers** unavailable: escalate to Speaker

### 4. Budget Awareness

The Deck Conductor tracks cumulative cloud API spend across all cycles — both draft and production. Ollama drafts are free, but cloud provider drafts at reduced quality still cost money. The budget cap declared by the Speaker covers the full session (drafts + production). Cost-optimisation routing prefers Imagen 4 Fast ($0.02/image) for backgrounds and textures, reserving GPT Image 1.5 ($0.133/image) for hero images requiring text accuracy. The Conductor reports running cost to the Speaker at each review point.

### 5. Draft-First Iteration

Decks are built iteratively, not in a single pass. The Conductor manages a draft/production lifecycle where the Speaker refines content, layout, and visual direction across multiple draft cycles before committing to a full-quality production render. Early drafts may use Ollama for layout and composition testing; later drafts use the target cloud provider at reduced quality for prompt refinement (since prompts are model-specific and don't transfer cleanly between providers). The DeckContext tracks which phase the deck is in, cumulative cost, and which slides have been approved.

### 6. Filesystem as State

All shared state is persisted as JSON files in `./tmp/deck/`. This design follows from the constraint that Claude Code skills have no persistent process, no database, and no in-memory state between invocations. Files on disk are the source of truth; conversation context is a convenience cache.

### 7. Correction Loops with Bounds

The QA correction loop is bounded at 2 iterations. After 2 failed QA cycles, the Deck Conductor escalates to the Speaker rather than looping indefinitely. The Presentation Reviewer's feedback goes to the Speaker for decision -- it does not trigger automatic correction.

### 8. Separation of Automated and Human-Judgement QA

The Visual QA (deck-qa) runs 27 automated, machine-checkable anti-pattern checks (contrast, margins, overflow, consistency, element layout, vision confidence). The Presentation Reviewer applies human-judgement-level assessment (narrative coherence, visual storytelling, pacing). These are separate steps with different purposes and different feedback paths.

### 9. Three-Stage Render Funnel

Iteration happens at the cheapest stages (Ollama free, cloud low-tier cheap). Production renders use proven prompts only.

### 10. Five Rendering Strategies

The pipeline supports five rendering strategies, each serving a distinct use case. Strategy selection is per-slide, recorded in the StrategyMap, and can be overridden by the Speaker.

| Strategy | Description | Best For |
|---|---|---|
| `full_render` | Entire slide is a single AI-generated image. No PptxGenJS text boxes. Speaker notes carry the delivery. | Title cards, section dividers, dramatic visual moments |
| `background` | AI generates an atmospheric/mood background image. Text goes in one of 5 predefined template zones with a semi-transparent overlay for readability. The image does not need to "know" where text goes. | Conceptual/emotional slides with bullet text |
| `backdrop` | AI generates a structured scene with figurative visual elements. A vision model (Claude vision) analyses the generated image to detect where those elements actually landed. The assembler places PptxGenJS text boxes at the detected positions with small semi-transparent backing pills. | Structured scenes with labelled elements (annotated processes, network diagrams) |
| `pragmatic_composition` | Individual element images are generated separately, then placed at exact pixel positions by the assembler on top of an atmospheric background image. Text labels are placed at predetermined positions adjacent to each element. No vision analysis needed -- positions are deterministic. | Precise grids/flows with multiple distinct items, feature showcases |
| `composed` | Standard PptxGenJS assembly. Shapes, text boxes, optional images placed programmatically. | Diagrams, data charts, code slides, text-heavy content |

#### backGROUND Template Zones

The `background` strategy supports 5 template zones, selected per-slide in the StrategyMap via the `backdrop_variant` field. This gives visual rhythm across background slides without changing the fundamental approach.

| Template | Overlay Position | Best For |
|---|---|---|
| `left_panel` | Left 40%, full height | Dense bullets (default) |
| `right_panel` | Right 40%, full height | Visual variety, image dominates left |
| `bottom_bar` | Bottom 30%, full width | Short text, image dominates |
| `top_band` | Top 25%, full width | Headline-heavy slides |
| `center_float` | Centered box, generous padding | Sparse text, image wraps |

#### backDROP Vision Analysis

Standard image generation models (FLUX, z-image-turbo, GPT-Image, Nanobanana) do not reliably follow precise spatial positioning instructions. They can do broad composition ("three things spread across the image") but not coordinate-level precision. The `backdrop` strategy solves this by using vision post-analysis to detect where elements actually landed, then placing text at the detected positions. If vision analysis fails or returns low confidence, the assembler falls back to prescribed positions from `element_layout`.

#### Pragmatic Composition Element Assembly

The `pragmatic_composition` strategy avoids the position detection problem entirely by generating elements individually and placing them at exact coordinates. Each slide produces 1 background image plus N element images (maximum 5 elements per slide). A shared prompt prefix with palette and style tokens maintains visual consistency across elements.

#### Strategy Selection Guide

| Slide Content | Best Strategy | Rationale |
|---|---|---|
| Dramatic visual moment, no text needed | `full_render` | Maximum visual impact |
| Conceptual/emotional with bullet text | `background` | Mood image + readable text zones |
| Structured scene with labelled elements | `backdrop` | Vision-detected element positioning |
| Precise grid/flow with multiple distinct items | `pragmatic_composition` | Deterministic positioning, style control |
| Diagrams, charts, data, code | `composed` | Programmatic precision |

#### Backward Compatibility

The original `backdrop_render` strategy value is retained in the StrategyMap schema for backward compatibility. Existing outlines that use `backdrop_render` map to the `background` strategy with the `left_panel` template zone. New slides should use `background` or `backdrop` explicitly.

---

## Human Actors

| Actor | Role | Relationship |
|---|---|---|
| **Speaker** | Primary user | Provides TalkBrief, reviews BrandProfile, makes creative decisions, approves budget, receives finished deck |
| **Reviewer** | Optional human reviewer | Reviews QAReport and Presentation Review output for content accuracy and brand compliance |

---

## Related Documentation

### L1 Service Documents

| Document | Path | Description |
|---|---|---|
| Design Services | [design-services.md](design-services.md) | Brand management, style derivation, layout intelligence, collaborative design workflow |
| Content Services | [content-services.md](content-services.md) | Outline generation, speaker notes, narrative architecture |
| Image Services | [image-services.md](image-services.md) | Provider discovery, routing, local/cloud generation, chart rendering, advisory persona |
| Assembly & QA Services | [assembly-qa-services.md](assembly-qa-services.md) | PPTX build, visual QA, file optimisation, presentation review |

### Reference Documents

| Document | Path | Description |
|---|---|---|
| Service Catalogue | [service-catalogue.md](service-catalogue.md) | Full listing of all 28 services with hierarchy |
| AI Persona Summaries | [ai-persona-summaries.md](ai-persona-summaries.md) | Detailed persona specifications |
| Interaction Matrix | [interaction-matrix.md](interaction-matrix.md) | All 31 interactions between entities |
| System Actor Registry | [system-actor-registry.md](system-actor-registry.md) | External systems, configuration, discovery |
| Data Contracts | [data-contracts.md](data-contracts.md) | All 11 data contracts with schemas |
| Canonical Model | [../../.bsa/models/jack-tar-deckhand.json](../../.bsa/models/jack-tar-deckhand.json) | Machine-readable source of truth |
| DeckContext Research | [../../research/12-deckcontext-state-management.md](../../research/12-deckcontext-state-management.md) | Full JSON schemas and state management design |
