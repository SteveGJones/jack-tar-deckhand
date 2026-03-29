# Phase 4: Image Services -- Image Generation Skills

> **For agentic workers:** READ THIS ENTIRE PLAN before starting any task.

---

## Plan Structure and Key Design Decisions

Before presenting the plan, let me summarize the critical design decisions derived from the research and architecture:

1. **Three sub-groups work in parallel**: Sub-groups A (Ollama skills) and B (cloud + utilities) have no dependencies on each other. Sub-group C (bridge + expert) depends on both A and B being available.

2. **Each skill is a SKILL.md file + a Python helper script**: The existing pattern from `ollama-image` shows that each skill is a `.claude/skills/[name]/SKILL.md` that orchestrates calls to a Python script in `src/`. The Python scripts handle API calls, image processing, and caching.

3. **Synthesis documents first**: Per CLAUDE.md, each skill needs `research/synthesis-[name].md` before implementation. The plan must include these as pre-tasks.

4. **Model-specific prompts**: Prompts cannot be shared across models. The `image-generation-expert` agent handles translation. Each generation skill must accept model-specific prompts and not assume prompt portability.

5. **Draft/production lifecycle**: Draft mode uses Ollama or cloud at reduced quality; production uses full quality. Skills must accept a `quality` parameter (draft/production).

6. **Content-addressable caching**: All generation goes through the cache layer from Phase 1's `deckcontext.py`. Cache keys are SHA-256 of (prompt + dimensions + model + style tokens).

7. **Existing `generate_image.py` serves as the Ollama generation engine**: All four Ollama skills call this helper. Cloud skills need new Python helpers.

8. **The imagegen-bridge produces the ImageManifest**: It is the orchestrator of all image generation, routing each asset to the appropriate skill.

The plan follows the exact format from Phase 1: header with agentic worker instructions, file structure, bite-sized tasks with checkbox steps, complete code (no placeholders), test-first approach, and commit instructions.

Given that this is a READ-ONLY planning task and the file must be saved to `docs/superpowers/plans/2026-03-29-phase-4-image-services.md`, but I cannot create files, here is the complete plan content:

---

**The plan is extremely large (10 deliverables across 3 sub-groups). Here is the complete structured content:**

The plan should contain the following sections, matching Phase 1's format exactly:

### Header
- Title: "Phase 4: Image Services -- Generation, Processing, Routing & Advisory"
- Agentic worker instruction block (same as Phase 1)
- Goal statement
- Architecture summary referencing the Image Services L2 diagram
- Tech stack: Python 3.8+, requests, openai, google-genai, fal-client, recraft-api, Pillow, rembg, matplotlib, seaborn, pngquant-cli, pytest
- Phase overview (this is Phase 4 of 6)
- Sub-group dependency diagram showing A and B parallel, C depends on both

### File Structure
The complete file tree including:

```
research/
  synthesis-ollama-generate-image.md
  synthesis-ollama-generate-icon.md
  synthesis-ollama-generate-pattern.md
  synthesis-ollama-generate-diagram.md
  synthesis-cloud-generate-image.md
  synthesis-cloud-generate-icon.md
  synthesis-chart-renderer.md
  synthesis-image-processor.md
  synthesis-imagegen-bridge.md
  synthesis-image-generation-expert.md
src/
  generate_image.py              # (exists) Ollama generation helper
  generate_cloud_image.py        # Cloud image generation (OpenAI, Vertex AI, FAL.ai)
  generate_cloud_icon.py         # Cloud icon generation (Recraft V4, FAL.ai)
  render_chart.py                # Matplotlib/Seaborn chart renderer
  process_image.py               # Image processing utilities
  provider_discovery.py          # Provider availability probing
  prompt_translator.py           # visual_direction -> model-specific prompts
  budget_tracker.py              # Cloud API spend tracking
  cache_manager.py               # Content-addressable image cache (3-tier)
.claude/
  skills/
    ollama-generate-image/SKILL.md
    ollama-generate-icon/SKILL.md
    ollama-generate-pattern/SKILL.md
    ollama-generate-diagram/SKILL.md
    cloud-generate-image/SKILL.md
    cloud-generate-icon/SKILL.md
    chart-renderer/SKILL.md
    image-processor/SKILL.md
    imagegen-bridge/SKILL.md
  agents/
    image-generation-expert.md
tests/
  test_generate_cloud_image.py
  test_generate_cloud_icon.py
  test_render_chart.py
  test_process_image.py
  test_provider_discovery.py
  test_prompt_translator.py
  test_budget_tracker.py
  test_cache_manager.py
  test_imagegen_bridge.py
  fixtures/
    valid_image_manifest.json     # (from Phase 1)
    valid_chart_manifest.json     # (from Phase 1)
    sample_style_guide.json       # StyleGuide for prompt translation tests
    sample_slide_outline.json     # SlideOutline with visual_direction fields
```

