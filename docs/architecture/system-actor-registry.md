# System Actor Registry -- Jack-Tar Deckhand

> Generated from canonical model: `jack-tar-deckhand.json` v1.0.0
> Date: 2026-03-28

This document catalogues all system actors (external systems, APIs, libraries, and infrastructure) that the Jack-Tar Deckhand architecture depends on. For each actor, it documents what services use it, how to configure it, and how the imagegen-bridge discovers its availability at runtime.

---

## Summary Table

| Actor ID | Name | Type | Services | Detection |
|---|---|---|---|---|
| `sys-ollama` | Ollama | Local inference runtime | 4 Ollama generation skills | HTTP health check |
| `sys-openai` | OpenAI API | Cloud image generation API | Cloud Image Generation | Env var check |
| `sys-google-vertex` | Google Vertex AI | Cloud image generation API | Cloud Image Generation | Env var check |
| `sys-fal` | FAL.ai | Cloud model aggregator API | Cloud Image Generation, Cloud Icon Generation | Env var check |
| `sys-recraft` | Recraft API | Cloud SVG generation API | Cloud Icon Generation | Env var check |
| `sys-pptxgenjs` | PptxGenJS | JavaScript library | PPTX Build | Always available (npm) |
| `sys-matplotlib` | Matplotlib | Python library | Chart Rendering | Always available (pip) |
| `sys-filesystem` | Filesystem | Local storage | Deck Conductor, PPTX Build | Always available |
| `actor-speaker` | Speaker | Human actor | Deck Conductor, Brand Profile Management, Presentation Engineering | N/A (human) |

---

## 1. Ollama

**Actor ID:** `sys-ollama`
**Type:** Local inference runtime

### Description

Local AI model server for image generation. Provides z-image-turbo (fast photorealism) and flux2-klein (precision/text). Free, sequential generation only. Requires local installation and sufficient hardware.

### Services That Use It

| Service | Relationship | Description |
|---|---|---|
| `image-ollama-generate` (Ollama Image Generation) | provides | Inference endpoint for raster image generation |
| `image-ollama-icon` (Ollama Icon Generation) | provides | Inference endpoint for icon generation |
| `image-ollama-pattern` (Ollama Pattern Generation) | provides | Inference endpoint for pattern generation |
| `image-ollama-diagram` (Ollama Diagram Generation) | provides | Inference endpoint for diagram generation |

### Configuration Requirements

| Requirement | Details |
|---|---|
| **Installation** | Ollama must be installed locally (`brew install ollama` on macOS or see ollama.com) |
| **Models** | At minimum: `ollama pull x/z-image-turbo` and `ollama pull x/flux2-klein` |
| **Hardware** | Sufficient GPU/RAM for local inference (minimum 8GB RAM recommended) |
| **Startup** | Ollama server must be running: `ollama serve` or the Ollama desktop application |
| **Env Vars** | None required (uses default localhost:11434) |

### Availability Detection

The imagegen-bridge discovers Ollama by sending an **HTTP health check** to `localhost:11434`. If Ollama is running, it responds with a 200 status. The bridge then queries available models via the Ollama API to confirm that the required image generation models are pulled.

**Detection sequence:**
1. HTTP GET to `http://localhost:11434/` -- checks server is running
2. HTTP GET to `http://localhost:11434/api/tags` -- lists available models
3. Filter for image generation models (z-image-turbo, flux2-klein)
4. Report available local generation capabilities

**Fallback:** If Ollama is not running or required models are not available, local image generation is unavailable. The bridge falls back to cloud providers if any are configured.

---

## 2. OpenAI API

**Actor ID:** `sys-openai`
**Type:** Cloud image generation API

### Description

GPT Image 1.5 -- highest quality general-purpose image generation. Best text rendering, strong prompt adherence. $0.009-$0.133/image depending on quality tier. Requires OPENAI_API_KEY.

### Services That Use It

| Service | Relationship | Description |
|---|---|---|
| `image-cloud-generate` (Cloud Image Generation) | provides | REST API for image generation |

### Configuration Requirements

| Requirement | Details |
|---|---|
| **Env Var** | `OPENAI_API_KEY` -- API key from platform.openai.com |
| **Account** | OpenAI account with API access and billing enabled |
| **Rate Limits** | Subject to OpenAI tier-based rate limits |
| **Cost** | $0.009/image (low quality) to $0.133/image (high quality) |

### Availability Detection

The imagegen-bridge checks for the presence of the `OPENAI_API_KEY` environment variable.

**Detection sequence:**
1. Check if `OPENAI_API_KEY` environment variable is set and non-empty
2. If present, mark OpenAI as available for cloud generation
3. No connectivity test at discovery time (deferred to first generation request)

