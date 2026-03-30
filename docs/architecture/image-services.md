# Image Services -- L1 Service Document

> Generated from canonical model: `jack-tar-deckhand.json` v1.0.0
> Date: 2026-03-29
> Service ID: `image-services`
> Parent: `presentation-engineering` (L0)

---

## Mission

Generate, manipulate, and optimise visual assets from text prompts and data. Image Services is the largest L1 domain, comprising 8 skills, 1 capability, and 1 AI Persona (advisory). It handles provider discovery, intelligent routing, local and cloud image generation, chart rendering, post-processing, and advisory quality scoring.

---

## Scope

Image Services is the visual asset authority for the pipeline. It answers three questions:

1. **What providers are available?** (Image Routing & Discovery)
2. **What is the best image for each slide?** (generation skills + Image Generation Expert)
3. **Are the images production-ready?** (Image Post-Processing)

The domain owns all image generation and routing decisions within its scope. The Deck Conductor provides budget constraints and triggers draft vs production renders, but does not select providers or tune prompts -- that is Image Services' domain expertise.

---

## L2 Sub-Services

| Service ID | Name | Type | Skill | System Actor |
|---|---|---|---|---|
| `image-routing-discovery` | Image Routing & Discovery | Skill | `imagegen-bridge` | Probes all providers |
| `image-ollama-generate` | Ollama Image Generation | Skill | `ollama-generate-image` | Ollama |
| `image-ollama-icon` | Ollama Icon Generation | Skill | `ollama-generate-icon` | Ollama |
| `image-ollama-pattern` | Ollama Pattern Generation | Skill | `ollama-generate-pattern` | Ollama |
| `image-ollama-diagram` | Ollama Diagram Generation | Skill | `ollama-generate-diagram` | Ollama |
| `image-cloud-generate` | Cloud Image Generation | Skill | `cloud-generate-image` | OpenAI, Google Vertex AI, FAL.ai |
| `image-cloud-icon` | Cloud Icon Generation | Skill | `cloud-generate-icon` | Recraft, FAL.ai |
| `image-chart-renderer` | Chart Rendering | Skill | `chart-renderer` | Matplotlib |
| `image-post-processing` | Image Post-Processing | Skill | `image-processor` | -- |
| `image-generation-expert` | Image Generation Expert | AI Persona | -- (agent/advisory) | -- |

### L2 Diagram

![Image Services L2](diagrams/jack-tar-deckhand-image-services-l2.svg)

---

## Image Routing & Discovery (`imagegen-bridge`)

### Purpose

Entry point for all image generation requests. Discovers available providers at runtime, routes each request to the best model based on asset type, quality tier, and budget, and returns generated images.

### Provider Discovery

At the start of each pipeline run, the imagegen-bridge probes all potential providers:

| Provider | Detection Method | Cost | Best For |
|---|---|---|---|
| Ollama (local) | HTTP health check to localhost:11434 | Free | Fast iteration, backgrounds, patterns |
| FAL.ai | FAL_KEY env var | $0.01-$0.10/image | FLUX.2 Pro, Recraft V4 SVG, Ideogram |
| OpenAI | OPENAI_API_KEY env var | $0.009-$0.133/image | Highest quality, best text rendering |
| Google Vertex AI | GOOGLE_CLOUD_PROJECT env var | $0.02-$0.04/image | Budget workhorse, backgrounds |
| Recraft (direct) | RECRAFT_API_KEY env var | $0.04-$0.30/image | Native SVG icons (if FAL unavailable) |

### Routing Logic

The router selects providers based on asset type, available providers, quality tier (draft vs production), and remaining budget. Cost-optimisation prefers Imagen 4 Fast ($0.02/image) for backgrounds and textures, reserving GPT Image 1.5 ($0.133/image) for hero images requiring text accuracy.

### Graceful Degradation

1. Cloud preferred model unavailable: try alternative cloud provider
2. All cloud unavailable: fall back to local Ollama
3. Ollama unavailable: use placeholder images (coloured rectangles with alt text)
4. All providers unavailable: escalate to Speaker

---

## Local Generation Skills (Ollama)

Four Ollama skills handle local generation for different asset types. These are **upstream skills -- do not fork or modify them**. The imagegen-bridge handles all DeckContext integration.