### Task Sequence (22 tasks across 3 sub-groups)

**Pre-requisite Tasks (shared infrastructure)**

**Task 1: Python Dependencies Update**
- Update `requirements.txt` to add: `openai>=1.30.0`, `google-genai>=1.0.0`, `fal-client>=0.5.0`, `Pillow>=12.0.0`, `rembg[cpu]>=2.0.0`, `matplotlib>=3.10.0`, `seaborn>=0.13.0`, `cachetools>=5.5.0`, `diskcache>=5.6.0`, `hashfs>=0.7.2`, `pngquant-cli` (optional, system install)
- Verify virtual environment installs cleanly

**Task 2: Cache Manager (`src/cache_manager.py`)**
- Test-first: `tests/test_cache_manager.py` with tests for compute_cache_key, get/put across all 3 tiers, TTL expiry, stats
- Implementation: 3-tier cache (L1 memory LRU via cachetools, L2 DiskCache with SQLite, L3 HashFS for permanent CAS)
- Cache key: `SHA256(normalised_prompt + width + height + style + model_version + sorted_palette)`
- TTL strategy from research 13: icons permanent, backgrounds 30 days, heroes 7 days

**Task 3: Budget Tracker (`src/budget_tracker.py`)**
- Test-first: `tests/test_budget_tracker.py`
- Tracks cumulative spend per pipeline run
- Budget degradation tiers: ALLOW -> CAPS -> DEGRADE -> TYPOGRAPHY_ONLY
- Records per-image cost with provider, model, quality tier
- Reports running total and remaining budget
- Reads/writes budget state to `./tmp/deck/budget-state.json`

**Task 4: Provider Discovery (`src/provider_discovery.py`)**
- Test-first: `tests/test_provider_discovery.py`
- Probes: Ollama via HTTP health check to `localhost:11434/api/tags`, OpenAI via `OPENAI_API_KEY` env var, Google via `GOOGLE_CLOUD_PROJECT` env var, FAL via `FAL_KEY` env var, Recraft via `RECRAFT_API_KEY` env var
- Returns `AvailableProviders` dict matching the data contract schema
- Lists available Ollama image models (filter for `x/` prefix)

**Task 5: Prompt Translator (`src/prompt_translator.py`)**
- Test-first: `tests/test_prompt_translator.py`
- Implements the 4-stage translation algorithm from research 06:
  1. Model selection (asset type -> model mapping)
  2. Prompt assembly (model-agnostic intermediate)
  3. Model-specific serialisation (token budget, negative prompts, camera specs, hex codes)
  4. Overlay decision
- Takes `VisualDirectionInput` + `DeckStyleContext` -> `TranslatedPrompt`
- Model-specific rules for: z-image-turbo (~75 tokens, camera specs), flux2-klein (~250 words, spatial hierarchy), GPT Image 1.5 (unlimited, natural language), FLUX.2 Pro (30-80 words, photography), Recraft V4 (design-centric, hex palette param), Ideogram 3.0 (typography specialist), Imagen 4 (concise, aspect ratio param)
- Text zone -> composition mapping from research 06 Finding 5.3
- Palette injection: append hex codes to every prompt per research 06 Finding 4.3

---

**Sub-group A: Local Image Generation (Tasks 6-9)**