---

## 3. Google Vertex AI

**Actor ID:** `sys-google-vertex`
**Type:** Cloud image generation API

### Description

Imagen 4 and Gemini Flash -- cost-effective image generation. Imagen 4 Fast at $0.02/image is the budget workhorse for backgrounds and textures. Requires GOOGLE_CLOUD_PROJECT and service account.

### Services That Use It

| Service | Relationship | Description |
|---|---|---|
| `image-cloud-generate` (Cloud Image Generation) | provides | Vertex AI predict endpoint for image generation |

### Configuration Requirements

| Requirement | Details |
|---|---|
| **Env Var** | `GOOGLE_CLOUD_PROJECT` -- GCP project ID with Vertex AI enabled |
| **Auth** | Service account credentials or Application Default Credentials (ADC) |
| **APIs Enabled** | Vertex AI API must be enabled in the GCP project |
| **Cost** | Imagen 4 Fast: ~$0.02/image; Imagen 4: ~$0.04/image |

### Availability Detection

The imagegen-bridge checks for the presence of the `GOOGLE_CLOUD_PROJECT` environment variable.

**Detection sequence:**
1. Check if `GOOGLE_CLOUD_PROJECT` environment variable is set and non-empty
2. If present, mark Google Vertex AI as available for cloud generation
3. Authentication is verified at first generation request via ADC or service account

---

## 4. FAL.ai

**Actor ID:** `sys-fal`
**Type:** Cloud model aggregator API

### Description

Unified access to 600+ models including FLUX.2 Pro (photorealism), Recraft V4 (SVG icons), and Ideogram 3.0 (typography). Single API key. Recommended aggregation layer. Requires FAL_KEY.

### Services That Use It

| Service | Relationship | Description |
|---|---|---|
| `image-cloud-generate` (Cloud Image Generation) | provides | Aggregated API for FLUX.2 and Ideogram models |
| `image-cloud-icon` (Cloud Icon Generation) | provides | Aggregated API for Recraft V4 SVG generation |

### Configuration Requirements

| Requirement | Details |
|---|---|
| **Env Var** | `FAL_KEY` -- API key from fal.ai dashboard |
| **Account** | FAL.ai account with billing enabled |
| **Models** | Access to FLUX.2 Pro, Recraft V4, Ideogram 3.0 (available on all plans) |
| **Cost** | Varies by model; typically $0.01-$0.10/image |

### Availability Detection

The imagegen-bridge checks for the presence of the `FAL_KEY` environment variable.

**Detection sequence:**
1. Check if `FAL_KEY` environment variable is set and non-empty
2. If present, mark FAL.ai as available for cloud generation and SVG icon generation
3. FAL.ai provides access to multiple models through a single key, so one check covers FLUX.2, Recraft V4, and Ideogram

---

## 5. Recraft API

**Actor ID:** `sys-recraft`
**Type:** Cloud SVG generation API

### Description

Recraft V4 -- the only AI model generating production-quality native SVG. Essential for scalable icons and brand assets. $0.04-$0.30/image. Requires RECRAFT_API_KEY. Also accessible via FAL.ai.

### Services That Use It

| Service | Relationship | Description |
|---|---|---|
| `image-cloud-icon` (Cloud Icon Generation) | provides | Direct API for SVG icon generation |

### Configuration Requirements

| Requirement | Details |
|---|---|
| **Env Var** | `RECRAFT_API_KEY` -- API key from recraft.ai |
| **Account** | Recraft account with API access |
| **Cost** | $0.04-$0.30/image depending on quality and SVG complexity |
| **Alternative** | Also accessible via FAL.ai (FAL_KEY), so direct Recraft key is optional if FAL is configured |

### Availability Detection

The imagegen-bridge checks for the presence of the `RECRAFT_API_KEY` environment variable.

**Detection sequence:**
1. Check if `RECRAFT_API_KEY` environment variable is set and non-empty
2. If present, mark Recraft as available for direct SVG generation
3. Note: Recraft V4 is also accessible via FAL.ai, so if FAL_KEY is set, Recraft SVG capability is available even without RECRAFT_API_KEY

---

## 6. PptxGenJS

**Actor ID:** `sys-pptxgenjs`
**Type:** JavaScript library

### Description

Open-source PPTX generation library (v4.0.1, MIT). The rendering engine for assembling slides. Runs via Node.js in Claude Code. Supports slides, text, images, shapes, tables, charts, masters, speaker notes.

### Services That Use It

| Service | Relationship | Description |
|---|---|---|
| `assembly-pptx-build` (PPTX Build) | provides | PPTX file generation engine |

### Configuration Requirements