| Skill | Asset Types | Models | Notes |
|---|---|---|---|
| `ollama-generate-image` | Hero images, backgrounds | z-image-turbo, flux2-klein | General-purpose raster generation |
| `ollama-generate-icon` | Icons, pictograms | z-image-turbo | Icon-specific prompt wrapping |
| `ollama-generate-pattern` | Textures, repeating patterns | z-image-turbo | Seamless tiling guidance |
| `ollama-generate-diagram` | Conceptual diagrams | flux2-klein | Honest about text quality limitations |

---

## Cloud Generation Skills

Two cloud skills handle generation via cloud APIs with provider routing:

### Cloud Image Generation (`cloud-generate-image`)

Generates images via cloud APIs with automatic provider selection:

| Provider | Model | Strengths |
|---|---|---|
| OpenAI | GPT Image 1.5 | Highest quality, best text rendering, strong prompt adherence |
| Google Vertex AI | Imagen 4 / Imagen 4 Fast | Cost-effective, good for backgrounds and textures |
| FAL.ai | FLUX.2 Pro, Ideogram 3.0 | Photorealism (FLUX.2), typography (Ideogram) |

### Cloud Icon Generation (`cloud-generate-icon`)

Generates SVG icons via Recraft V4 (native SVG output) or raster icons via cloud models. SVG output is preferred for scalability.

| Provider | Model | Output Format |
|---|---|---|
| Recraft (direct or via FAL.ai) | Recraft V4 | Native SVG |
| Cloud image providers | Various | Raster (PNG) |

---

## Chart Rendering (`chart-renderer`)

Generate publication-quality data visualisations via Matplotlib and Seaborn at 300 DPI, styled to the brand palette. Uses the Agg backend for headless rendering (no display server required). Custom `.mplstyle` files enforce brand consistency.

Supported chart types: bar, line, area, pie, donut, scatter, comparison_table, timeline, stat_card.

---

## Image Post-Processing (`image-processor`)

Background removal (rembg), resize, crop, colour correction, and file optimisation (pngquant) for generated images. Applied after generation and before assembly.

---

## Image Generation Expert (AI Persona -- Advisory)

**Persona ID:** `persona-image-generation-expert`
**Authority Model:** Invoker (acts on behalf of the calling skill, escalates to Deck Conductor)
**Confidence Threshold:** 0.7 minimum for autonomous advice

### Role

Advisory persona consulted by image generation skills for:
- Prompt engineering and prompt construction advice
- Model-specific prompt translation (prompts tuned for Ollama produce different results on GPT Image 1.5)
- Quality scoring against a 6-dimension rubric (composition, colour, clarity, relevance, technical quality, text accuracy)
- Iteration convergence guidance (accept, refine prompt, rewrite, try different model)
- Model selection advice given asset type and available providers

### Boundaries

- Never generates images directly -- only advises
- Never makes routing decisions -- the imagegen-bridge routes using the expert's advice
- Never accesses or modifies DeckContext state
- Never communicates with the Speaker directly -- all communication through the Conductor or calling skill

For the full persona specification, see [AI Persona Summaries](ai-persona-summaries.md).

---

## Data Contracts

### Consumed

| Contract | Source | Description |
|---|---|---|
| SlideOutline | Content Services (narrative-architect) | visual_direction field provides prompt context per slide |
| StyleGuide | Design Services (slide-stylist) | Palette for colour enforcement, image_style_tokens for style consistency |
| BrandProfile | Design Services (brand-manager) | approved_image_styles and prohibited_image_styles for prompt compliance |
| Budget constraints | Deck Conductor | Per-image and total budget caps |
| TalkBrief | Speaker (via Deck Conductor) | data_sources for chart rendering |

### Produced

| Contract | File | Consumers | Description |
|---|---|---|---|
| ImageManifest | `./tmp/deck/image-manifest.json` | deck-assembler | Registry of all generated images with metadata, file paths, prompts, model used |
| ChartManifest | `./tmp/deck/chart-manifest.json` | deck-assembler | Registry of all rendered charts with metadata |
| AvailableProviders | (in-memory / conversation) | Deck Conductor, generation skills | Runtime manifest of which providers are available |

---

## Key Interactions

### Inbound

| Source | Type | Data |
|---|---|---|
| Deck Conductor | invocation | SlideOutline (visual_direction), StyleGuide (palette), budget constraints |

### Outbound

| Target | Type | Data |
|---|---|---|
| Assembly & QA Services | data-provision | ImageManifest + ChartManifest consumed by deck-assembler |

### Internal Interactions