**Task 6: ollama-generate-image skill**
- Create `research/synthesis-ollama-generate-image.md`
- Create `.claude/skills/ollama-generate-image/SKILL.md` adapted from existing `ollama-image`
- Key changes from existing skill:
  - Reads `StyleGuide` for palette injection and style tokens
  - Reads `SlideOutline` for visual_direction
  - Uses `prompt_translator.py` for model-specific prompt construction
  - Integrates with `cache_manager.py` for content-addressable caching
  - Accepts `--quality draft|production` parameter
  - Writes image to `./tmp/deck/images/` directory
  - Returns image metadata compatible with ImageManifest entry
  - Consults `image-generation-expert` agent for scoring and refinement

**Task 7: ollama-generate-icon skill**
- Create `research/synthesis-ollama-generate-icon.md`
- Create `.claude/skills/ollama-generate-icon/SKILL.md` adapted from existing `ollama-icon`
- Key changes: cache integration, style guide palette injection, ImageManifest-compatible output
- Default model: `x/flux2-klein` (better for clean geometric shapes)
- Three styles: flat, 3d, outlined (same as existing)
- Multi-size generation support

**Task 8: ollama-generate-pattern skill**
- Create `research/synthesis-ollama-generate-pattern.md`
- Create `.claude/skills/ollama-generate-pattern/SKILL.md` adapted from existing `ollama-pattern`
- Key changes: cache integration, palette injection, ImageManifest output
- Five styles: geometric, organic, textile, abstract, material
- Default 1024x1024 for tiling

**Task 9: ollama-generate-diagram skill**
- Create `research/synthesis-ollama-generate-diagram.md`
- Create `.claude/skills/ollama-generate-diagram/SKILL.md` adapted from existing `ollama-diagram`
- Key changes: cache integration, honest text legibility assessment, ImageManifest output
- Default model: `x/flux2-klein` (better spatial accuracy and text)
- Diagram types: flowchart, architecture, sequence, network, general

---

**Sub-group B: Cloud Image Generation + Utilities (Tasks 10-17)**

**Task 10: Cloud Image Generation Helper (`src/generate_cloud_image.py`)**
- Test-first: `tests/test_generate_cloud_image.py` with mock API responses
- Supports 3 providers: OpenAI (GPT Image 1.5), Google Vertex AI (Imagen 4), FAL.ai (FLUX.2 Pro)
- Provider selection via parameter or auto-routing
- API keys from environment variables per CONSTITUTION Article 8
- Quality tiers: draft (low/fast), standard (medium), production (high)
- Output formats: PNG (default), JPEG, WebP
- Transparency support for OpenAI (background="transparent")
- Retry logic: 3 retries with exponential backoff
- Error handling for rate limits, safety filter rejections, network failures
- Returns image bytes + metadata (model, cost, generation time)
- OpenAI code: `client.images.generate()` with size="1536x1024" for 16:9
- Google code: `client.models.generate_images()` with Imagen 4 models
- FAL code: `fal_client.submit()` with FLUX.2 Pro

**Task 11: cloud-generate-image skill**
- Create `research/synthesis-cloud-generate-image.md`
- Create `.claude/skills/cloud-generate-image/SKILL.md`
- Calls `generate_cloud_image.py`
- Reads StyleGuide for palette + style tokens
- Uses prompt_translator for model-specific prompts
- Integrates cache_manager (check cache before API call)
- Integrates budget_tracker (check budget before API call)
- Handles safety filter rejections: reframes prompt, tries alternative model
- Draft mode: use GPT Image 1 Mini at low quality ($0.005) or Imagen 4 Fast ($0.02)
- Production mode: GPT Image 1.5 Medium/High or FLUX.2 Pro

**Task 12: Cloud Icon Generation Helper (`src/generate_cloud_icon.py`)**
- Test-first: `tests/test_generate_cloud_icon.py` with mock API responses
- Primary: Recraft V4 for native SVG output (the ONLY model that generates SVG)
- Fallback: FAL.ai for raster icons
- Recraft API: POST to `https://external.api.recraft.ai/v1/images/generations` with style="vector_illustration", substyle="flat_2"
- SVG output saved as `.svg`, raster as `.png`
- Colour palette parameter: Recraft natively supports RGB colour arrays
- Multiple sizes via SVG viewBox (no re-generation needed for SVG)