| Requirement | Details |
|---|---|
| **Runtime** | Node.js (available in Claude Code environment) |
| **Installation** | `npm install pptxgenjs` (v4.0.1) |
| **Env Vars** | None |
| **License** | MIT |

### Availability Detection

PptxGenJS is a npm package that is installed as a project dependency. It is always available when Node.js is available. No runtime discovery is needed -- the deck-assembler skill installs it as part of its execution if not already present.

---

## 7. Matplotlib

**Actor ID:** `sys-matplotlib`
**Type:** Python library

### Description

Python charting library for headless data visualisation at 300 DPI. Uses Agg backend (no display server needed). Styled via .mplstyle files for brand consistency.

### Services That Use It

| Service | Relationship | Description |
|---|---|---|
| `image-chart-renderer` (Chart Rendering) | provides | Chart rendering engine |

### Configuration Requirements

| Requirement | Details |
|---|---|
| **Runtime** | Python 3.x (available in Claude Code environment) |
| **Installation** | `pip install matplotlib seaborn` |
| **Backend** | Uses `Agg` backend for headless rendering (no display server required) |
| **Env Vars** | None |
| **Styling** | Custom `.mplstyle` files can enforce brand palette consistency |

### Availability Detection

Matplotlib is a pip package installed as a project dependency. It is always available when Python is available. No runtime discovery is needed -- the chart-renderer skill installs it as part of its execution if not already present.

---

## 8. Filesystem

**Actor ID:** `sys-filesystem`
**Type:** Local storage

### Description

Project-local `./tmp/deck/` directory for DeckContext state persistence. JSON files for contracts, image files for generated assets, .pptx for output. Per CONSTITUTION.md Article 4.6, uses `./tmp/` not `/tmp/`.

### Services That Use It

| Service | Relationship | Description |
|---|---|---|
| `deck-conductor` (Deck Conductor) | provides | State persistence for DeckContext |
| `assembly-pptx-build` (PPTX Build) | provides | Output directory for .pptx files |

### Configuration Requirements

| Requirement | Details |
|---|---|
| **Path** | `./tmp/deck/` (relative to project root) |
| **Git** | `./tmp/` is gitignored per CONSTITUTION.md Article 4.6 |
| **Env Vars** | None |
| **Permissions** | Read/write access to the project directory |

### Availability Detection

The filesystem is always available. The Deck Conductor creates the `./tmp/deck/` directory structure at pipeline startup if it does not already exist.

---

## 9. Speaker

**Actor ID:** `actor-speaker`
**Type:** Human actor

### Description

Primary user of the Jack-Tar Deckhand pipeline. Provides the talk brief, makes creative decisions, reviews output, and approves budget. The Speaker is the ultimate authority for all escalation decisions.

### Services That Use It

| Service | Relationship | Description |
|---|---|---|
| `deck-conductor` (Deck Conductor) | invokes | Initiates the pipeline by providing a TalkBrief |
| `design-brand-profile-management` (Brand Profile Management) | reviews-and-approves | Reviews extracted BrandProfile before pipeline continues |
| `presentation-engineering` (Presentation Engineering) | consumes | Receives the finished .pptx and review feedback |

### Availability Detection

The Speaker is always available as a human actor in the Claude Code conversation context. No runtime discovery is needed.

---

## Provider Discovery Summary

The imagegen-bridge performs provider discovery at the start of every pipeline run. The result is an `AvailableProviders` manifest that the Deck Conductor uses to plan image generation routing.

### Discovery Priority Order

| Priority | Provider | Detection | Cost | Best For |
|---|---|---|---|---|
| 1 | Ollama (local) | HTTP health check | Free | Fast iteration, backgrounds, patterns |
| 2 | FAL.ai | FAL_KEY env var | $0.01-$0.10 | FLUX.2 Pro, Recraft V4 SVG, Ideogram |
| 3 | OpenAI | OPENAI_API_KEY env var | $0.009-$0.133 | Highest quality, best text rendering |
| 4 | Google Vertex AI | GOOGLE_CLOUD_PROJECT env var | $0.02-$0.04 | Budget workhorse, backgrounds |
| 5 | Recraft (direct) | RECRAFT_API_KEY env var | $0.04-$0.30 | Native SVG icons (if FAL unavailable) |

### Graceful Degradation Chain

If no providers are available, the pipeline escalates to the Speaker. The degradation chain for any given image request is:

1. **Cloud preferred model** (e.g., GPT Image 1.5 for hero images)
2. **Cloud alternative** (e.g., Imagen 4 Fast for budget-constrained)
3. **Local Ollama** (free but lower quality)
4. **Placeholder** (coloured rectangle with alt text -- allows assembly to proceed)
5. **Escalate** (no providers available at all -- halt and notify Speaker)