| Source | Target | Type | Description |
|---|---|---|---|
| Image Routing & Discovery | Image Generation Expert | consultation | Model selection advice |
| Image Routing & Discovery | Ollama Image Generation | invocation | Routed local generation request |
| Image Routing & Discovery | Cloud Image Generation | invocation | Routed cloud generation request |
| Ollama Image Generation | Image Generation Expert | consultation | Prompt engineering, quality scoring |
| Cloud Image Generation | Image Generation Expert | consultation | Model-specific prompt translation |
| Ollama Image Generation | Ollama | invocation | REST API inference call |
| Cloud Image Generation | OpenAI / Google / FAL.ai | invocation | Cloud API generation |
| Cloud Icon Generation | Recraft / FAL.ai | invocation | SVG icon generation |
| Chart Rendering | Matplotlib | invocation | Headless chart generation at 300 DPI |

### System Actor Dependencies

| System Actor | Type | Detection | Services |
|---|---|---|---|
| Ollama | Local runtime | HTTP health check | 4 Ollama generation skills |
| OpenAI API | Cloud API | OPENAI_API_KEY env var | Cloud Image Generation |
| Google Vertex AI | Cloud API | GOOGLE_CLOUD_PROJECT env var | Cloud Image Generation |
| FAL.ai | Cloud aggregator | FAL_KEY env var | Cloud Image Generation, Cloud Icon Generation |
| Recraft API | Cloud API | RECRAFT_API_KEY env var | Cloud Icon Generation |
| Matplotlib | Python library | Always available | Chart Rendering |

---

## Implementation Status

| Component | Skill | Source | Tests | Status |
|---|---|---|---|---|
| Image Routing & Discovery | `imagegen-bridge` | `src/image_router.py` | 35 | Done (Phase 4C) |
| Ollama Image Generation | `ollama-generate-image` | `src/generate_image.py` | -- | Upstream (do not fork) |
| Ollama Icon Generation | `ollama-generate-icon` | -- | -- | Upstream (do not fork) |
| Ollama Pattern Generation | `ollama-generate-pattern` | -- | -- | Upstream (do not fork) |
| Ollama Diagram Generation | `ollama-generate-diagram` | -- | -- | Upstream (do not fork) |
| Cloud Image Generation | `cloud-generate-image` | `src/generate_cloud_image.py` | 49 | Done (Phase 4B) |
| Cloud Icon Generation | `cloud-generate-icon` | `src/generate_cloud_icon.py` | 28 | Done (Phase 4B) |
| Chart Rendering | `chart-renderer` | `src/render_chart.py` | 15 | Done (Phase 1) |
| Image Post-Processing | `image-processor` | `src/process_image.py` | 19 | Done (Phase 4A) |
| Provider Discovery | (within imagegen-bridge) | `src/provider_discovery.py` | 24 | Done (Phase 4A) |
| Budget Tracker | (within imagegen-bridge) | `src/budget_tracker.py` | 17 | Done (Phase 4A) |
| Cache Manager | (within imagegen-bridge) | `src/cache_manager.py` | 15 | Done (Phase 4A) |
| Prompt Translator | (within imagegen-bridge) | `src/prompt_translator.py` | 20 | Done (Phase 4A) |
| Image Generation Expert | -- | -- | -- | Planned (Phase 6) |

Image Services is the most implementation-complete domain. All infrastructure (Phases 4A, 4B, 4C) is done with 260 tests passing. The Image Generation Expert AI Persona is planned for Phase 6 alongside the Deck Conductor.

---

## Related Documentation

| Document | Path |
|---|---|
| Architecture Overview | [architecture-overview.md](architecture-overview.md) |
| Service Catalogue | [service-catalogue.md](service-catalogue.md) |
| AI Persona Summaries | [ai-persona-summaries.md](ai-persona-summaries.md) |
| System Actor Registry | [system-actor-registry.md](system-actor-registry.md) |
| Data Contracts | [data-contracts.md](data-contracts.md) |
| Image Services L2 Diagram | [diagrams/jack-tar-deckhand-image-services-l2.svg](diagrams/jack-tar-deckhand-image-services-l2.svg) |
| Research #04 (Image Generation) | [../../research/04-image-generation-landscape.md](../../research/04-image-generation-landscape.md) |
| Research #05 (Ollama Integration) | [../../research/05-ollama-image-generation.md](../../research/05-ollama-image-generation.md) |
| Research #06 (Cloud Providers) | [../../research/06-cloud-image-generation.md](../../research/06-cloud-image-generation.md) |