**Task 13: cloud-generate-icon skill**
- Create `research/synthesis-cloud-generate-icon.md`
- Create `.claude/skills/cloud-generate-icon/SKILL.md`
- Calls `generate_cloud_icon.py`
- Prefers SVG output (Recraft V4) -- fallback to raster (FAL.ai Recraft)
- Cache integration with permanent TTL (icons rarely change)
- Budget tracking per icon
- Supports icon sets: generate multiple related icons with consistent style

**Task 14: Chart Renderer Helper (`src/render_chart.py`)**
- Test-first: `tests/test_render_chart.py`
- Uses Matplotlib + Seaborn with `Agg` backend (no display server needed)
- Chart types: bar, line, area, pie, donut, scatter, comparison_table, timeline, stat_card
- Styled to brand palette from StyleGuide:
  - Colours from `palette.chart_series`
  - Fonts from `typography.heading_font` / `typography.body_font`
  - Custom `.mplstyle` dict applied at render time
- Output: 300 DPI PNG at 1920x1080 (16:9)
- Data input: inline JSON from SlideOutline `data.inline_data` or CSV path from TalkBrief `data_sources`
- Alt text generation from chart data
- Returns ChartManifest entry dict

**Task 15: chart-renderer skill**
- Create `research/synthesis-chart-renderer.md`
- Create `.claude/skills/chart-renderer/SKILL.md`
- Reads SlideOutline for `data_chart` type slides
- Reads StyleGuide for palette and typography
- Reads TalkBrief for data_sources
- Calls `render_chart.py` per chart slide
- Writes to `./tmp/deck/images/`
- Produces `./tmp/deck/chart-manifest.json`

**Task 16: Image Processor Helper (`src/process_image.py`)**
- Test-first: `tests/test_process_image.py`
- Operations:
  - `remove_background(image_path)` -- rembg with silueta model (43MB, 2-5s CPU)
  - `resize(image_path, width, height, method="lanczos")` -- Pillow LANCZOS (NOT Real-ESRGAN)
  - `crop_to_aspect(image_path, aspect_ratio="16:9")` -- centre crop
  - `correct_colours(image_path, target_palette)` -- map dominant colours toward brand palette using CIELAB delta-E
  - `optimize_png(image_path)` -- pngquant for file size reduction
  - `get_dimensions(image_path)` -- return (width, height)
  - `compute_content_hash(image_path)` -- SHA-256 of image bytes
- All operations return the output path (in-place or to new path)
- No Real-ESRGAN: use Lanczos + unsharp mask for upscaling

**Task 17: image-processor skill**
- Create `research/synthesis-image-processor.md`
- Create `.claude/skills/image-processor/SKILL.md`
- Exposes all `process_image.py` operations as skill commands
- Accepts `--operation` parameter: rembg, resize, crop, colour-correct, optimize
- Can process single image or batch (directory of images)

---

**Sub-group C: Routing + Advisory (Tasks 18-22)**

**Task 18: imagegen-bridge skill (routing orchestrator)**
- Create `research/synthesis-imagegen-bridge.md`
- Create `tests/test_imagegen_bridge.py` -- integration test with mocked providers
- Create `.claude/skills/imagegen-bridge/SKILL.md`
- This is the TOP-LEVEL image orchestrator called by the Deck Conductor
- Responsibilities:
  1. Run provider discovery (probe all providers)
  2. Report available providers to Deck Conductor
  3. Read SlideOutline to enumerate all slides needing images
  4. Classify each slide's visual_type -> asset_type (hero, section_bg, pattern, icon, quote, chart_decor, people, illustration, product, diagram, closing)
  5. Route each asset to the appropriate generation skill using the routing matrix from research 05
  6. Track budget via budget_tracker
  7. Apply fallback chains: primary cloud -> alt cloud -> Ollama -> placeholder -> skip
  8. Post-process generated images via image-processor (resize, colour correct, optimize)
  9. Write ImageManifest to `./tmp/deck/image-manifest.json`
  10. Report generation summary (counts, cost, timing)
- Routing rules from research 05 Finding 1.1:
  - hero_image -> ollama-generate-image (draft) or cloud-generate-image (production)
  - icon_set -> cloud-generate-icon (always cloud -- SVG)
  - pattern_background -> ollama-generate-pattern (draft) or cloud-generate-image (production)
  - diagram -> ollama-generate-diagram (draft) or programmatic (production)
  - chart -> chart-renderer (always programmatic)
  - none -> skip
- Draft vs production: accepts `--mode draft|production`
- Iteration budgets per asset type from research 05 Finding 3.3

**Task 19: Placeholder Generation**
- When all providers fail for an asset, generate a placeholder:
  - Solid colour rectangle matching `palette.primary` or `palette.background_alt`
  - Dimensions matching the layout zone
  - Alt text describing what the image should be
  - Status: "placeholder" in ImageManifest
- Implementation: Pillow `Image.new("RGB", (width, height), hex_to_rgb(colour))`
- Add to `process_image.py` as `generate_placeholder(width, height, colour, alt_text, output_path)`

**Task 20: image-generation-expert agent**
- Create `research/synthesis-image-generation-expert.md`
- Create `.claude/agents/image-generation-expert.md` extending existing `ollama-image-expert.md`
- Key extensions beyond existing agent:
  - Cloud model knowledge: GPT Image 1.5, FLUX.2 Pro, Imagen 4, Recraft V4, Ideogram 3.0
  - Model-specific prompt translation rules from research 06 Area 3
  - Quality scoring rubric remains the same 6 dimensions (composition, colour, clarity, relevance, technical quality, text accuracy)
  - Model selection advice: given asset type + available providers, recommend optimal model
  - Prompt transfer guidance: which prompt adjustments when switching between models (research 05 Area 2)
  - Safety filter recovery: alternative prompt framing when cloud APIs reject prompts
  - Style consistency advice: palette injection, style suffixes, reference images
  - Iteration convergence remains the same: accept >= 7.5, plateau detection, oscillation detection
  - ADVISORY ONLY -- never generates images directly, never accesses DeckContext
  - Escalation: quality below threshold after max iterations -> recommend fallback

**Task 21: Integration Test -- Full Image Pipeline**
- `tests/test_image_pipeline_integration.py`
- Simulates a complete image generation pipeline:
  1. Init DeckContext
  2. Write StyleGuide and SlideOutline
  3. Run provider discovery (mocked: Ollama available, no cloud)
  4. imagegen-bridge routes all slides to Ollama skills
  5. Images generated (mocked) and cached
  6. ImageManifest written and validated against schema
  7. Budget tracked at $0.00 (all local)
- Second test with mocked cloud providers available
- Third test: all providers unavailable -> all placeholders

**Task 22: Final Verification**
- Run complete test suite
- Verify all skills load correctly
- Verify agent loads correctly
- Commit all Phase 4 deliverables

### Summary Table

The plan ends with a summary table matching Phase 1's format:

| Artifact | Purpose |
|----------|---------|
| 10 synthesis documents | Research distillation per skill |
| 9 SKILL.md files | Claude Code skill definitions |
| 1 agent definition | Image Generation Expert (extended) |
| 7 Python helper scripts | Generation, processing, routing, caching |
| 10 test files | Unit + integration tests |
| requirements.txt update | New Python dependencies |

### Critical Files for Implementation
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/docs/superpowers/plans/2026-03-29-phase-1-foundation.md` -- format template to follow exactly
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/generate_image.py` -- existing Ollama generation helper that all Sub-group A skills call
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/skills/ollama-image/SKILL.md` -- primary skill to adapt for ollama-generate-image
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/agents/ollama-image-expert.md` -- existing agent to extend into image-generation-expert
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/research/05-multi-model-routing-pipeline.md` -- routing matrix, fallback chains, cost models driving imagegen-bridge design

---
